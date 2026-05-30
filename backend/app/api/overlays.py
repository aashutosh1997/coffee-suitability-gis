"""Raster-overlay discovery endpoint (FR-13).

Returns a TiTiler-ready tile URL template per dataset already seeded into MinIO. The
frontend uses these as MapLibre raster sources so the agronomist can see *what the
input data looks like* (altitude/temperature/precipitation) under the AOI, not just
the final score. The endpoint reuses `cog_reader.resolve_dataset` so a re-seed
(2026.1 -> 2026.2, synthetic -> real CHELSA) flips provenance for free with no
frontend change.

Colormap and rescale are decided server-side per dataset so the legend in the UI
and the tile rendering can never drift apart (R-OVLCMAP).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from fastapi import APIRouter

from app.schemas.overlays import BandSpec, OverlayLayer, OverlaysResponse
from app.settings import settings
from geo.cog_reader import DemNotFound, resolve_dataset

log = logging.getLogger(__name__)

router = APIRouter(tags=["overlays"])

# Bounding box that covers every seeded extent (pilot + Nepal-wide). Used purely to
# satisfy `resolve_dataset`'s ST_Intersects lookup -- it does not constrain the tile
# render. Matches the Nepal seed range in data-pipelines/ingest/seed_pilot.py.
_DISCOVERY_GEOMETRY: dict[str, Any] = {
    "type": "Polygon",
    "coordinates": [
        [[80.0, 26.0], [89.0, 26.0], [89.0, 31.0], [80.0, 31.0], [80.0, 26.0]]
    ],
}
_MONTH_NAMES = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


@dataclass(frozen=True)
class _OverlaySpec:
    key: str
    dataset: str
    name: str
    units: str
    colormap: str
    rescale: tuple[float, float]
    band_count: int = 1


# Registry of what the UI can ask for. Order = display order in the panel.
_REGISTRY: list[_OverlaySpec] = [
    _OverlaySpec(
        key="altitude",
        dataset=settings.dem_dataset_name,
        name="Altitude",
        units="m",
        colormap="terrain",
        rescale=(0, 3500),
    ),
    _OverlaySpec(
        key="temperature",
        dataset=settings.temperature_dataset_name,
        name="Annual mean temperature",
        units="°C",
        colormap="rdylbu_r",
        rescale=(0, 30),
    ),
    _OverlaySpec(
        key="precip-annual",
        dataset=settings.precip_annual_dataset_name,
        name="Annual precipitation",
        units="mm/yr",
        colormap="blues",
        rescale=(0, 4000),
    ),
    _OverlaySpec(
        key="precip-monthly",
        dataset=settings.precip_monthly_dataset_name,
        name="Monthly precipitation",
        units="mm/month",
        colormap="blues",
        rescale=(0, 800),
        band_count=12,
    ),
]


def _tiler_source_url(object_key: str) -> str:
    """Translate a provenance object_key into a URL TiTiler can open.

    Remote mode stores bucket-relative keys (`dem/.../2026.1.tif`); local-fixture
    mode returns absolute filesystem paths. Anything already URL-shaped is passed
    through unchanged.
    """
    if object_key.startswith(("s3://", "/", "http://", "https://")):
        return object_key
    return f"s3://{settings.minio_bucket}/{object_key}"


def _build_layer(spec: _OverlaySpec) -> OverlayLayer | None:
    try:
        prov = resolve_dataset(_DISCOVERY_GEOMETRY, spec.dataset)
    except DemNotFound:
        log.warning(
            "overlays: dataset %r not seeded; skipping layer %r", spec.dataset, spec.key
        )
        return None

    source_url = _tiler_source_url(prov["object_key"])
    lo, hi = spec.rescale
    base = settings.titiler_base_url.rstrip("/")
    # TiTiler 2.x routes tiles under
    # /{collection}/tiles/{tileMatrixSetId}/{z}/{x}/{y}.{ext}.
    # WebMercatorQuad is the standard slippy-map TMS that MapLibre expects.
    template = (
        f"{base}/cog/tiles/WebMercatorQuad/{{z}}/{{x}}/{{y}}.png"
        f"?url={source_url}&rescale={lo},{hi}&colormap_name={spec.colormap}"
    )

    bands = (
        [BandSpec(n=i + 1, name=_MONTH_NAMES[i]) for i in range(spec.band_count)]
        if spec.band_count > 1
        else None
    )

    return OverlayLayer(
        key=spec.key,
        name=spec.name,
        units=spec.units,
        dataset=spec.dataset,
        source=prov.get("source"),
        resolution=prov.get("resolution"),
        retrieved=prov.get("retrieved"),
        version=prov.get("version"),
        colormap=spec.colormap,
        rescale=spec.rescale,
        band_count=spec.band_count,
        bands=bands,
        tile_url_template=template,
    )


@router.get("/overlays", response_model=OverlaysResponse)
def list_overlays() -> OverlaysResponse:
    layers = [layer for spec in _REGISTRY if (layer := _build_layer(spec)) is not None]
    return OverlaysResponse(layers=layers)
