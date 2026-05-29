"""Recent-conditions context endpoint: source fallback + graceful degradation.

The two upstream fetchers are monkeypatched so the test never touches the network.
"""

from app.context import recent_climate as rc

POINT = {"lon": 83.89, "lat": 28.07}

NASA_RESULT = {
    "source": "NASA POWER",
    "annual_mean_temp_c": 18.5,
    "annual_precip_mm": 1850.0,
    "period": "multi-year climatology",
    "note": None,
    "available": True,
}
OPEN_METEO_RESULT = {
    "source": "Open-Meteo",
    "annual_mean_temp_c": 19.1,
    "annual_precip_mm": 1700.0,
    "period": "2025 observed",
    "note": None,
    "available": True,
}


def _boom(*_args, **_kwargs):
    async def _raise(lon, lat):
        raise RuntimeError("network down")

    return _raise


def test_nasa_power_success(client, monkeypatch):
    async def fake_nasa(lon, lat):
        return NASA_RESULT

    monkeypatch.setattr(rc, "_nasa_power", fake_nasa)
    resp = client.get("/context/recent-climate", params=POINT)
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "NASA POWER" and body["available"] is True
    assert body["annual_mean_temp_c"] == 18.5


def test_falls_back_to_open_meteo(client, monkeypatch):
    monkeypatch.setattr(rc, "_nasa_power", _boom())

    async def fake_open_meteo(lon, lat):
        return OPEN_METEO_RESULT

    monkeypatch.setattr(rc, "_open_meteo", fake_open_meteo)
    resp = client.get("/context/recent-climate", params=POINT)
    assert resp.status_code == 200
    assert resp.json()["source"] == "Open-Meteo"


def test_both_unreachable_degrades_gracefully(client, monkeypatch):
    monkeypatch.setattr(rc, "_nasa_power", _boom())
    monkeypatch.setattr(rc, "_open_meteo", _boom())
    resp = client.get("/context/recent-climate", params=POINT)
    # Always 200 — the endpoint never fails an assessment-adjacent lookup.
    assert resp.status_code == 200
    body = resp.json()
    assert body["available"] is False
    assert body["source"] is None and body["note"]
