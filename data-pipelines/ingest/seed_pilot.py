"""Seed a region's DEM + climate: fetch -> merge -> COG -> MinIO -> provenance.

Chains the ingest steps into one idempotent flow so the engine has data. Two regions:
- `--region pilot`: the Gulmi box at ~30 m; `--fallback-fixture` runs offline.
- `--region nepal`: the whole country from Copernicus GLO-90 (~90 m, ~9x smaller
  than 30 m so the national mosaic stays tractable). Climate derives from that DEM.

The registered provenance `extent` is what cog_reader matches AOIs against, so it
must reflect the actual COG coverage.

Usage:
    python -m ingest.seed_pilot --version 2026.1                    # pilot (30 m)
    python -m ingest.seed_pilot --version 2026.1 --fallback-fixture # pilot offline
    python -m ingest.seed_pilot --version 2026.1 --region nepal     # all Nepal (90 m)
"""

from __future__ import annotations

import argparse
import shutil
import tempfile
from collections.abc import Callable
from pathlib import Path

from ingest import fetch_climate, fetch_dem, push_minio, register_provenance

DATASET = "copernicus-glo30"

# Climate datasets seeded alongside the DEM (Phase 2). Each entry:
#   (dataset_name, builder(out, source_dem)->path, resolution label, detail label)
# Production source is CHELSA/WorldClim (ADR-0007); offline this is the synthetic
# DEM-derived generator in fetch_climate. dataset_name stays stable across sources so
# cog_reader's provenance lookup does not change.
CLIMATE_DATASETS: list[tuple[str, Callable[[str, str | None], str], str, str]] = [
    ("chelsa-tas-annual", fetch_climate.fetch_temperature, "~1 km", "annual mean degC"),
    ("chelsa-pr-annual", fetch_climate.fetch_precip_annual, "~1 km", "annual mm"),
    ("chelsa-pr-monthly", fetch_climate.fetch_precip_monthly, "~1 km", "12 monthly mm"),
]
# Copernicus GLO-30 1x1 degree tiles (SW corner) covering the pilot districts.
DEFAULT_TILES: list[tuple[int, int]] = [
    (27, 83),
    (27, 84),
    (27, 85),
    (28, 83),
    (28, 84),
    (28, 85),
]
# 1x1 deg tiles (SW corner) over Nepal's bbox (~lon 80-88.2, lat 26.3-30.5).
NEPAL_TILES: list[tuple[int, int]] = [
    (lat, lon) for lat in range(26, 31) for lon in range(80, 89)
]


def _extent_wkt_4326(path: str) -> str:
    import rasterio
    from rasterio.warp import transform_bounds

    with rasterio.open(path) as src:
        left, bottom, right, top = src.bounds
        if src.crs and src.crs.to_epsg() != 4326:
            left, bottom, right, top = transform_bounds(
                src.crs, "EPSG:4326", left, bottom, right, top
            )
    return (
        f"POLYGON(({left} {bottom}, {right} {bottom}, {right} {top}, "
        f"{left} {top}, {left} {bottom}))"
    )


def build_region_cog(
    out_path: str, tiles: list[tuple[int, int]], fallback: bool
) -> str:
    """Produce the pilot-region COG. Fallback = use the committed fixture directly."""
    import rasterio
    from rasterio.merge import merge as rio_merge
    from rio_cogeo.cogeo import cog_translate
    from rio_cogeo.profiles import cog_profiles

    if fallback:
        # The fixture is already a valid COG — use it as the region raster.
        shutil.copyfile(fetch_dem.FIXTURE, out_path)
        return out_path

    tmpdir = Path(tempfile.mkdtemp(prefix="seed_dem_"))
    tile_paths = []
    for lat, lon in tiles:
        dest = tmpdir / f"tile_N{lat}_E{lon}.tif"
        fetch_dem.fetch(lat, lon, dest, fallback_fixture=False)
        tile_paths.append(str(dest))

    datasets = [rasterio.open(p) for p in tile_paths]
    mosaic, transform = rio_merge(datasets)
    meta = datasets[0].meta.copy()
    for ds in datasets:
        ds.close()
    meta.update(height=mosaic.shape[1], width=mosaic.shape[2], transform=transform)

    merged = tmpdir / "merged.tif"
    with rasterio.open(merged, "w", **meta) as dst:
        dst.write(mosaic)
    cog_translate(str(merged), out_path, cog_profiles.get("deflate"), quiet=True)
    return out_path


