"""Terrain derivatives: slope, aspect, hillshade, sky-view factor.

NumPy implementations are the always-available baseline. The spike also tries richdem
for slope/aspect when importable, to benchmark it against the NumPy path (the data for
ADR follow-ups). WhiteboxTools is the production-grade SVF option noted in the report.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def slope_aspect(
    dem: NDArray[np.float64], xres: float, yres: float
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Slope (percent) and aspect (degrees, 0=N clockwise) via gradient (Horn-like)."""
    dzdy, dzdx = np.gradient(dem, yres, xres)
    slope_rad = np.arctan(np.hypot(dzdx, dzdy))
    slope_pct = np.tan(slope_rad) * 100.0
    aspect = np.degrees(np.arctan2(dzdy, -dzdx))
    aspect = (90.0 - aspect) % 360.0
    return slope_pct, aspect


def hillshade(
    slope_pct: NDArray[np.float64],
    aspect_deg: NDArray[np.float64],
    azimuth: float = 315.0,
    altitude: float = 45.0,
) -> NDArray[np.float64]:
    slope_rad = np.arctan(slope_pct / 100.0)
    aspect_rad = np.radians(aspect_deg)
    az = np.radians(360.0 - azimuth + 90.0)
    alt = np.radians(altitude)
    shaded = np.sin(alt) * np.cos(slope_rad) + np.cos(alt) * np.sin(slope_rad) * np.cos(
        az - aspect_rad
    )
    return np.clip(shaded, 0.0, 1.0)


def sky_view_factor(
    dem: NDArray[np.float64],
    xres: float,
    yres: float,
    n_directions: int = 16,
    max_radius: int = 15,
) -> NDArray[np.float64]:
    """Approximate sky-view factor by scanning horizon angles in N directions.

    This is the heaviest terrain step in the spike (O(rows*cols*dirs*radius)), which is
    why it is benchmarked. Production would use WhiteboxTools / a horizon engine.
    """
    horizon_sum = np.zeros_like(dem, dtype=np.float64)
    for angle in np.linspace(0.0, 2.0 * np.pi, n_directions, endpoint=False):
        dx = np.cos(angle)
        dy = np.sin(angle)
        max_ang = np.full_like(dem, -np.inf, dtype=np.float64)
        for r in range(1, max_radius + 1):
            sx = int(round(dx * r))
            sy = int(round(dy * r))
            if sx == 0 and sy == 0:
                continue
            shifted = np.roll(np.roll(dem, sy, axis=0), sx, axis=1)
            dist = np.hypot(sx * xres, sy * yres)
            ang = np.arctan2(shifted - dem, dist)
            max_ang = np.maximum(max_ang, ang)
        max_ang = np.where(np.isfinite(max_ang), max_ang, 0.0)
        horizon_sum += np.sin(np.clip(max_ang, 0.0, None))
    svf = 1.0 - horizon_sum / float(n_directions)
    return np.clip(svf, 0.0, 1.0)


def slope_aspect_richdem(
    dem_path: str,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Optional richdem path (benchmarked in the spike). Raises if richdem absent."""
    import richdem as rd

    arr = rd.LoadGDAL(dem_path)
    slope = rd.TerrainAttribute(arr, attrib="slope_percentage")
    aspect = rd.TerrainAttribute(arr, attrib="aspect")
    return np.asarray(slope, dtype=np.float64), np.asarray(aspect, dtype=np.float64)
