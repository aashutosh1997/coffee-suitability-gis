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

## Phase 2 additions (Climate & Shading)

| ID | Risk | Likelihood | Impact | Mitigation | Owner (role) |
|----|------|:----------:|:------:|------------|--------------|
| **R-SVFPERF** | Sky-view factor is O(rows·cols·dirs·radius) — the heaviest terrain step; on the synchronous point path it could blow the < 5 s budget (NFR-1). | M | M | Point shading uses a capped 11x11 window + `max_radius=5` (milliseconds); the full-array SVF runs only in the async polygon worker; a < 5 s point timing test guards it. | GIS Specialist |
| **R-CHELSCALE** | CHELSA stores temperature/precip scaled (e.g. K×10 or °C×0.1 with an offset); a wrong transform silently scores nonsense. | M | H | `fetch_climate` normalizes to plain °C/mm at ingest and a loud range-assert fails the ingest on out-of-range values; the synthetic fixture is already in native units. | Data Engineer |
| **R-FROSTFP** | Frost-pocket is a categorical **hard limit forcing class N**; a false positive wrongly condemns a viable plot. | M | H | Conservative 3-signal AND gate (TPI + flat slope + cool altitude) for points and a ≥10% cell fraction for polygons; documented Phase-2 heuristic with tunable thresholds, flagged for agronomist / Phase-3 validation; flags a site for review rather than failing silently. | Agronomist |
| **R-CLIMRES** | ~1 km climate vs ~30 m DEM — a coarse climate cell can hide the microclimate the terrain shows (extends R-CLIM). | H | M | Climate sampled at the AOI point / polygon centroid; explicit resolution-mismatch `uncertainty_notes` entry + per-factor `resolution` provenance in the UI (FR-15); ADR-0007 records the trade-off. | GIS Specialist |
| **R-MONTHLY** | The rainfall-distribution modifier needs 12-band monthly normals; if that dataset is missing the even-flowering bonus silently never applies. | L | M | `monthly_precip` is optional to `assess_factors`; the engine passes `None` and skips the modifier (precip still scored on the annual total); the synthetic 12-band fixture exercises the bonus path in CI. | Data Engineer |
| **R-RECENTAPI** | NASA POWER / Open-Meteo may be unreachable (offline/CI, rate limits, outage). | M | L | A separate non-scoring endpoint with a short timeout and two-tier fallback to graceful nulls + a note; never imported by the scoring/engine path, so assessments are unaffected; the UI shows an "unavailable" state. | Backend Engineer |

## Phase 3 additions (Refinement & Validation)

