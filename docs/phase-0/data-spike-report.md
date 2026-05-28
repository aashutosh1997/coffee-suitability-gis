# Phase 0 — Data Spike Report: DEM & Climate Dataset Selection

**Date:** 2026-05-28
**Phase:** 0 — Discovery & Foundations
**Pilot region:** Nepal mid-hills — Gulmi, Syangja, Kavre (~27–28°N), steep terraced subtropical highland
**Owning hat:** GIS Specialist / Geospatial Data Scientist
**Decisions recorded in:** [ADR-0006](../adr/0006-dem-copernicus-glo30.md) (DEM), [ADR-0007](../adr/0007-climate-chelsa-plus-point-apis.md) (climate)

---

## 1. Objective

[`docs/06-data-sources.md`](../06-data-sources.md) lists candidate elevation and climate sources
and explicitly defers the final pick to "the Phase 0 data spike — verify the current terms of
each before relying on it, and record the decision in an ADR." This report does that for the
**pilot region**: evaluate the candidate DEMs and climate datasets against **Nepal mid-hills
realities** — steep, dissected, heavily terraced terrain at ~28°N with a strong monsoon — and
recommend a baseline stack.

The DEM drives **altitude, slope, aspect, terrain shading/insolation, and the frost-pocket
cold-air-drainage check**. Climate normals drive the **temperature and precipitation** factors
and the **rainfall-distribution modifier** (monthly normals). Point-weather APIs supply
**recent/observed** conditions (FR-8).

## 2. DEM comparison

All four candidates are ~30 m, global, and open. The differentiators for *this* terrain are
**void/artifact behavior on steep slopes**, **latitude coverage** (28°N is well within all of
them, but worth confirming), and **licensing**.

| DEM | Native res. | Void / artifact behavior in steep terrain | Latitude coverage | Access / licensing |
|-----|-------------|-------------------------------------------|-------------------|--------------------|
| **Copernicus DEM GLO-30** | ~30 m (1 arc-sec) | Modern, edited/hydro-conditioned; **fewest voids**, well-behaved on steep slopes; based on TanDEM-X radar | Global (−90 to +90) | Free, open; via Copernicus / AWS Open Data / OpenTopography |
| **SRTM (v3 / 1 arc-sec)** | ~30 m | Mature & well-documented, but classic **radar voids/spikes in steep, shadowed mountain terrain** — a real concern in the dissected mid-hills | **60°N–56°S** (covers 28°N fine, but not polar) | Free, open (NASA/USGS) |
| **NASADEM** | ~30 m | **Reprocessed SRTM with improved void-filling** and better registration; clear upgrade over raw SRTM | Same as SRTM (60°N–56°S) | Free, open (NASA/USGS) |
| **ASTER GDEM (v3)** | ~30 m | **Widest latitude coverage but noisiest**; optical-stereo artifacts (cloud/striping), needs more cleanup | Global incl. high latitudes | Free, open (NASA/METI) |

### 2.1 DEM recommendation: **Copernicus DEM GLO-30**

- **Best void behavior in steep terrain.** The mid-hills are exactly where SRTM's radar voids and
  ASTER's optical noise hurt — and where clean slope/aspect/shading derivatives matter most for
  our model. GLO-30's edited, hydro-conditioned surface is the most reliable starting point.
- **Global, modern, open**, no latitude gap at 28°N, and easy programmatic access (AWS Open Data /
  OpenTopography) that fits the ingestion pipeline (doc 06: fetch → reproject/clip → COG → PostGIS).
- NASADEM is a strong **fallback / cross-check** (and useful if a specific GLO-30 tile shows an
  artifact); raw SRTM and ASTER are not recommended as the primary for this terrain.

### 2.2 ~30 m terrace-smoothing caveat

At ~30 m a single pixel can span several narrow bench terraces, so the DEM **smooths terraced
microtopography** (doc 06 caveat; doc 03 `uncertainty_notes` example). Implications:

- **Slope** on small terraced plots is **underestimated/averaged** — the model may read a
  hillside as gentler than the lived terrace structure.
- **Altitude** at a point is fine for the band lookup, but polygon altitude statistics are
  smoothed.
- **Mitigation now:** surface this in every assessment's `uncertainty_notes` (FR-15 provenance,
  doc 03 contract) so agronomists can weight the result accordingly, and lean on expert override
  (FR-17) for borderline terraced plots.
- **Mitigation later:** evaluate **national/regional LiDAR or finer DEMs** for the operating area
  if the co-op needs true terrace-scale terrain (doc 06 explicitly flags this as a later option).
  Out of scope for the Phase 0 minimal slice.

## 3. Climate comparison

### 3.1 Long-term normals (baseline suitability)

