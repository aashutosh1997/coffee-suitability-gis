"""Offline test of the region-COG builder (no network/MinIO/PostGIS)."""

import pytest

pytest.importorskip("rasterio")
pytest.importorskip("rio_cogeo")

from ingest.seed_pilot import _extent_wkt_4326, build_region_cog  # noqa: E402


def test_build_region_cog_fallback_produces_valid_cog(tmp_path):
    out = str(tmp_path / "region.tif")
    build_region_cog(out, tiles=[], fallback=True)

    from rio_cogeo.cogeo import cog_validate

    is_valid, errors, _warnings = cog_validate(out)
    assert is_valid, f"not a valid COG: {errors}"

    wkt = _extent_wkt_4326(out)
    assert wkt.startswith("POLYGON((")