def build_nepal_cog(
    out_path: str, tiles: list[tuple[int, int]], resolution: int = 90
) -> str:
    """Fetch Copernicus tiles for Nepal, merge, and write a national COG.

    Tiles that fail to download are SKIPPED (not fixture-substituted); raises if none
    succeed (so a blocked network fails loudly rather than seeding a tiny fixture).
    """
    import rasterio
    from rasterio.merge import merge as rio_merge
    from rio_cogeo.cogeo import cog_translate
    from rio_cogeo.profiles import cog_profiles

    tmpdir = Path(tempfile.mkdtemp(prefix="seed_nepal_"))
    tile_paths = []
    for lat, lon in tiles:
        dest = tmpdir / f"tile_N{lat}_E{lon}.tif"
        if fetch_dem.try_fetch_tile(lat, lon, dest, resolution=resolution):
            tile_paths.append(str(dest))
    if not tile_paths:
        raise RuntimeError(
            "No Copernicus tiles could be fetched — national coverage needs the real "
            "DEM download (network blocked?)."
        )
    print(f"seed_pilot: merging {len(tile_paths)}/{len(tiles)} tiles")
    datasets = [rasterio.open(p) for p in tile_paths]
    mosaic, transform = rio_merge(datasets)
    meta = datasets[0].meta.copy()
    for ds in datasets:
        ds.close()
    meta.update(height=mosaic.shape[1], width=mosaic.shape[2], transform=transform)

    merged = tmpdir / "merged.tif"
    with rasterio.open(merged, "w", **meta) as dst:
        dst.write(mosaic)
    cog_translate(str(merged), out_path, cog_profiles.get("deflate"), quiet=True)
    return out_path


def seed(
    version: str,
    tiles: list[tuple[int, int]] | None = None,
    fallback: bool = False,
    bucket: str | None = None,
    resolution: int = 90,
    region: str = "pilot",
) -> str:
    out_cog = tempfile.mkstemp(prefix=f"{region}_{version}_", suffix=".tif")[1]
    if region == "nepal":
        build_nepal_cog(out_cog, tiles or NEPAL_TILES, resolution)
        dem_source = f"Copernicus DEM GLO-{resolution}"
        dem_res = f"~{resolution} m"
    else:
        build_region_cog(out_cog, tiles or DEFAULT_TILES, fallback)
        dem_source = "synthetic fixture" if fallback else "Copernicus DEM GLO-30"
        dem_res = "~30 m (synthetic fixture)" if fallback else "~30 m"

    object_key = f"dem/{DATASET}/{region}/{version}.tif"
    push_minio.push(out_cog, object_key, bucket)

    register_provenance.register(
        dataset_name=DATASET,
        source=dem_source,
        resolution=dem_res,
        crs="EPSG:4326",
        version=version,
        object_key=object_key,
        extent_wkt=_extent_wkt_4326(out_cog),
    )
    print(f"seed_pilot: registered {DATASET} {version} -> {object_key}")

    seed_climate(version, bucket, source_dem=out_cog, region=region)
    return object_key


def seed_climate(
    version: str,
    bucket: str | None = None,
    source_dem: str | None = None,
    region: str = "pilot",
) -> list[str]:
    """Seed temperature / precip / monthly-precip COGs derived from `source_dem`."""
    keys: list[str] = []
    for name, build, resolution, detail in CLIMATE_DATASETS:
        out = tempfile.mkstemp(prefix=f"{name}_{version}_", suffix=".tif")[1]
        build(out, source_dem)
        object_key = f"climate/{name}/{region}/{version}.tif"
        push_minio.push(out, object_key, bucket)
        register_provenance.register(
            dataset_name=name,
            source=f"synthetic (DEM-derived, {detail})",
            resolution=f"{resolution} (synthetic, DEM-derived)",
            crs="EPSG:4326",
            version=version,
            object_key=object_key,
            extent_wkt=_extent_wkt_4326(out),
        )
        print(f"seed_pilot: registered {name} {version} -> {object_key}")
        keys.append(object_key)
    return keys


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed a region's DEM + climate")
    parser.add_argument("--version", default="2026.1")
    parser.add_argument("--region", default="pilot", choices=["pilot", "nepal"])
    parser.add_argument(
        "--resolution",
        type=int,
        default=90,
        choices=[30, 90],
        help="Copernicus DEM resolution for --region nepal (90 m recommended)",
    )
    parser.add_argument("--fallback-fixture", action="store_true")
    parser.add_argument("--bucket", default=None)
    args = parser.parse_args()
    seed(
        args.version,
        fallback=args.fallback_fixture,
        bucket=args.bucket,
        resolution=args.resolution,
        region=args.region,
    )


if __name__ == "__main__":
    main()
