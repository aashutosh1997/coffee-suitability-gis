# Phase 0 — Delivery Plan

*Owner: Delivery / Project Manager. Status: in progress (Phase 0).*

## Goal

De-risk the unknowns and stand up the engineering foundation, so that Phase 1 starts
against agreed thresholds, chosen datasets, a green CI pipeline, and a deployable walking
skeleton. This plan operationalizes [doc 07](../07-roadmap-and-phases.md) for the locked
**Nepal mid-hills pilot** (Gulmi, Syangja, Kavre).

## Exit criteria (the four documented gates)

Phase 0 is **done** when all four are true:

1. **Thresholds agreed** — the suitability thresholds/weights are fixed with the co-op's
   agronomist(s) and captured as version-controlled config ([doc 03](../03-suitability-model.md)).
2. **Datasets chosen** — DEM and climate datasets selected for the pilot box, resolution
   validated against real plot sizes, licenses confirmed ([doc 06](../06-data-sources.md)).
3. **CI green** — the CI pipeline runs and passes on the scaffolded repo.
4. **Walking skeleton deploys locally** — a thin end-to-end stack (containerized) stands up
   and serves a trivial request on a developer machine.

## Workstreams and responsible role hats

RACI-lite is per [doc 08](../08-team-and-roles.md): in Phase 0 the **Product Owner,
Agronomist, Delivery/PM, GIS Specialist, and DevOps/Platform** drive (`R`); **Backend, UX,
and Data Engineer** contribute (`C`). "Lead" below = the `R` for that workstream.

| # | Workstream | Lead (drives, R) | Contributors (C) | Output / artifact |
|---|-----------|------------------|------------------|-------------------|
| WS1 | **Discovery & charter** (region, users, concurrency, success metrics, Phase 1 scope, open questions) | Product Owner | Delivery/PM, GIS Specialist | [discovery-charter.md](discovery-charter.md) |
| WS2 | **Agronomy workshop** — fix suitability thresholds/weights | Agronomist | Product Owner, GIS Specialist | Versioned scoring config ([doc 03](../03-suitability-model.md)) |
| WS3 | **Data spike** — evaluate DEM/climate resolution vs. real plot sizes; pick datasets; confirm licenses | GIS Specialist | Data Engineer | Dataset decision + license notes ([doc 06](../06-data-sources.md)) |
| WS4 | **Architecture spike** — heaviest geoprocessing step (terrain shading over a polygon) | GIS Specialist | Backend Eng | Spike findings + polygon-<60 s feasibility call |
| WS5 | **Repo / CI / containers / dev env scaffold** | DevOps/Platform | Backend Eng | Scaffolded repo, green CI, container baselines ([doc 09](../09-development-setup.md)) |
| WS6 | **Walking skeleton** — thin end-to-end stack that deploys locally | DevOps/Platform | Backend Eng | Locally-deployable skeleton |
| WS7 | **Validation / ground-truth dataset** — start assembling (gates Phase 3) | Agronomist | Product Owner, GIS Specialist | Seed ground-truth set of known plots |
| WS8 | **UX discovery** — low-fi flow sketches for non-GIS field officers | UX/UI Designer | Product Owner | Flow sketches for the Phase 1 MVP |
| WS9 | **Planning, ceremonies, risk** | Delivery/PM | (all) | This plan + [risk register](risk-register.md) |

## Indicative ~4-week schedule

A ~4-week Phase 0 (per [doc 07](../07-roadmap-and-phases.md)). Workstreams overlap; the
table shows what **lands** each week.

| Week | Focus | What lands |
|------|-------|-----------|
| **W1** | Frame & set up | Charter draft circulated (WS1); repo + CI skeleton up (WS5 start); risk register opened (WS9); open questions sent to co-op. |
| **W2** | Domain & data | Agronomy workshop held, draft thresholds captured (WS2); data spike under way, candidate DEM/climate datasets shortlisted (WS3); UX flow sketches drafted (WS8). |
| **W3** | Spikes & skeleton | Architecture/terrain-shading spike results + polygon-<60 s call (WS4); datasets chosen with licenses confirmed (WS3 done); walking skeleton deploying locally (WS6); CI green on scaffold (WS5 done); ground-truth seed started (WS7). |
| **W4** | Lock & gate | Thresholds signed off as versioned config (WS2 done); exit-criteria review; Phase 1 backlog ready; co-op answers to open questions folded into the charter. |

## Refined planning estimates — Phases 1–5

Baseline durations from [doc 07](../07-roadmap-and-phases.md). **All estimates are to be
confirmed** once Phase 0 closes (region footprint, data resolution, concurrency, and the
spike outcomes feed directly into these). The "Phase 0 input" column notes what could move
each number.

| Phase | Theme | Baseline (doc 07) | Status of estimate | Key Phase 0 input that could shift it |
|-------|-------|-------------------|--------------------|---------------------------------------|
| **1** | Core Geospatial MVP (terrain + map) | ~6 weeks | To be confirmed | Terrain-shading spike (WS4); real plot sizes (Q1) |
| **2** | Climate & Shading (full v1 model) | ~6 weeks | To be confirmed | Chosen climate dataset (WS3); shading feasibility (WS4) |
| **3** | Refinement & Validation | ~6 weeks | To be confirmed | Ground-truth set readiness (WS7); agronomist availability |
| **4** | Hardening & On-Prem Deployment | ~4 weeks | To be confirmed | On-prem hardware sizing (Q3); concurrency target |
| **5** | Cloud Migration & Advanced *(optional)* | ~8 weeks | To be confirmed | Only if scale/ML are needed post-launch |

> Note: the [doc 07](../07-roadmap-and-phases.md) Gantt shows indicative day-counts
> (Phase 1–3 at 45d each, Phases 0/4 at 30d, Phase 5 at 60d). The week figures above are
> the prose estimates from the same doc; both are planning figures pending Phase 0 sign-off.

## Exit-criteria checklist

| Done | Exit criterion | Owning hat | Current status |
|:----:|----------------|------------|----------------|
| [ ] | **Thresholds agreed** & captured as versioned config | Agronomist | In progress — agronomy workshop scheduled (W2), sign-off targeted W4. |
| [ ] | **Datasets chosen** (DEM + climate), resolution validated, licenses confirmed | GIS Specialist | In progress — data spike running; shortlist due W2, decision W3. |
| [ ] | **CI green** on the scaffolded repo | DevOps/Platform | In progress — repo + CI scaffold being stood up (W1–W3). |
| [ ] | **Walking skeleton deploys locally** | DevOps/Platform | In progress — targeted W3 once container baselines land. |

## Cadence & ceremonies

Kept light for a small Phase 0 team; demos and risk review run every phase
([doc 07](../07-roadmap-and-phases.md) cross-cutting).

- **Weekly demo / review** — end of each week; show the increment (charter draft, CI, spike
  results, skeleton) to the Product Owner and co-op stakeholders.
- **Async daily standup** — written check-in (done / next / blockers); no scheduled meeting.
- **Risk review** — reviewed at the weekly demo and formally at the W4 exit gate (see the
  [risk register](risk-register.md)).
