"""cog_reader in local-file mode against the committed fixture (no MinIO/PostGIS)."""

import json

import numpy as np
import pytest

pytest.importorskip("rasterio")
pytest.importorskip("geopandas")

from geo import cog_reader  # noqa: E402
from tests.conftest import FIXTURE_AOI  # noqa: E402

# A point inside the fixture DEM extent (bbox ~ lon 83.86-83.925, lat 28.035-28.10).
POINT_LON, POINT_LAT = 83.89, 28.07


def test_resolve_dem_local_mode_returns_fixture_provenance():
    prov = cog_reader.resolve_dem(
        {"type": "Point", "coordinates": [POINT_LON, POINT_LAT]}
    )
    assert prov["source"] == "local fixture"
    assert prov["object_key"].endswith(".tif")


def test_sample_point_returns_neighbourhood_window():
    src = cog_reader.sample_point(POINT_LON, POINT_LAT, neighborhood=1)
    assert src.array.shape == (3, 3)
    center = src.array[1, 1]
    assert 600 < float(center) < 2000  # plausible mid-hills elevation (m)
    assert src.xres_m > 0 and src.yres_m > 0  # metric pixel size derived


def test_clip_polygon_returns_clipped_array():
    with open(FIXTURE_AOI) as handle:
        geometry = json.load(handle)["features"][0]["geometry"]
    src = cog_reader.clip_polygon(geometry)
    assert src.array.ndim == 2 and src.array.size > 0
    finite = src.array[np.isfinite(src.array)]
    assert finite.size > 0 and float(finite.min()) >= 0.0
