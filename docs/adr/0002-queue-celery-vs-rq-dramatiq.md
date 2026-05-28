# ADR-0002: Use Celery (with Redis broker) for the async job queue

## Status

Accepted

## Date

2026-05-28

## Deciders

Backend Engineer, GIS Specialist, DevOps/Platform.

## Context

Heavy geoprocessing — clipping rasters to a polygon AOI, zonal statistics, slope/aspect,
hillshade/sky-view/insolation — is too slow to block an HTTP request, so it must run
asynchronously on workers (NFR-3, heavy path in [04-architecture.md](../04-architecture.md)).
Two further needs shape the choice:

1. **Scheduled ingestion refreshes.** Data-ingestion jobs re-fetch and re-tile DEM/climate
   sources on a cadence ([06-data-sources.md](../06-data-sources.md)).
2. **Multi-step workflows.** Polygon geoprocessing is a pipeline (clip → derive → score →
   store) that benefits from fan-out/fan-in.

Redis is already in the stack as the result cache, so it is the natural broker.

Alternatives considered:

- **RQ** — simplest to operate, but **no native scheduling** (needs an add-on) and no
  workflow/canvas primitives; we would hand-roll the pieces Celery ships.
- **Dramatiq** — lighter and ergonomic, but **fewer batteries**: scheduling and complex
  chaining are not first-class, and the ecosystem/community is smaller.

## Decision

Adopt **Celery with a Redis broker** for all asynchronous work.

- Use **Celery Beat** for scheduled data-ingestion refreshes and weather-cache expiry.
- Use Celery **canvas** (chains/groups/chords) for multi-step polygon geoprocessing.
- Keep heavy logic in the shared geoprocessing library so the same code serves the API's
  fast point path and the worker's heavy polygon path.

Celery wins on maturity, the built-in scheduler (which we need regardless), workflow
primitives that match the geoprocessing pipeline, and the largest ecosystem/operational
knowledge base.

## Consequences

### Positive

- Beat removes the need for a separate cron/scheduler component for ingestion.
- Canvas models the multi-step polygon pipeline directly.
- Mature, well-documented, large talent pool; reuses the existing Redis dependency.

### Negative

- More configuration and operational surface than RQ/Dramatiq (worker pools, result
  backend, broker tuning) — mitigated because every component is containerized
  ([ADR-0003](0003-containerize-for-onprem-to-cloud-portability.md)) with a standard
  worker image and config.
- Redis-as-broker durability must be configured deliberately (persistence/acks).

## Related

- Async architecture & heavy path: [04-architecture.md](../04-architecture.md).
- Stack rationale (Celery vs RQ/Dramatiq flagged for Phase 0): [05-tech-stack.md](../05-tech-stack.md).
- Containerization that bounds the operational cost: [ADR-0003](0003-containerize-for-onprem-to-cloud-portability.md).
