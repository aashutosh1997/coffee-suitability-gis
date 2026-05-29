"""Recent-conditions climate context (Phase 2, NON-SCORING).

Queries NASA POWER (no key, primary) then Open-Meteo (fallback) for recent annual mean
temperature + precipitation near a point, shown as context beside the suitability
result. It NEVER affects the score and is never imported by the scoring/engine path, so
offline/CI assessments are unaffected. If both services are unreachable (or httpx is
missing) it returns available=False with a note — graceful degradation (NFR-8).
Coordinates are rounded so repeat lookups hit the same upstream cache.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel

POWER_URL = "https://power.larc.nasa.gov/api/temporal/climatology/point"
OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"
TIMEOUT_S = 6.0
_FILL = -999.0  # NASA POWER nodata sentinel


class RecentClimate(BaseModel):
    source: str | None
    annual_mean_temp_c: float | None
    annual_precip_mm: float | None
    period: str | None
    note: str | None
    available: bool


def _unavailable() -> dict:
    return {
        "source": None,
        "annual_mean_temp_c": None,
        "annual_precip_mm": None,
        "period": None,
        "note": "Live recent-conditions service is unreachable; showing baseline only.",
        "available": False,
    }


async def _nasa_power(lon: float, lat: float) -> dict | None:
    import httpx

    params: dict[str, str | float] = {
        "parameters": "T2M,PRECTOTCORR",
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "format": "JSON",
    }
    async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
        resp = await client.get(POWER_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
    param = data["properties"]["parameter"]
    temp = float(param["T2M"]["ANN"])
    precip_daily = float(param["PRECTOTCORR"]["ANN"])
    if temp <= _FILL or precip_daily <= _FILL:
        return None
    return {
        "source": "NASA POWER",
        "annual_mean_temp_c": round(temp, 1),
        "annual_precip_mm": round(precip_daily * 365.25, 0),
        "period": "multi-year climatology",
        "note": None,
        "available": True,
    }


async def _open_meteo(lon: float, lat: float) -> dict | None:
    import httpx

    year = datetime.now(UTC).year - 1
    params: dict[str, str | float] = {
        "latitude": lat,
        "longitude": lon,
        "start_date": f"{year}-01-01",
        "end_date": f"{year}-12-31",
        "daily": "temperature_2m_mean,precipitation_sum",
        "timezone": "UTC",
    }
    async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
        resp = await client.get(OPEN_METEO_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
    daily = data["daily"]
    temps = [t for t in daily["temperature_2m_mean"] if t is not None]
    precs = [p for p in daily["precipitation_sum"] if p is not None]
    if not temps or not precs:
        return None
    return {
        "source": "Open-Meteo",
        "annual_mean_temp_c": round(sum(temps) / len(temps), 1),
        "annual_precip_mm": round(sum(precs), 0),
        "period": f"{year} observed",
        "note": None,
        "available": True,
    }


async def recent_climate(lon: float, lat: float) -> dict:
    """NASA POWER -> Open-Meteo -> graceful nulls. Never raises; never scores."""
    for fetch in (_nasa_power, _open_meteo):
        try:
            result = await fetch(round(lon, 2), round(lat, 2))
        except Exception:
            continue
        if result is not None:
            return result
    return _unavailable()
