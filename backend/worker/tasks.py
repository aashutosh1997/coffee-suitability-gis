from typing import Any

from app.suitability.config_loader import load_config
from app.suitability.engine import assess_stub
from worker.celery_app import celery_app


@celery_app.task(name="terrabean.ping")
def ping() -> str:
    """Smoke task — used by the worker healthcheck (celery inspect ping)."""
    return "pong"


@celery_app.task(name="terrabean.assess_polygon")
def assess_polygon(geometry: dict[str, Any]) -> dict[str, Any]:
    """Heavy polygon path (Phase 0 stub). Returns the doc-03 contract by alias."""
    config = load_config()
    return assess_stub(geometry, config).model_dump(by_alias=True)
