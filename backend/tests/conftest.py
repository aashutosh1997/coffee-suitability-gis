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

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

CONFIG_PATH = str(_CONFIG)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
