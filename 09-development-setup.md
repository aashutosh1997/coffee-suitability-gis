# 09 — Development Setup

> **Placeholder — to be completed during Phase 0** as the toolchain is finalized and the
> walking skeleton lands. This file captures the intended shape so the team agrees on it
> up front.

## Prerequisites (intended)
- Docker + Docker Compose
- Python 3.12+ (with a virtual environment tool — `uv` or `venv`)
- Node.js 20+ and a package manager (pnpm/npm)
- `make` (task runner convenience)
- GDAL system libraries (for rasterio/GeoPandas) — pinned versions documented in Phase 0

## Intended local workflow
```bash
# 1. Configure environment
cp .env.example .env        # then fill in local secrets

# 2. Bring up the stack (PostGIS, Redis, MinIO, API, worker, web, tiles)
docker compose up --build

# 3. Seed a small pilot-region dataset (clipped test COGs) — script added in Phase 1
make seed-pilot-data

# 4. Run tests
make test                   # backend pytest + frontend vitest
make lint                   # ruff/black + eslint/prettier
```

## Service ports (intended defaults)
| Service | Port |
|---------|------|
| Web (Vite dev) | 5173 |
| API (FastAPI) | 8000 |
| PostGIS | 5432 |
| Redis | 6379 |
| MinIO (API / console) | 9000 / 9001 |
| Keycloak | 8080 |
| TiTiler | 8001 |

## Branching & quality gates (intended)
- Trunk-based with short-lived feature branches; PRs require green CI + one review.
- CI runs lint, type-check, unit + integration tests, and builds container images.
- Suitability-model config changes require an agronomist review and a version bump ([doc 03](03-suitability-model.md)).

## Data handling in dev
- **Never commit large rasters.** Large data lives in MinIO/object storage (see `.gitignore`).
- Commit only **small clipped fixtures** needed for tests.
