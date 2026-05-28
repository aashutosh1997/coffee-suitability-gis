"""Read the pilot DEM for an AOI — from MinIO over GDAL /vsis3, or a local file.

Two modes:
- **Remote (default):** look up which COG covers the AOI in the PostGIS provenance table
  (ST_Intersects on the dataset extent), then read it from MinIO via /vsis3 for
  efficient windowed reads.
- **Local fallback:** when `settings.cog_local_dir` is set (tests / offline dev), read a
  local COG directly with a static provenance dict — no MinIO or PostGIS needed.

Point reads use a small window (slope needs neighbours); polygon reads clip to the AOI.
Reuses the clip + geographic->metric pixel-size approach from geo/spike_terrain.py.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import date
from typing import Any

import numpy as np
from numpy.typing import NDArray

from app.settings import settings


class DemNotFound(Exception):
    """No ingested DEM covers the requested AOI (FR-3: outside the pilot region)."""


@dataclass
class DemSource:
    array: NDArray[np.float64]  # nodata -> np.nan
    xres_m: float
    yres_m: float
    crs: str
    provenance: dict[str, Any] = field(default_factory=dict)


# --- mode helpers ---------------------------------------------------------------


def _local_file() -> str | None:
    """Resolve the local COG path from settings.cog_local_dir (file or directory)."""
    target = settings.cog_local_dir
    if not target:
        return None
    if os.path.isdir(target):
        tifs = sorted(f for f in os.listdir(target) if f.endswith(".tif"))
        if not tifs:
            return None
        return os.path.join(target, tifs[0])
    return target


def _configure_gdal_s3() -> None:
    """Configure GDAL /vsis3 for MinIO via the environment.

    rasterio forbids passing AWS *credentials* as rasterio.Env kwargs (they must come
    from the environment / boto3), so we set them on os.environ. GDAL wants
    AWS_S3_ENDPOINT as host:port (no scheme); MinIO is path-style, plain http locally.
    """
    endpoint = settings.minio_endpoint
    os.environ.setdefault("AWS_ACCESS_KEY_ID", settings.minio_root_user)
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", settings.minio_root_password)
    os.environ["AWS_S3_ENDPOINT"] = endpoint.split("://", 1)[-1]
    os.environ["AWS_VIRTUAL_HOSTING"] = "FALSE"
    os.environ["AWS_HTTPS"] = "YES" if endpoint.startswith("https://") else "NO"
    os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")


def _dsn() -> str:
    return settings.database_url.replace("postgresql+psycopg://", "postgresql://")


# --- provenance resolution ------------------------------------------------------


def resolve_dem(geometry: dict[str, Any]) -> dict[str, Any]:
    """Provenance row for the COG covering the AOI, or a static dict in local mode."""
    if _local_file():
        return {
            "dataset": settings.dem_dataset_name,
            "source": "local fixture",
            "resolution": "~30 m (synthetic fixture)",
            "retrieved": str(date.today()),
            "object_key": _local_file(),
            "version": "fixture",
        }

    import psycopg

    with psycopg.connect(_dsn()) as conn:
        row = conn.execute(
            """
            SELECT object_key, source, resolution, retrieved_at, version
            FROM dataset_provenance
            WHERE dataset_name = %s
              AND ST_Intersects(extent, ST_GeomFromGeoJSON(%s))
            ORDER BY retrieved_at DESC
            LIMIT 1
            """,
            (settings.dem_dataset_name, json.dumps(geometry)),
        ).fetchone()

    if row is None:
        raise DemNotFound(
            "No ingested DEM covers this location. It is outside the pilot region "
            "or the pilot data has not been seeded yet."
        )
    return {
        "dataset": settings.dem_dataset_name,
        "object_key": row[0],
        "source": row[1],
        "resolution": row[2],
        "retrieved": str(row[3].date()) if row[3] else None,
        "version": row[4],
    }


@contextmanager
def _open(provenance: dict[str, Any]) -> Iterator[Any]:
    import rasterio

    local = _local_file()
    if local:
        with rasterio.open(local) as src:
            yield src
    else:
        _configure_gdal_s3()
        path = f"/vsis3/{settings.minio_bucket}/{provenance['object_key']}"
        with rasterio.Env():
            with rasterio.open(path) as src:
                yield src


def _metric_resolution(src: Any, center_lat: float) -> tuple[float, float]:
    xres = abs(src.transform.a)
    yres = abs(src.transform.e)
    if src.crs and src.crs.is_geographic:
        metres_per_deg = 111_320.0
        return xres * metres_per_deg * np.cos(
            np.radians(center_lat)
        ), yres * metres_per_deg
    return xres, yres


def _to_float_nan(array: NDArray[Any], nodata: float | None) -> NDArray[np.float64]:
    out = array.astype(np.float64)
    if nodata is not None:
        out = np.where(out == nodata, np.nan, out)
    return out


# --- read paths -----------------------------------------------------------------


def sample_point(lon: float, lat: float, neighborhood: int = 1) -> DemSource:
    """Read a (2n+1)x(2n+1) window centred on the point (slope needs neighbours)."""
    from rasterio.windows import Window

    provenance = resolve_dem({"type": "Point", "coordinates": [lon, lat]})
    with _open(provenance) as src:
        row, col = src.index(lon, lat)
        size = 2 * neighborhood + 1
        window = Window(col - neighborhood, row - neighborhood, size, size)
        data = src.read(1, window=window, boundless=True, fill_value=src.nodata)
        array = _to_float_nan(data, src.nodata)
        xres_m, yres_m = _metric_resolution(src, lat)
        crs = str(src.crs)
    return DemSource(
        array=array, xres_m=xres_m, yres_m=yres_m, crs=crs, provenance=provenance
    )


def clip_polygon(geometry: dict[str, Any]) -> DemSource:
    """Clip the DEM to the polygon; reuses geo/spike_terrain.py clip + metric res."""
    import geopandas as gpd
    from rasterio.mask import mask
    from shapely.geometry import shape

    provenance = resolve_dem(geometry)
    geom = shape(geometry)
    center_lat = geom.centroid.y
    gdf = gpd.GeoDataFrame(geometry=[geom], crs="EPSG:4326")

    with _open(provenance) as src:
        aoi = gdf.to_crs(src.crs)
        clipped, _ = mask(src, aoi.geometry, crop=True, filled=True, nodata=np.nan)
        array = _to_float_nan(clipped[0], None)  # already filled with nan
        xres_m, yres_m = _metric_resolution(src, center_lat)
        crs = str(src.crs)
    return DemSource(
        array=array, xres_m=xres_m, yres_m=yres_m, crs=crs, provenance=provenance
    )
