# ADR-0006: Use Copernicus DEM GLO-30 as the elevation source

## Status

Accepted (pending final confirmation from the Phase 0 data spike)

## Date

2026-05-28

## Deciders

GIS Specialist, Data Engineer, Agronomist.

## Context

Elevation is the backbone factor: altitude, slope, aspect, and all terrain shading derive
from the DEM ([06-data-sources.md](../06-data-sources.md), [03-suitability-model.md](../03-suitability-model.md)).
The pilot region is the **Nepal mid-hills** (Gulmi/Syangja/Kavre, ~27-28 deg N) — steep,
mountainous, terraced terrain where DEM **void handling and vertical accuracy matter more
than headline resolution**, since the leading global options are all ~30 m.

Candidate ~30 m global, open DEMs:

- **SRTM** — long-standing and well-documented, but has **voids in steep/mountainous
  terrain** exactly like the mid-hills.
- **NASADEM** — reprocessed SRTM with improved void filling; better than raw SRTM but still
  SRTM-lineage.
- **ASTER GDEM** — wider latitude coverage but **noisier**, poorer for slope/aspect.
- **Copernicus DEM GLO-30** — modern, global, **fewest voids in mountainous terrain**, open
  via AWS Open Data with **no API key**, which simplifies the ingestion pipeline.

## Decision

Adopt **Copernicus DEM GLO-30 (~30 m)** as the elevation source.

It wins on terrain quality where this project actually operates (mountainous, void-prone),
on being modern and global, and on frictionless open access (AWS Open Data, no key) that
fits the pre-ingest-to-COG pipeline ([04-architecture.md](../04-architecture.md)).

This is **pending final confirmation by the Phase 0 data spike**, which checks DEM quality
against real plot sizes; the result is recorded in
[../phase-0/data-spike-report.md](../phase-0/data-spike-report.md).

## Consequences

### Positive

- Best void behavior and consistency for slope/aspect/shading in steep terrain.
- No-key open access keeps ingestion simple and reproducible (provenance per FR-15/NFR-16).

### Negative

- At **~30 m the DEM smooths small terraced plots**, the dominant land form in the mid-hills;
  fine terrace-scale relief is lost. We flag resolution-driven uncertainty in results and
  plan to **evaluate national/regional LiDAR or higher-res DEMs** for finer detail in a later
  phase ([06-data-sources.md](../06-data-sources.md) resolution caveat).

## Related

- DEM options & resolution caveat: [06-data-sources.md](../06-data-sources.md).
- Phase 0 spike that confirms this: [../phase-0/data-spike-report.md](../phase-0/data-spike-report.md).
- Climate-source counterpart: [ADR-0007](0007-climate-source-worldclim-vs-chelsa.md).
- Ingestion to COG: [04-architecture.md](../04-architecture.md).
