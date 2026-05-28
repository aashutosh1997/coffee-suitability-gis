# Phase 0 — Discovery Charter

*Owner: Product Owner. Status: in progress (Phase 0).*

## Purpose

Phase 0 (Discovery & Foundations) exists to **de-risk the unknowns before we build**:
to confirm *where* the tool operates, *who* uses it, *what "good" looks like*, and the
*minimum* first slice worth shipping. This charter is the Product Owner's record of those
decisions. It refines the broad statements in [doc 01](../01-vision-and-scope.md) into
concrete, agreed targets, and surfaces the open questions the co-op must answer for the
plan to hold. It is a living document for Phase 0 and is expected to be updated as the
co-op confirms the assumptions flagged below.

## Operating region (confirmed for the pilot)

The pilot is **locked to the Nepal mid-hills** — the **Gulmi, Syangja, and Kavre**
districts, roughly **27–28°N (subtropical)**. This band is representative of the co-op's
Arabica-growing terrain: terraced mid-elevation hillsides where altitude, slope, aspect,
and microclimate vary sharply over short distances.

| Item | Value |
|------|-------|
| Pilot districts | Gulmi, Syangja, Kavre |
| Latitude band | ~27.5°N – 28.2°N (subtropical mid-hills) |
| Indicative bounding box | lon **83.6°E – 85.6°E**, lat **27.5°N – 28.2°N** |
| Box status | **Indicative only** — to be refined against the co-op's actual member-plot footprint |

The bounding box above is a planning placeholder for sizing data ingestion and tiling. It
is **not** the final coverage extent; it will be tightened (or extended) once the co-op
shares the real geographic spread of member plots.

**Coverage expands beyond the pilot post-launch.** The architecture, data pipeline, and
suitability model are built region-agnostic so that, after the pilot validates the
approach, additional districts (and eventually other co-op regions) can be onboarded by
ingesting their tiles — not by re-engineering the tool.

## Operating context

TerraBean is an **internal, authenticated tool** for the cooperative's **agronomists and
field officers**. It is a triage and screening aid that turns a location into an
explainable suitability rating; it is explicitly **not** a public product. The following
non-goals are carried forward from [doc 01](../01-vision-and-scope.md) and remain binding
for the pilot:

- **Not** a public, anonymous consumer app — access is via the org's SSO only.
- **Not** a real-time pest/disease forecasting system.
- **Not** a farm-management / ERP system (no yield tracking, payments, or traceability).
- **Not** a substitute for soil testing or a field visit — it supports the expert, it does
  not replace them.
- **Not** financial or investment advice about land purchases (see "suitability ≠
  profitability" in the risk register).

## Users & concurrency

The pilot user base is the co-op's own agronomy staff and field officers.

| Parameter | Planning assumption |
|-----------|---------------------|
| Named pilot users | ~15–30 field officers / agronomists |
| Design concurrency target | **~50 concurrent users** (per NFR-2) |
| Primary devices | Desktop/laptop in office; tablet for semi-field use is a later phase |
| Access model | Authenticated SSO (OIDC); roles *viewer / agronomist / admin* (FR-19) |

These are **planning assumptions to confirm with the co-op.** The named-user range drives
support and training scope; the ~50-concurrent design target (a headroom figure above the
expected pilot load) drives sizing and the load test in Phase 4. Both are revisited once
the co-op confirms actual staff numbers and usage patterns.

## Success metrics (refines doc 01)

Concrete, measurable targets for the pilot. These sharpen the qualitative criteria in
[doc 01](../01-vision-and-scope.md) into numbers we can verify.

| Dimension | Measurable target | How verified |
|-----------|-------------------|--------------|
| **Accuracy** | ≥ **80%** suitability-class agreement with senior-agronomist judgment on a validation set of known plots | Validation harness vs. ground-truth set (assembled from Phase 0) |
| **Speed (point)** | Point assessment returns in **< 5 s** on a warm cache (NFR-1) | Performance test, p95 latency |
| **Speed (polygon)** | Polygon assessment returns in **< 60 s** for typical co-op plot sizes (NFR-1) | Performance test on representative plot geometries |
| **Adoption** | ≥ **50 assessments / month** within **3 months** of launch | Usage metrics / audit log |
| **Transparency** | **100%** of ratings show a per-factor breakdown **and** data provenance | Automated check on result payload; UX review |
| **Coverage** | Works across the **pilot bounding box** (lon 83.6–85.6°E, lat 27.5–28.2°N) | Spot-assessments across the box; out-of-region rejection (FR-3) |

The polygon-speed target is contingent on the terrain-shading architecture spike — see the
[risk register](risk-register.md) (R-PERF).

## Prioritized Phase 1 scope (terrain-only MVP)

Phase 1 ships the **thinnest end-to-end slice that proves the pipeline**: a location in →
terrain facts + a terrain-only suitability score out, on a map. Climate, shading, soil, and
the full weighted model are deliberately deferred to later phases.

**In scope (Phase 1 — Must):**

1. Accept a **point** (lat/lon) or a **polygon** (drawn or uploaded) as input (FR-1, FR-2).
2. Derive **altitude** (point value / min-mean-max over a polygon) (FR-5).
3. Derive **slope** and **aspect** from the DEM (FR-6).
4. Produce a **terrain-only suitability score** (altitude + slope + aspect) to exercise the
   scoring-config pipeline end to end (subset of FR-12).
5. **Display** the AOI and terrain results on an interactive map with a basic result panel
   (FR-13), including the per-factor values that fed the score.

**Explicitly deferred (not Phase 1):** temperature/rainfall factors, terrain/canopy
shading, soil, the full weighted-overlay model, PDF report, expert override, batch input.

**Phase 1 acceptance:** an agronomist can drop a pin or draw a plot inside the pilot box and
see altitude/slope/aspect plus a terrain-only suitability rating rendered on the map.

## Open questions for the co-op

These must be answered to firm up the assumptions above and the Phase 0 plan.

| # | Question | Why it matters |
|---|----------|----------------|
| Q1 | What are the **real plot sizes** (typical and largest) for member farms? | Drives the polygon-speed NFR, zonal-stats cost, and the DEM-resolution spike. |
| Q2 | What **working language(s)** do field officers use? | Determines whether UI localization (NFR-18) is pilot-scope or later. |
| Q3 | What **on-prem hardware** is available (CPU/RAM/disk/GPU)? | Drives container sizing, concurrency feasibility, and the on-prem deploy plan. |
| Q4 | What is the co-op's **data-retention policy** for plot coordinates and audit logs? | Plot coordinates are sensitive member data (NFR-12/13); sets retention config. |
| Q5 | Any **licensing preference or constraint** (open-data only, attribution rules, redistribution limits)? | Constrains DEM/climate dataset selection in the data spike. |
