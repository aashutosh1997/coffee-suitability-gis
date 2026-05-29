"""Non-scoring context endpoints (Phase 2).

`GET /context/recent-climate` surfaces recent observed temperature/rainfall beside the
suitability result. It is intentionally separate from /assess: the score is driven only
by the version-controlled normals, and it never blocks or alters an assessment.
"""

from fastapi import APIRouter

from app.context.recent_climate import RecentClimate, recent_climate

router = APIRouter(tags=["context"])


@router.get("/context/recent-climate", response_model=RecentClimate)
async def recent_climate_endpoint(lon: float, lat: float) -> RecentClimate:
    data = await recent_climate(lon, lat)
    return RecentClimate(**data)
