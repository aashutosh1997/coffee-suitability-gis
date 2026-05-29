"""Terrain shading classifier (Phase 2).

Maps DEM-derived signals — sky-view factor, relative insolation (aspect/slope sun
exposure), and a Topographic Position Index for cold-air pooling — plus the temperature
context onto exactly one of the categorical shading bands in the agronomy config:

    moderate_shade_warm_site | adequate_exposure_cool_site | heavy_shade_light_limited
    extreme_exposure_hot_site | frost_pocket (hard limit)

This is a DOCUMENTED PHASE-2 HEURISTIC. Every threshold below is tunable and is flagged
for validation with co-op agronomists in Phase 3 (per ADR-0007: ~1 km climate grids miss
microclimate, so terrain analysis + expert review compensate). Canopy shading from
land-cover is a Phase-3 addition.

Reuses geo.terrain (sky_view_factor, slope_aspect) and geo.insolation. We use the
*normalized* cosine-incidence (insolation with ghi=1.0), so the GHI magnitude cancels
and results stay deterministic — pvlib / GRASS r.sun are the production upgrades.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from geo import insolation, terrain

# --- band labels (must match config/suitability/arabica-2026.1.yaml) ------------
FROST_POCKET = "frost_pocket"
HEAVY_SHADE = "heavy_shade_light_limited"
EXTREME_EXPOSURE = "extreme_exposure_hot_site"
MODERATE_SHADE = "moderate_shade_warm_site"
ADEQUATE_EXPOSURE = "adequate_exposure_cool_site"

# --- TUNABLE heuristic constants (validate with agronomists, Phase 3) -----------
SVF_MAX_RADIUS = 5  # horizon-scan radius (cells) for the point 11x11 window
SVF_OPEN = 0.97  # sky-view >= this => effectively open / unshaded
SVF_ENCLOSED = 0.85  # sky-view <= this => heavily enclosed (deep valley / steep face)
INSOLATION_HOT = 0.85  # relative insolation >= this => high solar load (hot aspect)
WARM_SITE_T = 20.0  # degC: mean-annual-T at/above this => "warm site"
# Frost-pocket (cold-air pooling) gate — ALL must hold:
TPI_FROST = -8.0  # m: cell >= 8 m below its neighbourhood mean (closed depression)
SLOPE_FLAT = 4.0  # percent: near-flat floor where cold air pools, no drainage
FROST_ALT_MIN = 1300.0  # m: cool enough for radiative frost in the mid-hills
FROST_CELL_FRAC = 0.10  # polygon: fraction of cells meeting the gate to flag the plot

# Fixed reference sun for the relative-exposure model (~mid-day, mid-hills latitude).
SUN_AZIMUTH = 180.0
SUN_ELEVATION = 50.0

Signals = dict[str, float | None]


def decide_band(
    svf: float, insolation_rel: float, frost: bool, temperature_degC: float | None
) -> str:
    """Pure decision rules (evaluate in order; first match wins)."""
    if frost:
        return FROST_POCKET
    if svf <= SVF_ENCLOSED and insolation_rel < INSOLATION_HOT:
        return HEAVY_SHADE
    warm = temperature_degC is not None and temperature_degC >= WARM_SITE_T
    if svf >= SVF_OPEN and insolation_rel >= INSOLATION_HOT and warm:
        return EXTREME_EXPOSURE
    if warm:
        return MODERATE_SHADE
    return ADEQUATE_EXPOSURE


def _fill(arr: NDArray[np.float64]) -> NDArray[np.float64] | None:
    if not np.isfinite(arr).any():
        return None
    return np.nan_to_num(arr, nan=float(np.nanmean(arr)))


def _center(arr: NDArray[np.float64]) -> float:
    return float(arr[arr.shape[0] // 2, arr.shape[1] // 2])


def _exposure(
    filled: NDArray[np.float64], xres_m: float, yres_m: float
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    slope_arr, aspect_arr = terrain.slope_aspect(filled, xres_m, yres_m)
    ins_arr = insolation.relative_insolation(
        slope_arr, aspect_arr, 1.0, sun_azimuth=SUN_AZIMUTH, sun_elevation=SUN_ELEVATION
    )
    return slope_arr, aspect_arr, ins_arr


def classify_shading_point(
    dem_window: NDArray[np.float64],
    xres_m: float,
    yres_m: float,
    altitude_m: float,
    temperature_degC: float | None,
) -> tuple[str, Signals]:
    """Classify shading at a point from an ~11x11 DEM window centered on the AOI."""
    filled = _fill(dem_window)
    if filled is None or min(filled.shape) < 3:
        return decide_band(1.0, 0.0, False, temperature_degC), {
            "svf": None,
            "insolation_rel": None,
            "tpi_m": None,
        }
    svf_arr = terrain.sky_view_factor(filled, xres_m, yres_m, max_radius=SVF_MAX_RADIUS)
    slope_arr, _aspect, ins_arr = _exposure(filled, xres_m, yres_m)
    svf = _center(svf_arr)
    insolation_rel = _center(ins_arr)
    slope_pct = _center(slope_arr)
    tpi = altitude_m - float(np.nanmean(filled))
    frost = tpi <= TPI_FROST and slope_pct <= SLOPE_FLAT and altitude_m >= FROST_ALT_MIN
    label = decide_band(svf, insolation_rel, frost, temperature_degC)
    signals: Signals = {
        "svf": round(svf, 3),
        "insolation_rel": round(insolation_rel, 3),
        "tpi_m": round(tpi, 2),
        "slope_pct": round(slope_pct, 2),
    }
    return label, signals


def classify_shading_polygon(
    dem_clip: NDArray[np.float64],
    xres_m: float,
    yres_m: float,
    altitude_m: float,
    temperature_degC: float | None,
) -> tuple[str, Signals]:
    """Classify a clipped plot: mean exposure + frost-pocket cell fraction."""
    valid = np.isfinite(dem_clip)
    filled = _fill(dem_clip)
    if filled is None or min(filled.shape) < 3:
        return decide_band(1.0, 0.0, False, temperature_degC), {
            "svf": None,
            "insolation_rel": None,
            "frost_cell_fraction": None,
        }
    svf_arr = terrain.sky_view_factor(filled, xres_m, yres_m)
    slope_arr, _aspect, ins_arr = _exposure(filled, xres_m, yres_m)
    svf = float(np.nanmean(np.where(valid, svf_arr, np.nan)))
    insolation_rel = float(np.nanmean(np.where(valid, ins_arr, np.nan)))
    mean_elev = float(np.nanmean(filled))
    tpi_cells = filled - mean_elev
    frost_cells = (
        (tpi_cells <= TPI_FROST)
        & (slope_arr <= SLOPE_FLAT)
        & (filled >= FROST_ALT_MIN)
        & valid
    )
    frac = float(frost_cells.sum()) / float(valid.sum())
    frost = frac >= FROST_CELL_FRAC
    label = decide_band(svf, insolation_rel, frost, temperature_degC)
    signals: Signals = {
        "svf": round(svf, 3),
        "insolation_rel": round(insolation_rel, 3),
        "frost_cell_fraction": round(frac, 3),
    }
    return label, signals
