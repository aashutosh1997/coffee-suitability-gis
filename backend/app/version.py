import os

__version__ = "0.1.0"


def git_sha() -> str:
    """Short git SHA injected at image build time (GIT_SHA build arg); 'dev' locally."""
    return os.getenv("GIT_SHA", "dev")
