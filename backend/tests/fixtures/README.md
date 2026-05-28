# Test fixtures

Small, committed fixtures so the terrain spike and COG-conversion tests run **fully
offline** (CI and dev without network). Large rasters are never committed — they live in
MinIO/object storage (see root `.gitignore`, which allows only `tests/fixtures/**/*.tif`).

## `dem/nepal_aoi_clip_glo30.tif`

A **synthetic** ~30 m elevation surface (~50 KB COG, EPSG:4326) over a Gulmi (Nepal
mid-hills) AOI. It is deliberately synthetic — NOT real Copernicus data — so tests need no
download. Regenerate reproducibly (seeded):

```bash
cd backend
uv run --extra geo python ../scripts/make_fixture_dem.py
```

The real ingestion path that fetches and clips **actual Copernicus GLO-30** (ADR-0006)
lives in `data-pipelines/ingest/` (`fetch_dem.py` → `reproject_clip_cog.py`), with an
automatic fixture fallback when offline.

## `aoi/gulmi_test_polygon.geojson`

A tiny AOI polygon (~3 km box) inside the DEM extent, used to exercise clip + zonal stats.

> When a real clipped DEM replaces the synthetic one, keep it small (a few hundred KB) and
> record the exact `gdalwarp` / `rio cogeo` command that produced it here, for provenance.
