from functools import lru_cache

import yaml

from app.schemas.config import SuitabilityConfig
from app.settings import settings


@lru_cache(maxsize=8)
def load_config(path: str | None = None) -> SuitabilityConfig:
    """Load + validate the suitability config.

    Cached per process: the config is immutable for a given version, so this keeps
    every assessment reproducible (NFR-16). A version bump means a new file/path,
    which is a distinct cache key.
    """
    config_path = path or settings.suitability_config_path
    with open(config_path) as handle:
        raw = yaml.safe_load(handle)
    return SuitabilityConfig.model_validate(raw)
