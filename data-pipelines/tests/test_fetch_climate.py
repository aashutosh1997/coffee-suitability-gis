"""Offline test of the synthetic climate-COG generator (no network/MinIO/PostGIS)."""

import pytest

pytest.importorskip("rasterio")
pytest.importorskip("rio_cogeo")

from ingest import fetch_climate  # noqa: E402


def test_temperature_cog_is_valid_and_in_range(tmp_path):
    out = str(tmp_path / "tas.tif")
    fetch_climate.fetch_temperature(out)

    import numpy as np
    import rasterio
    from rio_cogeo.cogeo import cog_validate

    is_valid, errors, _ = cog_validate(out)
    assert is_valid, f"not a valid COG: {errors}"
    with rasterio.open(out) as src:
        assert src.count == 1
        arr = src.read(1)
        arr = np.where(arr == src.nodata, np.nan, arr)
    # Lapse-rate temperature over the mid-hills should land in a plausible band.
    assert 10.0 < float(np.nanmin(arr)) < float(np.nanmax(arr)) < 30.0


def test_monthly_precip_has_twelve_bands_summing_to_annual(tmp_path):
    annual_path = str(tmp_path / "pr.tif")
    monthly_path = str(tmp_path / "pr12.tif")
    fetch_climate.fetch_precip_annual(annual_path)
    fetch_climate.fetch_precip_monthly(monthly_path)

    import numpy as np
    import rasterio

    with rasterio.open(annual_path) as src:
        annual = src.read(1).astype("float64")
    with rasterio.open(monthly_path) as src:
        assert src.count == 12
        monthly = src.read().astype("float64")
    # Monthly bands sum (per cell) back to the annual total.
    assert np.allclose(monthly.sum(axis=0), annual, rtol=1e-3)


def test_monthly_precip_has_a_dry_winter(tmp_path):
    # The monsoon model must produce a distinct 2-4 month dry period (the flowering
    # trigger the rainfall modifier rewards).
    monthly_path = str(tmp_path / "pr12.tif")
    fetch_climate.fetch_precip_monthly(monthly_path)

    import rasterio

    with rasterio.open(monthly_path) as src:
        monthly = src.read().astype("float64")
    centre = monthly[:, monthly.shape[1] // 2, monthly.shape[2] // 2]
    mean_month = centre.mean()
    dry_months = int((centre < 0.30 * mean_month).sum())
    assert 2 <= dry_months <= 4
