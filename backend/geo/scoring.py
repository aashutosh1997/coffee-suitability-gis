"""Suitability scoring — pure functions over already-computed raw factor values.

No I/O (no rasterio/DB), so it is fully unit-testable. Implements the doc-03 model:
per-factor band lookup -> sub-score, hard-limit override -> class N, weighted overlay
over the ASSESSED factors only (re-normalized), class mapping, and limiting factor.

Numeric factors score via half-open band lookup; categorical factors (e.g. shading)
score by a band LABEL the engine computes. A factor with a None raw value is reported
as "not assessed" and excluded from the (re-normalized) weighted score. When monthly
precipitation normals are supplied, the configured rainfall-distribution modifier
adjusts the precipitation sub-score (the even-flowering trigger).
"""

from __future__ import annotations

import math
from typing import Any

from app.schemas.assess import FactorResult, Overall
from app.schemas.config import (
    Band,
    ClassThresholds,
    Factor,
    RainfallDistributionModifier,
    SuitabilityConfig,
)

NOT_ASSESSED = "not_assessed"
DRY_MONTH_FRACTION = 0.30  # a month under 30% of the mean month counts as "dry"

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


def find_band_by_label(factor: Factor, label: str) -> Band | None:
    """Categorical lookup: the first band whose label matches (case-sensitive)."""
    for band in factor.bands:
        if band.label == label:
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


def _explain_categorical(factor: Factor, band: Band) -> str:
    text = f"{factor.name.capitalize()} classified as {band.label}"
    if band.condition:
        text += f": {band.condition}"
    if band.hard_limit:
        text += " — a hard limit, so the site is Not Suitable"
    return text + "."


def score_factor(
    factor: Factor, raw_value: float | str | None, provenance: dict[str, Any]
) -> tuple[FactorResult, bool]:
    """Return (FactorResult, hard_limit_hit).

    raw_value None -> not-assessed result. For categorical factors raw_value is the
    band LABEL the engine computed (e.g. shading); for numeric it is the measured value.
    """
    if raw_value is None:
        result = FactorResult(
            name=factor.name,
            raw_value=None,
            unit=factor.unit,
            band=NOT_ASSESSED,
            sub_score=0.0,
            weight=factor.weight,
            explanation=(
                f"{factor.name.capitalize()} could not be assessed "
                "(no data available for this area)."
            ),
            source={},
        )
        return result, False

    if factor.kind == "categorical":
        return _score_categorical(factor, str(raw_value), provenance)

    value = float(raw_value)
    band = find_band(factor, value)
    if band is None:
        result = FactorResult(
            name=factor.name,
            raw_value=round(value, 2),
            unit=factor.unit,
            band="unscored",
            sub_score=0.0,
            weight=factor.weight,
            explanation=f"{factor.name} value {_fmt(round(value, 1))} matched no band.",
            source=provenance,
        )
        return result, False

    result = FactorResult(
        name=factor.name,
        raw_value=round(value, 2),
        unit=factor.unit,
        band=band.label,
        sub_score=band.sub_score,
        weight=factor.weight,
        explanation=_explain(factor, value, band),
        source=provenance,
    )
    return result, band.hard_limit


def _score_categorical(
    factor: Factor, label: str, provenance: dict[str, Any]
) -> tuple[FactorResult, bool]:
    band = find_band_by_label(factor, label)
    if band is None:
        result = FactorResult(
            name=factor.name,
            raw_value=None,
            unit=factor.unit,
            band="unscored",
            sub_score=0.0,
            weight=factor.weight,
            explanation=f"{factor.name} category {label!r} matched no band.",
            source=provenance,
        )
        return result, False
    result = FactorResult(
        name=factor.name,
        raw_value=None,
        unit=factor.unit,
        band=band.label,
        sub_score=band.sub_score,
        weight=factor.weight,
        explanation=_explain_categorical(factor, band),
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


def _longest_dry_run(dry: list[bool]) -> int:
    """Longest run of consecutive dry months, wrapping December -> January."""
    if all(dry):
        return len(dry)
    best = run = 0
    for flag in dry + dry:  # double the year so a Dec->Jan run is counted once
        run = run + 1 if flag else 0
        best = max(best, run)
    return min(best, len(dry))


def rainfall_distribution_delta(
    monthly: list[float], mod: RainfallDistributionModifier
) -> tuple[float, str]:
    """Modifier delta + explanation from 12 monthly precip normals (Jan..Dec)."""
    annual = sum(monthly)
    if annual <= 0:
        return 0.0, ""
    mean_month = annual / 12.0
    dry = [m < DRY_MONTH_FRACTION * mean_month for m in monthly]
    longest = _longest_dry_run(dry)
    if mod.dry_period_months_min <= longest <= mod.dry_period_months_max:
        return mod.bonus, (
            f"A distinct {longest}-month dry period triggers even flowering "
            f"({mod.bonus:+.2f})."
        )
    if longest == 0:
        return mod.aseasonal_penalty, (
            f"Aseasonal rainfall offers no flowering trigger "
            f"({mod.aseasonal_penalty:+.2f})."
        )
    return 0.0, ""


def _provenance_for(provenance: dict[str, Any], name: str) -> dict[str, Any]:
    """Per-factor source if keyed by factor name; otherwise broadcast to all factors."""
    if provenance and all(isinstance(v, dict) for v in provenance.values()):
        return provenance.get(name, {})
    return provenance


def assess_factors(
    config: SuitabilityConfig,
    raw_values: dict[str, float | str | None],
    provenance: dict[str, Any],
    monthly_precip: list[float] | None = None,
) -> tuple[list[FactorResult], Overall]:
    """Score every config factor. Factors absent from raw_values are 'not assessed'.

    `provenance` may be a single dict (broadcast to every assessed factor) or a dict
    keyed by factor name (per-factor source). With `monthly_precip` (12 values) and a
    configured rainfall-distribution modifier, the precipitation sub-score is adjusted.
    """
    results: list[FactorResult] = []
    hard_limit_hit = False
    for factor in config.factors:
        value = raw_values.get(factor.name)
        prov = _provenance_for(provenance, factor.name) if value is not None else {}
        result, hit = score_factor(factor, value, prov)
        results.append(result)
        hard_limit_hit = hard_limit_hit or hit

    assessed_names = {name for name, value in raw_values.items() if value is not None}

    if monthly_precip is not None and config.rainfall_distribution_modifier is not None:
        precip = next((r for r in results if r.name == "precipitation"), None)
        if (
            precip is not None
            and precip.name in assessed_names
            and precip.band not in (NOT_ASSESSED, "unscored")
        ):
            delta, note = rainfall_distribution_delta(
                monthly_precip, config.rainfall_distribution_modifier
            )
            if delta:
                adjusted = min(max(precip.sub_score + delta, 0.0), 1.0)
                precip.sub_score = round(adjusted, 3)
                precip.explanation = f"{precip.explanation} {note}"

    overall = aggregate(
        results, assessed_names, hard_limit_hit, config.class_thresholds
    )
    return results, overall
