# ADR-0003: Containerize every component for on-prem-to-cloud portability

## Status

Accepted

## Date

2026-05-28

## Deciders

DevOps/Platform, Backend Engineer, Delivery/PM, Product Owner.

## Context

TerraBean launches **on-premises** inside the cooperative (no hard dependency on any one
cloud vendor, NFR-4) but must be able to move to managed cloud later **without a rewrite**
(NFR-5/6, [07-roadmap-and-phases.md](../07-roadmap-and-phases.md) Phase 5). If portability
is bolted on later it becomes a migration project; if it is a design constraint from day
one it becomes a config change.

The risk is host-coupling: services that assume local filesystem paths, a fixed hostname,
a specific OS, or a vendor SDK make the eventual cloud jump expensive and lossy.

Alternatives considered:

- **Host-native processes (systemd/venv)** — simplest on a single box, but couples the app
  to that host and makes cloud migration a re-platforming effort.
- **Cloud-native from day one** (managed k8s, S3, managed Postgres) — violates the on-prem-
  first requirement and adds cost/lock-in before it is needed.

## Decision

**Every component runs as a container**, and external interfaces are chosen so the runtime
is swappable rather than rewritten:

- **Object storage is S3-compatible**: MinIO on-prem now, swap the endpoint/credentials for
  S3/GCS/Azure Blob later (same API). Rasters are stored as COGs that read identically from
  either ([04-architecture.md](../04-architecture.md), [06-data-sources.md](../06-data-sources.md)).
- **Auth is OIDC** via **Keycloak**, replaceable by a managed OIDC provider.
- **Orchestration is a ladder**, not a fork: **Docker Compose → k3s → managed Kubernetes**,
  running the **same images** at every rung.
- All config (endpoints, secrets, credentials) is injected via environment/secret stores —
  **nothing host-specific is baked into an image**.

On-prem → cloud is therefore an **infrastructure/config change, not a code rewrite**.

## Consequences

### Positive

- One artifact set runs everywhere; cloud migration is incremental and low-risk.
- No vendor lock-in at the storage, auth, or orchestration layers.
- Local dev mirrors production (same images).

### Negative

- Container/image discipline is mandatory: no host paths, no hardcoded hostnames, no
  vendor-specific SDK calls, config strictly externalized.
- A baseline operational cost (image builds, a registry, container runtime) even for the
  small initial footprint.

## Related

- Migration path table & principles: [04-architecture.md](../04-architecture.md).
- Orchestration choice at launch: [ADR-0005](0005-orchestration-compose-vs-k3s-at-launch.md).
- Queue operational cost bounded by this ADR: [ADR-0002](0002-queue-celery-vs-rq-dramatiq.md).
- Referenced by the project README and the Phase 5 cloud plan.
