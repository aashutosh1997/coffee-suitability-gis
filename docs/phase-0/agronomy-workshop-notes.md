# Phase 0 — Agronomy Calibration Workshop Notes

**Date:** 2026-05-28
**Phase:** 0 — Discovery & Foundations
**Pilot region:** Nepal mid-hills — Gulmi, Syangja, Kavre districts (~27–28°N), subtropical highland
**Model config under calibration:** `config/suitability/arabica-2026.1.yaml` (version **2026.1**)
**Owning hat:** Agronomist

---

## 1. Purpose

This workshop translates the **species-level Arabica suitability defaults** in
[`docs/03-suitability-model.md`](../03-suitability-model.md) into a **region-calibrated**
starting configuration for the cooperative's pilot operating area. Doc 03 is explicit that
its thresholds are "sensible starting defaults for tropical highland Arabica [that] MUST be
reviewed and calibrated with the cooperative's agronomists for the specific region(s) before
launch" and that "optimal bands shift with latitude." The pilot region — the Nepal mid-hills
at roughly 27–28°N — is a **subtropical highland**, not equatorial, so at minimum the altitude
band needs adjustment. This document records those decisions and their agronomic rationale.

The numbers themselves are being committed by a teammate to `config/suitability/arabica-2026.1.yaml`
(NFR-14: thresholds are version-controlled configuration, not code). This file is the
**agronomic rationale of record** that justifies what goes into that YAML.

## 2. Attendees (simulated Phase 0 workshop)

| Role | In the workshop for |
|------|---------------------|
| Senior Agronomist (co-op, lead) | Owns the suitability logic; final sign-off on thresholds (doc 08: "critical" in P0/P2/P3) |
| Senior Agronomist (co-op, field) | 20+ yrs cultivation experience across the mid-hills; tacit knowledge being captured |
| GIS Specialist / Geospatial Data Scientist | Maps each factor to an available dataset and its resolution; flags what terrain analysis can/can't see |
| Product Owner (co-op) | Confirms pilot districts and that ground-truth plots can be sourced |

## 3. Scope of this calibration

Of the six model factors, **only altitude is re-banded** in version 2026.1. Temperature,
precipitation, slope, and shading/solar **retain the doc-03 species-level defaults** pending
local validation against ground-truth plots (Section 6). Two **modifiers** are confirmed for
the monsoon context: a rainfall-distribution bonus and a frost-pocket hard limit. Soil remains
out of scope (Phase 3+, advisory).

Factor weights are **unchanged** from doc 03 and locked for 2026.1:
altitude **0.25**, mean annual temperature **0.25**, annual precipitation **0.20**,
slope **0.15**, shading/solar **0.15**. Class cutoffs unchanged: S1 ≥0.80, S2 0.60–0.79,
S3 0.40–0.59, N <0.40.

## 4. Per-factor calibration decisions

### 4.1 Altitude — RE-BANDED for ~28°N (the headline decision)

**Doc-03 default (tropical):** optimal 1,200–2,000 m.
**Calibrated for Nepal mid-hills (subtropical):**

| Band | Range (m) | Sub-score |
|------|-----------|-----------|
| Optimal | 1,000–1,500 | 1.0 |
| Good | 800–1,000 or 1,500–1,700 | 0.8 |
| Marginal | 600–800 or 1,700–1,900 | 0.4 |
| Unsuitable | < 600 or > 1,900 | 0.0 (**hard limit**) |

**Why the optimal band shifts LOWER than equatorial Arabica.**
Altitude is a proxy for temperature. Arabica's true requirement is a **temperature window**
(roughly 18–22 °C mean annual, doc 03); altitude only matters because air cools with elevation
(the environmental lapse rate, ~6.5 °C per 1,000 m). The altitude that delivers that 18–22 °C
window depends on how warm sea level is at a given latitude:

- **Near the equator (0–10°N/S)**, lowlands are very hot year-round, so you must climb to
  ~1,200–2,000 m to reach Arabica's optimal temperatures — hence the tropical default.
- **At ~28°N (Nepal mid-hills)**, the subtropical setting means the whole temperature profile
  sits **cooler at a given elevation** than at the equator, and there is a genuine cool winter.
  The 18–22 °C mean-annual window is therefore reached **lower down the slope**, around
  **1,000–1,500 m**. Pushing the optimum up to 2,000 m here would place it where the climate is
  too cool and frost-prone, slowing growth and risking lethal cold.
- Consequently the **upper hard limit is pulled down to 1,900 m** (vs 2,400 m tropical):
  above this in the mid-hills, frost frequency and very slow maturation make Arabica unviable.
  The **lower edge (600 m)** reflects that below it the mid-hill valleys get too warm, favoring
  accelerated ripening, leaf rust, and coffee berry borer.

This is the concrete expression of doc 03's note that "nearer the equator the optimal altitude
band sits higher." The mid-hills are well off the equator, so the band sits lower.

> Cross-check: the calibrated altitude bands should produce mean annual temperatures that fall
> inside the temperature factor's optimal/good bands for the same site. Where altitude says
> "optimal" but modeled temperature says "marginal," trust temperature — it is the more direct
> driver — and treat the mismatch as a calibration signal during validation.

### 4.2 Mean annual temperature — DEFAULT retained (weight 0.25)

Optimal 18–22 °C, hard limits <14 °C / >25 °C (doc 03). Temperature is the **strongest and
most direct** climatic driver, and the species window is well established and not
latitude-dependent (latitude affects *where* you find it, not *what it is*). Kept as-is; it is
also the cross-check against the re-banded altitude (above). Validate against CHELSA-derived
mean annual temperature at the ground-truth plots before any change.

