from pathlib import Path

import pytest

# The geo stack is the [geo] extra; skip cleanly where it isn't installed (lean CI job).
pytest.importorskip("rasterio")
pytest.importorskip("geopandas")

from geo.spike_terrain import run  # noqa: E402

_FIXTURES = Path(__file__).resolve().parent / "fixtures"
DEM = _FIXTURES / "dem" / "nepal_aoi_clip_glo30.tif"
AOI = _FIXTURES / "aoi" / "gulmi_test_polygon.geojson"


def test_spike_runs_and_outputs_are_sane():
    timings, stats, total, shape = run(str(DEM), str(AOI))

    assert shape[0] > 0 and shape[1] > 0
    assert stats["elevation_m"]["count"] > 0
    # Slope is a non-negative percentage; SVF is bounded in [0, 1].
    assert stats["slope_pct"]["min"] >= 0.0
    assert 0.0 <= stats["svf"]["mean"] <= 1.0
    assert 0.0 <= stats["aspect_deg"]["max"] <= 360.0
    # Every step recorded a timing.
    assert {label for label, _ in timings} >= {
        "read+clip",
        "slope+aspect",
        "sky_view_factor",
        "zonal_stats",
    }
