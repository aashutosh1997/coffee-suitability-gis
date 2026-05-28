"""API integration tests for the real engine (local-file DEM mode via conftest)."""

import pytest

pytest.importorskip("rasterio")
pytest.importorskip("geopandas")

# Point inside the committed fixture DEM extent.
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
ASSESSED = {"altitude", "slope"}
NOT_ASSESSED = {"temperature", "precipitation", "shading"}


def test_point_returns_real_terrain_assessment(client):
    resp = client.post("/assess", json={"geometry": POINT})
    assert resp.status_code == 200
    body = resp.json()

    assert body["model_config_version"] == "2026.1"
    assert body["overall"]["class"] in {"S1", "S2", "S3", "N"}
    assert body["overall"]["limiting_factor"] in ASSESSED

    factors = {f["name"]: f for f in body["factors"]}
    # Terrain factors are really assessed (real value + a named band).
    for name in ASSESSED:
        assert factors[name]["raw_value"] is not None
        assert factors[name]["band"] not in (None, "not_assessed")
        assert factors[name]["source"].get("dataset")  # provenance attached
    # Climate/shading explicitly not assessed this phase.
    for name in NOT_ASSESSED:
        assert factors[name]["raw_value"] is None
        assert factors[name]["band"] == "not_assessed"


def test_polygon_enqueues_async_job(client):
    resp = client.post("/assess", json={"geometry": POLYGON})
    assert resp.status_code == 202
    assert "job_id" in resp.json()


def test_polygon_engine_scores_real_terrain():
    # The async worker path runs this directly; exercise the real clip+zonal+score.
    from app.suitability.config_loader import load_config
    from app.suitability.engine import assess_polygon_geometry
    from tests.conftest import CONFIG_PATH

    response = assess_polygon_geometry(POLYGON, load_config(CONFIG_PATH))
    factors = {f.name: f for f in response.factors}
    assert factors["altitude"].raw_value is not None
    assert factors["slope"].raw_value is not None
    assert response.overall.class_ in {"S1", "S2", "S3", "N"}
    assert factors["temperature"].band == "not_assessed"
