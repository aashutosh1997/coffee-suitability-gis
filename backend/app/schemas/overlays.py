"""Response models for the raster-overlay discovery endpoint (FR-13).

The frontend never hard-codes S3 keys: it asks `/overlays` and gets a TiTiler-ready
URL template per dataset, plus the same provenance fields shown in the result panel
(FR-15). One source of truth means a re-seed flips provenance for free.
"""

from __future__ import annotations

from pydantic import BaseModel


class BandSpec(BaseModel):
    n: int  # 1-indexed band number, suitable for TiTiler's `bidx` query param
    name: str  # display label (e.g. "Jan")


class OverlayLayer(BaseModel):
    key: str  # stable id used by the frontend (e.g. "altitude")
    name: str  # display label
    units: str
    dataset: str  # provenance dataset_name
    source: str | None
    resolution: str | None
    retrieved: str | None
    version: str | None
    colormap: str
    rescale: tuple[float, float]
    band_count: int
    bands: list[BandSpec] | None  # populated only when band_count > 1
    tile_url_template: str  # MapLibre-ready, with literal {z}/{x}/{y} placeholders


class OverlaysResponse(BaseModel):
    layers: list[OverlayLayer]