### 4.3 Annual precipitation — DEFAULT retained (weight 0.20)

Optimal 1,400–2,000 mm, hard floor <1,000 mm (doc 03). The mid-hills sit comfortably in the
monsoon belt and typically receive ample annual rainfall, so the **annual total is rarely the
binding constraint** here — *distribution* matters more (see modifier below). Defaults retained.

### 4.4 Slope — DEFAULT retained (weight 0.15)

Optimal 5–25%, unsuitable >60% (doc 03). The mid-hills are steep and heavily **terraced**;
moderate-to-steep slopes are the norm and are managed with terracing. The default bands already
reward moderate slope (drainage, cold-air movement) and penalise both waterlogging flats and
ungovernable >60% faces. Retained — but note the DEM-resolution caveat in Section 7.

### 4.5 Shading / solar exposure — DEFAULT retained (weight 0.15)

Default conditions from doc 03 retained. The important interaction for this region is captured
by the **frost-pocket hard-limit candidate** (doc 03 lists frost-pocket / strong cold-air
pooling at sub-score 0.2, hard-limit candidate) — see Section 5.2. Canopy-shade refinement waits
for land-cover data (Phase 3+).

## 5. Monsoon-context modifiers

### 5.1 Rainfall-distribution modifier — small POSITIVE bonus for the dry winter

Arabica wants "abundant, well-distributed rain **plus a short dry/cool period to trigger even
flowering**" (doc 03). The Nepal mid-hills monsoon is strongly seasonal: **wet June–September**,
then a **distinct dry, cool winter (November–February)**.

- That dry/cool winter is a textbook **even-flowering trigger**: it imposes the water stress
  followed by rain that synchronises blossom, which in turn gives a more uniform ripening and an
  easier, higher-quality selective harvest.
- This is exactly the "distinct dry period of 2–4 months" case for which doc 03 prescribes a
  **small bonus**. Nov–Feb is ~4 months, squarely in range.
- **Decision:** apply the **small positive** rainfall-distribution modifier for the pilot region,
  computed from monthly climate normals (CHELSA monthly), not the inverse penalty. The monsoon is
  decidedly *not* aseasonal, so the penalty branch does not apply here.
- **Magnitude:** small and bounded, so it nudges borderline scores without overpowering the
  weighted factors. Exact value lives in the YAML; validate it does not flip classes on its own.

### 5.2 Frost-pocket / cold-air pooling — HARD-LIMIT candidate

The mid-hills' steep, dissected terrain creates **valley-bottom and basin frost pockets** where
cold air drains and pools on clear winter nights — a real risk Nov–Feb at the upper/cooler end of
the cultivation range. Gridded ~1 km climate **cannot see** these microclimates (doc 01 risk:
"gridded climate misses frost pockets, valley fog, local cold-air drainage"), but **terrain
analysis can** (cold-air-drainage / sky-view indicators from the DEM, per doc 03's shading factor
and doc 06's computed insolation).

- **Decision:** where the terrain model flags **strong cold-air pooling / frost-pocket**, treat
  it as a **hard limit → class N**, consistent with Liebig's law of the minimum (one fatal factor
  ruins the site). Frost is lethal to Arabica.
- This is a conservative, safety-first default for the pilot: better to flag a marginal frost-risk
  site for expert review than to recommend planting into a killing frost. Field officers can route
  flagged sites to a senior agronomist (expert override, FR-17).

## 6. Validation handoff (this is a starting point, not a finished model)

These bands and modifiers are **expert priors**. They become trustworthy only after comparison
against the co-op's real plots. The procedure (doc 03 validation plan, doc 01 ≥80% accuracy
target) is detailed in [`ground-truth-plan.md`](ground-truth-plan.md):

1. Assemble ≥30–50 labelled plots spanning all suitability classes and the full altitude range.
2. Run the model at config version 2026.1; compare predicted class vs observed status.
3. Measure agreement (target **≥80%**).
4. Tune bands/weights/modifiers; **bump the config version** on every change; re-validate.

## 7. Known limitations feeding into validation

- **DEM ~30 m smooths terraces** (doc 06 caveat): slope and altitude on small terraced plots
  carry uncertainty; the model must surface this in `uncertainty_notes` (doc 03 output contract).
- **~1 km climate grids** average over terrain — the frost-pocket terrain check (5.2) is the
  primary microclimate compensation, but it is itself unvalidated until ground truth confirms it.
- All non-altitude bands are **untouched species defaults** — expect the temperature and
  precipitation edges in particular to need local tuning once plot data arrives.

---

> ## CAVEAT — READ BEFORE TRUSTING THESE NUMBERS
>
> **Everything in version 2026.1 is an EXPERT STARTING DEFAULT, not a validated model.**
> Only the **altitude band** has been calibrated for latitude; temperature, precipitation,
> slope, and shading remain species-level defaults from doc 03. The rainfall bonus and
> frost-pocket hard limit are reasoned priors, not measured.
>
> These thresholds **MUST be validated and tuned against the cooperative's real ground-truth
> plots before launch.** Do not present results to farmers as authoritative until the ≥80%
> agreement target (doc 01) is met on a labelled validation set.
>
> **Every change to a threshold, weight, band edge, or modifier MUST bump the model config
> version** (e.g. 2026.1 → 2026.2). Thresholds are version-controlled configuration, never
> hard-coded (**NFR-14**), and every rating must be reproducible from inputs + config version
> (**NFR-16**). This is how a tuned model stays auditable and how past assessments remain
> explainable.
