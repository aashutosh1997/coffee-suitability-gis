# 01 — Vision & Scope

## Problem

A coffee cooperative needs a fast, consistent, evidence-based way to judge whether a
plot of land is suitable for Arabica coffee. Today this judgment relies on the tacit
knowledge of a few senior agronomists and scattered field visits. It is slow, hard to
scale across many member farmers, and inconsistent from one assessor to the next.

The physical drivers of Arabica suitability — **altitude, temperature, rainfall, slope,
aspect, and shading** — are all derivable from open geospatial data given a location.
A tool that turns coordinates into a transparent suitability assessment lets the co-op
advise more farmers, more consistently, with less field time.

## Vision

> Given the coordinates (or drawn boundary) of any plot, return within seconds a clear,
> explainable Arabica-suitability rating, broken down by factor, on a map the agronomist
> can interpret and share.

"Explainable" is a first-class goal. The tool must never be a black box: every rating
shows the underlying numbers (e.g. "mean annual temp 24.1 °C → marginal") so a human
expert can sanity-check and override it.

## Goals

1. Accept a point coordinate **or** a polygon boundary as input.
2. Derive altitude, slope, aspect, and terrain/canopy shading from elevation and land-cover data.
3. Retrieve temperature and rainfall (climate normals + recent observations) for the location.
4. Score each factor against agronomic thresholds and produce an overall suitability class.
5. Visualize results on an interactive map with per-factor overlays.
6. Generate a shareable report (PDF/print) for a plot.
7. Let an agronomist adjust model weights/thresholds and record an expert override.

## Non-goals (initially)

- **Not** a public, anonymous consumer app — it is an internal, authenticated tool.
- **Not** a real-time pest/disease forecasting system (possible later).
- **Not** a farm-management / ERP system (yield tracking, payments, traceability).
- **Not** a substitute for soil testing or a field visit — it is a *triage and screening* aid.
- **Not** providing financial or investment advice about land purchases.

## Success criteria

| Dimension | Target |
|-----------|--------|
| Accuracy | Suitability class agrees with senior agronomist judgment on ≥ 80% of a validation set of known plots |
| Speed | Point assessment < 5 s; polygon assessment < 60 s for typical co-op plot sizes |
| Adoption | Field officers run ≥ 50 assessments/month within 3 months of launch |
| Transparency | 100% of ratings show per-factor breakdown and data provenance |
| Coverage | Works across the co-op's operating region(s) defined in Phase 0 |

## Key assumptions & risks

- **Data resolution.** Global open DEMs (~30 m) and climate grids (~1 km) may be coarse
  for very small plots; we mitigate with the best available regional data and clear
  uncertainty messaging. (Tracked as a Phase 0 spike.)
- **Climate ≠ microclimate.** Gridded climate misses frost pockets, valley fog, and local
  cold-air drainage. Terrain analysis partially compensates; expert review covers the rest.
- **Suitability ≠ profitability.** The tool assesses biophysical suitability only.
- **Ground truth for validation** must be assembled with the agronomy team early.
