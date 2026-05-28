import os
from pathlib import Path

# Point the config loader at the repo's committed config BEFORE the app imports its
# settings. Repo layout: <root>/backend/tests/conftest.py -> parents[2] == <root>.
_CONFIG = (
    Path(__file__).resolve().parents[2]
    / "config"
    / "suitability"
    / "arabica-2026.1.yaml"
)
os.environ.setdefault("SUITABILITY_CONFIG_PATH", str(_CONFIG))

# Put cog_reader in local-file mode against the committed fixture so the real engine
# runs without MinIO/PostGIS. Must be set before app.settings is imported.
_FIXTURES = Path(__file__).resolve().parent / "fixtures"
os.environ.setdefault("COG_LOCAL_DIR", str(_FIXTURES / "dem"))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

CONFIG_PATH = str(_CONFIG)
FIXTURE_DEM = str(_FIXTURES / "dem" / "nepal_aoi_clip_glo30.tif")
FIXTURE_AOI = str(_FIXTURES / "aoi" / "gulmi_test_polygon.geojson")


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
