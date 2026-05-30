# Phase 3 — Validation Report

**Date:** 2026-05-30
**Phase:** 3 — Refinement & Validation (validation-spine slice)
**Owning hats:** Agronomist + GIS Specialist (analysis); Backend + QA (harness)
**Config versions:** `arabica-2026.1` (baseline) → `arabica-2026.2` (tuned)
**Generated artifacts:** [`validation-2026.1.md`](validation-2026.1.md) /
[`.json`](validation-2026.1.json), [`validation-2026.2.md`](validation-2026.2.md) /
[`.json`](validation-2026.2.json)

---

> ⚠️ **SYNTHETIC DATA — THIS IS NOT AN ACCURACY CLAIM.** Every number below is produced
> against [`config/ground-truth/synthetic_plots.csv`](../../config/ground-truth/synthetic_plots.csv)
> — a stratified but **fabricated** plot set that carries **no agronomic meaning**. It exists
> only to exercise the validation harness end-to-end and prove the mechanism works. The ≥80%
> launch target ([doc 01](../01-vision-and-scope.md)) is meaningful **only** against real
> co-op-labelled plots ([ground-truth-plan.md §5](../phase-0/ground-truth-plan.md)). Treating
> the agreement % here as model accuracy would be wrong.

## 1. What this validates

Phase 2 delivered the full v1 five-factor model, but `arabica-2026.1` is a set of **expert
priors** — only altitude is region-calibrated. The product's credibility rests on doc 01's
criterion (*suitability class agrees with senior agronomist judgment on ≥80% of known plots*),
and that gate **is** Phase 3. Since no real labelled plots exist yet, this slice builds and
exercises the **validation harness** — the machine that will measure that ≥80% once real data
arrives — and demonstrates the **version-controlled tuning loop** on synthetic data.

## 2. Method

1. **Plot set:** 40 synthetic plots, stratified across S1/S2/S3/N expectations, ~150–2,250 m,
   the three pilot districts (Gulmi/Syangja/Kavre) + a few extended-region Terai lowland sites,
   with frost-pocket candidates and deliberate model/observation mismatches.
2. **Run the model** at a pinned config version for each plot's coordinates (real national
   GLO-90 DEM + DEM-derived climate, seeded in Phase 2), via the in-process engine.
3. **Map predicted class → expected observed status** ([ground-truth-plan §4.2](../phase-0/ground-truth-plan.md)):
   `S1|S2 → thriving`, `S3 → struggling`, `N → failed`. The mapping is recorded so the metric is
   reproducible and itself reviewable.
4. **Agreement %** = fraction of scored plots where `mapped(predicted) == observed`; reported
   with a 3×3 confusion matrix and a per-factor diagnosis of disagreements.

Harness: [`backend/app/validation/`](../../backend/app/validation/). Reproduce with `make validate`.

## 3. Baseline result — `arabica-2026.1`

**Agreement: 18/40 = 45.0%** (0 excluded).

Confusion matrix (rows = observed, columns = mapped prediction):

| observed \ predicted | thriving | struggling | failed |
|---|---|---|---|
| **thriving** | 14 | 0 | 1 |
| **struggling** | 10 | 0 | 2 |
| **failed** | 9 | 0 | 4 |

## 4. Diagnosis

Two structural findings — **independent of the synthetic labels** — dominate:

- **The "struggling" (S3) column is empty.** The model never returns S3. Inspecting the per-plot
  scores, sites either clear the weighted overlay (score ≥0.60 → S1/S2) or trip a **hard limit**
  (altitude <600 m / >1,900 m, frost pocket → N). Scores that *land* in the S3 range (0.40–0.59)
  do so only because a hard limit already forced N. So the rating jumps straight from "moderately
  suitable" to "not suitable" with **no marginal middle** — a model-shape problem worth fixing
  regardless of any ground truth.
- **Strong optimistic bias on the synthetic set.** Many plots labelled struggling/failed score
  0.78–1.00 (→ S1/S2/thriving). This is expected and instructive: the smooth DEM-derived climate
  does **not** encode the real-world stressors the synthetic labels imagined (poor management,
  pests, irregular rainfall, young plants, sheltered microclimates). **Gridded biophysical data
  cannot see these** — exactly why real ground truth and expert review are non-negotiable
  (extends risk **R-CLIM** / **R-MISUSE**).

Limiting factor among disagreements (2026.1): `slope (10), altitude (8), shading (4)` — i.e. the
weakest of otherwise-high factors, consistent with the optimistic-bias reading.

## 5. Tuning round — `arabica-2026.2`

Per [NFR-16](../02-requirements.md), `2026.1` is **never edited in place** — the change ships as a
new version. The one change addresses finding #1 (the unreachable S3), **justified on model-shape
grounds, not fitted to the synthetic labels**:

> Widen S3 upward so moderate limitations read as "marginally suitable" instead of being lumped
> with optimal sites: `class_thresholds` S2 floor **0.60 → 0.70**, S3 floor **0.40 → 0.50**.
> (Factors, weights, and bands are byte-for-byte identical to 2026.1.)

