# Phase 0 — Ground-Truth Validation Plan

**Date:** 2026-05-28
**Phase:** 0 — Discovery & Foundations (planning); execution begins now and feeds Phase 3
**Pilot region:** Nepal mid-hills — Gulmi, Syangja, Kavre (~27–28°N)
**Owning hats:** Agronomist + GIS Specialist
**Related:** [`agronomy-workshop-notes.md`](agronomy-workshop-notes.md), [`docs/03-suitability-model.md`](../03-suitability-model.md) (validation plan), [`docs/01-vision-and-scope.md`](../01-vision-and-scope.md) (≥80% accuracy success criterion)
**Label template (being created by a teammate):** `config/ground-truth/template.csv`

---

## 1. Why ground truth matters — and why it must start NOW

The suitability model (doc 03) is a transparent rule-based weighted overlay, and its current
configuration (version **2026.1**) is a set of **expert priors** — only the altitude band has
been latitude-calibrated; everything else is a species default or a reasoned modifier (see the
agronomy workshop notes). **A model built from priors is not a validated model.** The whole
product's credibility rests on doc 01's success criterion:

> "Suitability class agrees with senior agronomist judgment on **≥ 80%** of a validation set of
> known plots."

We cannot measure that, or tune toward it, without a **labelled set of real plots**. Therefore:

- **Ground truth GATES Phase 3.** Phase 3 is where the model is calibrated and accuracy is signed
  off (doc 08: Agronomist + GIS Specialist are critical/driving in P3). The model cannot be
  declared launch-ready until it clears ≥80% on labelled data.
- **Collection is slow** — it depends on the co-op's field officers and senior agronomists, real
  plots, and at least one cultivation cycle of observed outcomes. **So data collection must begin
  in Phase 0**, in parallel with engineering, or it becomes the critical-path blocker for launch.
- Ground truth is also the **only** way to validate things gridded data cannot see — the
  frost-pocket hard limit and the terrace-smoothing uncertainty (data-spike report) need real
  outcomes to confirm or refute.

## 2. Labelling schema

Each row is one observed plot. The columns below match the CSV template a teammate is creating at
`config/ground-truth/template.csv` (this document defines the columns and their meaning; the
teammate commits the template + synthetic example rows — not real data).

| Column | Type / allowed values | Meaning & notes |
|--------|-----------------------|-----------------|
| `plot_id` | string, unique | Stable identifier for the plot (e.g. `GUL-001`). |
| `latitude` | decimal degrees (WGS84) | Plot centroid latitude. Within the supported region (FR-3). |
| `longitude` | decimal degrees (WGS84) | Plot centroid longitude. |
| `district` | string | One of the pilot districts: Gulmi / Syangja / Kavre (extendable later). |
| `elevation_m_observed` | number (metres) | **Field-measured/GPS** elevation — kept separate from the DEM value so we can also check DEM accuracy vs reality. |
| `observed_status` | enum: `thriving` \| `struggling` \| `failed` | The ground-truth label (see Section 3 mapping). |
| `cultivar` | string | Arabica cultivar (e.g. local selection / known variety) — context for interpreting outcome. |
| `planting_year` | integer (year) | Establishes plant age; very young plants are inconclusive. |
| `notes` | free text | Anything affecting the outcome: management, frost event, pest, irrigation, aspect, shade trees. |
| `labelled_by` | string | Senior agronomist who assigned the label (accountability). |
| `label_date` | date (ISO 8601) | When the label was assigned. |

> The three-way `observed_status` (thriving / struggling / failed) deliberately mirrors doc 03's
> validation language ("thriving / struggling / failed") so the label maps cleanly onto predicted
> suitability classes (Section 4).

## 3. Collection method

1. **Field officers record plots.** During routine field visits, officers capture
   `plot_id`, coordinates, `elevation_m_observed` (GPS), `district`, `cultivar`, `planting_year`,
   and `notes`. Coordinates are treated as sensitive co-op/member data (NFR-12).
2. **Senior agronomists assign `observed_status`.** The expert label is **not** crowdsourced —
   a senior agronomist judges thriving / struggling / failed using the plot record plus their
   knowledge, and fills `labelled_by` + `label_date`. This keeps the ground truth as the
   authoritative human judgment the model is measured against.
3. **Target sample: ≥30–50 plots**, deliberately stratified to:
   - **span all suitability classes** S1 / S2 / S3 / N (we need failures and marginal sites, not
     just good ones — otherwise accuracy is unmeasurable at the boundaries), and
   - **span the full altitude range** of the calibrated bands (~600–1,900 m), including sites near
     the band edges and at least a few suspected **frost-pocket** sites to test that hard limit.
   - cover all three pilot districts.
   This is the minimum for a meaningful first validation; more plots tighten confidence and are
   gathered continuously toward Phase 3.

## 4. Validation procedure

Driven by the Agronomist + GIS Specialist; mirrors doc 03's validation plan and doc 01's target.

1. **Run the model** at the pinned config version (2026.1) for each labelled plot's coordinates.
2. **Map predicted class → expected status** for comparison:
   - S1 / S2 → expected **thriving**
   - S3 → expected **struggling**
   - N → expected **failed**
   (The exact mapping is itself reviewable — record it alongside results so the agreement metric
   is reproducible.)
3. **Compare predicted vs observed** and **measure agreement** (a confusion matrix over the
   classes plus an overall agreement %). **Target ≥ 80%** (doc 01 / doc 03).
4. **Diagnose disagreements.** Where the model is wrong, inspect the per-factor breakdown: is it a
   band edge, a weight, the frost-pocket check, or DEM/climate resolution (terrace smoothing)?
   Use `notes` to rule out non-biophysical causes (bad management, drought year).
5. **Tune** weights / band edges / modifiers in `config/suitability/arabica-2026.x.yaml`.
   **Bump the config version on every change** (2026.1 → 2026.2 → …; NFR-14/16). Never edit a
   published version in place — reproducibility depends on it.
6. **Re-validate** against the same labelled set after every tuning round; iterate until ≥80% is
   met and stable, then have the senior agronomist **sign off** (the Phase 3 gate).
7. As more plots arrive, **hold out** a portion where possible so we are not only tuning to and
   testing on the same rows.

## 5. Status of the data (important)

> **Only a template and synthetic example rows exist right now.** Real, labelled ground-truth
> data **must be supplied by the cooperative** — its field officers collect the plots and its
> senior agronomists assign the `observed_status` labels. The synthetic examples in
> `config/ground-truth/template.csv` exist solely to define the schema, exercise the validation
> harness, and let engineering build the pipeline; **they carry no agronomic meaning and must
> never be used to claim accuracy.** The ≥80% target is only meaningful against real co-op data.
