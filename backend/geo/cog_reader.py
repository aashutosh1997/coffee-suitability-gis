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


def _local_file(dataset_name: str | None = None) -> str | None:
    """Resolve a local COG path from settings.cog_local_dir (file or directory).

    In a directory, a dataset is `{dir}/{dataset_name}.tif`; the first `.tif` is the
    legacy fallback for single-fixture dirs.
    """
    target = settings.cog_local_dir
    if not target:
        return None
    if os.path.isdir(target):
        if dataset_name:
            named = os.path.join(target, f"{dataset_name}.tif")
            if os.path.exists(named):
                return named
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


def resolve_dataset(
    geometry: dict[str, Any], dataset_name: str | None = None
) -> dict[str, Any]:
    """Provenance for the COG of `dataset_name` covering the AOI (DEM by default).

    Local mode returns a static dict for the fixture; remote mode looks it up in PostGIS
    by name + ST_Intersects.
    """
    name = dataset_name or settings.dem_dataset_name
    if _local_file(name):
        return {
            "dataset": name,
            "source": "local fixture",
            "resolution": "local fixture",
            "retrieved": str(date.today()),
            "object_key": _local_file(name),
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
            (name, json.dumps(geometry)),
        ).fetchone()

    if row is None:
        raise DemNotFound(
            f"No ingested '{name}' dataset covers this location. It is outside the "
            "pilot region or the pilot data has not been seeded yet."
        )
    return {
        "dataset": name,
        "object_key": row[0],
        "source": row[1],
        "resolution": row[2],
        "retrieved": str(row[3].date()) if row[3] else None,
        "version": row[4],
    }


# Back-compat alias: callers/tests that read the DEM still use resolve_dem(geometry).
resolve_dem = resolve_dataset


@contextmanager
def _open(provenance: dict[str, Any], dataset_name: str | None = None) -> Iterator[Any]:
    import rasterio

    name = dataset_name or settings.dem_dataset_name
    local = _local_file(name)
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


def sample_point(
    lon: float, lat: float, neighborhood: int = 1, dataset_name: str | None = None
) -> DemSource:
    """Read a (2n+1)x(2n+1) window centred on the point (slope needs neighbours)."""
    from rasterio.windows import Window

    geometry = {"type": "Point", "coordinates": [lon, lat]}
    provenance = resolve_dataset(geometry, dataset_name)
    with _open(provenance, dataset_name) as src:
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


def sample_point_value(
    lon: float, lat: float, dataset_name: str
) -> tuple[float | None, dict[str, Any]]:
    """Single value at the point for a (single-band) dataset, with its provenance."""
    src = sample_point(lon, lat, neighborhood=0, dataset_name=dataset_name)
    value = float(src.array[0, 0])
    return (value if np.isfinite(value) else None), src.provenance


def sample_point_monthly(
    lon: float, lat: float, dataset_name: str
) -> tuple[list[float] | None, dict[str, Any]]:
    """Read all 12 bands at the point for the monthly-precip stack, with provenance."""
    from rasterio.windows import Window

    geometry = {"type": "Point", "coordinates": [lon, lat]}
    provenance = resolve_dataset(geometry, dataset_name)
    with _open(provenance, dataset_name) as src:
        row, col = src.index(lon, lat)
        window = Window(col, row, 1, 1)
        values = []
        for band in range(1, src.count + 1):
            data = src.read(band, window=window, boundless=True, fill_value=src.nodata)
            values.append(float(_to_float_nan(data, src.nodata)[0, 0]))
    if not values or not all(np.isfinite(v) for v in values):
        return None, provenance
    return values, provenance


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
        try:
            clipped, _ = mask(src, aoi.geometry, crop=True, filled=True, nodata=np.nan)
        except ValueError as exc:
            # rasterio raises "Input shapes do not overlap raster" when the AOI falls
            # outside the actual COG pixels (e.g. a provenance extent that over-claims
            # coverage). Treat it as out-of-region rather than an opaque crash.
            if "overlap" in str(exc).lower():
                raise DemNotFound(
                    "This area is outside the ingested pilot region."
                ) from exc
            raise
        array = _to_float_nan(clipped[0], None)  # already filled with nan
        xres_m, yres_m = _metric_resolution(src, center_lat)
        crs = str(src.crs)
    return DemSource(
        array=array, xres_m=xres_m, yres_m=yres_m, crs=crs, provenance=provenance
    )
