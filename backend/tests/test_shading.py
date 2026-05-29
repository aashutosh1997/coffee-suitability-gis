"""Unit tests for the Phase-2 terrain-shading classifier."""

import numpy as np
import pytest

pytest.importorskip("numpy")

from geo import shading  # noqa: E402
from geo.shading import (  # noqa: E402
    ADEQUATE_EXPOSURE,
    EXTREME_EXPOSURE,
    FROST_POCKET,
    HEAVY_SHADE,
    MODERATE_SHADE,
    classify_shading_point,
    classify_shading_polygon,
    decide_band,
)

RES = 30.0  # ~30 m DEM cells


# --- pure decision rules --------------------------------------------------------


def test_decide_frost_overrides_everything():
    label = decide_band(svf=1.0, insolation_rel=0.9, frost=True, temperature_degC=24)
    assert label == FROST_POCKET


def test_decide_enclosed_light_limited():
    assert decide_band(0.80, 0.70, False, 17.0) == HEAVY_SHADE


def test_decide_extreme_exposure_hot_open():
    assert decide_band(0.99, 0.90, False, 24.0) == EXTREME_EXPOSURE


def test_decide_warm_default_is_moderate_shade():
    assert decide_band(0.92, 0.80, False, 21.0) == MODERATE_SHADE


def test_decide_cool_default_is_adequate_exposure():
    assert decide_band(0.92, 0.80, False, 16.0) == ADEQUATE_EXPOSURE


def test_decide_missing_temperature_treated_as_cool():
    assert decide_band(0.99, 0.90, False, None) == ADEQUATE_EXPOSURE


# --- point classification over synthetic DEM windows ----------------------------


def test_point_flat_warm_site_runs_and_returns_valid_label():
    window = np.full((11, 11), 1400.0)
    label, signals = classify_shading_point(window, RES, RES, 1400.0, 24.0)
    assert label in {
        MODERATE_SHADE,
        ADEQUATE_EXPOSURE,
        EXTREME_EXPOSURE,
        HEAVY_SHADE,
    }
    assert signals["svf"] is not None


def test_point_single_pixel_depression_is_frost_pocket():
    # A flat field with the centre cell 12 m lower => closed depression, slope ~0.
    window = np.full((11, 11), 1400.0)
    window[5, 5] = 1388.0
    label, signals = classify_shading_point(window, RES, RES, 1388.0, 16.0)
    assert label == FROST_POCKET
    assert signals["tpi_m"] is not None and signals["tpi_m"] <= shading.TPI_FROST


def test_point_warm_depression_below_alt_floor_is_not_frost():
    # Same depression but at a low, warm altitude (below the frost floor) => not frost.
    window = np.full((11, 11), 900.0)
    window[5, 5] = 888.0
    label, _ = classify_shading_point(window, RES, RES, 888.0, 24.0)
    assert label != FROST_POCKET


def test_point_all_nodata_falls_back_safely():
    window = np.full((11, 11), np.nan)
    label, _ = classify_shading_point(window, RES, RES, 1400.0, 16.0)
    assert label == ADEQUATE_EXPOSURE


# --- polygon classification -----------------------------------------------------


def test_polygon_basin_flags_frost_via_cell_fraction():
    # A broad flat low basin: an 8x8 block 12 m below the surrounding field in a 15x15
    # clip => well over the 10% frost-cell fraction at a cool altitude.
    clip = np.full((15, 15), 1400.0)
    clip[3:11, 3:11] = 1388.0
    label, signals = classify_shading_polygon(clip, RES, RES, 1395.0, 16.0)
    assert label == FROST_POCKET
    assert signals["frost_cell_fraction"] is not None
    assert signals["frost_cell_fraction"] >= shading.FROST_CELL_FRAC


def test_polygon_flat_warm_plot_is_not_frost():
    clip = np.full((15, 15), 1400.0)
    label, _ = classify_shading_polygon(clip, RES, RES, 1400.0, 24.0)
    assert label != FROST_POCKET
