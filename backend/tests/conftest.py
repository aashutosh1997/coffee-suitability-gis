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

# Put cog_reader in local-file mode against the committed fixtures so the real engine
# runs without MinIO/PostGIS. The `cogs/` dir holds one COG per dataset_name (DEM +
# climate). Must be set before app.settings is imported.
_FIXTURES = Path(__file__).resolve().parent / "fixtures"
os.environ.setdefault("COG_LOCAL_DIR", str(_FIXTURES / "cogs"))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

CONFIG_PATH = str(_CONFIG)
FIXTURE_DEM = str(_FIXTURES / "cogs" / "copernicus-glo30.tif")
FIXTURE_AOI = str(_FIXTURES / "aoi" / "gulmi_test_polygon.geojson")
FIXTURE_TEMPERATURE = str(_FIXTURES / "cogs" / "chelsa-tas-annual.tif")
FIXTURE_PRECIP_ANNUAL = str(_FIXTURES / "cogs" / "chelsa-pr-annual.tif")
FIXTURE_PRECIP_MONTHLY = str(_FIXTURES / "cogs" / "chelsa-pr-monthly.tif")


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
