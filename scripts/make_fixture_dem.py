"""Regenerate the small committed DEM test fixture (reproducible).

This writes a SYNTHETIC ~30 m elevation surface over a Gulmi (Nepal mid-hills) AOI as a
Cloud-Optimized GeoTIFF. It is deliberately synthetic so the terrain spike and COG tests
run fully offline (CI/dev without network); it is NOT real Copernicus data. The real
ingestion path that fetches and clips actual Copernicus GLO-30 lives in
data-pipelines/ingest/. Large rasters are never committed (see .gitignore).

Run (needs the [geo] extra):
    cd backend && uv run --extra geo python ../scripts/make_fixture_dem.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles

OUT = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "tests"
    / "fixtures"
    / "dem"
    / "nepal_aoi_clip_glo30.tif"
)

# AOI-covering bbox (slightly larger than gulmi_test_polygon.geojson so clip is interior).
WEST, NORTH = 83.860, 28.100
RES = 0.0005  # ~55 m; small enough to keep the fixture tiny
NX, NY = 130, 130


def synthetic_elevation() -> np.ndarray:
    xx, yy = np.meshgrid(np.linspace(0, 1, NX), np.linspace(0, 1, NY))
    elev = (
        1000.0
        + 500.0 * np.sin(3.0 * np.pi * xx) * np.cos(2.0 * np.pi * yy)
        + 300.0 * yy
        + 80.0 * np.sin(12.0 * np.pi * xx)
    )
    rng = np.random.default_rng(42)
    elev = elev + rng.normal(0.0, 15.0, elev.shape)
    return np.clip(elev, 900.0, 1900.0).astype("float32")


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    elev = synthetic_elevation()
    transform = from_origin(WEST, NORTH, RES, RES)
    profile = {
        "driver": "GTiff",
        "dtype": "float32",
        "count": 1,
        "height": NY,
        "width": NX,
        "crs": "EPSG:4326",
        "transform": transform,
    }
    tmp = OUT.parent / "_tmp_dem.tif"
    with rasterio.open(tmp, "w", **profile) as dst:
        dst.write(elev, 1)
    cog_translate(str(tmp), str(OUT), cog_profiles.get("deflate"), quiet=True)
    tmp.unlink(missing_ok=True)
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
