"""Phase 0 terrain-shading architecture spike (the heaviest geoprocessing step).

Given a DEM COG and an AOI polygon, this clips the DEM, derives slope/aspect/hillshade,
computes a sky-view factor and modeled insolation, runs zonal statistics, and TIMES each
step against the polygon NFR budget (< 60 s, NFR-1). Results feed
docs/phase-0/terrain-spike-report.md and the go/no-go on the async polygon path.

Usage:
    python -m geo.spike_terrain <dem.tif> <aoi.geojson> [--repeat N]
"""

from __future__ import annotations

import argparse
import time
from contextlib import contextmanager
from typing import Any

import numpy as np

from geo import insolation, terrain, zonal

POLYGON_BUDGET_SECONDS = 60.0  # NFR-1


@contextmanager
def _timed(label: str, store: list[tuple[str, float]]):
    start = time.perf_counter()
    yield
    store.append((label, time.perf_counter() - start))


def run(
    dem_path: str, aoi_path: str, repeat: int = 1
) -> tuple[list[tuple[str, float]], dict[str, Any], float, tuple[int, int]]:
    """Run the spike once (median of `repeat` for the timing table). Returns
    (timings, zonal_stats, total_seconds, dem_shape)."""
    import geopandas as gpd
    import rasterio
    from rasterio.mask import mask

    all_runs: list[list[tuple[str, float]]] = []
    stats: dict[str, Any] = {}
    shape: tuple[int, int] = (0, 0)

    for _ in range(repeat):
        timings: list[tuple[str, float]] = []
        aoi = gpd.read_file(aoi_path)

        with rasterio.open(dem_path) as src:
            aoi_in_crs = aoi.to_crs(src.crs)
            xres = abs(src.transform.a)
            yres = abs(src.transform.e)
            is_geographic = bool(src.crs and src.crs.is_geographic)
            bounds = aoi_in_crs.total_bounds  # (minx, miny, maxx, maxy)
            with _timed("read+clip", timings):
                clipped, _ = mask(
                    src, aoi_in_crs.geometry, crop=True, filled=True, nodata=np.nan
                )
            dem = clipped[0].astype(np.float64)

        # Slope math needs metric spacing. The DEM is geographic (degrees), so convert
        # pixel size to metres at the AOI's latitude. Production reprojects to UTM 45N
        # (EPSG:32645) for Nepal — noted in docs/phase-0/terrain-spike-report.md.
        if is_geographic:
            center_lat = (bounds[1] + bounds[3]) / 2.0
            metres_per_deg = 111_320.0
            xres_m = xres * metres_per_deg * np.cos(np.radians(center_lat))
            yres_m = yres * metres_per_deg
        else:
            xres_m, yres_m = xres, yres

        shape = dem.shape
        fill = float(np.nanmean(dem)) if np.isfinite(dem).any() else 0.0
        dem_filled = np.nan_to_num(dem, nan=fill)

        with _timed("slope+aspect", timings):
            slope, aspect = terrain.slope_aspect(dem_filled, xres_m, yres_m)
        with _timed("hillshade", timings):
            _ = terrain.hillshade(slope, aspect)
        with _timed("sky_view_factor", timings):
            svf = terrain.sky_view_factor(dem_filled, xres_m, yres_m)
        with _timed("insolation", timings):
            try:
                ghi = insolation.clear_sky_ghi(28.0, 83.8, "2026-03-21 06:00")
            except Exception:
                ghi = 900.0  # fallback if pvlib unavailable
            _ = insolation.relative_insolation(slope, aspect, ghi)
        with _timed("zonal_stats", timings):
            stats = {
                "elevation_m": zonal.zonal_stats_array(dem),
                "slope_pct": zonal.zonal_stats_array(slope),
                "aspect_deg": zonal.zonal_stats_array(aspect),
                "svf": zonal.zonal_stats_array(svf),
            }
        all_runs.append(timings)

    labels = [label for label, _ in all_runs[0]]
    median_timings = [
        (label, float(np.median([run[i][1] for run in all_runs])))
        for i, label in enumerate(labels)
    ]
    total = sum(t for _, t in median_timings)
    return median_timings, stats, total, shape


def main() -> None:
    parser = argparse.ArgumentParser(description="TerraBean terrain-shading spike")
    parser.add_argument("dem")
    parser.add_argument("aoi")
    parser.add_argument("--repeat", type=int, default=1)
    args = parser.parse_args()

    timings, stats, total, shape = run(args.dem, args.aoi, repeat=args.repeat)

    print(f"\nDEM clipped shape: {shape[0]} x {shape[1]} cells\n")
    print(f"{'step':<18}{'seconds':>10}")
    print("-" * 28)
    for label, secs in timings:
        print(f"{label:<18}{secs:>10.4f}")
    print("-" * 28)
    print(f"{'TOTAL':<18}{total:>10.4f}")
    verdict = "WITHIN" if total < POLYGON_BUDGET_SECONDS else "OVER"
    print(
        f"\nPolygon budget (NFR-1): {POLYGON_BUDGET_SECONDS:.0f}s -> {verdict} budget"
    )
    print("\nZonal stats:")
    for name, values in stats.items():
        print(f"  {name}: {values}")


if __name__ == "__main__":
    main()
