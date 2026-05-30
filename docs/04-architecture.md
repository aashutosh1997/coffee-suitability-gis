# 04 — Architecture

## Guiding principles

1. **Portable by default.** Containerized, open-source, vendor-neutral so on-prem → cloud
   is an infra change, not a rewrite (NFR-4/5/6, [ADR-0003](adr/0003-containerize-for-onprem-to-cloud-portability.md)).
2. **Async for heavy work.** Geoprocessing runs in workers off a queue; the API stays snappy (NFR-3).
3. **Cache aggressively.** Regional rasters are pre-processed once; point/weather lookups are cached.
4. **Explainable & reproducible.** Scoring config is versioned; every result records its provenance (NFR-14/16).
5. **Separation of concerns.** A shared geoprocessing library is used by both the API (fast point path) and workers (heavy polygon path).

## Component overview

```mermaid
flowchart TB
    subgraph Client
      WEB["React + MapLibre web app"]
    end

    subgraph Edge
      RP["Reverse proxy / TLS<br/>(Traefik or Nginx)"]
      AUTH["Keycloak (OIDC SSO)"]
    end

    subgraph Services
      API["API service<br/>(FastAPI)"]
      WORKER["Geoprocessing workers<br/>(Celery)"]
      TILES["Tile server<br/>(TiTiler)"]
      INGEST["Data ingestion jobs<br/>(scheduled)"]
    end

    subgraph Data
      PG[("PostgreSQL + PostGIS")]
      REDIS[("Redis<br/>broker + cache")]
      OBJ[("Object storage<br/>MinIO / S3-compatible<br/>COGs")]
    end

    subgraph External["External open data"]
      DEM["Copernicus DEM / SRTM"]
      CLIM["WorldClim / CHELSA / ERA5"]
      WX["NASA POWER / Open-Meteo"]
      SOIL["SoilGrids"]
      LC["ESA WorldCover / canopy height"]
    end

    WEB --> RP --> API
    WEB -. login .-> AUTH
    RP --> TILES
    API <--> REDIS
    API --> PG
    API -- "enqueue heavy jobs" --> REDIS
    WORKER <--> REDIS
    WORKER --> PG
    WORKER --> OBJ
    TILES --> OBJ
    INGEST --> OBJ
    INGEST --> PG
    INGEST -. fetch/cache .-> DEM & CLIM & SOIL & LC
    WORKER -. point query .-> WX
```

## Request flows

### Fast path — single point
For a point, the answer is usually a set of lookups against pre-ingested regional rasters
plus a cached weather query, so it can be served synchronously.

```mermaid
sequenceDiagram
    participant U as User (web)
    participant A as API (FastAPI)
    participant C as Redis cache
    participant P as PostGIS / COGs
    participant W as Weather API

    U->>A: POST /assess {lat, lon}
    A->>C: cached result?
    alt cache hit
        C-->>A: result
    else miss
        A->>P: sample DEM (alt/slope/aspect), climate normals
        A->>W: recent temp/rainfall (cached per cell)
        A->>A: run suitability model (config vX)
        A->>C: store result
    end
    A-->>U: suitability JSON (+ provenance)
```

### Heavy path — polygon AOI
For a polygon we run zonal statistics, terrain shading, and possibly canopy analysis —
too heavy to block a request, so it is queued.

```mermaid
sequenceDiagram
    participant U as User (web)
    participant A as API
    participant Q as Redis (queue)
    participant K as Celery worker
    participant P as PostGIS / COGs

    U->>A: POST /assess {polygon}
    A->>Q: enqueue job
    A-->>U: 202 Accepted {job_id}
    K->>Q: pick up job
    K->>P: clip DEM/climate to AOI, zonal stats
    K->>K: slope/aspect, hillshade, sky-view, insolation
    K->>K: run suitability model, store result
    U->>A: GET /assess/{job_id} (poll or websocket)
    A-->>U: status → result when ready
```

## Components in detail

| Component | Responsibility |
|-----------|----------------|
| **Web app** | AOI input (point/draw/upload), map display (MapLibre), factor overlays, report export, override UI |
| **API (FastAPI)** | AuthN/Z, request validation, fast point path, job orchestration, results API, config management |
| **Geoprocessing library** | Shared Python module: raster sampling, slope/aspect, hillshade/sky-view/insolation, zonal stats, suitability engine. Used by both API and workers |
| **Workers (Celery)** | Long-running polygon analysis, batch jobs, report rendering |
| **Tile server (TiTiler)** | Serve DEM/derivative/result rasters as web map tiles from COGs. Dev: reachable on `:8001`; production fronts api+titiler behind a single **Caddy** origin (auto-TLS, served by the GCP demo deploy per [ADR-0009](adr/0009-gcp-single-vm-demo-deployment.md); on-prem equivalent is nginx + certbot). The browser never picks the COG URL itself — the API's `/overlays` endpoint hands it a TiTiler-ready tile template per dataset, with provenance and colormap baked in (FR-13, [ADR-0008](adr/0008-titiler-raster-overlays.md)) |
| **Reverse proxy / edge** | **Caddy** (demo deploy, per [ADR-0009](adr/0009-gcp-single-vm-demo-deployment.md)) or nginx (on-prem) terminates TLS and reverse-proxies a single public origin to `api:8000` (`/api/*`), `titiler:80` (`/tiles/*`), and the built SPA (`/`). Single-origin design collapses CORS to nothing and lets the backend hand out relative URLs |
| **Data ingestion** | Scheduled jobs that fetch, reproject, tile, and store DEM/climate/soil/land-cover as Cloud-Optimized GeoTIFFs for the supported region(s); refresh weather caches |
| **PostGIS** | Plots/AOIs, assessment results, audit log, model config versions, vector layers |
| **Object storage (MinIO)** | COG rasters; S3-compatible so cloud migration = endpoint swap |
| **Redis** | Celery broker + result cache |
| **Keycloak** | OIDC SSO, roles (viewer/agronomist/admin) |
| **Observability** | Prometheus (metrics), Grafana (dashboards), Loki (logs), health checks |

## Data strategy: pre-ingest, don't fetch-on-request

Global rasters (DEM, climate) are large. Rather than hitting external sources per request,
**ingestion jobs pre-process the co-op's region(s) of interest into COGs** stored in object
storage and indexed in PostGIS. Assessments then read from fast local storage. Only
**point weather observations** (NASA POWER / Open-Meteo) are fetched on demand and cached.
This is what keeps the fast path under 5 s and removes a hard runtime dependency on
external uptime (supports NFR-8 graceful degradation).

## On-prem → cloud migration path

Because every box above is a container and storage is S3-compatible:

| Concern | On-prem (start) | Cloud (later) |
|---------|-----------------|---------------|
| Orchestration | Docker Compose, then **k3s** | Managed Kubernetes (EKS/GKE/AKS) |
| Object storage | MinIO | S3 / GCS / Azure Blob (same API) |
| Database | PostGIS container | Managed Postgres + PostGIS |
| Queue/cache | Redis container | Managed Redis |
| Auth | Keycloak | Keycloak or managed OIDC |
| Provisioning | Terraform + Ansible | Terraform (swap provider) |

The migration is therefore incremental and low-risk — see [ADR-0003](adr/0003-containerize-for-onprem-to-cloud-portability.md).
