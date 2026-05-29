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
TEMPERATURE_DATASET = "chelsa-tas-annual"
PRECIP_MONTHLY_DATASET = "chelsa-pr-monthly"


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


def test_sample_point_value_temperature_dataset():
    value, prov = cog_reader.sample_point_value(
        POINT_LON, POINT_LAT, TEMPERATURE_DATASET
    )
    assert value is not None and 10.0 < value < 30.0  # plausible mid-hills mean T
    assert prov["dataset"] == TEMPERATURE_DATASET


def test_resolve_dataset_by_name_picks_the_named_fixture():
    prov = cog_reader.resolve_dataset(
        {"type": "Point", "coordinates": [POINT_LON, POINT_LAT]},
        TEMPERATURE_DATASET,
    )
    assert prov["object_key"].endswith(f"{TEMPERATURE_DATASET}.tif")


def test_sample_point_monthly_returns_twelve_values():
    values, prov = cog_reader.sample_point_monthly(
        POINT_LON, POINT_LAT, PRECIP_MONTHLY_DATASET
    )
    assert values is not None and len(values) == 12
    assert all(v >= 0.0 for v in values)
    assert prov["dataset"] == PRECIP_MONTHLY_DATASET


def test_clip_polygon_outside_raster_raises_dem_not_found():
    # A polygon far from the fixture extent must surface a clean out-of-region error
    # rather than a raw rasterio "shapes do not overlap" crash.
    far = {
        "type": "Polygon",
        "coordinates": [
            [
                [90.0, 20.0],
                [90.01, 20.0],
                [90.01, 20.01],
                [90.0, 20.01],
                [90.0, 20.0],
            ]
        ],
    }
    with pytest.raises(cog_reader.DemNotFound):
        cog_reader.clip_polygon(far)
