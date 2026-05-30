"""Tests for the FR-13 overlay-discovery endpoint."""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from app.api import overlays as overlays_mod


def test_overlays_returns_all_four_seeded_layers(client):
    resp = client.get("/overlays")
    assert resp.status_code == 200
    body = resp.json()

    keys = [layer["key"] for layer in body["layers"]]
    assert keys == ["altitude", "temperature", "precip-annual", "precip-monthly"]


def test_each_layer_carries_titiler_url_and_provenance(client):
    body = client.get("/overlays").json()
    for layer in body["layers"]:
        url = urlparse(layer["tile_url_template"])
        # MapLibre needs literal {z}/{x}/{y} placeholders in the path. TiTiler 2.x
        # requires the tileMatrixSetId before them; WebMercatorQuad is the standard.
        assert "/cog/tiles/WebMercatorQuad/{z}/{x}/{y}.png" in url.path
        qs = parse_qs(url.query)
        assert qs["colormap_name"][0] == layer["colormap"]
        lo_str, hi_str = qs["rescale"][0].split(",")
        assert float(lo_str) == layer["rescale"][0]
        assert float(hi_str) == layer["rescale"][1]
        assert qs["url"][0]  # an actual data source URL was substituted
        # Provenance fields populated from PostGIS / local fixture.
        assert layer["dataset"]
        assert layer["source"]


def test_monthly_layer_exposes_twelve_band_metadata(client):
    body = client.get("/overlays").json()
    monthly = next(layer for layer in body["layers"] if layer["key"] == "precip-monthly")
    assert monthly["band_count"] == 12
    assert monthly["bands"] is not None
    assert [b["n"] for b in monthly["bands"]] == list(range(1, 13))
    assert monthly["bands"][0]["name"] == "Jan"
    assert monthly["bands"][11]["name"] == "Dec"

    # Single-band layers do not carry a bands array.
    altitude = next(layer for layer in body["layers"] if layer["key"] == "altitude")
    assert altitude["band_count"] == 1
    assert altitude["bands"] is None


def test_missing_provenance_skips_layer_gracefully(client, monkeypatch):
    # Simulate one dataset (temperature) not being seeded: the endpoint must drop
    # that layer rather than 500-ing the whole panel.
    real_resolve = overlays_mod.resolve_dataset

    def stub(geometry, dataset_name):
        if dataset_name == "chelsa-tas-annual":
            raise overlays_mod.DemNotFound("not seeded in this test")
        return real_resolve(geometry, dataset_name)

    monkeypatch.setattr(overlays_mod, "resolve_dataset", stub)
    body = client.get("/overlays").json()
    keys = [layer["key"] for layer in body["layers"]]
    assert "temperature" not in keys
    assert {"altitude", "precip-annual", "precip-monthly"}.issubset(keys)


def test_titiler_base_url_setting_is_honored(client, monkeypatch):
    monkeypatch.setattr(
        overlays_mod.settings, "titiler_base_url", "http://tiles.example.test:9999"
    )
    body = client.get("/overlays").json()
    for layer in body["layers"]:
        assert layer["tile_url_template"].startswith(
            "http://tiles.example.test:9999/cog/tiles/"
        )
