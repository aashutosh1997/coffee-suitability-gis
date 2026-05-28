# Phase 0 — Terrain-Shading Architecture Spike

**Date:** 2026-05-28 · **Owning hat:** GIS Specialist / Geospatial Data Scientist
**Goal:** de-risk the heaviest geoprocessing step — terrain shading over a polygon — and
decide it can meet the **polygon < 60 s** target (NFR-1) on the async path (NFR-3).

## What the spike does

`backend/geo/spike_terrain.py` runs the full terrain pipeline over an AOI polygon and
times each step:

1. **read + clip** the DEM to the AOI (`rasterio.mask`, AOI reprojected to the DEM CRS).
2. **slope + aspect** (NumPy gradient / Horn-style; metric pixel spacing — see note).
3. **hillshade** (NumPy).
4. **sky-view factor** — multi-direction horizon scan (the expensive step).
5. **insolation** — clear-sky GHI (pvlib) projected by incidence angle.
6. **zonal statistics** over the clipped arrays.

Run it:

```bash
cd backend
uv run --extra geo python -m geo.spike_terrain \
  tests/fixtures/dem/nepal_aoi_clip_glo30.tif \
  tests/fixtures/aoi/gulmi_test_polygon.geojson --repeat 3
```

## Result (committed Gulmi fixture, 60×60 clipped cells, median of 3)

| Step | Seconds |
|------|---------|
| read + clip | 0.003 |
| slope + aspect | 0.000 |
| hillshade | 0.000 |
| sky_view_factor | 0.016 |
| insolation | 0.009 |
| zonal_stats | 0.000 |
| **TOTAL** | **~0.03** |

Sanity of outputs on the fixture: elevation 900–1719 m, slope ≥ 0 %, aspect 0–360°,
SVF in [0, 1]. **Verdict: WITHIN the 60 s budget** by a wide margin at fixture scale.

> The fixture is a small (~50 KB) synthetic ~30 m DEM over a Gulmi AOI so the spike runs
> offline (see `backend/tests/fixtures/README.md`). It validates the *pipeline shape and
> per-step cost ordering*, not absolute production timing.

## Library decisions (and why)

| Step | Phase 0 choice | Production option to revisit | Rationale |
|------|----------------|------------------------------|-----------|
| slope/aspect | NumPy gradient | richdem / `gdaldem` / WhiteboxTools | NumPy needs no compiled dep and is fast enough; `slope_aspect_richdem()` is wired for a benchmark where richdem installs cleanly. |
| sky-view factor | NumPy horizon scan | WhiteboxTools | Good enough to prove cost; WhiteboxTools is the accurate production engine. |
| insolation | pvlib clear-sky + incidence | **GRASS `r.sun`** (Phase 2) | pvlib is pure-Python and light; r.sun gives true terrain-shaded/cast-shadow insolation — the Phase 2 upgrade. |
| zonal stats | NumPy reduce | **exactextract** | exactextract handles fractional pixel coverage at polygon edges — more accurate for small terraced plots than all-or-nothing rasterstats. |

`richdem`, `WhiteboxTools`, and `exactextract` are deliberately **out of the `[geo]`
extra** (they need C/C++ compilation and are flaky via wheels); the spike uses them only
if importable, else the NumPy path. This keeps `uv sync --extra geo` and CI reliable.

## Scaling note — the real concern for Phase 1/2

SVF is `O(rows · cols · directions · radius)` and dominates. A real co-op polygon at 30 m
can be 10³–10⁴× more cells than the fixture. Mitigations already designed in:

- The polygon path is **async (Celery)** — it never blocks the API (NFR-3), so wall-clock
  matters for UX, not for request timeouts.
- DEMs are **pre-ingested as COGs** (doc 04) — windowed reads, no per-request fetch.
- Reproject to **UTM 45N (EPSG:32645)** once at ingest so slope math uses true metres
  (the spike converts degrees→metres at the AOI latitude as a stand-in).
- If SVF becomes the bottleneck at scale, move it to WhiteboxTools / `r.sun` and/or
  precompute terrain derivatives per region at ingest rather than per assessment.

**Go/no-go:** GO. The pipeline is correct and the cost order is understood; the < 60 s
target is achievable on the async path with pre-ingested COGs. Re-benchmark on a
real Copernicus GLO-30 clip and a representative plot early in Phase 1.
