# Phase 3 — Refinement & Validation (plan, validation-spine slice)

**Date:** 2026-05-30
**Phase:** 3 — Refinement & Validation ([doc 07](../07-roadmap-and-phases.md))
**Goal (doc 07):** *make it trustworthy* — validate against ground truth, tune to the ≥80%
agreement target, and have experts trust and use the model.

Phase 3 as scoped in the roadmap is large. **This iteration delivers the validation spine
only** — the harness + tuning loop that the whole "make it trustworthy" goal hinges on — and
explicitly defers the supporting model/UX work to a later iteration.

## In scope (this slice)

- **Ground-truth ingestion** — a labelled-plot CSV loader matching the
  [ground-truth schema](../phase-0/ground-truth-plan.md).
- **Validation harness** — run the pinned-config model per plot, map predicted class → observed
  status, emit a **confusion matrix + agreement %** + per-factor disagreement diagnosis.
- **Tuning loop** — diagnose, change config, **bump the version** (never edit in place, NFR-16),
  re-validate, compare. Demonstrated 2026.1 → 2026.2.
- **Synthetic stratified plot set** — clearly marked, no agronomic claim — to exercise the
  pipeline end-to-end and produce a real report.
- **Report artifacts** — machine-readable JSON + markdown per version, plus a curated
  [validation report](validation-report.md).

## Deferred (later Phase 3 iteration / Phase 4)

Soil factor (SoilGrids), canopy shading from land-cover (ESA WorldCover), agronomist controls
(in-app weight/threshold edits, expert overrides, audit log), batch assessment + save/compare,
TiTiler raster factor-layer map overlays (FR-13), and field-officer UX polish.

## Stakeholders (doc 08 RACI — P3 column)

| Stakeholder (hat) | Role this slice |
|---|---|
| **Agronomist (R)** | Owns the predicted-class → observed-status mapping; diagnoses disagreements; decides the tuning change; provisional (synthetic) sign-off |
| **GIS Specialist (R)** | Validation analysis: confusion matrix, agreement %, per-factor diagnosis |
| **Backend Engineer (R)** | Validation harness package + CLI; ground-truth loader; report renderer |
| **QA Engineer (R)** | Harness unit tests (stub predictor) + live-fixture integration test; suites green |
| **Delivery/PM (R)** | Exit-criteria tracking; Phase 3 risk-register addendum |
| **Product Owner (R)** | Accepts the "validation harness + report" demo |
| **Data Engineer (C)** | Synthetic stratified ground-truth CSV |

## Exit criteria (this slice)

1. `make validate` runs the model over a labelled plot set and writes a confusion-matrix report
   (markdown + JSON) with an agreement %.
2. The tuning loop produces a **new** config version (2026.1 untouched) and the report shows
   before/after agreement.
3. Harness unit + integration tests green; ruff/mypy clean.
4. The report **honestly states** the synthetic data proves the mechanism, not accuracy — the
   ≥80% gate stays open until real co-op data + agronomist sign-off (**R-GT**).

See the [validation report](validation-report.md) for the actual run, diagnosis, and tuning round.
