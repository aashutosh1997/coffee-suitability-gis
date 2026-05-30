# ADR-0009: GCP single-VM demo deployment (Docker Compose + Caddy)

## Status

Accepted (implemented 2026-05-30 — production Dockerfile + Caddyfile + Compose
override at [`frontend/Dockerfile.prod`](../../frontend/Dockerfile.prod),
[`infra/caddy/Caddyfile`](../../infra/caddy/Caddyfile),
[`docker-compose.prod.yml`](../../docker-compose.prod.yml); GCP provisioning
scripts at [`infra/gcp/`](../../infra/gcp/); operational targets in
[`Makefile`](../../Makefile) and runbook in
[`infra/gcp/README.md`](../../infra/gcp/README.md)).

## Date

2026-05-30

## Deciders

DevOps/Platform, Backend Engineer, Frontend Engineer, Delivery/PM.

## Context

The roadmap puts cloud at **Phase 5**
([07-roadmap-and-phases.md:73-78](../07-roadmap-and-phases.md#L73-L78)) — managed
k8s, S3/GCS, Cloud SQL, the full cloud-native treatment. The user is mid-Phase 3
and wants a public deployable demo **now** with a $300 free GCP trial, stretched
as long as possible to share with stakeholders.

[ADR-0003](0003-containerize-for-onprem-to-cloud-portability.md) already
established that *"on-prem → cloud is an infrastructure/config change, not a
code rewrite,"* and [ADR-0005](0005-orchestration-compose-vs-k3s-at-launch.md)
already endorsed Docker Compose for *"a small, single-host deployment for one
cooperative."* So a thin demo slice fits cleanly inside the documented ladder
without violating either.

The hard constraint is the **$300 ceiling**. Each managed alternative
individually breaks that constraint at the scale of one demo:

| Option | Approx monthly minimum | Runway on $300 | Verdict |
|---|---|---|---|
| **GCE e2-small + Compose + Caddy** | **~$17.65** | **~17 months** | Chosen |
| GCE e2-medium + Compose + Caddy | ~$30.65 | ~9.5 months | Headroom upgrade path |
| GKE Autopilot | ~$74 cluster fee + workloads | ~4 months | Burns budget on the control plane |
| Cloud Run + Cloud SQL + Memorystore + GCS | ~$45+ (Memorystore alone $35) | ~6 months | Phase 5 target but too costly *now* |
| App Engine Flex + managed Postgres | ~$50+ | ~5 months | Same story |

## Decision

Adopt a **single Compute Engine `e2-small` VM in `asia-southeast1` (Singapore),
running the existing `docker-compose.yml` extended by a thin `docker-compose.prod.yml`
override, fronted by Caddy as the single reverse proxy with auto-TLS** for the
duration of the $300-credit demo window. Phase 4 hardening and Phase 5 cloud-
native migration are explicitly out of scope for this slice.

Concrete shape:

- **Region:** `asia-southeast1` (Singapore) — closest sensible GCP region to the
  Nepal pilot. Latency to Kathmandu ~80 ms (vs ~300 ms from us-central1).
- **Machine:** e2-small (2 vCPU shared, 2 GB RAM) + 4 GB swap file. e2-medium
  resize is one stop/start cycle if the worker OOMs (R-VMSPILL).
- **Disk:** 50 GB `pd-standard` boot disk. Docker named volumes (`pgdata`,
  `miniodata`, `caddy_data`) live on it and survive a stop/start. Half the
  price of pd-balanced; SSD I/O is not the bottleneck here.
- **Reverse proxy:** Caddy 2 in a separate container (the *web* service in
  `docker-compose.prod.yml`) replaces the Vite dev server. Caddy serves the
  built SPA AND reverse-proxies `/api/* → api:8000` and `/tiles/* → titiler:80`.
  Browser hits **one origin** so CORS collapses to nothing — exactly the topology
  [ADR-0008](0008-titiler-raster-overlays.md) anticipated.
- **TLS:** Let's Encrypt via Caddy's built-in `tls` directive. Cert lives in
  the `caddy_data` volume and survives restarts.
- **Build:** `frontend/Dockerfile.prod` is a multi-stage Node-24 → caddy:2-alpine
  image with `dist/` baked at `/srv` and the Caddyfile baked at `/etc/caddy/Caddyfile`.
  `VITE_API_BASE` is a build-arg so the same image works for any deploy.
- **Backend URL flipping is env-only:** `TITILER_BASE_URL=/tiles` and
  `CORS_ORIGINS=["https://<host>"]` in the VM's `.env`. The `/overlays`
  endpoint already honors `titiler_base_url` and returns relative tile templates
  for free — no code change needed.
- **Pinned image tags** for `minio` (`RELEASE.2025-09-07T16-13-09Z`) and TiTiler
  (`2.0.2`) in the prod override; `latest` is a footgun in production.
- **Secrets** stay in a non-committed `.env` on the VM with mode `600`. GCP
  Secret Manager + Workload Identity is the right answer for production but
  belongs in Phase 4/5 — not in a demo deploy.
- **Backups:** weekly disk snapshot policy (4-week retention) costs ~$1.30/mo
  and restores to a fresh VM in minutes via `gcloud compute disks create
  --source-snapshot=...`. Cloud SQL PITR is Phase 5.
- **Cost hygiene:** `make vm-stop` from the laptop drops compute charges ~95%
  while disk + snapshot accrue at ~$3.30/mo; runway extends to **~48 months**
  if the VM only runs ~8 h/day. Budget alerts at 17/33/67/97% of $300 are part
  of the deploy runbook.

## Out of scope (this slice)

- **GKE / Cloud Run / managed databases.** Each individually busts the $300
  budget; collectively the cost would consume the credits in under 4 months.
- **High availability, autoscaling, rolling deploy.** A single VM with a single
  replica of every service. `make deploy` causes a few seconds of downtime. A
  real Phase 4 production review would reject this.
- **Workload Identity / VPC Service Controls / per-tier service accounts.** A
  same-VM all-tier deploy means a single container RCE reaches everything.
  Acceptable for a stakeholder demo, not for handling real user data.
- **GitHub Actions deploy.** `make deploy` is a manual SSH-and-run for now.
  A 20-line workflow that SSHes in and re-runs `make deploy` on `main` push is
  a documented follow-up.
- **Centralized observability.** Container logs go to `docker logs`; GCP serial
  console catches kernel/systemd issues. Prometheus/Grafana/Loki are Phase 4.

## Consequences

### Positive

- **17 months of always-on runway** on the $300 trial, ~48 months with
  overnight-stop hygiene. Both numbers comfortably outlast the demo window.
- **Topology matches what the architecture docs already anticipated** — one
  nginx-class origin in front of api+titiler ([ADR-0008](0008-titiler-raster-overlays.md),
  [04-architecture.md:120](../04-architecture.md#L120)). The Caddy choice (vs
  nginx + certbot) is a smaller-footprint, declarative-config simplification
  consistent with single-host scale.
- **No code changes** to flip from dev to prod — only env vars and a compose
  override. The existing test suites (73 backend, 41 frontend) all keep
  passing because they run against the unchanged `docker-compose.yml` /
  local-fixture mode.
- **Phase 5 migration stays a config swap, not a rewrite.** When real load
  arrives, move `minio` → GCS, `postgis` → Cloud SQL, `redis` → Memorystore
  one at a time. The container images and the application code don't change.

### Negative

- **Single point of failure.** VM down = service down. Acceptable demo SLA.
- **No managed backups.** Disk snapshots only, weekly cadence. A `pgdata`
  corruption between Mondays loses up to a week of writes (acceptable for a
  read-mostly demo with rebuildable seed data).
- **DNS A-record drift on stop/start.** External IP is ephemeral; `make vm-start`
  prints the new IP and reminds the user to update the registrar. A reserved
  static IP would fix this but costs $1.46/mo when the VM is stopped — not worth
  it at this scale.
- **Image tags need maintenance.** MinIO + TiTiler get security fixes weekly.
  Re-pin every couple of months; the runbook documents the procedure.
- **No CI/CD.** Promotion is manual. A push-to-deploy workflow is a few
  follow-up hours of work but explicitly out of scope here.

## Trigger conditions for graduating to Phase 5

This deployment is **explicitly time-bounded by the $300 credit window** and
the demo's purpose. Promote to the proper cloud architecture when **any** of:

- Real cooperative users start hitting it (real auth, real audit, real backups).
- Concurrent load exceeds what one e2-medium can serve (resize is cheap; >1
  replica needs an orchestrator).
- A pre-launch security review demands per-tier service accounts and managed
  secrets.
- The credits run out and the monthly cost is no longer "absorbed by experimentation."

At that point: managed Postgres ([ADR-0003](0003-containerize-for-onprem-to-cloud-portability.md)
already names Cloud SQL), GCS for MinIO, Memorystore for Redis, GKE Autopilot
or k3s on multi-node (per [ADR-0005](0005-orchestration-compose-vs-k3s-at-launch.md))
for the orchestrator, Cloud Armor / IAP for the edge, Workload Identity for
service-to-service auth. None of those moves touch application code.

## Related

- ADR-0003 — containerize for portability (the enabling decision).
- ADR-0005 — Docker Compose at launch (the orchestration decision that this
  extends to "and on a single cloud VM too").
- ADR-0008 — TiTiler raster overlays + single-origin nginx topology
  (the anticipated production routing this implements).
- [04-architecture.md](../04-architecture.md) — components, on-prem ↔ cloud
  table, prod topology.
- [Risk register](../phase-0/risk-register.md) — R-VMSPILL, R-LELIMIT,
  R-COSTDRIFT added in this slice.
