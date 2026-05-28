# ADR-0005: Use Docker Compose (not k3s) for the initial on-prem deployment

## Status

Accepted

## Date

2026-05-28

## Deciders

DevOps/Platform, Delivery/PM, Backend Engineer.

## Context

The initial on-prem footprint is a **small, single-host** deployment for one cooperative
([07-roadmap-and-phases.md](../07-roadmap-and-phases.md) Phase 4). All components are already
containerized and run the same images at every orchestration rung
([ADR-0003](0003-containerize-for-onprem-to-cloud-portability.md)), so the choice here is
purely *which orchestrator to start with* — not whether we can move later.

The early needs are: bring a defined set of services up/down together, manage dependencies
and health, mount volumes for PostGIS/MinIO, and let a small co-op-facing team operate it.
There is no multi-node, no autoscaling, and no HA requirement at launch.

Alternatives considered:

- **k3s now** — lightweight Kubernetes; gives HA, rolling deploys, and a head start on the
  cloud k8s endgame, but adds real operational complexity (cluster lifecycle, manifests,
  ingress, storage classes) for a single host with one operator. Premature.
- **Host-native processes** — rejected by [ADR-0003](0003-containerize-for-onprem-to-cloud-portability.md).

Because ADR-0003 makes k3s a later **infrastructure swap, not a rewrite**, starting on
Compose costs us nothing strategically.

## Decision

Use **Docker Compose** for the initial on-prem deployment. **Defer k3s.**

Compose is the simplest thing that runs a single-host multi-container stack, and it matches
what developers already use locally. We **revisit and adopt k3s when HA / multi-node is
actually needed** (around Phase 4 hardening into Phase 5), at which point it becomes the
stepping stone to managed cloud Kubernetes.

## Consequences

### Positive

- Minimal operational burden for a small team; fastest path to a live on-prem launch.
- Dev/prod parity — the same Compose-style workflow used in development.

### Negative

- No built-in HA, self-healing, or rolling updates; single-host is a single point of failure
  until k3s/cloud — acceptable for the initial footprint, backed by backups (NFR-10).
- A future migration step to k3s remains on the roadmap (low-risk by design).

## Related

- Portability ladder that makes this reversible: [ADR-0003](0003-containerize-for-onprem-to-cloud-portability.md).
- Orchestration progression & deploy phases: [05-tech-stack.md](../05-tech-stack.md),
  [04-architecture.md](../04-architecture.md), [07-roadmap-and-phases.md](../07-roadmap-and-phases.md).
