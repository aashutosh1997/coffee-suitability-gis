from typing import Any

from app.suitability.config_loader import load_config
from app.suitability.engine import assess_polygon_geometry
from worker.celery_app import celery_app


@celery_app.task(name="terrabean.ping")
def ping() -> str:
    """Smoke task — used by the worker healthcheck (celery inspect ping)."""
    return "pong"


@celery_app.task(name="terrabean.assess_polygon")
def assess_polygon(geometry: dict[str, Any]) -> dict[str, Any]:
    """Heavy polygon path: clip DEM, derive terrain, score. Returns doc-03 by alias."""
    config = load_config()
    return assess_polygon_geometry(geometry, config).model_dump(by_alias=True)
