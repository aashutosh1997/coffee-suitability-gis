# Phase 0 — Risk Register

*Owner: Delivery / Project Manager. Status: in progress (Phase 0).*

Risks tracked for the Nepal mid-hills pilot. **Likelihood** and **Impact** are rated
**L / M / H**. Owner is a **role hat** (per [doc 08](../08-team-and-roles.md)), not a named
person.

| ID | Risk | Likelihood | Impact | Mitigation | Owner (role) |
|----|------|:----------:|:------:|------------|--------------|
| **R-DEM** | ~30 m global DEM **smooths small terraced plots** common in the Nepal mid-hills, blurring slope/aspect and altitude on narrow terraces. | H | H | Data spike (WS3) evaluates best available regional/higher-res DEM vs. real plot sizes (Q1); surface uncertainty in the UI; allow agronomist override; flag plots below a resolution threshold. | GIS Specialist |
| **R-CLIM** | Gridded **~1 km climate misses microclimate** — frost pockets, valley fog, cold-air drainage in the hills — so a "suitable" grid cell can hide a frost-prone plot. | H | H | Terrain analysis (shading, frost-pocket detection, cold-air-drainage cues) partially compensates; mandatory expert review; clear "microclimate not captured" caveat on results. | GIS Specialist |
| **R-MISUSE** | **"Suitability ≠ profitability"** — users read a biophysical score as an investment/purchase recommendation. | M | H | Explicit non-goal in the [charter](discovery-charter.md) & [doc 01](../01-vision-and-scope.md); in-product disclaimer; training frames the tool as triage, not financial advice. | Product Owner |
| **R-GT** | **Ground-truth dataset availability gates Phase 3** validation; if known-plot data is thin or late, the ≥80% accuracy target can't be measured. | M | H | Start assembling the validation set **in Phase 0** (WS7); agronomist owns collection; track set size weekly; size Phase 3 against actual readiness. | Agronomist |
| **R-NUMPY** | **numpy 2.x vs. geospatial-stack compatibility** — rasterio/GDAL/shapely/scipy pins may conflict with numpy 2.x and break builds. | M | M | Pin a known-good resolved set in Phase 0 (WS5); CI guards the lockfile; isolate via containers; document the working matrix. | DevOps/Platform |
| **R-NET** | **Network-limited data downloads in dev/CI** — large DEM/climate fetches are slow/flaky, stalling local dev and CI. | M | M | **Mitigated by committed fixtures + a fallback path**: small clipped sample tiles committed for the pilot box; tests/CI run offline against fixtures; full downloads cached/optional. | Data Engineer |
| **R-GDAL** | **GDAL / rasterio build fragility** — native geospatial libs are notoriously hard to build/version across machines. | M | M | Standardize on prebuilt container images with GDAL baked in (WS5); no host-level GDAL builds; pin image digests; document the dev-env path ([doc 09](../09-development-setup.md)). | DevOps/Platform |
| **R-HW** | **On-prem hardware sizing** uncertain — CPU/RAM/disk (and GPU) for the co-op's servers may not meet the concurrency/perf targets. | M | M | Open question Q3 to the co-op; size against the ~50-concurrent design target; load test in Phase 4; containerized so cloud is a fallback ([doc 07](../07-roadmap-and-phases.md) Phase 5). | DevOps/Platform |
| **R-AGRO** | **Agronomist availability** — the agronomist is on the **critical path for the model** (thresholds, ground truth, validation sign-off); limited availability blocks Phases 0/2/3. | M | H | Secure committed (even part-time) agronomist time up front; front-load the workshop (WS2); the lean-team note in [doc 08](../08-team-and-roles.md) makes this role non-negotiable. | Delivery/PM |
| **R-PERF** | **Polygon < 60 s NFR feasibility** is uncertain — terrain shading over a polygon is the heaviest step and may exceed the target on realistic plots/hardware. | M | M | **Depends on the terrain-shading spike (WS4) outcome**; if at risk, fall back to async job + tiling/precompute, cap polygon size, or relax the band; decision recorded at the Phase 0 exit gate. | GIS Specialist |

## How risks are reviewed

Risks are reviewed **every phase** as a cross-cutting activity (per
[doc 07](../07-roadmap-and-phases.md)). In Phase 0 they are revisited at the weekly demo
and formally re-scored at the W4 exit gate; thereafter the register is reviewed at each
phase boundary, with new risks added, closed risks retired, and likelihood/impact
re-rated as spikes and validation produce evidence. The Delivery/PM owns the register;
each risk's role owner drives its mitigation.

## Phase 1 additions (Core Geospatial MVP)

| ID | Risk | Likelihood | Impact | Mitigation | Owner (role) |
|----|------|:----------:|:------:|------------|--------------|
| **R-VSIS3** | GDAL `/vsis3` MinIO config is fiddly (path-style vs virtual-host, http vs https, endpoint scheme) — easy to get a silent 403/404 on COG open. | M | M | `cog_reader` builds the env from settings (scheme stripped, `AWS_VIRTUAL_HOSTING=FALSE`, `AWS_HTTPS=NO`), mirroring the TiTiler service; a local-file fallback keeps dev/CI independent of MinIO. | DevOps/Platform |
| **R-PTSLOPE** | A point has no neighbours, so slope/aspect would be meaningless from a single pixel. | M | M | `sample_point` reads a 3x3 window and derives slope on the neighbourhood, taking the centre; edge pixels degrade gracefully. | GIS Specialist |
| **R-GEOIMG** | Moving the geo stack into the slim api/worker image could break if any wheel lacks a manylinux build. | L | M | rasterio/geopandas ship manylinux wheels (bundled GDAL); CI `docker-build` smoke-builds the image; documented fallback is the `ghcr.io/osgeo/gdal` base. | DevOps/Platform |
| **R-TILEDL** | Copernicus GLO-30 tiles (~30-50 MB each, up to ~6 for the pilot) are slow or blocked. | M | L | Seed only district-intersecting tiles; per-tile automatic fixture fallback; real fetch never runs in CI. | Data Engineer |
| **R-POLYMEAN** | Polygon scored on the zonal mean hides intra-plot variation (a half-optimal/half-unsuitable plot averages to "good"). | H | M | Accepted for the MVP and flagged in `uncertainty_notes`; per-pixel class distribution is the Phase 2/3 upgrade. | GIS Specialist |
| **R-EXTENT** | If seeding registers provenance without a real `extent`, the AOI->DEM `ST_Intersects` lookup returns nothing and every assessment 422s. | M | H | `seed_pilot` computes `extent_wkt` from the produced COG bounds (reprojected to 4326) and always registers it; verified by the seed flow. | Data Engineer |
