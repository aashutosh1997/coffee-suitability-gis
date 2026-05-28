"""Suitability scoring engine.

Phase 0 STUB: produces a schema-valid response in the docs/03 output contract shape,
wiring the real factor weights and config version from the loaded config, but with
placeholder raw values/scores. The real weighted-overlay engine (raster sampling,
hard limits, limiting-factor reporting) lands in Phase 1+ in the shared geo library.
"""

from __future__ import annotations

from typing import Any

from app.schemas.assess import AssessResponse, FactorResult, Overall
from app.schemas.config import SuitabilityConfig

_STUB_SOURCE: dict[str, Any] = {
    "dataset": "pending",
    "resolution": "pending",
    "retrieved": None,
}


def assess_stub(geometry: dict[str, Any], config: SuitabilityConfig) -> AssessResponse:
    factors = [
        FactorResult(
            name=factor.name,
            raw_value=None,
            unit=factor.unit,
            band=None,
            sub_score=0.0,
            weight=factor.weight,
            explanation=(
                "Phase 0 stub: geoprocessing not yet wired; value pending Phase 1."
            ),
            source=dict(_STUB_SOURCE),
        )
        for factor in config.factors
    ]
    return AssessResponse(
        aoi={"geometry": geometry},
        overall=Overall(class_="N/A", score=0.0, limiting_factor=None),
        factors=factors,
        model_config_version=config.model_config_version,
        uncertainty_notes=[
            "Phase 0 stub response — the scoring engine is implemented in Phase 1.",
        ],
    )
