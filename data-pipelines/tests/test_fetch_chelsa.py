"""Offline test of the real-CHELSA fetcher (mocks rasterio so no network is hit)."""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("rasterio")
pytest.importorskip("rio_cogeo")
import numpy as np  # noqa: E402

from ingest import fetch_chelsa  # noqa: E402


def _affine(width: int, height: int):
    from rasterio.transform import from_bounds

    return from_bounds(80.0, 26.0, 89.0, 31.0, width, height)


@contextmanager
def _fake_clip(data: np.ndarray):
    """Patch _clip_normalized to return precomputed (data, transform, crs).

    Leaves rasterio.open alone so _write_cog can write a real COG and assertions can
    read it back.
    """
    transform = _affine(data.shape[-1], data.shape[-2])
    with patch.object(
        fetch_chelsa, "_clip_normalized", return_value=(data, transform, "EPSG:4326")
    ):
        yield


def test_temperature_writes_a_valid_cog_with_normalized_celsius(tmp_path):
    # 16.35 degC is what real CHELSA returns at Gulmi (confirmed against /vsicurl).
    data = np.full((20, 20), 16.35, dtype="float64")
    out = str(tmp_path / "tas.tif")
    with _fake_clip(data):
        fetch_chelsa.fetch_temperature(out, source_dem=None)
    import rasterio
    from rio_cogeo.cogeo import cog_validate

    is_valid, errors, _ = cog_validate(out)
    assert is_valid, f"not a valid COG: {errors}"
    with rasterio.open(out) as got:
        assert got.count == 1
        arr = got.read(1)
    assert float(np.nanmin(arr)) == pytest.approx(16.35, abs=0.01)


def test_precip_annual_writes_mm_values(tmp_path):
    data = np.full((10, 10), 3294.8, dtype="float64")
    out = str(tmp_path / "pr.tif")
    with _fake_clip(data):
        fetch_chelsa.fetch_precip_annual(out, source_dem=None)
    import rasterio

    with rasterio.open(out) as got:
        assert float(np.nanmin(got.read(1))) == pytest.approx(3294.8, abs=0.1)


def test_precip_monthly_stacks_twelve_bands(tmp_path):
    data = np.full((6, 6), 50.0, dtype="float64")
    out = str(tmp_path / "pr12.tif")
    with _fake_clip(data):
        fetch_chelsa.fetch_precip_monthly(out, source_dem=None)
    import rasterio

    with rasterio.open(out) as got:
        assert got.count == 12
        arr = got.read()
        assert arr.shape == (12, 6, 6)
        assert float(np.nanmin(arr)) == pytest.approx(50.0, abs=0.1)


def test_range_assert_fails_loudly_on_unscaled_temperature(tmp_path):
    """A wrong scale assumption would make raw uint16 values land in absurd ranges."""
    data = np.full((4, 4), 2895.0, dtype="float64")  # raw uint16, no scale applied
    out = str(tmp_path / "tas.tif")
    with _fake_clip(data):
        with pytest.raises(ValueError, match="temperature out of plausible range"):
            fetch_chelsa.fetch_temperature(out, source_dem=None)


def test_clip_normalized_applies_file_scale_and_offset():
    """_clip_normalized reads scale+offset from the source file, never hard-coded."""
    src = MagicMock()
    src.scales = (0.1,)
    src.offsets = (-273.15,)
    src.transform = _affine(4, 4)
    src.crs = "EPSG:4326"
    src.read.return_value = np.full((4, 4), 2895, dtype="uint16")
    src.window_transform.return_value = src.transform
    cm = MagicMock()
    cm.__enter__.return_value = src
    cm.__exit__.return_value = False
    with (
        patch("rasterio.open", return_value=cm),
        patch("rasterio.windows.from_bounds", return_value=MagicMock()),
    ):
        data, _t, _c = fetch_chelsa._clip_normalized(
            "https://example/CHELSA_bio1.tif", (80.0, 26.0, 89.0, 31.0)
        )
    assert float(np.nanmin(data)) == pytest.approx(16.35, abs=0.01)


def test_open_failure_raises_chelsa_unavailable():
    with patch("rasterio.open", side_effect=OSError("network down")):
        with pytest.raises(fetch_chelsa.ChelsaUnavailable):
            fetch_chelsa._clip_normalized("https://example/x.tif", (0, 0, 1, 1))


def test_bbox_from_dem_pads_default_nepal_when_no_source():
    w, s, e, n = fetch_chelsa._bbox_from_dem(None)
    pad = fetch_chelsa.BBOX_PADDING_DEG
    assert w == pytest.approx(80.0 - pad)
    assert s == pytest.approx(26.0 - pad)
    assert e == pytest.approx(89.0 + pad)
    assert n == pytest.approx(31.0 + pad)
