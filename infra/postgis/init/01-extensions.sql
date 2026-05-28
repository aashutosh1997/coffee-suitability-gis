-- Runs once on first PostGIS container init (docker-entrypoint-initdb.d).
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_raster;
