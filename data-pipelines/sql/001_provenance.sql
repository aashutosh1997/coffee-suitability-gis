-- Dataset provenance (FR-15 / NFR-16): every ingested raster records where it came
-- from, at what resolution, when, and which object it maps to in MinIO. Assessments
-- join factor -> provenance so a result can always state its data lineage.
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS dataset_provenance (
    id            serial PRIMARY KEY,
    dataset_name  text        NOT NULL,
    source        text        NOT NULL,
    resolution    text,
    crs           text,
    retrieved_at  timestamptz NOT NULL DEFAULT now(),
    version       text        NOT NULL,
    object_key    text        NOT NULL,
    extent        geometry(Polygon, 4326),
    checksum      text,
    created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS dataset_provenance_extent_gix
    ON dataset_provenance USING gist (extent);

CREATE INDEX IF NOT EXISTS dataset_provenance_name_version_ix
    ON dataset_provenance (dataset_name, version);
