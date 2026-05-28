# TerraBean data-pipelines image — runs on the official GDAL base so the geo stack and
# CLI tools (gdalwarp, rio cogeo) share a consistent GDAL/PROJ/GEOS (see ADR-0006).
FROM ghcr.io/osgeo/gdal:ubuntu-small-3.9.3

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3-pip \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --break-system-packages uv

WORKDIR /pipelines

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
ENV PATH="/pipelines/.venv/bin:$PATH"

COPY ingest ./ingest
COPY sql ./sql

# Default: ingest the pilot DEM with an automatic offline fixture fallback.
CMD ["python", "-m", "ingest.fetch_dem", "--fallback-fixture", "--out", "/tmp/dem.tif"]
