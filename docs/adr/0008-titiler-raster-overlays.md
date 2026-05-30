# ADR-0008: Raster factor-layer overlays via TiTiler with a backend discovery endpoint

## Status

Accepted (implemented 2026-05-30 — `/overlays` endpoint in
[`backend/app/api/overlays.py`](../../backend/app/api/overlays.py); MapLibre raster
layer + UI in
[`frontend/src/components/RasterOverlayLayer.tsx`](../../frontend/src/components/RasterOverlayLayer.tsx)
and
[`frontend/src/components/OverlayPanel.tsx`](../../frontend/src/components/OverlayPanel.tsx);
TiTiler unprofile-gated in [`docker-compose.yml`](../../docker-compose.yml)).

## Date

2026-05-30

## Deciders

GIS Specialist, Backend Engineer, Frontend Engineer.

## Context

[FR-13](../02-requirements.md) is a Must: *"Display the AOI and results on an
interactive map with toggleable factor layers."* The architecture
([04-architecture.md](../04-architecture.md)) already designates **TiTiler** as the
tier that serves COGs from MinIO as web map tiles, and the docker-compose stack
already shipped a TiTiler service, but no overlay UI or discovery layer existed —
the frontend showed only the basemap and the AOI outline.

Two open questions had to be settled:

1. **How does the frontend know which COG to point TiTiler at?** Hard-coding S3
   keys in the React app would couple the UI to the seed pipeline (a re-seed or
   version bump from `2026.1` to `2026.2` would silently break it) and would
   bypass the existing provenance machinery in
   [`backend/geo/cog_reader.py`](../../backend/geo/cog_reader.py).
2. **Where do colormap + rescale live?** TiTiler accepts both as query parameters,
   so either side (backend or frontend) *could* own them. But a frontend that
   chooses a colormap independently from a backend-defined legend can silently
   drift — a different colormap or a wrong rescale mis-reads the data
   (R-OVLCMAP).

## Decision

- **A thin backend discovery endpoint, `GET /overlays`,** returns a list of layers
  with: `key`, `name`, `units`, `dataset`, `source`, `resolution`, `retrieved`,
  `version`, `colormap`, `rescale`, `band_count`, optional `bands[]`, and a
  fully-assembled `tile_url_template` ready to drop into a MapLibre `raster`
  source. The endpoint reuses `cog_reader.resolve_dataset()` to look up the
  current `object_key` per dataset against `dataset_provenance`, so a re-seed
  flips provenance for free with no frontend change.
- **Colormap and rescale are decided server-side, per dataset.** The
  `_REGISTRY` in `app/api/overlays.py` is the single source of truth; the legend
  in the UI reads the same values, so the gradient the user sees and the tiles
  TiTiler renders cannot drift apart.
- **TiTiler is unprofile-gated** in `docker-compose.yml` so `docker compose up`
  brings it up by default on `:8001` with `CORS_ALLOW_ORIGINS=*` (dev) and a
  `/healthz` healthcheck. The on-prem deployment fronts both `api` and `titiler`
  behind nginx; in that topology CORS is moot and the browser hits a single
  origin.
- **Single MapLibre raster source per layer**, mirroring the
  [`AOILayer.tsx`](../../frontend/src/components/AOILayer.tsx) lifecycle: add on
  first mount, update opacity / visibility / band on prop change, clean up on
  unmount. The AOI vector outline always renders **on top** via the
  `beforeId="aoi-fill"` insertion point so the agronomist never loses sight of
  the plot they drew.
- **Layers are stackable**, not mutually exclusive — an agronomist can lay
  precipitation over altitude with opacity, which is the whole point.
- **No raster caching tier this round.** MinIO + TiTiler over a same-host
  Docker network is sub-100ms per tile for the pilot bbox; a CDN/edge-cache is
  a Phase 4 concern.

## Out of scope (this slice)

- **Slope, aspect, hillshade overlays.** The engine derives these in-memory at
  assessment time ([`backend/app/suitability/factors.py`](../../backend/app/suitability/factors.py));
  persisting them as standalone COGs is the same shape as the CHELSA fetcher
  (one ingest module + a `dataset_provenance` row) but is a meaningful scope
  expansion that belongs in its own slice.
- **Soil overlay.** Still gated on SoilGrids ingestion (deferred Phase 3 item);
  once ingested, adding it to `_REGISTRY` is one entry.
- **Computed result overlays.** Per-pixel suitability rasters from the async
  polygon worker (the natural Phase 3/4 progression to overlay the *score*
  itself, not just the inputs) — needs the worker to write a result COG first.

## Consequences

### Positive

- Frontend never hard-codes an S3 key. Re-seeding (synthetic ↔ real CHELSA,
  `2026.1` ↔ `2026.2`) updates the overlay provenance badge and the tile source
  automatically.
- Colormap and rescale can never drift between legend and tile rendering — both
  read the same backend value.
- Adding a new overlay is one `_OverlaySpec` entry plus (if needed) one
  colormap gradient stop set in `ColorbarLegend.tsx`.

### Negative

- A separate browser origin (`:8001`) in dev requires CORS. Production avoids
  this by fronting api+titiler behind nginx.
- `_REGISTRY` is hand-curated. Forgetting to add a new dataset means it won't
  show up in the panel until a code change — acceptable given how rarely new
  datasets land.
- No raster cache means TiTiler is hit per tile per pan/zoom. Fine at pilot
  scale; will need a CDN once concurrency rises (Phase 4 / 5 perf pass).

## Related

- FR-13 — [02-requirements.md](../02-requirements.md).
- Architecture's TiTiler block — [04-architecture.md](../04-architecture.md).
- Provenance lookup reused — [`backend/geo/cog_reader.py`](../../backend/geo/cog_reader.py).
- Risk register additions — [phase-0/risk-register.md](../phase-0/risk-register.md) (R-OVLPERF, R-OVLCMAP).
