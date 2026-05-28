# 09 — Development Setup

> **Finalized in Phase 0** alongside the walking skeleton. This reflects the toolchain
> as actually scaffolded; ports and versions below are what `docker compose up` runs.

## Prerequisites

- **Docker + Docker Compose** (the only hard requirement to run the full stack).
- **Python 3.12** with **[uv](https://docs.astral.sh/uv/)** — backend dependency/venv
  manager (lockfile-based; `uv sync --frozen`).
- **Node.js 20+** with **npm** — frontend (a `package-lock.json` is committed; CI uses
  `npm ci`).
- **make** — task-runner convenience (see `Makefile`).
- **GDAL** is **not** needed on the host: the API/worker image is pure-Python (slim) and
  the geospatial stack installs as binary wheels. The `data-pipelines` image builds on the
  official `ghcr.io/osgeo/gdal:ubuntu-small-3.9.3` base for CLI tools (see ADR-0006).

## Local workflow

```bash
# 1. Configure environment
cp .env.example .env        # adjust local secrets if desired

# 2. Bring up the walking skeleton (PostGIS, Redis, MinIO+init, API, worker, web)
docker compose up --build
#    Add TiTiler (behind a profile, no real COG yet):  docker compose --profile tiles up

# 3. Smoke-check
curl localhost:8000/health        # {"status":"ok"}
curl localhost:8000/version       # {... "model_config_version":"2026.1"}
open http://localhost:5173        # health badge + MapLibre map over the Nepal pilot

# 4. Tests / lint (run against each sub-project; see Makefile)
make test                         # backend pytest + frontend vitest
make lint                         # ruff + mypy ; eslint + prettier + tsc
make spike-terrain                # terrain-shading benchmark on the committed fixture
make seed-pilot-data              # fetch pilot DEM -> COG -> MinIO (offline fixture fallback)
```

Backend-only loop (without Docker):

```bash
cd backend
uv sync --extra dev --extra geo   # omit --extra geo for the API/worker-only stack
uv run pytest
uv run ruff check . && uv run mypy app worker
```

## Service ports (compose defaults)

| Service | Port | Phase 0 status |
|---------|------|----------------|
| Web (Vite dev) | 5173 | core |
| API (FastAPI) | 8000 | core |
| PostGIS | 5432 | core |
| Redis | 6379 | core |
| MinIO (API / console) | 9000 / 9001 | core |
| TiTiler | 8001 | `tiles` profile (optional) |
| Keycloak | 8080 | deferred to Phase 4 |

## Repository layout (as built)

```
docs/            # design docs (01–09), docs/adr/ (ADR-0001..0007), docs/phase-0/
config/          # suitability/ (versioned thresholds) + ground-truth/ template
backend/         # FastAPI app/, Celery worker/, shared geo/ library, tests/ (+fixtures)
frontend/        # Vite + React + TS + MapLibre web slice
data-pipelines/  # ingestion: DEM -> reproject/clip -> COG -> MinIO + PostGIS provenance
infra/           # postgis/minio init, titiler, k3s (deferred)
docker-compose.yml + .override.yml, .env.example, Makefile, .github/workflows/ci.yml
```

## Branching & quality gates

- Trunk-based with short-lived feature branches; PRs require **green CI + one review**.
- CI (`.github/workflows/ci.yml`) runs: backend lint+type (ruff, ruff-format, mypy),
  backend pytest (with PostGIS/Redis service containers), a **geo-spike** job (terrain
  spike + COG conversion on the fixture), frontend (eslint, prettier, tsc, vitest), and
  docker image builds.
- **Suitability-model config changes require agronomist review and a version bump**
  ([doc 03](03-suitability-model.md), `config/suitability/README.md`).

## Data handling in dev

- **Never commit large rasters.** Large data lives in MinIO/object storage
  (root `.gitignore` allows only the small `backend/tests/fixtures/**/*.tif`).
- Commit only **small clipped fixtures** needed for tests; document how each was produced
  (`backend/tests/fixtures/README.md`).

## Notes / deviations from the early design sketch

- **npm** is used for the frontend (not pnpm) — simpler default; switch is trivial if the
  team prefers pnpm later.
- **uv** manages the backend (the design mentioned `uv` or `venv`); the lockfiles make CI
  reproducible.
- A few image tags (MinIO, TiTiler) are on `latest` with a TODO to pin to dated releases.
