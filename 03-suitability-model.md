# 03 — Arabica Suitability Model

This is the heart of the product: how raw geospatial values become a suitability rating.
The approach is a **multi-criteria land evaluation**, structured after the **FAO Land
Suitability Classification** framework (classes S1–S3 / N), combining a weighted score
with hard limiting-factor constraints.

> ⚠️ **The thresholds below are sensible starting defaults for tropical highland Arabica
> and MUST be reviewed and calibrated with the cooperative's agronomists for the specific
> region(s) before launch.** They live in version-controlled configuration, not in code
> (NFR-14). Optimal bands shift with latitude — nearer the equator the optimal altitude
> band sits higher.

## Suitability classes (output)

| Class | Label | Meaning |
|-------|-------|---------|
| S1 | Highly Suitable | All key factors optimal; minimal limitations |
| S2 | Moderately Suitable | Minor limitations, manageable with good practice |
| S3 | Marginally Suitable | Significant limitations; viable only with inputs/management |
| N  | Not Suitable | One or more factors outside the viable range |

## Factors, default thresholds, and per-factor scoring

Each factor maps a raw value to a sub-score in `[0, 1]`. Bands below are defaults.

### 1. Altitude (m above sea level) — *weight 0.25*
Higher elevation slows cherry maturation → denser beans → better cup quality, but excess
elevation brings frost risk and very slow growth.

| Band | Range (m) | Sub-score |
|------|-----------|-----------|
| Optimal | 1,200–2,000 | 1.0 |
| Good | 1,000–1,200 or 2,000–2,200 | 0.8 |
| Marginal | 800–1,000 or 2,200–2,400 | 0.4 |
| Unsuitable | < 800 or > 2,400 | 0.0 (hard limit) |

### 2. Mean annual temperature (°C) — *weight 0.25*
The single strongest climatic driver. Sustained heat accelerates ripening and favors
leaf rust and the coffee berry borer; frost is lethal.

| Band | Range (°C) | Sub-score |
|------|-----------|-----------|
| Optimal | 18–22 | 1.0 |
| Good | 16–18 or 22–23 | 0.8 |
| Marginal | 14–16 or 23–25 | 0.4 |
| Unsuitable | < 14 or > 25 | 0.0 (hard limit) |

### 3. Annual precipitation (mm) — *weight 0.20*
Arabica wants abundant, well-distributed rain plus a short dry/cool period to trigger
even flowering.

| Band | Range (mm) | Sub-score |
|------|-----------|-----------|
| Optimal | 1,400–2,000 | 1.0 |
| Good | 1,200–1,400 or 2,000–2,500 | 0.8 |
| Marginal | 1,000–1,200 (irrigation likely) or 2,500–3,000 (disease risk) | 0.4 |
| Unsuitable | < 1,000 or > 3,000 | 0.1 |

**Rainfall distribution modifier:** if a distinct dry period of 2–4 months is present,
apply a small bonus; if rainfall is essentially aseasonal (no flowering trigger), apply
a small penalty. Computed from monthly climate normals.

### 4. Slope (%) — *weight 0.15*
Moderate slopes give drainage and air movement; steep slopes mean erosion and no
mechanization; flats can waterlog.

| Band | Range (%) | Sub-score |
|------|-----------|-----------|
| Optimal | 5–25 | 1.0 |
| Good | 2–5 or 25–45 | 0.7 |
| Marginal | 0–2 or 45–60 (terracing essential) | 0.3 |
| Unsuitable | > 60 | 0.0 |

### 5. Shading / solar exposure — *weight 0.15*
Arabica is an understorey plant; in hot or marginal climates it benefits from partial
shade (≈ 35–65%). This factor combines **terrain shading** (computed from the DEM:
sky-view factor + modeled annual insolation, including frost-pocket / cold-air-drainage
indicators) with **canopy shading** (from land-cover / canopy-height data, when available).

| Condition | Sub-score |
|-----------|-----------|
| Moderate shade available/feasible in a warm site | 1.0 |
| Adequate exposure in a cool optimal-altitude site | 0.9 |
| Heavy shade where light is already limiting | 0.5 |
| Frost-pocket / strong cold-air pooling detected | 0.2 (hard-limit candidate) |
| Extreme exposure in a hot site, no shade feasible | 0.3 |

### 6. Soil (Phase 3+, optional) — *weight folded in once available*
pH 5.0–6.0, depth > 1 m, well-drained loam (volcanic ideal). Pulled from open soil grids;
treated as advisory until validated locally.

## Aggregation logic

```
1. Compute each factor sub-score s_i in [0,1] from its raw value and band table.
2. HARD LIMITS: if any factor flagged "hard limit" is 0.0 (or a frost pocket is
   detected), the overall class is N (Not Suitable) regardless of the weighted score.
   This implements Liebig's law of the minimum — one fatal factor ruins the site.
3. Otherwise compute weighted score:  S = Σ (w_i * s_i) / Σ w_i
4. Map S to a class:
       S ≥ 0.80  → S1 Highly Suitable
       0.60–0.79 → S2 Moderately Suitable
       0.40–0.59 → S3 Marginally Suitable
       < 0.40    → N  Not Suitable
5. The factor with the lowest sub-score is reported as the "limiting factor".
```

## Output contract (per assessment)

```jsonc
{
  "aoi": { "type": "Point|Polygon", "geometry": { /* GeoJSON */ } },
  "overall": { "class": "S2", "score": 0.74, "limiting_factor": "precipitation" },
  "factors": [
    {
      "name": "temperature",
      "raw_value": 21.3, "unit": "degC",
      "band": "optimal", "sub_score": 1.0, "weight": 0.25,
      "explanation": "Mean annual temperature 21.3 °C is within the optimal 18–22 °C band.",
      "source": { "dataset": "WorldClim v2.1", "resolution": "~1 km", "retrieved": "2026-..." }
    }
    // ... one per factor
  ],
  "expert_override": null,
  "model_config_version": "2026.1",
  "uncertainty_notes": ["DEM resolution ~30 m may smooth small terraced plots."]
}
```

## Validation plan

- Assemble a labelled set of known plots (thriving / struggling / failed) with the agronomy team.
- Run the model; compare predicted class to ground truth; measure agreement (target ≥ 80%, NFR/Vision).
- Tune weights and band edges; **version every config change** so results stay reproducible (NFR-16).
- Re-validate after any threshold change.

## Roadmap of the model itself

- **v1 — Rule-based weighted overlay** (this document). Transparent, easy to explain and tune.
- **v2 — Add soil + rainfall-distribution refinements.**
- **v3 (later) — Optional ML layer** trained on the co-op's own outcome data to refine
  weights, always presented alongside the explainable rule-based score, never replacing it.
