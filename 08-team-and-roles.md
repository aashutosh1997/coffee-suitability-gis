# 08 — Team & Roles

A **full cross-functional team** for the whole software lifecycle. For an internal co-op
tool, the standout point is that this project lives or dies on **domain expertise**: an
agronomist is not optional decoration, they are a core team member who defines and
validates the product's central logic.

People can wear more than one hat — the list is **roles**, not necessarily headcount.
A lean version of this team is noted at the end.

## Core roles

### Product & domain
| Role | Responsibility | Heaviest phases |
|------|----------------|-----------------|
| **Product Owner** (from the co-op) | Owns priorities, represents field officers & members, accepts work | All, esp. 0 & 3 |
| **Agronomist / Coffee cultivation expert** | Defines suitability thresholds & weights, supplies & validates ground truth, signs off on accuracy | 0, 2, 3 (critical) |
| **Delivery/Project Manager (Scrum Master)** | Plans phases, removes blockers, runs ceremonies, manages risk | All |

### Build
| Role | Responsibility | Heaviest phases |
|------|----------------|-----------------|
| **GIS Specialist / Geospatial Data Scientist** | Terrain/shading algorithms, suitability engine, data evaluation, validation analysis | 0, 1, 2, 3 |
| **Backend Engineer(s)** (Python) | FastAPI services, Celery workers, geoprocessing library, scoring config system | 1–4 |
| **Frontend Engineer(s)** (React/TS) | Web app, MapLibre map, AOI tools, result/override UI, reports | 1–4 |
| **Data Engineer** | Ingestion pipelines (DEM/climate/soil → COG → PostGIS), caching, refresh jobs | 1–3 |
| **DevOps / Platform Engineer** | Containers, CI/CD, on-prem deploy (Compose/k3s), IaC, observability, **cloud migration** | 0, 4, 5 |
| **UX/UI Designer** | Flows and visuals usable by non-GIS field officers; map/result design | 0–3 |
| **QA / Test Engineer** | Test strategy, automation (unit/integration/e2e), validation harness for scoring | 1–4 |

### Specialist / later-phase
| Role | Responsibility | Phases |
|------|----------------|--------|
| **ML Engineer** | Optional ML suitability layer on co-op outcome data | 5 |
| **Security reviewer** | Auth model, data protection, deployment hardening (can be a focused engagement) | 4 |
| **Technical Writer** | User guide + runbooks + training material (often shared/part-time) | 3–4 |

## Role involvement by phase (RACI-lite)

`R` = drives, `C` = contributes/consulted, blank = minimal.

| Role | P0 | P1 | P2 | P3 | P4 | P5 |
|------|----|----|----|----|----|----|
| Product Owner | R | C | C | R | C | C |
| Agronomist | R | C | R | R | C |  |
| Delivery/PM | R | R | R | R | R | R |
| GIS Specialist | R | R | R | R | C | C |
| Backend Eng | C | R | R | R | R | C |
| Frontend Eng |  | R | R | R | C | C |
| Data Engineer | C | R | R | C |  | C |
| DevOps/Platform | R | C | C | C | R | R |
| UX/UI Designer | C | R | R | C |  |  |
| QA Engineer |  | R | R | R | R | C |
| ML Engineer |  |  |  |  |  | R |
| Security reviewer |  |  |  |  | R | C |
| Tech Writer |  |  |  | C | R |  |

## Lifecycle coverage

- **Requirements/Design:** Product Owner, Agronomist, GIS Specialist, UX, PM.
- **Implementation:** Backend, Frontend, Data, GIS, DevOps.
- **Testing/Validation:** QA + Agronomist (domain validation is its own kind of testing here).
- **Deployment/Ops:** DevOps/Platform, with backups/monitoring/runbooks.
- **Maintenance/Evolution:** the same team, plus ML/Security for Phase 5.

## A leaner version (if full headcount isn't available)
The minimum viable team still **must** include the agronomist and a GIS-capable engineer:
- Agronomist (part-time, co-op) — non-negotiable for the model.
- Full-stack engineer with geospatial skills (covers backend + GIS + some data).
- Frontend engineer (covers UX + web).
- DevOps-leaning engineer (covers infra + data pipelines + on-prem/cloud).
- Product Owner + PM, possibly the same co-op person.
Trade-off: slower delivery and more context-switching, but the critical roles are covered.
