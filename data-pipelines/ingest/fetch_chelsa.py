"""Fetch real CHELSA V2.1 climate normals (1981-2010) via /vsicurl and clip a region.

ADR-0007 picks CHELSA ~1 km as the production baseline -- strong in complex mountainous
terrain (Nepal mid-hills). The engine + cog_reader + validation harness already expect
`chelsa-tas-annual`, `chelsa-pr-annual`, `chelsa-pr-monthly`; this module just produces
them from real data instead of the DEM-derived synthetic stand-in in `fetch_climate.py`
(which stays as the offline/CI fallback).

CHELSA V2.1 storage (verified empirically against the public files):
- bio1  (annual mean temperature) -- uint16, scale=0.1, offset=-273.15 -> degC.
- bio12 (annual precipitation)    -- uint16, scale=0.1, offset=0       -> mm/year.
- pr_NN (monthly precipitation)   -- uint16, scale=0.1, offset=0       -> mm/month.
We read each file's own `scales`/`offsets` so the math survives a version bump.

Network errors raise `ChelsaUnavailable` so `seed_pilot` can fall back per-dataset to
the synthetic generator (R-NET). The same `_assert_range` guard the synthetic path uses
catches a wrong scaling assumption loudly (R-CHELSCALE).
"""

from __future__ import annotations

from typing import Any

from ingest.fetch_climate import (
    PRECIP_RANGE_MM,
    TEMP_RANGE_C,
    _assert_range,
    _write_cog,
)

CHELSA_BASE = "https://os.zhdk.cloud.switch.ch/chelsav2/GLOBAL/climatologies/1981-2010"
# Pad the clip bbox so cells on the DEM boundary are not edge-clipped (~1 km grid).
BBOX_PADDING_DEG = 0.1
# Fallback bbox if no source DEM is passed (used by ad-hoc CLI runs).
DEFAULT_NEPAL_BBOX = (80.0, 26.0, 89.0, 31.0)


class ChelsaUnavailable(Exception):
    """A CHELSA /vsicurl read failed; caller should fall back to synthetic."""


def _bbox_from_dem(source_dem: str | None) -> tuple[float, float, float, float]:
    """Bounds of the source DEM in EPSG:4326, padded; defaults to all-Nepal."""
    if not source_dem:
        w, s, e, n = DEFAULT_NEPAL_BBOX
        return (
            w - BBOX_PADDING_DEG,
            s - BBOX_PADDING_DEG,
            e + BBOX_PADDING_DEG,
            n + BBOX_PADDING_DEG,
        )
    import rasterio
    from rasterio.warp import transform_bounds

    with rasterio.open(source_dem) as src:
        left, bottom, right, top = src.bounds
        if src.crs and src.crs.to_epsg() != 4326:
            left, bottom, right, top = transform_bounds(
                src.crs, "EPSG:4326", left, bottom, right, top
            )
    return (
        left - BBOX_PADDING_DEG,
        bottom - BBOX_PADDING_DEG,
        right + BBOX_PADDING_DEG,
        top + BBOX_PADDING_DEG,
    )


def _clip_normalized(
    url: str, bbox: tuple[float, float, float, float]
) -> tuple[Any, Any, Any]:
    """Open via /vsicurl, clip to bbox, apply scale+offset.

    Returns `(data, transform, crs)`. Reads the file's own `scales`/`offsets` so the
    math stays self-consistent across CHELSA version bumps.
    """
    import rasterio
    from rasterio.windows import from_bounds

    try:
        src_cm = rasterio.open(f"/vsicurl/{url}")
    except Exception as exc:  # network error, 404, malformed TIF
        raise ChelsaUnavailable(f"Could not open {url}: {exc}") from exc

    with src_cm as src:
        window = from_bounds(*bbox, transform=src.transform)
        try:
            raw = src.read(1, window=window)
        except Exception as exc:
            raise ChelsaUnavailable(f"Could not read clip from {url}: {exc}") from exc
        scale = src.scales[0] if src.scales else 1.0
        offset = src.offsets[0] if src.offsets else 0.0
        data = raw.astype("float64") * scale + offset
        transform = src.window_transform(window)
        crs = src.crs
    return data, transform, crs


def fetch_temperature(out: str, source_dem: str | None = None) -> str:
    """CHELSA bio1 -> annual mean temperature COG (single band, degC)."""
    bbox = _bbox_from_dem(source_dem)
    url = f"{CHELSA_BASE}/bio/CHELSA_bio1_1981-2010_V.2.1.tif"
    data, transform, crs = _clip_normalized(url, bbox)
    _assert_range(data, *TEMP_RANGE_C, "CHELSA temperature")
    return _write_cog(data, transform, crs, out)


def fetch_precip_annual(out: str, source_dem: str | None = None) -> str:
    """CHELSA bio12 -> annual precipitation COG (single band, mm/year)."""
    bbox = _bbox_from_dem(source_dem)
    url = f"{CHELSA_BASE}/bio/CHELSA_bio12_1981-2010_V.2.1.tif"
    data, transform, crs = _clip_normalized(url, bbox)
    _assert_range(data, *PRECIP_RANGE_MM, "CHELSA precipitation")
    return _write_cog(data, transform, crs, out)


def fetch_precip_monthly(out: str, source_dem: str | None = None) -> str:
    """CHELSA monthly pr -> 12-band COG (Jan..Dec, mm/month)."""
    import numpy as np

    bbox = _bbox_from_dem(source_dem)
    bands: list[Any] = []
    transform = crs = None
    for month in range(1, 13):
        url = f"{CHELSA_BASE}/pr/CHELSA_pr_{month:02d}_1981-2010_V.2.1.tif"
        data, transform, crs = _clip_normalized(url, bbox)
        bands.append(data)
    shapes = {b.shape for b in bands}
    if len(shapes) != 1:
        raise ChelsaUnavailable(
            f"CHELSA monthly pr clips have inconsistent shapes: {shapes}"
        )
    stack = np.stack(bands, axis=0)
    _assert_range(stack, *PRECIP_RANGE_MM, "CHELSA monthly precipitation")
    return _write_cog(stack, transform, crs, out)
