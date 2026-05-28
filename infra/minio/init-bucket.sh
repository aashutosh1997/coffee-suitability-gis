#!/bin/sh
# One-shot: wait for MinIO, then create the COG bucket (idempotent).
set -e

echo "init-bucket: waiting for MinIO at ${MINIO_ENDPOINT} ..."
until mc alias set local "${MINIO_ENDPOINT}" "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}" >/dev/null 2>&1; do
  sleep 2
done

mc mb --ignore-existing "local/${MINIO_BUCKET}"
echo "init-bucket: bucket '${MINIO_BUCKET}' is ready."
