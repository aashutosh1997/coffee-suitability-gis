from fastapi import APIRouter

from app.suitability.config_loader import load_config
from app.version import __version__, git_sha

router = APIRouter(tags=["meta"])


@router.get("/version")
def version() -> dict[str, str]:
    config = load_config()
    return {
        "version": __version__,
        "git_sha": git_sha(),
        "model_config_version": config.model_config_version,
    }