| ID | Risk | Likelihood | Impact | Mitigation | Owner (role) |
|----|------|:----------:|:------:|------------|--------------|
| **R-OVERFIT** | The validation set is small (≥30–50 plots) and the same set is used to diagnose and to re-validate — tuning the config to it risks **overfitting** and inflating the agreement %. | H | H | Hold out a portion of plots where size allows ([ground-truth-plan §4.7](ground-truth-plan.md)); cap the number of tuning rounds per real-data delivery; require the change to be **agronomically motivated**, not just metric-chasing; every change ships as a new config version (NFR-16) so any regression is traceable and reversible. | Agronomist |
| **R-SYNTH** | The Phase-3 slice ran the harness against a **synthetic** plot set; an agreement % from synthetic data could be mistaken for real model accuracy. | M | H | Synthetic CSV header, generated reports, and the curated [validation report](../phase-3/validation-report.md) all carry an explicit "SYNTHETIC — not an accuracy claim" warning; the ≥80% gate (doc 01) is documented as openable **only** with real co-op data. | Delivery/PM |
| **R-MAPPING** | The predicted-class → observed-status mapping (S1\|S2→thriving, S3→struggling, N→failed) is itself a modeling choice; a different mapping changes the agreement metric. | M | M | The mapping is **recorded in every report** alongside the matrix so the metric is reproducible and reviewable; treated as an agronomist decision to confirm at sign-off ([ground-truth-plan §4.2](ground-truth-plan.md)). | Agronomist |
| **R-S3GAP** | The 2026.1 weighted overlay never returned the S3 ("marginally suitable") class — sites either cleared the bands (S1/S2) or hit a hard limit (N), masking marginal sites as binary thrive-or-fail. | H | M | Surfaced by the first validation run; addressed in 2026.2 by widening the S3 threshold band (S2 floor 0.60→0.70, S3 floor 0.40→0.50) — purely on model-shape grounds, not fitted to synthetic labels. The validation report quantifies the before/after. | GIS Specialist |
| **R-CLIMSYNTH** | DEM-derived synthetic climate cannot encode real stressors (management, irregular rainfall, microclimate); validating against it under-detects climate-driven disagreements. | L | M | **Resolved 2026-05-30**: real CHELSA V2.1 (ADR-0007) now ingested via `fetch_chelsa.py` and seeded into MinIO/provenance; the synthetic generator is retained ONLY as the offline/CI fallback (R-NET). The first CHELSA re-run is captured in `docs/phase-3/validation-report.md` §6 and immediately surfaced precipitation as a real limiting factor on 6 Gulmi plots — exactly the climate signal the synthetic could not produce. | Data Engineer |
| **R-OVLPERF** | A busy overlay panel issues a tile request per layer per pan/zoom; without a cache TiTiler can spike under concurrent users. | M | L | Overlays are opt-in (start off); the pilot bbox is small; same-host TiTiler+MinIO keeps per-tile latency sub-100 ms. CDN/edge-cache deferred to Phase 4 per [ADR-0008](../adr/0008-titiler-raster-overlays.md). | DevOps/Platform |
| **R-OVLCMAP** | A wrong colormap or rescale silently mis-reads the raster — e.g. a 0–800 mm/month gradient stretched to 0–4000 makes wet sites look dry. | L | M | Colormap + rescale are server-side authority in `app/api/overlays.py:_REGISTRY`; the legend in the UI reads the same values from `/overlays` so render and legend cannot drift. Provenance badge on every layer surfaces the data source the user is looking at. | GIS Specialist |

## Demo-deployment additions (GCP single-VM, [ADR-0009](../adr/0009-gcp-single-vm-demo-deployment.md))

| ID | Risk | Likelihood | Impact | Mitigation | Owner (role) |
|----|------|:----------:|:------:|------------|--------------|
| **R-VMSPILL** | e2-small (2 GB RAM) could OOM during a heavy polygon assessment — rasterio loading multi-band stacks can spike to >1 GB. | M | L | 4 GB swap file provisioned in `infra/gcp/startup.sh` with `vm.swappiness=10`; resize to e2-medium is one `gcloud compute instances stop && set-machine-type && start` cycle (+~$13/mo). The async polygon worker keeps the heavy path off the synchronous API. | DevOps/Platform |
| **R-LELIMIT** | If Caddy restart-loops the deploy could trip Let's Encrypt rate limits (5 duplicate certs/week per domain), locking out new certs for ~1 week. | L | L | Caddy's built-in exponential backoff + the `caddy_data` named volume mean one cert is issued per domain and reused across restarts; only a misconfigured Caddyfile or DEPLOY_HOSTNAME change in a tight loop would trigger this. | DevOps/Platform |
| **R-COSTDRIFT** | The easiest way to burn through the $300 credit is to leave the VM running idle while nobody is demoing. Always-on e2-small is ~$0.59/day. | M | L | `make vm-stop` from the laptop drops compute charges ~95% (~$0.10/day for disk+snapshot only); GCP budget alerts at 17/33/67/97% of $300 documented in `infra/gcp/README.md`. | Delivery/PM |
| **R-IPDRIFT** | The VM uses an **ephemeral** external IP; `make vm-stop` then `vm-start` can hand out a new IP, breaking the domain's A record until updated. | M | L | `make vm-start` prints the (possibly new) IP with an "update your A record" reminder; a reserved static IP would fix it but costs $1.46/mo while VM is stopped — not worth it for a demo. DNS TTL recommended at 300 s. | DevOps/Platform |
| **R-PINSTALE** | Pinned image tags for MinIO + TiTiler (per ADR-0009) miss security fixes silently if never re-pinned. | M | L | Runbook documents the re-pin procedure; quarterly check before any new demo. The api+worker images are built from source on each `make deploy`. | DevOps/Platform |
