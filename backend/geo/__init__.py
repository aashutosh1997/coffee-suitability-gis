"""Shared geoprocessing library (used by the API fast path and Celery workers).

Phase 0 contains the terrain-shading architecture spike (spike_terrain.py) and the
NumPy/optional-lib implementations it benchmarks. The full suitability engine wiring
lands in Phase 1+. Heavy geo dependencies are the [geo] extra; nothing here is imported
by the API/worker at runtime in Phase 0.
"""
