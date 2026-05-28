# 02 — Requirements

Requirements are tagged `FR-*` (functional) and `NFR-*` (non-functional), with a
**MoSCoW** priority (Must / Should / Could / Won't-for-now).

## Functional requirements

### Input & area of interest (AOI)
- **FR-1 (Must)** — Accept a single point as latitude/longitude (decimal degrees).
- **FR-2 (Must)** — Accept a polygon AOI, either drawn on the map or uploaded (GeoJSON/KML/shapefile).
- **FR-3 (Should)** — Validate coordinates (range, CRS) and reject/flag locations outside the supported region.
- **FR-4 (Could)** — Bulk input: upload a CSV/file of many plots for batch assessment.

### Analysis
- **FR-5 (Must)** — Derive **altitude** at the point / altitude statistics (min/mean/max) over a polygon.
- **FR-6 (Must)** — Derive **slope** and **aspect** from the DEM.
- **FR-7 (Must)** — Retrieve **mean annual temperature** and **annual precipitation** (climate normals).
- **FR-8 (Should)** — Retrieve **recent/observed** temperature & rainfall (last N years) for trend context.
- **FR-9 (Should)** — Compute **terrain shading / solar exposure** (hillshade, sky-view factor, modeled insolation).
- **FR-10 (Could)** — Estimate **canopy shading** from land-cover / canopy-height data.
- **FR-11 (Could)** — Retrieve **soil** attributes (pH, depth, texture, drainage) from open soil grids.
- **FR-12 (Must)** — Run the **suitability model** (see [doc 03](03-suitability-model.md)) producing per-factor scores and an overall class.

### Output & interaction
- **FR-13 (Must)** — Display the AOI and results on an interactive map with toggleable factor layers.
- **FR-14 (Must)** — Show a **per-factor breakdown** with the raw value, the threshold band it fell into, and a plain-language explanation.
- **FR-15 (Must)** — Show **data provenance** (which dataset/date each value came from).
- **FR-16 (Should)** — Generate a **printable/PDF report** for a plot.
- **FR-17 (Should)** — Allow an agronomist to **adjust weights/thresholds** and re-run, and to record an **expert override** with a note.
- **FR-18 (Could)** — **Save / compare** multiple assessed plots.

### Accounts & access
- **FR-19 (Must)** — Authenticated access via the org's SSO (OIDC); roles: *viewer*, *agronomist*, *admin*.
- **FR-20 (Should)** — Audit log of assessments and overrides (who, when, what).

## Non-functional requirements

### Performance & scale
- **NFR-1 (Must)** — Point assessment returns in < 5 s (warm cache); polygon < 60 s typical.
- **NFR-2 (Should)** — Support the co-op's expected concurrency (size to be confirmed in Phase 0; design for ~50 concurrent users).
- **NFR-3 (Must)** — Heavy geoprocessing runs **asynchronously** (job queue) so the UI stays responsive.

### Portability & deployment
- **NFR-4 (Must)** — Run fully **on-premises** with no hard dependency on a specific cloud vendor.
- **NFR-5 (Must)** — All components **containerized**; same images run on-prem and in cloud.
- **NFR-6 (Should)** — Object storage is **S3-compatible** so on-prem (MinIO) → cloud (S3/GCS) is a config change.
- **NFR-7 (Should)** — Infrastructure defined as code (reproducible environments).

### Reliability & operability
- **NFR-8 (Must)** — Graceful degradation: if a data source/API is down, return partial results with a clear flag rather than failing entirely.
- **NFR-9 (Should)** — Centralized logs, metrics, and health checks for all services.
- **NFR-10 (Should)** — Automated DB backups (PostGIS) and documented restore.

### Security & privacy
- **NFR-11 (Must)** — Authn/authz on every endpoint; secrets never committed to the repo.
- **NFR-12 (Should)** — Plot coordinates treated as sensitive co-op/member data; encrypted at rest and in transit.
- **NFR-13 (Should)** — Audit trail retained per the org's data-retention policy.

### Quality & maintainability
- **NFR-14 (Must)** — Suitability thresholds/weights are **configuration**, not hard-coded, and version-controlled.
- **NFR-15 (Should)** — Automated tests (unit for scoring logic, integration for geoprocessing, e2e for key flows).
- **NFR-16 (Should)** — Every rating is reproducible: same inputs + same config version → same output.

### Usability & accessibility
- **NFR-17 (Should)** — Usable by non-GIS-expert field officers; sensible defaults, minimal jargon in the UI.
- **NFR-18 (Could)** — Localized UI for the co-op's working language(s).
- **NFR-19 (Could)** — Works on tablets for semi-field use; consider an offline mode in a later phase.