**Agreement: 19/40 = 47.5%** (+2.5 pp). The S3 column is now populated:

| observed \ predicted | thriving | struggling | failed |
|---|---|---|---|
| **thriving** | 14 | 0 | 1 |
| **struggling** | 9 | **1** | 2 |
| **failed** | 8 | **1** | 4 |

One plot (`SYA-004`, score 0.66) moved S2 → S3 and now agrees with its "struggling" label; no
"thriving" plot regressed. The headline number barely moves — **as it should**: you cannot tune a
biophysical model to labels that encode non-biophysical causes, and chasing this synthetic
agreement % upward would be the overfitting trap (**R-OVERFIT**). The win is qualitative: the model
can now **express** marginal suitability.

## 6. Real-CHELSA re-run (2026-05-30 — `arabica-2026.1` and `arabica-2026.2`)

Following the synthetic baseline above, the climate datasets were re-seeded from **real
CHELSA V2.1 (1981–2010 climatology)** via `/vsicurl/` per [ADR-0007](../adr/0007-climate-source-worldclim-vs-chelsa.md),
implemented in [`data-pipelines/ingest/fetch_chelsa.py`](../../data-pipelines/ingest/fetch_chelsa.py).
The synthetic DEM-derived generator remains as the offline/CI fallback (R-NET).
**Same harness, same synthetic plot set, same configs — only the climate input changed.**
The generated machine reports at the top of this document
([`validation-2026.1.md`](validation-2026.1.md) / [`.json`](validation-2026.1.json),
[`validation-2026.2.md`](validation-2026.2.md) / [`.json`](validation-2026.2.json)) now
reflect this real-CHELSA run.

**Headline:**

| Config | Synthetic agreement | **CHELSA agreement** | Δ |
|---|---|---|---|
| 2026.1 | 18/40 = 45.0% | **17/40 = 42.5%** | −2.5 pp |
| 2026.2 | 19/40 = 47.5% | **18/40 = 45.0%** | −2.5 pp |

**The headline % moved less than the diagnosis quality did — which is the real win.**
Limiting-factor tally in 2026.1 disagreements:

| Limiting factor | Synthetic | **CHELSA** |
|---|---|---|
| slope | 10 | 8 |
| altitude | 8 | 7 |
| **precipitation** | **0** | **6** |
| temperature | 0 | 1 |
| shading | 4 | 1 |

**Precipitation is now a real limiting factor on 6 Gulmi plots.** Why: real CHELSA puts
Gulmi annual precip at ~3,294 mm — above the model's 3,000 mm "unsuitable" threshold (the
0.1 floor), so plots that were uniformly optimal under the smooth synthetic climate now
read as too-wet, with disease-pressure agronomy implications. This is exactly the kind of
real signal the synthetic generator could not produce.

**CHELSA 2026.2 confusion matrix** (rows = observed, columns = mapped prediction):

| observed \ predicted | thriving | struggling | failed |
|---|---|---|---|
| **thriving** | 12 | 2 | 1 |
| **struggling** | 8 | **2** | 2 |
| **failed** | 6 | **3** | 4 |

The S3 "struggling" column now carries **5 plots** (vs 1 under synthetic 2026.2, vs 0
under synthetic 2026.1). Predicted-class distribution under CHELSA 2026.2: S1=11, S2=15,
**S3=7**, N=7 — the model now expresses all four FAO suitability classes, which the
synthetic climate prevented. Off-diagonal disagreements are now concentrated in the
"by-one-class" cells (thriving↔struggling, struggling↔failed) rather than the
extreme thriving↔failed swings that dominated under synthetic.

**Honest reading:** the remaining ~55% of disagreements are largely the deliberate
non-biophysical noise baked into the synthetic labels (poor management, young plants,
exceptional microclimate). Real CHELSA fixes the *climate input* but not the *labels* —
the agreement % stays a mechanism-quality signal (R-SYNTH), not an accuracy claim. The
real test still requires the cooperative's labelled plots.

## 7. Sign-off (synthetic — provisional)

The validation **mechanism** is accepted: the harness ingests labelled plots, runs the
pinned config against real CHELSA + DEM, and produces a reproducible confusion matrix +
agreement % + per-factor diagnosis. The version-bumped tuning loop works (2026.1 →
2026.2, both reproducible from committed configs). The climate input is now real (ADR-0007
implemented).

**The ≥80% accuracy gate remains OPEN.** It cannot be closed against synthetic labels.
Closing it requires the cooperative's real labelled plots (≥30–50, stratified per
[ground-truth-plan §3](../phase-0/ground-truth-plan.md)) and a **senior agronomist's
sign-off** — the launch-gating critical path (**R-GT**). When that data lands, re-run
`make validate` against it (no code change needed) and iterate the config versions until
≥80% is met and stable.
