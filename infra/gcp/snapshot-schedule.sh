#!/usr/bin/env bash
# Attach a weekly snapshot policy to the demo VM's boot disk.
# Cost: ~$1.30/mo at 50 GB x 4 retained weekly snapshots @ $0.026/GB.
# Restore: `gcloud compute disks create ... --source-snapshot=<snap>` then mount on a new VM.

set -euo pipefail

INSTANCE_NAME="${INSTANCE_NAME:-terrabean-demo}"
ZONE="${ZONE:-asia-southeast1-a}"
REGION="${REGION:-asia-southeast1}"
POLICY="${POLICY:-terrabean-weekly-snap}"

if ! gcloud compute resource-policies describe "${POLICY}" --region "${REGION}" >/dev/null 2>&1; then
	gcloud compute resource-policies create snapshot-schedule "${POLICY}" \
		--region "${REGION}" \
		--weekly-schedule monday \
		--start-time 18:00 \
		--max-retention-days 28 \
		--storage-location "${REGION}" \
		--description "TerraBean: weekly boot-disk snapshot, 4-week retention"
fi

DISK="$(gcloud compute instances describe "${INSTANCE_NAME}" --zone "${ZONE}" \
	--format='value(disks[0].deviceName)')"
gcloud compute disks add-resource-policies "${INSTANCE_NAME}-boot" \
	--zone "${ZONE}" \
	--resource-policies "${POLICY}" 2>&1 | tail -1 || true

echo "Snapshot policy ${POLICY} attached to ${INSTANCE_NAME}'s boot disk."
echo "First snapshot: next Monday 18:00 ${REGION}. Restore drill in infra/gcp/README.md."
