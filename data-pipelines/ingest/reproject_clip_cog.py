"""Reproject + clip a DEM to an AOI and write a Cloud-Optimized GeoTIFF (doc 06).

COG is the storage format so TiTiler/workers can do efficient partial reads from MinIO.
"""

from __future__ import annotations

import os
from pathlib import Path


def clip_to_cog(
    src_path: str, aoi_path: str, out_path: str, dst_crs: str | None = None
) -> str:
    import geopandas as gpd
    import rasterio
    from rasterio.mask import mask
    from rasterio.warp import calculate_default_transform, reproject
    from rio_cogeo.cogeo import cog_translate
    from rio_cogeo.profiles import cog_profiles

    aoi = gpd.read_file(aoi_path)

    with rasterio.open(src_path) as src:
        aoi_in_src = aoi.to_crs(src.crs)
        clipped, transform = mask(src, aoi_in_src.geometry, crop=True)
        meta = src.meta.copy()
        meta.update(
            height=clipped.shape[1], width=clipped.shape[2], transform=transform
        )
        src_crs = src.crs

    tmp = f"{out_path}.tmp.tif"
    with rasterio.open(tmp, "w", **meta) as dst:
        dst.write(clipped)

    # Optional reprojection (e.g. to a metric UTM CRS for terrain math downstream).
    reproj_tmp = None
    if dst_crs and str(dst_crs) != str(src_crs):
        reproj_tmp = f"{out_path}.reproj.tif"
        with rasterio.open(tmp) as src:
            new_transform, width, height = calculate_default_transform(
                src.crs, dst_crs, src.width, src.height, *src.bounds
            )
            meta = src.meta.copy()
            meta.update(
                crs=dst_crs, transform=new_transform, width=width, height=height
            )
            with rasterio.open(reproj_tmp, "w", **meta) as dst:
                for i in range(1, src.count + 1):
                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_crs=src.crs,
                        dst_crs=dst_crs,
                    )
        cog_source = reproj_tmp
    else:
        cog_source = tmp

    cog_translate(cog_source, out_path, cog_profiles.get("deflate"), quiet=True)

    for path in (tmp, reproj_tmp):
        if path and os.path.exists(path):
            os.remove(path)
    return out_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Clip a DEM to an AOI and write a COG")
    parser.add_argument("src")
    parser.add_argument("aoi")
    parser.add_argument("out")
    parser.add_argument("--dst-crs", default=None, help="e.g. EPSG:32645 (UTM 45N)")
    args = parser.parse_args()
    result = clip_to_cog(args.src, args.aoi, args.out, dst_crs=args.dst_crs)
    print(f"wrote COG: {Path(result)}")
