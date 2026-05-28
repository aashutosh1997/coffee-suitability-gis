"""Suitability scoring — pure functions over already-computed raw factor values.

No I/O (no rasterio/DB), so it is fully unit-testable. Implements the doc-03 model:
per-factor band lookup -> sub-score, hard-limit override -> class N, weighted overlay
over the ASSESSED factors only (re-normalized), class mapping, and limiting factor.

Phase 1 assesses terrain only (altitude + slope). Climate/shading factors arrive with a
None raw value and are reported as "not assessed" and excluded from the weighted score.
"""

from __future__ import annotations

import math
from typing import Any

from app.schemas.assess import FactorResult, Overall
from app.schemas.config import Band, ClassThresholds, Factor, SuitabilityConfig

NOT_ASSESSED = "not_assessed"

_UNIT_LABEL = {"m": "m", "percent": "%", "degC": "°C", "mm": "mm"}


def _fmt(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:g}"


def _unit(unit: str | None) -> str:
    return _UNIT_LABEL.get(unit or "", unit or "")


def find_band(factor: Factor, value: float) -> Band | None:
    """First band whose half-open interval [min, max) contains value (null = +-inf)."""
    for band in factor.bands:
        low = -math.inf if band.min is None else band.min
        high = math.inf if band.max is None else band.max
        if low <= value < high:
            return band
    return None


def _range_text(band: Band, unit: str | None) -> str:
    u = _unit(unit)
    suffix = f" {u}" if u else ""
    if band.min is not None and band.max is not None:
        return f"{_fmt(band.min)}–{_fmt(band.max)}{suffix}"
    if band.min is not None:
        return f"above {_fmt(band.min)}{suffix}"
    if band.max is not None:
        return f"below {_fmt(band.max)}{suffix}"
    return ""


def _explain(factor: Factor, value: float, band: Band) -> str:
    u = _unit(factor.unit)
    val = f"{_fmt(round(value, 1))}{(' ' + u) if u else ''}"
    text = f"{factor.name.capitalize()} {val} is in the {band.label} band"
    rng = _range_text(band, factor.unit)
    if rng:
        text += f" ({rng})"
    if band.hard_limit:
        text += " — a hard limit, so the site is Not Suitable"
    return text + "."


def score_factor(
    factor: Factor, raw_value: float | None, provenance: dict[str, Any]
) -> tuple[FactorResult, bool]:
    """Return (FactorResult, hard_limit_hit). raw_value None -> not-assessed result."""
    if raw_value is None:
        result = FactorResult(
            name=factor.name,
            raw_value=None,
            unit=factor.unit,
            band=NOT_ASSESSED,
            sub_score=0.0,
            weight=factor.weight,
            explanation=(
                f"{factor.name.capitalize()} is not assessed in this phase "
                "(terrain-only MVP; arrives in Phase 2)."
            ),
            source={},
        )
        return result, False

    band = find_band(factor, raw_value)
    if band is None:
        result = FactorResult(
            name=factor.name,
            raw_value=round(raw_value, 2),
            unit=factor.unit,
            band="unscored",
            sub_score=0.0,
            weight=factor.weight,
            explanation=f"{factor.name} value {raw_value} matched no band.",
            source=provenance,
        )
        return result, False

    result = FactorResult(
        name=factor.name,
        raw_value=round(raw_value, 2),
        unit=factor.unit,
        band=band.label,
        sub_score=band.sub_score,
        weight=factor.weight,
        explanation=_explain(factor, raw_value, band),
        source=provenance,
    )
    return result, band.hard_limit


def map_class(score: float, thresholds: ClassThresholds) -> str:
    if score >= thresholds.S1:
        return "S1"
    if score >= thresholds.S2:
        return "S2"
    if score >= thresholds.S3:
        return "S3"
    return "N"


def aggregate(
    results: list[FactorResult],
    assessed_names: set[str],
    hard_limit_hit: bool,
    thresholds: ClassThresholds,
) -> Overall:
    """Weighted overlay over assessed factors only (re-normalized denominator)."""
    assessed = [r for r in results if r.name in assessed_names]
    denom = sum(r.weight for r in assessed)
    score = sum(r.weight * r.sub_score for r in assessed) / denom if denom else 0.0
    cls = "N" if hard_limit_hit else map_class(score, thresholds)
    limiting = min(assessed, key=lambda r: r.sub_score).name if assessed else None
    return Overall(class_=cls, score=round(score, 3), limiting_factor=limiting)


def assess_factors(
    config: SuitabilityConfig,
    raw_values: dict[str, float],
    provenance: dict[str, Any],
) -> tuple[list[FactorResult], Overall]:
    """Score every config factor. Factors absent from raw_values are 'not assessed'.

    `raw_values` carries the factors we measured this phase (altitude, slope); the rest
    resolve to None and are excluded from the weighted score.
    """
    results: list[FactorResult] = []
    hard_limit_hit = False
    for factor in config.factors:
        value = raw_values.get(factor.name)
        result, hit = score_factor(
            factor, value, provenance if value is not None else {}
        )
        results.append(result)
        hard_limit_hit = hard_limit_hit or hit
    assessed_names = {name for name, value in raw_values.items() if value is not None}
    overall = aggregate(
        results, assessed_names, hard_limit_hit, config.class_thresholds
    )
    return results, overall
