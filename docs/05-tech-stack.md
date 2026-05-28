# 05 — Tech Stack

Every choice below favors **open-source, containerizable, vendor-neutral** components so
the on-prem-first / cloud-later posture holds (NFR-4/5/6). Rationale is given because the
*why* matters more than the *what* when the team starts making trade-offs.

## Frontend

| Concern | Choice | Why |
|---------|--------|-----|
| Language | **TypeScript** | Type safety across a data-heavy UI |
| Framework | **React** | Large talent pool, ecosystem, fits a cross-functional team |
| Build | **Vite** | Fast dev server and builds |
| Mapping | **MapLibre GL JS** | Open-source vector maps with **no proprietary token/vendor lock-in** (unlike Mapbox GL). `deck.gl` available for heavy data layers |
| Map drawing | **Terra Draw** / Mapbox-draw-compatible tools | Draw/edit polygon AOIs |
| Data fetching | **TanStack Query** | Caching, polling for async job status |
| UI components | **Mantine** (or shadcn/ui) | Accessible, batteries-included; final pick in Phase 0 |

## Backend

| Concern | Choice | Why |
|---------|--------|-----|
| Language | **Python** | Unmatched geospatial + scientific ecosystem; same language for API, workers, and analysis |
| API framework | **FastAPI** | Async, fast, automatic OpenAPI docs, Pydantic validation |
| Async jobs | **Celery** (+ Redis broker) | Mature task queue for heavy geoprocessing; **RQ/Dramatiq** are lighter alternatives to weigh in Phase 0 |
| Validation/models | **Pydantic** | Strict request/response + config schemas |

### Geospatial & scientific libraries
| Purpose | Library |
|---------|---------|
| Raster I/O & sampling | **rasterio**, **rioxarray** |
| Vector geometry | **GeoPandas**, **Shapely**, **pyproj** |
| Zonal statistics | **rasterstats** / **exactextract** |
| Gridded climate (netCDF) | **xarray** |
| Terrain derivatives (slope/aspect/hillshade) | **GDAL**, **richdem** / **WhiteboxTools** |
| Solar / insolation / shading | **pvlib**, **GRASS GIS `r.sun`**, sky-view-factor tooling |
| Suitability ML (later) | **scikit-learn** |

## Data layer

| Concern | Choice | Why |
|---------|--------|-----|
| Database | **PostgreSQL + PostGIS** | The standard for geospatial; vector + raster, spatial indexing |
| Raster format | **Cloud-Optimized GeoTIFF (COG)** | Efficient partial reads from object storage; identical on-prem and cloud |
| Object storage | **MinIO** (S3-compatible) | Self-host now, swap endpoint for S3/GCS later |
| Tile serving | **TiTiler** (raster) + **pg_tileserv**/**Martin** (vector) | Serve map tiles directly from COGs/PostGIS |
| Cache / broker | **Redis** | Result cache + Celery broker |

## Infrastructure & DevOps

| Concern | Choice | Why |
|---------|--------|-----|
| Containers | **Docker** | Single artifact runs everywhere |
| Orchestration | **Docker Compose** → **k3s** (lightweight Kubernetes) | Compose for early on-prem; k3s makes the eventual jump to managed cloud k8s trivial |
| Provisioning | **Terraform** (+ **Ansible** for on-prem host config) | IaC that works on-prem and across clouds |
| CI/CD | **GitHub Actions** or **GitLab CI** | Lint, test, build images, deploy |
| Reverse proxy / TLS | **Traefik** or **Nginx** | Routing, TLS termination |
| Auth | **Keycloak** (OIDC) | Self-hosted SSO with roles; cloud-portable |
| Observability | **Prometheus + Grafana + Loki + OpenTelemetry** | Metrics, dashboards, logs, tracing — all self-hostable |

## Testing & quality

| Concern | Choice |
|---------|--------|
| Python tests | **pytest** (unit for scoring, integration for geoprocessing) |
| Frontend tests | **Vitest** + **React Testing Library**; **Playwright** for e2e |
| Lint/format | **Ruff** + **Black** (Python), **ESLint** + **Prettier** (TS) |
| Type checking | **mypy** (Python), **tsc** (TS) |
| Geospatial fixtures | Small clipped test rasters committed as fixtures; large data stays in object storage |

## Things deliberately deferred / to confirm in Phase 0
- Final UI component library (Mantine vs shadcn/ui).
- Celery vs RQ/Dramatiq for the queue.
- Whether k3s is needed at launch or Compose suffices for the initial on-prem footprint.
- Climate dataset selection — WorldClim vs CHELSA vs ERA5 — pinned in [doc 06](06-data-sources.md) after the Phase 0 data spike.
