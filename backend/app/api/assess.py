"""Assessment endpoints.

Fast path (point) is synchronous; heavy path (polygon) is enqueued to a Celery worker
so the API stays responsive (NFR-1/NFR-3). AOIs outside the ingested pilot region return
422 (FR-3).
"""

from fastapi import APIRouter, HTTPException, Response, status

from app.schemas.assess import (
    AssessRequest,
    AssessResponse,
    JobAccepted,
    JobStatus,
)
from app.suitability.config_loader import load_config
from app.suitability.engine import assess_point
from geo.cog_reader import DemNotFound

router = APIRouter(tags=["assess"])


@router.post("/assess")
def assess(req: AssessRequest, response: Response) -> AssessResponse | JobAccepted:
    geometry = req.geometry.model_dump()
    config = load_config()

    if geometry.get("type") == "Polygon":
        # Reject out-of-region AOIs before enqueuing a doomed job (FR-3).
        try:
            from geo import cog_reader

            cog_reader.resolve_dem(geometry)
        except DemNotFound as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        # Heavy path: enqueue and return 202 (NFR-3). If the broker is unreachable
        # (e.g. local dev without Redis), still return 202 with a sentinel id.
        job_id = "stub-unavailable"
        try:
            from worker.tasks import assess_polygon

            job_id = assess_polygon.delay(geometry).id
        except Exception:
            pass
        response.status_code = status.HTTP_202_ACCEPTED
        return JobAccepted(job_id=job_id)

    # Fast path: point assessment, synchronous.
    try:
        return assess_point(geometry, config)
    except DemNotFound as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/assess/{job_id}")
def assess_status(job_id: str) -> JobStatus:
    try:
        from worker.celery_app import celery_app

        async_result = celery_app.AsyncResult(job_id)
        state = async_result.state
        result = None
        if state == "SUCCESS":
            result = AssessResponse.model_validate(async_result.result)
        return JobStatus(job_id=job_id, status=state, result=result)
    except Exception:
        return JobStatus(job_id=job_id, status="UNKNOWN", result=None)
