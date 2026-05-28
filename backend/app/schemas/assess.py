"""Request/response models for the assessment API.

The response mirrors the output contract in docs/03-suitability-model.md so the
contract is real from Phase 0 even though the scoring engine is still a stub.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class GeoJSONGeometry(BaseModel):
    type: str
    coordinates: Any


class AssessRequest(BaseModel):
    geometry: GeoJSONGeometry


class FactorResult(BaseModel):
    name: str
    raw_value: float | None
    unit: str | None
    band: str | None
    sub_score: float
    weight: float
    explanation: str
    source: dict[str, Any]


class Overall(BaseModel):
    # "class" is a Python keyword, so expose it via an alias.
    model_config = ConfigDict(populate_by_name=True)

    class_: str = Field(alias="class")
    score: float
    limiting_factor: str | None = None


class AssessResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    aoi: dict[str, Any]
    overall: Overall
    factors: list[FactorResult]
    expert_override: Any | None = None
    model_config_version: str
    uncertainty_notes: list[str] = []


class JobAccepted(BaseModel):
    job_id: str
    status: Literal["pending"] = "pending"


class JobStatus(BaseModel):
    job_id: str
    status: str
    result: AssessResponse | None = None
