from fastapi import APIRouter, Response

from app.db.session import db_ok
from app.settings import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness: process is up. No dependency checks (keep it cheap)."""
    return {"status": "ok"}


@router.get("/health/ready")
def ready(response: Response) -> dict[str, object]:
    """Readiness: dependencies reachable. 503 if any check fails (NFR-8/9)."""
    checks = {"postgis": db_ok(), "redis": _redis_ok()}
    healthy = all(checks.values())
    if not healthy:
        response.status_code = 503
    return {"status": "ok" if healthy else "degraded", "checks": checks}


def _redis_ok() -> bool:
    try:
        import redis

        client = redis.Redis.from_url(settings.redis_url, socket_connect_timeout=1)
        return bool(client.ping())
    except Exception:
        return False
