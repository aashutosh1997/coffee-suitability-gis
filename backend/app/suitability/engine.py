"""Suitability assessment engine (Phase 1: real terrain scoring).

Point = synchronous DEM window sample; polygon = clip + zonal mean (run in a worker).
Both derive altitude + slope (+ aspect for display) and score via geo.scoring. Climate
and shading are not assessed yet (Phase 2) and are reported as such. The AssessResponse
contract (docs/03-suitability-model.md) is unchanged from Phase 0.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from app.schemas.assess import AssessResponse
from app.schemas.config import SuitabilityConfig
from geo import cog_reader, scoring, terrain, zonal

DEM_RES_NOTE = "DEM resolution ~30 m may smooth small terraced plots."
TERRAIN_ONLY_NOTE = (
    "Terrain-only assessment (altitude + slope). Temperature, precipitation, and "
    "shading are not yet assessed and are excluded from the score."
)
_COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


def _aspect_note(aspect_deg: float) -> str:
    facing = _COMPASS[int((aspect_deg % 360) / 45 + 0.5) % 8]
    return (
        f"Mean aspect {aspect_deg:.0f} deg ({facing}-facing); informational this phase."
    )


def _provenance_source(provenance: dict[str, Any]) -> dict[str, Any]:
    return {
        "dataset": provenance.get("source") or provenance.get("dataset"),
        "resolution": provenance.get("resolution"),
        "retrieved": provenance.get("retrieved"),
    }


def _build_response(
    geometry: dict[str, Any],
    config: SuitabilityConfig,
    altitude: float,
    slope: float,
    aspect: float,
    provenance: dict[str, Any],
    extra_notes: list[str],
) -> AssessResponse:
    factors, overall = scoring.assess_factors(
        config,
        {"altitude": altitude, "slope": slope},
        _provenance_source(provenance),
    )
    notes = [TERRAIN_ONLY_NOTE, DEM_RES_NOTE, _aspect_note(aspect)] + extra_notes
    return AssessResponse(
        aoi={"geometry": geometry},
        overall=overall,
        factors=factors,
        model_config_version=config.model_config_version,
        uncertainty_notes=notes,
    )


def _terrain_at_center(array: np.ndarray, xres_m: float, yres_m: float):
    fill = float(np.nanmean(array)) if np.isfinite(array).any() else 0.0
    filled = np.nan_to_num(array, nan=fill)
    slope_pct, aspect_deg = terrain.slope_aspect(filled, xres_m, yres_m)
    center = (array.shape[0] // 2, array.shape[1] // 2)
    altitude = float(array[center])
    if not np.isfinite(altitude):
        altitude = fill
    return altitude, float(slope_pct[center]), float(aspect_deg[center])


def assess_point(geometry: dict[str, Any], config: SuitabilityConfig) -> AssessResponse:
    lon, lat = geometry["coordinates"][0], geometry["coordinates"][1]
    src = cog_reader.sample_point(lon, lat, neighborhood=1)
    altitude, slope, aspect = _terrain_at_center(src.array, src.xres_m, src.yres_m)
    return _build_response(
        geometry, config, altitude, slope, aspect, src.provenance, []
    )


def assess_polygon_geometry(
    geometry: dict[str, Any], config: SuitabilityConfig
) -> AssessResponse:
    src = cog_reader.clip_polygon(geometry)

    # A polygon smaller than ~3 DEM cells (~90 m) clips to too few pixels for a stable
    # slope gradient. Fall back to assessing its centroid as a point, and say so.
    if min(src.array.shape) < 3:
        from shapely.geometry import shape

        centroid = shape(geometry).centroid
        point_src = cog_reader.sample_point(centroid.x, centroid.y, neighborhood=1)
        altitude, slope, aspect = _terrain_at_center(
            point_src.array, point_src.xres_m, point_src.yres_m
        )
        note = (
            "Plot is smaller than the ~30 m DEM cell; assessed at its centroid. "
            "Draw a larger area for plot-wide terrain statistics."
        )
        return _build_response(
            geometry, config, altitude, slope, aspect, point_src.provenance, [note]
        )

    fill = float(np.nanmean(src.array)) if np.isfinite(src.array).any() else 0.0
    filled = np.nan_to_num(src.array, nan=fill)
    slope_pct, aspect_deg = terrain.slope_aspect(filled, src.xres_m, src.yres_m)
    altitude = float(zonal.zonal_stats_array(src.array)["mean"])
    slope = float(zonal.zonal_stats_array(slope_pct)["mean"])
    aspect = float(zonal.zonal_stats_array(aspect_deg)["mean"])
    note = (
        "Polygon rated on the mean terrain values across the plot; sub-plot variation "
        "is not reflected in this phase."
    )
    return _build_response(
        geometry, config, altitude, slope, aspect, src.provenance, [note]
    )
