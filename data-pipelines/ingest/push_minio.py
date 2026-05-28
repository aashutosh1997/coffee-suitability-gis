"""Upload a COG to MinIO (S3-compatible). Cloud migration = endpoint swap (ADR-0003)."""

from __future__ import annotations

import argparse
import os


def push(local_path: str, key: str, bucket: str | None = None) -> str:
    import boto3

    endpoint = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
    bucket = bucket or os.getenv("MINIO_BUCKET", "terrabean-cogs")
    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=os.getenv("MINIO_ROOT_USER", "terrabean"),
        aws_secret_access_key=os.getenv("MINIO_ROOT_PASSWORD", "change-me-locally"),
    )
    client.upload_file(local_path, bucket, key)
    uri = f"s3://{bucket}/{key}"
    print(f"push_minio: uploaded {local_path} -> {uri}")
    return uri


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload a file to MinIO")
    parser.add_argument("local_path")
    parser.add_argument("key", help="object key, e.g. dem/copernicus/nepal/2026.1.tif")
    parser.add_argument("--bucket", default=None)
    args = parser.parse_args()
    push(args.local_path, args.key, bucket=args.bucket)


if __name__ == "__main__":
    main()
