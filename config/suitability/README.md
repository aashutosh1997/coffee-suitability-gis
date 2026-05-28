# Suitability model configuration

The Arabica scoring model lives **here, as version-controlled configuration — not in
code** (NFR-14). The backend loads the active file (path from `SUITABILITY_CONFIG_PATH`,
default `arabica-2026.1.yaml`) and validates it against the Pydantic models in
`backend/app/schemas/config.py`. `config/suitability/schema.json` is an editor-validation
mirror of those models.

## Files

| File | Purpose |
|------|---------|
| `arabica-2026.1.yaml` | Active config: factor weights, threshold bands, class cutoffs. |
| `schema.json` | JSON Schema mirror for editor validation (source of truth is the Pydantic model). |

## How scoring works (summary; full logic in `docs/03-suitability-model.md`)

1. Each factor maps a raw value to a sub-score in `[0, 1]` via its `bands`.
2. **Hard limits:** if any band flagged `hard_limit: true` is hit (e.g. altitude out of
   range, lethal temperature, frost pocket), the overall class is **N** regardless of the
   weighted score (Liebig's law of the minimum).
3. Otherwise the weighted score is `S = Σ(wᵢ·sᵢ) / Σwᵢ`, mapped to a class via
   `class_thresholds`.
4. The lowest sub-score is reported as the **limiting factor**.

## Changing the model (review gate + versioning)

Threshold/weight changes are **not ordinary code changes**. They require:

1. **Agronomist review and sign-off** — the bands encode domain judgment.
2. **A new version file**, never an in-place edit: copy to `arabica-<YEAR>.<N>.yaml`,
   bump `model_config_version`, and point `SUITABILITY_CONFIG_PATH` at it. Old versions
   are retained so any historical assessment remains reproducible (NFR-16).
3. **Re-validation** against the ground-truth set after the change
   (`docs/phase-0/ground-truth-plan.md`); target ≥ 80% class agreement.

Weights must sum to ≈ 1.0 (the loader enforces this). Factor names must be unique.

## Current calibration

`arabica-2026.1.yaml` is calibrated for the **Nepal mid-hills (~27–28°N)**: the altitude
band is shifted lower than the equatorial tropical default (subtropical Arabica thrives
~1,000–1,500 m). The other factors use species-level defaults pending local validation.
Rationale: `docs/phase-0/agronomy-workshop-notes.md`. **These are expert starting
defaults — they must be validated against real co-op plots before launch.**
