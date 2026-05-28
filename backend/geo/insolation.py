"""Modeled insolation.

Phase 0 uses a lightweight cosine-incidence weighting of clear-sky GHI (pvlib when
available). GRASS GIS r.sun — true terrain-shaded insolation including cast shadows — is
the production upgrade for Phase 2 (noted in docs/phase-0/terrain-spike-report.md).
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def clear_sky_ghi(lat: float, lon: float, when: str) -> float:
    """Clear-sky global horizontal irradiance (W/m^2) at a location/time via pvlib."""
    import pandas as pd
    import pvlib

    times = pd.date_range(when, periods=1, freq="h", tz="UTC")
    location = pvlib.location.Location(latitude=lat, longitude=lon)
    clearsky = location.get_clearsky(times)
    return float(clearsky["ghi"].iloc[0])


def relative_insolation(
    slope_pct: NDArray[np.float64],
    aspect_deg: NDArray[np.float64],
    ghi: float,
    sun_azimuth: float = 180.0,
    sun_elevation: float = 50.0,
) -> NDArray[np.float64]:
    """Project GHI onto each sloped cell via the cosine of the incidence angle."""
    slope_rad = np.arctan(slope_pct / 100.0)
    aspect_rad = np.radians(aspect_deg)
    sun_az = np.radians(sun_azimuth)
    sun_el = np.radians(sun_elevation)
    cos_incidence = np.cos(slope_rad) * np.sin(sun_el) + np.sin(slope_rad) * np.cos(
        sun_el
    ) * np.cos(sun_az - aspect_rad)
    return np.clip(cos_incidence, 0.0, 1.0) * ghi
