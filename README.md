# TerraBean — Arabica Coffee Land-Suitability GIS

A web-based decision-support tool that takes the coordinates (or boundary) of a plot
of land and analyzes its suitability for growing **Arabica coffee** (_Coffea arabica_).
For a given location it derives **altitude, slope, aspect, terrain/canopy shading,
temperature, and rainfall** from open geospatial datasets, scores them against
agronomic thresholds, and returns a transparent, explainable suitability rating.

> **Status:** Phase 0 — Discovery & Foundations. The planning artifacts (vision,
> requirements, architecture, data sources, roadmap, team plan) live in `docs/`, and
> Phase 0 deliverables — the calibrated suitability config, the decision records, the
> discovery/spike reports, and a runnable "walking skeleton" — are landing now. See
> [docs/phase-0/](docs/phase-0/) for the Phase 0 outputs and exit-criteria status.

---

## Who this is for

This is an **internal tool for a coffee cooperative / organization**. It is intended
to help agronomists and field officers evaluate existing and prospective plots, advise
member farmers, and plan plantings — not as a public consumer product (at least
initially).

## Deployment posture

The system is designed to run **on-premises first**, with a deliberate path to **cloud**
if and when scale or availability needs grow. Every component is containerized and
vendor-neutral (open-source, S3-compatible storage, OIDC auth), so migrating to a
managed cloud is a configuration and infrastructure change rather than a rewrite. See
[ADR-0003](docs/adr/0003-containerize-for-onprem-to-cloud-portability.md).

---

## How to read this repository

Start with the vision, then follow the numbered documents in order.

| # | Document | What it covers |
|---|----------|----------------|
| 01 | [Vision & Scope](docs/01-vision-and-scope.md) | Problem, goals, non-goals, success criteria |
| 02 | [Requirements](docs/02-requirements.md) | Functional + non-functional requirements |
| 03 | [Suitability Model](docs/03-suitability-model.md) | The agronomic scoring logic (the heart of the product) |
| 04 | [Architecture](docs/04-architecture.md) | System components, data flow, diagrams |
| 05 | [Tech Stack](docs/05-tech-stack.md) | Chosen technologies and the rationale |
| 06 | [Data Sources](docs/06-data-sources.md) | GIS, elevation, climate, soil datasets and APIs |
| 07 | [Roadmap & Phases](docs/07-roadmap-and-phases.md) | Delivery plan from discovery to cloud |
| 08 | [Team & Roles](docs/08-team-and-roles.md) | Cross-functional team across the lifecycle |
| 09 | [Development Setup](docs/09-development-setup.md) | Local environment (to be fleshed out in Phase 0) |
| — | [ADRs](docs/adr/) | Architecture Decision Records |

## Repository layout

```
coffee-suitability-gis/
├── docs/              # All planning + design documents (start here)
├── backend/           # FastAPI API + Celery workers + geoprocessing (Phase 1+)
├── frontend/          # React + MapLibre web client (Phase 1+)
├── data-pipelines/    # Ingestion/prep of DEM, climate, soil into COG + PostGIS
├── infra/             # Docker Compose, k3s/k8s manifests, Terraform, Ansible
├── docker-compose.yml # Local/on-prem orchestration skeleton
└── .env.example       # Environment variable template
```

## License

Not yet selected — see the `LICENSE` placeholder. Decide during Phase 0 (likely an
internal/proprietary license for a co-op tool, or a permissive OSS license if the
co-op wants to share with peer organizations).
