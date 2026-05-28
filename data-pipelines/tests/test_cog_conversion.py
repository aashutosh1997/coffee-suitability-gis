from pathlib import Path

import pytest

pytest.importorskip("rasterio")
pytest.importorskip("rio_cogeo")
pytest.importorskip("geopandas")

from ingest.reproject_clip_cog import clip_to_cog  # noqa: E402

_FIXTURES = Path(__file__).resolve().parents[2] / "backend" / "tests" / "fixtures"
DEM = _FIXTURES / "dem" / "nepal_aoi_clip_glo30.tif"
AOI = _FIXTURES / "aoi" / "gulmi_test_polygon.geojson"


def test_clip_produces_valid_cog(tmp_path):
    out = str(tmp_path / "clip.tif")
    clip_to_cog(str(DEM), str(AOI), out)

    from rio_cogeo.cogeo import cog_validate

    is_valid, errors, _warnings = cog_validate(out)
    assert is_valid, f"not a valid COG: {errors}"
