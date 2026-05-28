# TerraBean API + Celery worker image.
#
# From Phase 1 the API/worker run the REAL geoprocessing engine, so they carry the [geo]
# stack at runtime. rasterio/geopandas/etc. install as manylinux wheels (bundling their
# own GDAL) on the slim base — no system GDAL needed. If wheels ever prove flaky here,
# the documented fallback is to base this image on ghcr.io/osgeo/gdal (as data-pipelines
# does). See docs/adr/0006 and docs/phase-0/risk-register.md.
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# curl for the healthcheck; libexpat1 is needed by the rasterio/pyproj wheels'
# bundled GDAL/PROJ stack (not present in python:3.12-slim).
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl libexpat1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app

# Dependency layer (cached): resolve from the committed lockfile for reproducibility.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --extra geo
ENV PATH="/app/.venv/bin:$PATH"

# Application code
COPY app ./app
COPY worker ./worker
COPY geo ./geo

ARG GIT_SHA=dev
ENV GIT_SHA=${GIT_SHA}

EXPOSE 8000
# Worker service overrides this command in docker-compose.yml.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
