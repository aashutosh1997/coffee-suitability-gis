"""Suitability assessment engine (Phase 2: full v1 model).

Points sample a DEM window synchronously; polygons clip + take zonal means in a worker.
Both derive altitude + slope, sample temperature and precipitation from the ~1 km
climate normals, and classify terrain shading, then score the full weighted overlay via
geo.scoring. Climate is sampled at the AOI point / polygon centroid because a plot is
far smaller than a ~1 km climate cell. The AssessResponse contract is unchanged.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from app.schemas.assess import AssessResponse
from app.schemas.config import SuitabilityConfig
from app.settings import settings
from geo import cog_reader, scoring, shading, terrain, zonal

PHASE2_NOTE = (
    "Full v1 model: altitude, slope, temperature, precipitation, and terrain shading "
    "are assessed. Canopy shading and soil arrive in a later phase."
)
DEM_RES_NOTE = "DEM resolution ~30 m may smooth small terraced plots."
CLIMATE_RES_NOTE = (
    "Climate factors come from ~1 km gridded normals — coarser than the ~30 m DEM, so "
    "microclimate (frost pockets, valley fog) is approximated from terrain (ADR-0007)."
)
SHADING_NOTE = (
    "Shading is a Phase-2 terrain heuristic (sky-view, insolation, frost pocket); "
    "thresholds are pending validation with co-op agronomists."
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


def _provenance_map(
    dem_prov: dict[str, Any],
    temp_prov: dict[str, Any],
    precip_prov: dict[str, Any],
    shading_signals: dict[str, float | None],
) -> dict[str, dict[str, Any]]:
    dem = _provenance_source(dem_prov)
    return {
        "altitude": dem,
        "slope": dem,
        "temperature": _provenance_source(temp_prov),
        "precipitation": _provenance_source(precip_prov),
        "shading": {
            "dataset": "terrain shading model",
            "resolution": dem.get("resolution"),
            "retrieved": dem.get("retrieved"),
            "method": "sky-view + insolation + frost-pocket",
            "signals": shading_signals,
        },
    }


def _safe_value(
    lon: float, lat: float, dataset_name: str
) -> tuple[float | None, dict[str, Any]]:
    try:
        return cog_reader.sample_point_value(lon, lat, dataset_name)
    except cog_reader.DemNotFound:
        return None, {}


def _safe_monthly(
    lon: float, lat: float, dataset_name: str
) -> tuple[list[float] | None, dict[str, Any]]:
    try:
        return cog_reader.sample_point_monthly(lon, lat, dataset_name)
    except cog_reader.DemNotFound:
        return None, {}


def _terrain_at_center(
    array: np.ndarray, xres_m: float, yres_m: float
) -> tuple[float, float, float]:
    fill = float(np.nanmean(array)) if np.isfinite(array).any() else 0.0
    filled = np.nan_to_num(array, nan=fill)
    slope_pct, aspect_deg = terrain.slope_aspect(filled, xres_m, yres_m)
    center = (array.shape[0] // 2, array.shape[1] // 2)
    altitude = float(array[center])
    if not np.isfinite(altitude):
        altitude = fill
    return altitude, float(slope_pct[center]), float(aspect_deg[center])


def _finalize(
    geometry: dict[str, Any],
    config: SuitabilityConfig,
    raw_values: dict[str, float | str | None],
    provenance_map: dict[str, dict[str, Any]],
    monthly_precip: list[float] | None,
    notes: list[str],
) -> AssessResponse:
    factors, overall = scoring.assess_factors(
        config, raw_values, provenance_map, monthly_precip=monthly_precip
    )
    return AssessResponse(
        aoi={"geometry": geometry},
        overall=overall,
        factors=factors,
        model_config_version=config.model_config_version,
        uncertainty_notes=notes,
    )


def _assess_at_point(
    lon: float,
    lat: float,
    geometry: dict[str, Any],
    config: SuitabilityConfig,
    extra_notes: list[str],
) -> AssessResponse:
    """Full assessment at a single coordinate (used by points and sub-grid polygons)."""
    dem_src = cog_reader.sample_point(lon, lat, neighborhood=1)
    altitude, slope, aspect = _terrain_at_center(
        dem_src.array, dem_src.xres_m, dem_src.yres_m
    )
    temperature, temp_prov = _safe_value(lon, lat, settings.temperature_dataset_name)
    precip, precip_prov = _safe_value(lon, lat, settings.precip_annual_dataset_name)
    monthly, _monthly_prov = _safe_monthly(
        lon, lat, settings.precip_monthly_dataset_name
    )

    svf_src = cog_reader.sample_point(lon, lat, neighborhood=shading.SVF_MAX_RADIUS)
    shading_label, signals = shading.classify_shading_point(
        svf_src.array, svf_src.xres_m, svf_src.yres_m, altitude, temperature
    )

    raw_values: dict[str, float | str | None] = {
        "altitude": altitude,
        "slope": slope,
        "temperature": temperature,
        "precipitation": precip,
        "shading": shading_label,
    }
    prov = _provenance_map(dem_src.provenance, temp_prov, precip_prov, signals)
    notes = [
        PHASE2_NOTE,
        DEM_RES_NOTE,
        CLIMATE_RES_NOTE,
        SHADING_NOTE,
        _aspect_note(aspect),
    ] + extra_notes
    return _finalize(geometry, config, raw_values, prov, monthly, notes)


def assess_point(geometry: dict[str, Any], config: SuitabilityConfig) -> AssessResponse:
    lon, lat = geometry["coordinates"][0], geometry["coordinates"][1]
    return _assess_at_point(lon, lat, geometry, config, [])


def assess_polygon_geometry(
    geometry: dict[str, Any], config: SuitabilityConfig
) -> AssessResponse:
    from shapely.geometry import shape

    src = cog_reader.clip_polygon(geometry)
    centroid = shape(geometry).centroid

    # A polygon smaller than ~3 DEM cells (~90 m) clips to too few pixels for a stable
    # slope gradient. Fall back to assessing its centroid as a point, and say so.
    if min(src.array.shape) < 3:
        note = (
            "Plot is smaller than the ~30 m DEM cell; assessed at its centroid. "
            "Draw a larger area for plot-wide terrain statistics."
        )
        return _assess_at_point(centroid.x, centroid.y, geometry, config, [note])

    fill = float(np.nanmean(src.array)) if np.isfinite(src.array).any() else 0.0
    filled = np.nan_to_num(src.array, nan=fill)
    slope_pct, aspect_deg = terrain.slope_aspect(filled, src.xres_m, src.yres_m)
    altitude = float(zonal.zonal_stats_array(src.array)["mean"])
    slope = float(zonal.zonal_stats_array(slope_pct)["mean"])
    aspect = float(zonal.zonal_stats_array(aspect_deg)["mean"])

    temperature, temp_prov = _safe_value(
        centroid.x, centroid.y, settings.temperature_dataset_name
    )
    precip, precip_prov = _safe_value(
        centroid.x, centroid.y, settings.precip_annual_dataset_name
    )
    monthly, _monthly_prov = _safe_monthly(
        centroid.x, centroid.y, settings.precip_monthly_dataset_name
    )
    shading_label, signals = shading.classify_shading_polygon(
        src.array, src.xres_m, src.yres_m, altitude, temperature
    )

    raw_values: dict[str, float | str | None] = {
        "altitude": altitude,
        "slope": slope,
        "temperature": temperature,
        "precipitation": precip,
        "shading": shading_label,
    }
    prov = _provenance_map(src.provenance, temp_prov, precip_prov, signals)
    polygon_note = (
        "Polygon rated on mean terrain across the plot; climate is sampled at the plot "
        "centroid (the ~1 km grid is coarser than the plot)."
    )
    notes = [
        PHASE2_NOTE,
        DEM_RES_NOTE,
        CLIMATE_RES_NOTE,
        SHADING_NOTE,
        _aspect_note(aspect),
        polygon_note,
    ]
    return _finalize(geometry, config, raw_values, prov, monthly, notes)
