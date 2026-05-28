from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import assess, health, version
from app.settings import settings
from app.version import __version__


def create_app() -> FastAPI:
    app = FastAPI(
        title="TerraBean API",
        version=__version__,
        summary="Arabica coffee land-suitability assessment (Phase 0 walking skeleton)",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(version.router)
    app.include_router(assess.router)
    return app


app = create_app()
