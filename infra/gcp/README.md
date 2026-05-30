# GCP demo deployment — single VM, Docker Compose + Caddy

The minimum-cost path to put TerraBean on the internet using a free $300 GCP
trial. See [ADR-0009](../../docs/adr/0009-gcp-single-vm-demo-deployment.md) for
why this shape (one VM, no managed services) was chosen over GKE / Cloud Run.

**Target burn:** ~$17.65/month always-on → ~17 months on $300 credits.
Stop the VM overnight via `make vm-stop` and that drops to ~$6/month → ~48 months.

## Prerequisites

- `gcloud` CLI installed and authenticated (`gcloud auth login`).
- A GCP project with **billing enabled** (free trial credits qualify) — set as
  the active project: `gcloud config set project <PROJECT_ID>`.
- A domain you control. Caddy will auto-provision a Let's Encrypt cert for it.

`provision.sh` enables `compute.googleapis.com` for you on first run; you do
not need to enable it manually.

## Deploy

```bash
# From your laptop, with the right GCP project active:
gcloud config set project <YOUR_PROJECT_ID>
bash infra/gcp/provision.sh
```

The script prints the VM's external IP. Point your domain's A record at it
(TTL 300 is fine). DNS usually propagates within a minute.

SSH in:

```bash
gcloud compute ssh terrabean-demo --zone asia-southeast1-a
sudo usermod -aG docker $(whoami)      # one-time: add yourself to docker group
exit                                    # re-login so the group takes effect
gcloud compute ssh terrabean-demo --zone asia-southeast1-a
```

On the VM:

```bash
cd /opt/coffee-suitability-gis
cp .env.prod.example .env
# Edit .env: set DEPLOY_HOSTNAME to your domain, generate strong passwords
# (openssl rand -base64 24 for each REPLACE_WITH_STRONG_PASSWORD).
make deploy           # docker compose up -d with the prod override
make deploy-seed      # one-time pilot DEM + climate seed (~5 min)
```

Browse `https://your.domain` — Caddy auto-issues the cert on first request.

## Optional but recommended

```bash
# Weekly disk snapshot (4-week retention, ~$1.30/mo):
bash infra/gcp/snapshot-schedule.sh

# Budget alerts at $50 / $100 / $200 / $290 (replace BILLING_ACCOUNT_ID):
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="TerraBean demo" \
  --budget-amount=300USD \
  --threshold-rule=percent=0.17 \
  --threshold-rule=percent=0.33 \
  --threshold-rule=percent=0.67 \
  --threshold-rule=percent=0.97
```

## Cost-saving toggles

| Command | Effect |
|---|---|
| `make vm-stop` | Stops the VM — compute charges pause (~95% saving). Disk + snapshot still accrue (~$3.30/mo). |
| `make vm-start` | Starts the VM. The ephemeral external IP **may change**; update your A record if so. |
| Delete the VM but keep the snapshot | ~$1.30/mo only. Restore by creating a new disk from the snapshot. |

## Restore from snapshot

```bash
SNAP=$(gcloud compute snapshots list --filter="sourceDisk~terrabean-demo-boot" --sort-by=~creationTimestamp --limit=1 --format='value(name)')
gcloud compute disks create terrabean-restore --source-snapshot="$SNAP" --zone asia-southeast1-a --type pd-standard
gcloud compute instances create terrabean-restored \
  --zone asia-southeast1-a --machine-type e2-small \
  --disk name=terrabean-restore,boot=yes \
  --tags http-server,https-server
```

## Resize for headroom

If polygon assessments OOM (R-VMSPILL), bump to e2-medium (~$13/mo extra):

```bash
make vm-stop
gcloud compute instances set-machine-type terrabean-demo \
  --zone asia-southeast1-a --machine-type e2-medium
make vm-start
```

## Tear down

```bash
gcloud compute instances delete terrabean-demo --zone asia-southeast1-a --quiet
gcloud compute snapshots list --filter="sourceDisk~terrabean-demo-boot" \
  --format='value(name)' | xargs -r gcloud compute snapshots delete --quiet
gcloud compute resource-policies delete terrabean-weekly-snap --region asia-southeast1 --quiet
gcloud compute firewall-rules delete terrabean-allow-http-https --quiet
```
