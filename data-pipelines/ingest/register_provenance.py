"""Record dataset provenance in PostGIS so every assessment can report it (FR-15) and
stay reproducible (NFR-16). See sql/001_provenance.sql for the schema.
"""

from __future__ import annotations

import argparse
import os
from datetime import UTC, datetime
from pathlib import Path

SQL_FILE = Path(__file__).resolve().parents[1] / "sql" / "001_provenance.sql"


def _dsn() -> str:
    # psycopg wants a libpq DSN; strip any SQLAlchemy "+driver" suffix.
    url = os.getenv(
        "DATABASE_URL",
        "postgresql://terrabean:change-me-locally@localhost:5432/terrabean",
    )
    return url.replace("postgresql+psycopg://", "postgresql://")


def ensure_schema(conn) -> None:
    conn.execute(SQL_FILE.read_text())


def register(
    dataset_name: str,
    source: str,
    resolution: str,
    crs: str,
    version: str,
    object_key: str,
    extent_wkt: str | None = None,
    checksum: str | None = None,
) -> None:
    import psycopg

    with psycopg.connect(_dsn(), autocommit=True) as conn:
        ensure_schema(conn)
        conn.execute(
            """
            INSERT INTO dataset_provenance
              (dataset_name, source, resolution, crs, retrieved_at, version,
               object_key, extent, checksum)
            VALUES (%s, %s, %s, %s, %s, %s, %s,
                    CASE WHEN %s IS NULL THEN NULL
                         ELSE ST_GeomFromText(%s, 4326) END,
                    %s)
            """,
            (
                dataset_name,
                source,
                resolution,
                crs,
                datetime.now(UTC),
                version,
                object_key,
                extent_wkt,
                extent_wkt,
                checksum,
            ),
        )
    print(f"register_provenance: recorded {dataset_name} {version} -> {object_key}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Register dataset provenance in PostGIS"
    )
    parser.add_argument("--dataset-name", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--resolution", required=True)
    parser.add_argument("--crs", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--object-key", required=True)
    parser.add_argument("--extent-wkt", default=None)
    parser.add_argument("--checksum", default=None)
    args = parser.parse_args()
    register(
        args.dataset_name,
        args.source,
        args.resolution,
        args.crs,
        args.version,
        args.object_key,
        extent_wkt=args.extent_wkt,
        checksum=args.checksum,
    )


if __name__ == "__main__":
    main()
