#!/usr/bin/env bash
# Provision the TerraBean demo VM on GCP.
#
# Prereqs:
#   - gcloud CLI installed and authenticated (`gcloud auth login`)
#   - active project set (`gcloud config set project <PROJECT_ID>`)
#   - billing enabled on the project (free $300 credits qualify)
#   - a domain you control (for Caddy auto-TLS)
#
# Total monthly cost target: ~$17.65 always-on, ~$6 if stopped 16h/day.
# See docs/adr/0009-gcp-single-vm-demo-deployment.md for the cost breakdown.

set -euo pipefail

INSTANCE_NAME="${INSTANCE_NAME:-terrabean-demo}"
ZONE="${ZONE:-asia-southeast1-a}"
MACHINE_TYPE="${MACHINE_TYPE:-e2-small}"
DISK_SIZE_GB="${DISK_SIZE_GB:-50}"
IMAGE_FAMILY="${IMAGE_FAMILY:-ubuntu-2404-lts-amd64}"
IMAGE_PROJECT="${IMAGE_PROJECT:-ubuntu-os-cloud}"
FIREWALL_RULE="${FIREWALL_RULE:-terrabean-allow-http-https}"

PROJECT="$(gcloud config get-value project 2>/dev/null || true)"
if [[ -z "${PROJECT}" ]]; then
	echo "ERROR: no active gcloud project. Run: gcloud config set project <PROJECT_ID>" >&2
	exit 1
fi

echo "Provisioning ${INSTANCE_NAME} in ${PROJECT}/${ZONE} (${MACHINE_TYPE}, ${DISK_SIZE_GB} GB pd-standard)."

# Required APIs. Doing this up front avoids the interactive "API not enabled,
# enable and retry? (y/N)" prompt that gcloud throws on the first compute call --
# the script can't see that prompt cleanly through a pipe and would hang.
REQUIRED_SERVICES=(compute.googleapis.com)
echo "Enabling required APIs: ${REQUIRED_SERVICES[*]}"
gcloud services enable "${REQUIRED_SERVICES[@]}" --quiet

# OS Login = passwordless SSH via Google identity, no SSH key sprawl.
gcloud compute project-info add-metadata \
	--metadata enable-oslogin=TRUE \
	--quiet

# Firewall: open 80 + 443 to anything tagged http-server / https-server.
if ! gcloud compute firewall-rules describe "${FIREWALL_RULE}" >/dev/null 2>&1; then
	gcloud compute firewall-rules create "${FIREWALL_RULE}" \
		--allow tcp:80,tcp:443 \
		--target-tags http-server,https-server \
		--description "TerraBean: Caddy on :80/:443"
fi

# VM. Tags pick up the firewall rule above.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
gcloud compute instances create "${INSTANCE_NAME}" \
	--zone "${ZONE}" \
	--machine-type "${MACHINE_TYPE}" \
	--image-family "${IMAGE_FAMILY}" \
	--image-project "${IMAGE_PROJECT}" \
	--boot-disk-size "${DISK_SIZE_GB}GB" \
	--boot-disk-type pd-standard \
	--boot-disk-device-name "${INSTANCE_NAME}-boot" \
	--tags http-server,https-server \
	--metadata-from-file "startup-script=${SCRIPT_DIR}/startup.sh"

IP="$(gcloud compute instances describe "${INSTANCE_NAME}" --zone "${ZONE}" \
	--format='value(networkInterfaces[0].accessConfigs[0].natIP)')"

cat <<EOF

VM provisioned. External IP: ${IP}

Next steps:
  1. Point your domain's A record at ${IP} (TTL 300 is plenty).
  2. Wait ~60 s for the startup-script to install Docker + clone the repo.
     Tail it with: gcloud compute ssh ${INSTANCE_NAME} --zone ${ZONE} -- sudo journalctl -u google-startup-scripts.service -f
  3. SSH in:        gcloud compute ssh ${INSTANCE_NAME} --zone ${ZONE}
  4. On the VM:     cd coffee-suitability-gis
                    cp .env.prod.example .env  # then edit -- set DEPLOY_HOSTNAME + strong passwords
                    make deploy
                    make deploy-seed          # one-time pilot DEM + climate seed
  5. Snapshot policy (optional, ~\$1.30/mo): bash infra/gcp/snapshot-schedule.sh
  6. Budget alert (optional): see docs/adr/0009-gcp-single-vm-demo-deployment.md

Cost-saving toggles (run from your laptop):
  make vm-stop     # ~95% off compute charges, disk + snapshot still accrue
  make vm-start
EOF
