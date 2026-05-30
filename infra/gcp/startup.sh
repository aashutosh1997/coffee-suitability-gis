#!/usr/bin/env bash
# Runs once on first VM boot (metadata startup-script). Installs Docker + compose,
# adds a 4 GB swapfile (R-VMSPILL mitigation), and clones the repo.
# Idempotent: a re-run will skip steps that already succeeded.

set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

REPO_URL="${REPO_URL:-https://github.com/aashutoshpyakurel/coffee-suitability-gis.git}"
REPO_DIR="/opt/terrabean"
SWAPFILE="/swapfile"

apt-get update -qq
apt-get install -y -qq \
	ca-certificates curl gnupg lsb-release git make

# Docker engine + compose-plugin via the official APT repo.
if ! command -v docker >/dev/null 2>&1; then
	install -m 0755 -d /etc/apt/keyrings
	curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
		| gpg --dearmor -o /etc/apt/keyrings/docker.gpg
	chmod a+r /etc/apt/keyrings/docker.gpg
	echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
		> /etc/apt/sources.list.d/docker.list
	apt-get update -qq
	apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
	systemctl enable --now docker
fi

# 4 GB swap so the Celery worker has a buffer during peak rasterio loads.
if ! grep -q "${SWAPFILE}" /etc/fstab; then
	fallocate -l 4G "${SWAPFILE}"
	chmod 600 "${SWAPFILE}"
	mkswap "${SWAPFILE}"
	swapon "${SWAPFILE}"
	echo "${SWAPFILE} none swap sw 0 0" >> /etc/fstab
	# Be conservative -- prefer real RAM, only swap when truly needed.
	echo "vm.swappiness=10" > /etc/sysctl.d/99-swappiness.conf
	sysctl -p /etc/sysctl.d/99-swappiness.conf
fi

# Clone the repo into /opt (owned by root; SSH'd user runs git pull via sudo or
# OS-Login + group membership).
if [[ ! -d "${REPO_DIR}/.git" ]]; then
	git clone --depth 1 "${REPO_URL}" "${REPO_DIR}"
fi

# Make the repo writeable by the docker group so OS-Login users can run `make deploy`
# without sudo. They still need to be added to the docker group on first SSH
# (gcloud compute ssh + sudo usermod -aG docker $(whoami) + re-login).
chgrp -R docker "${REPO_DIR}"
chmod -R g+rwX "${REPO_DIR}"

# Symlink at /home for convenience -- whoever SSHes in lands in their home dir.
ln -sf "${REPO_DIR}" /opt/coffee-suitability-gis

echo "startup-script: done. Next: SSH in, cp .env.prod.example .env, edit it, then 'make deploy'."
