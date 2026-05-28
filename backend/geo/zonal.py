"""Zonal statistics over an AOI.

Phase 0 reduces an already-clipped array with NumPy (NaN-aware). Production should use
exactextract for fractional-pixel coverage at polygon edges (more accurate over small
terraced plots) — benchmarked against rasterstats in the spike report.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def zonal_stats_array(arr: NDArray[np.float64]) -> dict[str, float | int]:
    data = arr[np.isfinite(arr)]
    if data.size == 0:
        return {
            "min": float("nan"),
            "mean": float("nan"),
            "max": float("nan"),
            "count": 0,
        }
    return {
        "min": float(np.min(data)),
        "mean": float(np.mean(data)),
        "max": float(np.max(data)),
        "count": int(data.size),
    }
