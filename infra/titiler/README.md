# TiTiler (raster tile server)

Serves DEM / derivative / result rasters as web-map tiles directly from Cloud-Optimized
GeoTIFFs in MinIO (doc 04). Runs from the upstream image — no custom build in Phase 0.

It is behind the `tiles` compose profile because there is no real COG to serve until the
data spike pushes one to MinIO (`make seed-pilot-data`):

```bash
docker compose --profile tiles up titiler
# then, once a COG exists in the bucket:
# http://localhost:8001/cog/viewer?url=s3://terrabean-cogs/dem/<...>.tif
```

S3/MinIO access is configured via the AWS_* env vars in docker-compose.yml (the
S3-compatible endpoint is the MinIO service). Vector tiles (pg_tileserv/Martin) are
deferred — the Phase 0 web slice only needs a basemap.
