import pytest

from app.schemas.config import SuitabilityConfig
from app.suitability.config_loader import load_config
from tests.conftest import CONFIG_PATH


def test_loads_and_reports_version():
    config = load_config(CONFIG_PATH)
    assert config.model_config_version == "2026.1"


def test_weights_sum_to_one():
    config = load_config(CONFIG_PATH)
    assert abs(sum(f.weight for f in config.factors) - 1.0) < 0.01


def test_expected_factors_present():
    config = load_config(CONFIG_PATH)
    names = {f.name for f in config.factors}
    assert {"altitude", "temperature", "precipitation", "slope", "shading"} == names


def test_altitude_has_hard_limit_band():
    config = load_config(CONFIG_PATH)
    altitude = next(f for f in config.factors if f.name == "altitude")
    assert any(b.hard_limit for b in altitude.bands)


def test_validator_rejects_bad_weights():
    bad = {
        "model_config_version": "test",
        "class_thresholds": {"S1": 0.8, "S2": 0.6, "S3": 0.4},
        "factors": [
            {
                "name": "altitude",
                "kind": "numeric",
                "weight": 0.5,  # sums to 0.5, not ~1.0
                "bands": [{"label": "x", "sub_score": 1.0}],
            }
        ],
    }
    with pytest.raises(ValueError):
        SuitabilityConfig.model_validate(bad)
