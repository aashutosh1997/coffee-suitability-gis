# ADR-0007: Use CHELSA for baseline climate normals (WorldClim as fallback)

## Status

Accepted (implemented 2026-05-30 — real CHELSA V2.1 ingest in
[`data-pipelines/ingest/fetch_chelsa.py`](../../data-pipelines/ingest/fetch_chelsa.py);
synthetic DEM-derived generator retained as offline/CI fallback per R-NET; WorldClim
fallback per ADR-0007 still deferred. First Nepal-wide CHELSA re-run captured in
[`docs/phase-3/validation-report.md`](../phase-3/validation-report.md) §6.)

## Date

2026-05-28 (decided); 2026-05-30 (implemented)

## Deciders

GIS Specialist, Data Engineer, Agronomist.

## Context

Two climate factors drive suitability — **mean annual temperature** and **annual
precipitation** — split into a baseline and a recent-conditions path
([03-suitability-model.md](../03-suitability-model.md), [06-data-sources.md](../06-data-sources.md)):

1. **Baseline normals** are pre-ingested gridded climatologies (FR-7).
2. **Recent/observed** conditions are point queries fetched on demand (FR-8).

The pilot region — the **Nepal mid-hills** (~27-28 deg N) — is exactly the
**complex, mountainous terrain** where gridded climate products diverge most, because
interpolation across steep relief is where a model's terrain handling shows.

Candidates for baseline normals (both ~1 km):

- **WorldClim v2.1** — the common default; well-established bioclimatic variables.
- **CHELSA** — high-resolution climatologies that are **often better in complex/mountainous
  terrain**, which is the defining feature of our operating area.

For recent conditions we considered ERA5 (reanalysis, needs registration) versus the point
weather APIs; the point APIs are simpler to cache for on-demand single-location lookups.

## Decision

Adopt **CHELSA (~1 km) for baseline climate normals**, with **WorldClim v2.1 as the
fallback** if the data spike finds gaps or quality issues for the region.

For **recent/observed** conditions, query **NASA POWER / Open-Meteo** on demand (point
queries, cached), per the fast-path design ([04-architecture.md](../04-architecture.md)).

CHELSA wins because its strength is precisely complex-terrain resolution, and the mid-hills
are complex terrain. This is **pending Phase 0 data-spike confirmation**, recorded in
[../phase-0/data-spike-report.md](../phase-0/data-spike-report.md).

## Consequences

### Positive

- Better-resolved baseline temperature/precipitation in steep terrain than WorldClim.
- Clean split: pre-ingested grids for the baseline, cached point APIs for recent conditions,
  keeping the fast path under target and degrading gracefully (NFR-1/NFR-8).

### Negative

- At **~1 km, grids miss microclimate** — frost pockets, valley fog, cold-air drainage — so
  the climate factor is necessarily coarse. Terrain analysis (slope/aspect/shading) and
  **expert agronomist review** compensate, and provenance flags the resolution (FR-15).
- Maintaining two baseline sources (primary + fallback) adds a small ingestion branch.

## Related

- Climate sources & normals-vs-observations split: [06-data-sources.md](../06-data-sources.md).
- Microclimate / climate-not-microclimate risk: [01-vision-and-scope.md](../01-vision-and-scope.md).
- Phase 0 spike that confirms this: [../phase-0/data-spike-report.md](../phase-0/data-spike-report.md).
- Elevation-source counterpart: [ADR-0006](0006-dem-source-copernicus-vs-srtm-vs-nasadem.md).
