"""Pydantic models for the version-controlled suitability config (NFR-14).

This module is the source of truth for the config shape; config/suitability/schema.json
is an editor-validation mirror. See docs/03-suitability-model.md for the model itself.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Band(BaseModel):
    """One scoring band. Numeric factors use min/max; categorical use condition."""

    label: str
    min: float | None = None
    max: float | None = None
    condition: str | None = None
    sub_score: float = Field(ge=0.0, le=1.0)
    hard_limit: bool = False


class Factor(BaseModel):
    name: str
    kind: Literal["numeric", "categorical"]
    unit: str | None = None
    weight: float = Field(ge=0.0, le=1.0)
    bands: list[Band] = Field(min_length=1)


class ClassThresholds(BaseModel):
    S1: float = Field(ge=0.0, le=1.0)
    S2: float = Field(ge=0.0, le=1.0)
    S3: float = Field(ge=0.0, le=1.0)


class RainfallDistributionModifier(BaseModel):
    dry_period_months_min: float
    dry_period_months_max: float
    bonus: float
    aseasonal_penalty: float


class SuitabilityConfig(BaseModel):
    # `model_config_version` lives in the protected `model_` namespace; allow it.
    model_config = ConfigDict(protected_namespaces=())

    model_config_version: str
    region: str | None = None
    based_on: str | None = None
    status: str | None = None
    class_thresholds: ClassThresholds
    rainfall_distribution_modifier: RainfallDistributionModifier | None = None
    factors: list[Factor] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_factors(self) -> SuitabilityConfig:
        names = [f.name for f in self.factors]
        if len(names) != len(set(names)):
            raise ValueError("factor names must be unique")
        total = sum(f.weight for f in self.factors)
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"factor weights must sum to ~1.0 (got {total:.3f})")
        return self