| Source | Res. | Behavior in complex terrain | Variables we need | Access / licensing |
|--------|------|-----------------------------|-------------------|--------------------|
| **WorldClim v2.1** | ~1 km | Common default; good globally, but interpolation can be **weaker in steep, sparsely-stationed mountains** | Monthly + annual temp & precip, bioclim | Free for academic/non-commercial; **verify terms for an internal co-op tool** |
| **CHELSA** | ~1 km | **Built for complex/mountainous terrain** — orographic/wind correction of precipitation and lapse-rate-aware temperature; generally better in the Himalaya foothills | Monthly + annual temp & precip, bioclim | Free, open |

#### Climate-normals recommendation: **CHELSA**

The pilot region is **complex mountain terrain with a monsoon precipitation regime** — exactly
the case CHELSA's orographic downscaling is designed for. Its monthly normals also feed the
**rainfall-distribution modifier** (dry-winter flowering trigger; see the agronomy notes) more
faithfully in this orographically-driven setting. WorldClim v2.1 is retained as a **cross-check
/ fallback** so we can sanity-check CHELSA values at the ground-truth plots.

### 3.2 Recent conditions / observations (FR-8)

| API | Access | Fit for our use |
|-----|--------|------------------|
| **NASA POWER** | Free, **no key** | Agro-climatology point queries; simple, robust, no registration — good default for on-demand temp/rainfall |
| **Open-Meteo** | Free API (non-commercial tiers) | Historical archive + forecast point queries; easy to cache; convenient for trend context |
| _ERA5 (CDS)_ | API, registration | Deep hourly reanalysis; heavier to operate — **not** needed for the pilot, keep in reserve |

#### Recent-conditions recommendation: **NASA POWER (primary) + Open-Meteo (secondary)**

NASA POWER's no-key access makes it the lowest-friction default for recent point temp/rainfall;
Open-Meteo provides a second source and an easily-cached historical archive for trend context.
These satisfy doc 06's "on-demand recent conditions" role and feed graceful degradation (NFR-8):
if one API is down, fall back to the other and flag partial results. They do **not** replace the
gridded normals, which remain the pre-ingested baseline for the suitability score.

## 4. License confirmation

All selected sources are **open / free to use**. Per doc 06, the exact current terms **must be
re-verified before relying on them** (licenses change), and the selection is recorded in ADRs.

| Source | Status | License (to re-verify before reliance) |
|--------|--------|-----------------------------------------|
| **Copernicus DEM GLO-30** | Selected (DEM) | Open / free use under Copernicus terms; commonly mirrored on AWS Open Data & OpenTopography |
| NASADEM | Fallback DEM | Open (NASA/USGS, public domain-style terms) |
| SRTM | Considered | Open (NASA/USGS) |
| ASTER GDEM | Considered | Open (NASA/METI) |
| **CHELSA** | Selected (climate normals) | Open / free use |
| WorldClim v2.1 | Cross-check | Free for academic/non-commercial — **confirm suitability for an internal co-op tool** |
| **NASA POWER** | Selected (recent) | Free, no key, open access |
| **Open-Meteo** | Selected (recent) | Free API; **non-commercial tiers — confirm tier vs co-op usage** |

> Action: before any production reliance, the GIS Specialist + Product Owner confirm each
> license against current published terms and note any commercial-tier requirements (WorldClim,
> Open-Meteo) in the relevant ADR.

## 5. Recommendation (summary)

For the Nepal mid-hills pilot:

- **DEM → Copernicus DEM GLO-30** (cleanest steep-terrain surface; NASADEM as fallback). → ADR-0006
- **Climate normals → CHELSA** (best in complex mountain terrain; WorldClim v2.1 as cross-check). → ADR-0007
- **Recent conditions → NASA POWER (primary) + Open-Meteo (secondary).** → ADR-0007

This matches the data-layer choices in doc 06 and feeds the ingestion pipeline (reproject/clip →
COG → PostGIS with version + retrieval date for provenance, FR-15 / NFR-16). Land cover/canopy
(ESA WorldCover) and soil (SoilGrids) remain **Phase 3+** and are out of scope here.

## 6. Honest note on method (offline-environment caveat)

A **fully precise** dataset comparison (exact void counts, slope-error statistics, CHELSA-vs-
WorldClim deltas at our plots) requires **downloading the full rasters and running them over the
pilot AOI**. The recommendations above are grounded in the documented characteristics of each
source and the known nature of the terrain, not yet in measured numbers for our specific tiles.

Because some **dev/CI environments are offline** (no network to the source archives), the
**engineering spike** that proves the toolchain (read DEM → derive slope/aspect → render a tile →
score a point) uses a **small clipped fixture raster** committed to the repo as a test fixture
(doc 05: "small clipped test rasters committed as fixtures; large data stays in object storage").
The fixture is enough to validate the pipeline end-to-end and keep tests deterministic; it is
**not** a substitute for the full-resolution regional download, which happens during data
ingestion once the AOI and licenses are confirmed. The quantitative dataset comparison should be
re-run on the real clipped tiles before launch and the ADRs updated if anything surprises us.
