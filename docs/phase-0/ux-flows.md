# Phase 0 — UX Flows & Wireframes

**Date:** 2026-05-28
**Phase:** 0 — Discovery & Foundations
**Owning hat:** UX/UI Designer
**Related:** [`docs/01-vision-and-scope.md`](../01-vision-and-scope.md) ("explainable" goal), [`docs/02-requirements.md`](../02-requirements.md) (FR-1/2/12/13/14/15/16/17, NFR-17/19), [ADR-0004](../adr/0004-ui-library-mantine.md) (UI library: Mantine), [`docs/03-suitability-model.md`](../03-suitability-model.md) (output contract)

---

## 1. Primary user & design principles

**Primary user: the non-GIS field officer.** They are a coffee/agronomy practitioner, not a GIS
analyst. The UI must let them get a trustworthy, understandable answer without learning GIS.

Design principles (from doc 01's "explainable" goal and NFR-17 "usable by non-GIS-expert field
officers; sensible defaults, minimal jargon"):

1. **Minimal jargon.** Plain language everywhere ("a bit too cool at this altitude"), never raw
   GIS terms ("sky-view factor", "CRS", "zonal stats") in the primary view. Technical detail is
   available on demand, not in the user's face.
2. **Sensible defaults.** The tool pre-fills everything it can (region, model config version, map
   center) so the happy path is: pick a place → run → read the answer.
3. **Explainability first.** The result is **never a bare verdict**. Every rating shows the
   per-factor breakdown, the raw value, the band it fell into, a plain-language reason, and where
   the data came from (FR-14, FR-15, doc 01: "must never be a black box"). The single biggest
   reason for the rating — the **limiting factor** — is shown up front.
4. **Trust through transparency, with an expert escape hatch.** An agronomist can disagree and
   record an **expert override** with a note (FR-17), so the human stays in charge.

## 2. Core user flow

```
[1] SIGN IN  (SSO / OIDC — Phase 4)
        |     roles: viewer / agronomist / admin (FR-19)
        v
[2] CHOOSE AOI
        |   - drop a point on the map           (FR-1)
        |   - draw a polygon                     (FR-2)
        |   - upload GeoJSON / KML / shapefile   (FR-2)
        |   (coordinates validated; out-of-region flagged — FR-3)
        v
[3] RUN ASSESSMENT
        |   point < 5 s; polygon runs async with progress (NFR-1, NFR-3)
        v
[4] VIEW RESULTS
        |   map (AOI + toggleable factor layers, FR-13)
        |   + result panel (overall S-class + limiting factor + per-factor cards)
        v
[5] (optional)
        |-- EXPORT PDF report           (FR-16)
        \-- RECORD EXPERT OVERRIDE      (agronomist role, FR-17)
```

**Note on Phase 0 scope:** sign-in (step 1, SSO) lands in **Phase 4**; for the Phase 0 web slice
it is stubbed/skipped. The override and PDF (step 5) are **Should** requirements that arrive in
later phases. The Phase 0 web slice is **intentionally minimal** — see Section 4.

## 3. Wireframes (low-fidelity)

### (a) Assessment screen — map + result panel

```
+--------------------------------------------------------------------------------+
|  TerraBean  ·  Coffee Land Suitability            region: Nepal mid-hills  [v] |
+--------------------------------------+-----------------------------------------+
|                                      |  RESULT                                 |
|   [ point ] [ polygon ] [ upload ]   |                                         |
|                                      |   +-----------------------------------+ |
|        (interactive map)             |   |   OVERALL:   [  S2  ]             | |
|                                      |   |   Moderately Suitable             | |
|         o  <- AOI marker             |   |   score 0.74                      | |
|        /                             |   +-----------------------------------+ |
|                                      |                                         |
|                                      |   Biggest limitation:                   |
|   Layers:                            |     >> Rainfall                         |
|    [x] Altitude                      |        a little high for this site      |
|    [ ] Temperature                   |                                         |
|    [ ] Rainfall                      |   Per-factor breakdown:                 |
|    [ ] Slope                         |     Altitude .............. Optimal     |
|    [ ] Shading                       |     Temperature ........... Optimal     |
|                                      |     Rainfall .............. Marginal  ! |
|                                      |     Slope ................. Good        |
|                                      |     Shading ............... Good        |
|                                      |                                         |
|  [ Run assessment ]                  |   [ Export PDF ]   [ Expert override ]  |
+--------------------------------------+-----------------------------------------+
   model config: 2026.1                            (override/PDF: later phases)
```

Notes:
- The **overall S-class badge** is the largest element, color-coded (S1 best → N worst), with the
  plain-language label beneath it, never the bare code alone.
- The **limiting factor** ("biggest limitation") is surfaced prominently — it is the one thing a
  field officer most needs (doc 03 reports it explicitly).
- Each per-factor row is clickable → expands the breakdown card (b).
- AOI tools (point / polygon / upload) sit on the map; layer toggles map to FR-13.
- `model config: 2026.1` is always visible for reproducibility/provenance (NFR-16).

### (b) Per-factor breakdown card

Shown when a factor row is expanded. Carries raw value, band, plain-language explanation, and data
provenance (FR-14 + FR-15) — the heart of "explainable."

```
+----------------------------------------------------------+
|  RAINFALL                                      [ Marginal ]
|----------------------------------------------------------|
|  Measured:   2,650 mm / year                             |
|  Band:       Marginal  (2,500–3,000 mm)                  |
|                                                          |
|  What this means:                                        |
|   "There is a lot of rain here. That raises the risk     |
|    of fungal disease, so this counts against the site."  |
|                                                          |
|  Weight in score: 0.20                                   |
|----------------------------------------------------------|
|  Data source:  CHELSA  ·  ~1 km  ·  retrieved 2026-05-28 |
|  Note: ~1 km climate grid averages over the local area.  |
+----------------------------------------------------------+
```

Notes:
- Raw value + unit, then the **band** (matching doc 03's table), then a **plain-language** reason
  — no model jargon.
- The **data source line** (dataset · resolution · retrieval date) satisfies provenance (FR-15)
  and lets an expert judge how much to trust a value given resolution (doc 06).
- Uncertainty notes (e.g. the ~30 m DEM terrace-smoothing caveat from the data spike) appear here
  for the relevant factors, mapping to the model's `uncertainty_notes` (doc 03 output contract).

### (c) Tablet / field layout — NOTE (later)

Tablet/semi-field use is **NFR-19 (Could)** and a **later phase** (offline mode later still). Not
designed in detail now; recording the intent so today's component choices don't paint us in:

```
  Phone/tablet (stacked, later):
  +-----------------------------+
  |  [ S2 ] Moderately Suitable |   <- result first (field officer wants the answer)
  |  Limiting: Rainfall         |
  +-----------------------------+
  |        (map below)          |
  |          o                  |
  +-----------------------------+
  |  v factor breakdown (tap)   |
  +-----------------------------+
```

- On narrow screens the **result leads** and the map follows (a field officer outdoors wants the
  verdict first); on desktop they sit side-by-side as in (a).
- Larger touch targets, fewer simultaneous layers. Mantine's responsive primitives support this
  without a redesign. Detailed tablet work and offline caching are deferred per NFR-19.

## 4. Tooling decisions & Phase 0 scope

- **UI component library: Mantine** (ADR-0004) — accessible, batteries-included components
  (cards, badges, tabs, responsive layout) that match the "minimal jargon, sensible defaults"
  principle and the doc 05 frontend stack (React + TypeScript + Vite + MapLibre GL JS).
- **Map: MapLibre GL JS** (doc 05) for the map area and toggleable factor layers; **Terra Draw**
  for polygon AOI drawing.
- **The Phase 0 web slice is intentionally minimal.** Its only job is to **prove the toolchain
  and render a map** — confirm React + Vite + Mantine + MapLibre build and run, a map tile
  renders, and a stubbed assessment result can be displayed. Auth (SSO), polygon async jobs, PDF
  export, expert override, and the tablet layout are **explicitly out of scope for Phase 0** and
  arrive in later phases (per [`docs/07-roadmap-and-phases.md`](../07-roadmap-and-phases.md)).
  These wireframes are the design target the later phases build toward, not the Phase 0 deliverable.
