"""Build pilot-region climate COGs: mean annual temperature, annual precipitation, and
the 12-band monthly precipitation stack (for the rainfall-distribution modifier).

Production source (ADR-0007, doc 06): CHELSA ~1 km climatologies (primary), WorldClim
v2.1 (fallback) — global rasters clipped to the pilot and normalized to plain degC / mm.
Those downloads are blocked in most dev/CI environments, so we ship a synthetic
generator that derives spatially-sensible climate from the committed DEM fixture (a
temperature lapse rate; an orographic precip gradient; a monsoon monthly cycle with a
distinct dry winter). The synthetic rasters are coarsened to ~1 km so they honestly show
the resolution mismatch vs the ~30 m DEM. The COG + provenance plumbing here is exactly
what real CHELSA/WorldClim ingestion reuses.

Usage:
    python -m ingest.fetch_climate --variable temperature --out /tmp/tas.tif
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

from ingest import fetch_dem

# --- synthetic climate model (TUNABLE; values are illustrative, not measured) ---
# Subtropical lapse rate chosen so the optimal altitude band (1000-1500 m) maps into the
# optimal temperature band (18-22 degC) for the Nepal mid-hills pilot.
T_SEA_LEVEL_C = 27.2
LAPSE_C_PER_M = 0.006
# Orographic precipitation: wetter with elevation, centred near the optimal band.
PRECIP_BASE_MM = 1450.0
PRECIP_ELEV_COEF = 0.30
# Monsoon monthly cycle (Jan..Dec): wet Jun-Sep, distinct dry winter Nov-Feb.
MONTHLY_WEIGHTS = [
    0.015,
    0.015,
    0.04,
    0.07,
    0.10,
    0.17,
    0.21,
    0.18,
    0.10,
    0.05,
    0.015,
    0.015,
]

COARSEN_TARGET_DEG = (
    0.01  # ~1 km climate grid (downsample factor derived per source DEM)
)
NODATA = -9999.0

# Plausibility guard: ingest fails loud if a (real-source scaling) bug pushes values
# out of range, rather than silently scoring nonsense. The lower bound spans the high
# Himalaya (annual mean ~ -26 degC at ~8800 m via the lapse rate) — legitimately cold,
# and correctly scored unsuitable; it is not an error for a national DEM.
TEMP_RANGE_C = (-35.0, 45.0)
PRECIP_RANGE_MM = (0.0, 8000.0)


def _coarse_dem(source_dem: str | None = None) -> tuple[Any, Any, Any]:  # noqa: F821
    """Downsample a source DEM to ~1 km; return (elev, transform, crs).

    `source_dem` defaults to the committed pilot fixture (offline/tests); the national
    seed passes the merged Nepal DEM so climate tracks real elevation. The downsample
    factor is derived from the source pixel size, so it works at 30 m, 55 m, or 90 m.
    """
    import numpy as np
    import rasterio
    from rasterio.enums import Resampling

    path = source_dem or str(fetch_dem.FIXTURE)
    with rasterio.open(path) as src:
        pixel_deg = abs(src.transform.a)
        factor = max(1, round(COARSEN_TARGET_DEG / pixel_deg))
        new_h = max(4, src.height // factor)
        new_w = max(4, src.width // factor)
        elev = src.read(
            1, out_shape=(new_h, new_w), resampling=Resampling.average
        ).astype("float64")
        transform = src.transform * src.transform.scale(
            src.width / new_w, src.height / new_h
        )
        crs = src.crs
        nodata = src.nodata
    if nodata is not None:
        elev = np.where(elev == nodata, np.nan, elev)
    return elev, transform, crs


def _write_cog(array: Any, transform: Any, crs: Any, out_path: str) -> str:
    import numpy as np
    import rasterio
    from rio_cogeo.cogeo import cog_translate
    from rio_cogeo.profiles import cog_profiles

    data = array[np.newaxis, ...] if array.ndim == 2 else array
    data = np.nan_to_num(data, nan=NODATA).astype("float32")
    count, height, width = data.shape
    tmp = f"{out_path}.tmp.tif"
    profile = {
        "driver": "GTiff",
        "dtype": "float32",
        "count": count,
        "height": height,
        "width": width,
        "transform": transform,
        "crs": crs,
        "nodata": NODATA,
    }
    with rasterio.open(tmp, "w", **profile) as dst:
        dst.write(data)
    cog_translate(tmp, out_path, cog_profiles.get("deflate"), quiet=True)
    if os.path.exists(tmp):
        os.remove(tmp)
    return out_path


def _annual_precip(elev: Any) -> Any:
    import numpy as np

    return np.clip(PRECIP_BASE_MM + PRECIP_ELEV_COEF * elev, 1000.0, 3000.0)


def _assert_range(array: Any, lo: float, hi: float, label: str) -> None:
    import numpy as np

    finite = array[np.isfinite(array)]
    if finite.size and (float(finite.min()) < lo or float(finite.max()) > hi):
        raise ValueError(
            f"{label} out of plausible range [{lo}, {hi}]: "
            f"min={float(finite.min()):.2f} max={float(finite.max()):.2f} "
            "(likely a source unit-scaling bug)."
        )


def fetch_temperature(out: str, source_dem: str | None = None) -> str:
    """Mean annual temperature (degC), single band."""
    elev, transform, crs = _coarse_dem(source_dem)
    temp = T_SEA_LEVEL_C - LAPSE_C_PER_M * elev
    _assert_range(temp, *TEMP_RANGE_C, "temperature")
    return _write_cog(temp, transform, crs, out)


def fetch_precip_annual(out: str, source_dem: str | None = None) -> str:
    """Annual precipitation (mm), single band."""
    elev, transform, crs = _coarse_dem(source_dem)
    precip = _annual_precip(elev)
    _assert_range(precip, *PRECIP_RANGE_MM, "precipitation")
    return _write_cog(precip, transform, crs, out)


def fetch_precip_monthly(out: str, source_dem: str | None = None) -> str:
    """Monthly precipitation (mm), 12 bands Jan..Dec; sums to the annual total."""
    import numpy as np

    elev, transform, crs = _coarse_dem(source_dem)
    annual = _annual_precip(elev)
    weights = np.asarray(MONTHLY_WEIGHTS, dtype="float64")
    weights = weights / weights.sum()
    monthly = np.stack([w * annual for w in weights], axis=0)
    _assert_range(monthly, *PRECIP_RANGE_MM, "monthly precipitation")
    return _write_cog(monthly, transform, crs, out)


VARIABLES = {
    "temperature": fetch_temperature,
    "precip-annual": fetch_precip_annual,
    "precip-monthly": fetch_precip_monthly,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a pilot climate COG")
    parser.add_argument("--variable", required=True, choices=sorted(VARIABLES))
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    path = VARIABLES[args.variable](args.out)
    print(f"fetch_climate: wrote {Path(path)}")


if __name__ == "__main__":
    main()
