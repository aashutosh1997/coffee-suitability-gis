"""Seed the pilot-region DEM end-to-end: fetch -> (merge) -> COG -> MinIO -> provenance.

Chains the existing ingest steps into one idempotent flow so the engine has a DEM.
Real Copernicus GLO-30 tiles are fetched by default; each tile falls back to the
committed fixture if the download is blocked (so this runs offline too). The registered
provenance `extent` is what cog_reader's ST_Intersects lookup matches an AOI against.

Usage:
    python -m ingest.seed_pilot --version 2026.1
    python -m ingest.seed_pilot --version 2026.1 --fallback-fixture   # offline
"""

from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path

from ingest import fetch_dem, push_minio, register_provenance

DATASET = "copernicus-glo30"
# Copernicus GLO-30 1x1 degree tiles (SW corner) covering the pilot districts.
DEFAULT_TILES: list[tuple[int, int]] = [
    (27, 83),
    (27, 84),
    (27, 85),
    (28, 83),
    (28, 84),
    (28, 85),
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


def seed(
    version: str,
    tiles: list[tuple[int, int]] | None = None,
    fallback: bool = False,
    bucket: str | None = None,
) -> str:
    tiles = tiles or DEFAULT_TILES
    out_cog = tempfile.mkstemp(prefix=f"pilot_{version}_", suffix=".tif")[1]
    build_region_cog(out_cog, tiles, fallback)

    object_key = f"dem/{DATASET}/nepal-pilot/{version}.tif"
    push_minio.push(out_cog, object_key, bucket)

    register_provenance.register(
        dataset_name=DATASET,
        source="synthetic fixture" if fallback else "Copernicus DEM GLO-30",
        resolution="~30 m (synthetic fixture)" if fallback else "~30 m",
        crs="EPSG:4326",
        version=version,
        object_key=object_key,
        extent_wkt=_extent_wkt_4326(out_cog),
    )
    print(f"seed_pilot: registered {DATASET} {version} -> {object_key}")
    return object_key


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the pilot-region DEM")
    parser.add_argument("--version", default="2026.1")
    parser.add_argument("--fallback-fixture", action="store_true")
    parser.add_argument("--bucket", default=None)
    args = parser.parse_args()
    seed(args.version, fallback=args.fallback_fixture, bucket=args.bucket)


if __name__ == "__main__":
    main()
