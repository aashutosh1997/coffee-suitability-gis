"""API integration tests for the real engine (local-file COG mode via conftest)."""

import time

import pytest

pytest.importorskip("rasterio")
pytest.importorskip("geopandas")

# Point inside the committed fixture extent.
POINT = {"type": "Point", "coordinates": [83.89, 28.07]}
POLYGON = {
    "type": "Polygon",
    "coordinates": [
        [
            [83.875, 28.055],
            [83.905, 28.055],
            [83.905, 28.085],
            [83.875, 28.085],
            [83.875, 28.055],
        ]
    ],
}
# Numeric factors that must now carry a real value + band (Phase 2 assesses all).
ASSESSED_NUMERIC = {"altitude", "slope", "temperature", "precipitation"}
ALL_FACTORS = ASSESSED_NUMERIC | {"shading"}


def test_point_returns_full_five_factor_assessment(client):
    resp = client.post("/assess", json={"geometry": POINT})
    assert resp.status_code == 200
    body = resp.json()

    assert body["model_config_version"] == "2026.1"
    assert body["overall"]["class"] in {"S1", "S2", "S3", "N"}
    assert body["overall"]["limiting_factor"] in ALL_FACTORS

    factors = {f["name"]: f for f in body["factors"]}
    for name in ASSESSED_NUMERIC:
        assert factors[name]["raw_value"] is not None
        assert factors[name]["band"] not in (None, "not_assessed")
        assert factors[name]["source"].get("dataset")  # provenance attached (FR-15)

    # Shading is categorical: assessed (a band label) but carries no numeric raw value.
    shading = factors["shading"]
    assert shading["band"] not in (None, "not_assessed")
    assert shading["raw_value"] is None

    # The full v1 model leaves nothing "not assessed".
    assert all(f["band"] != "not_assessed" for f in body["factors"])


def test_point_assessment_under_five_seconds(client):
    start = time.perf_counter()
    resp = client.post("/assess", json={"geometry": POINT})
    assert resp.status_code == 200
    assert time.perf_counter() - start < 5.0  # NFR-1


def test_polygon_enqueues_async_job(client):
    resp = client.post("/assess", json={"geometry": POLYGON})
    assert resp.status_code == 202
    assert "job_id" in resp.json()


def test_polygon_engine_scores_all_factors():
    # The async worker path runs this directly; exercise the real clip + climate score.
    from app.suitability.config_loader import load_config
    from app.suitability.engine import assess_polygon_geometry
    from tests.conftest import CONFIG_PATH

    response = assess_polygon_geometry(POLYGON, load_config(CONFIG_PATH))
    factors = {f.name: f for f in response.factors}
    assert factors["altitude"].raw_value is not None
    assert factors["slope"].raw_value is not None
    assert factors["temperature"].raw_value is not None
    assert factors["temperature"].band != "not_assessed"
    assert factors["precipitation"].band != "not_assessed"
    assert factors["shading"].band not in (None, "not_assessed")
    assert response.overall.class_ in {"S1", "S2", "S3", "N"}


def test_tiny_polygon_falls_back_to_centroid():
    # A sub-grid polygon clips to too few pixels for a gradient; must not crash and must
    # still assess climate + shading at the centroid.
    from app.suitability.config_loader import load_config
    from app.suitability.engine import assess_polygon_geometry
    from tests.conftest import CONFIG_PATH

    tiny = {
        "type": "Polygon",
        "coordinates": [
            [
                [83.8900, 28.0700],
                [83.8901, 28.0700],
                [83.8901, 28.0701],
                [83.8900, 28.0701],
                [83.8900, 28.0700],
            ]
        ],
    }
    response = assess_polygon_geometry(tiny, load_config(CONFIG_PATH))
    factors = {f.name: f for f in response.factors}
    assert factors["altitude"].raw_value is not None
    assert factors["temperature"].raw_value is not None
    assert any("centroid" in note for note in response.uncertainty_notes)
