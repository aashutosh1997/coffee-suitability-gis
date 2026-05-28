"""Unit tests for the pure scoring service (no geo stack / DB needed)."""

from app.suitability.config_loader import load_config
from geo import scoring
from geo.scoring import aggregate, assess_factors, find_band, map_class, score_factor
from tests.conftest import CONFIG_PATH

CONFIG = load_config(CONFIG_PATH)
PROV = {"dataset": "Copernicus GLO-30", "resolution": "30 m", "retrieved": "2026-05-28"}


def _factor(name: str):
    return next(f for f in CONFIG.factors if f.name == name)


# --- band lookup ----------------------------------------------------------------


def test_find_band_half_open_lower_edge_inclusive():
    # altitude optimal is 1000-1500; 1000 must land in optimal, not the band below.
    band = find_band(_factor("altitude"), 1000.0)
    assert band is not None and band.label == "optimal"


def test_find_band_upper_edge_exclusive():
    # 1500 is the exclusive top of optimal -> falls into the next (good) band.
    band = find_band(_factor("altitude"), 1500.0)
    assert band is not None and band.label == "good"


def test_find_band_null_bounds_are_infinite():
    low = find_band(_factor("altitude"), 100.0)
    high = find_band(_factor("altitude"), 5000.0)
    assert low is not None and low.hard_limit is True
    assert high is not None and high.hard_limit is True


# --- per-factor scoring ----------------------------------------------------------


def test_score_factor_optimal_altitude():
    result, hard = score_factor(_factor("altitude"), 1300.0, PROV)
    assert result.sub_score == 1.0 and result.band == "optimal" and hard is False
    assert result.source == PROV


def test_score_factor_hard_limit_flagged():
    result, hard = score_factor(_factor("altitude"), 2500.0, PROV)
    assert result.sub_score == 0.0 and hard is True


def test_score_factor_none_is_not_assessed():
    result, hard = score_factor(_factor("temperature"), None, PROV)
    assert result.band == scoring.NOT_ASSESSED
    assert result.raw_value is None and hard is False


# --- class mapping ---------------------------------------------------------------


def test_map_class_thresholds():
    t = CONFIG.class_thresholds
    assert map_class(0.85, t) == "S1"
    assert map_class(0.70, t) == "S2"
    assert map_class(0.50, t) == "S3"
    assert map_class(0.30, t) == "N"


# --- aggregation: the re-normalization invariant --------------------------------


def test_terrain_optimal_scores_s1_via_renormalization():
    # altitude(0.25)+slope(0.15) both optimal -> S=(0.25+0.15)/0.40=1.0 -> S1,
    # NOT 0.40 (which would happen if the denominator stayed 1.0).
    results, overall = assess_factors(CONFIG, {"altitude": 1300.0, "slope": 12.0}, PROV)
    assert overall.score == 1.0
    assert overall.class_ == "S1"


def test_climate_factors_excluded_from_denominator():
    results, overall = assess_factors(CONFIG, {"altitude": 1300.0, "slope": 12.0}, PROV)
    not_assessed = [r for r in results if r.band == scoring.NOT_ASSESSED]
    assert {r.name for r in not_assessed} == {"temperature", "precipitation", "shading"}


def test_hard_limit_forces_class_n_regardless_of_score():
    # Altitude out of range (hard limit) but slope optimal -> overall N.
    _results, overall = assess_factors(
        CONFIG, {"altitude": 2500.0, "slope": 12.0}, PROV
    )
    assert overall.class_ == "N"


def test_limiting_factor_is_lowest_assessed_subscore():
    # altitude optimal (1.0), slope marginal flats 0-2 -> 0.3; slope is limiting.
    _results, overall = assess_factors(CONFIG, {"altitude": 1300.0, "slope": 1.0}, PROV)
    assert overall.limiting_factor == "slope"


def test_aggregate_empty_assessed_is_safe():
    overall = aggregate([], set(), False, CONFIG.class_thresholds)
    assert overall.class_ == "N" and overall.limiting_factor is None
