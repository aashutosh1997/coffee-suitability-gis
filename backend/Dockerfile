# TerraBean API + Celery worker image.
#
# Pure-Python slim base on purpose: in Phase 0 the API and worker do NOT touch the
# geospatial stack (the scoring engine is a stub), so we avoid the heavy GDAL base
# image here. The geoprocessing library / terrain spike run via the [geo] extra in the
# GDAL-based data-pipelines image (see docs/adr/0006 and docs/phase-0/risk-register.md).
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app

# Dependency layer (cached): resolve from the committed lockfile for reproducibility.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:$PATH"

# Application code
COPY app ./app
COPY worker ./worker

ARG GIT_SHA=dev
ENV GIT_SHA=${GIT_SHA}

EXPOSE 8000
# Worker service overrides this command in docker-compose.yml.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
