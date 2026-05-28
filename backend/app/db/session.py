from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.settings import settings

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(settings.database_url, pool_pre_ping=True)
    return _engine


def db_ok() -> bool:
    """Readiness check — used by /health/ready, never on the request hot path."""
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
