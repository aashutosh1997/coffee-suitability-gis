# k3s manifests (deferred)

Per [ADR-0005](../../docs/adr/0005-orchestration-compose-vs-k3s-at-launch.md), the
initial on-prem footprint runs on **Docker Compose**. k3s/Kubernetes manifests are
deferred until high-availability / multi-node operation is needed (Phase 4/5).

Because every component is already a container with S3-compatible storage and OIDC auth
([ADR-0003](../../docs/adr/0003-containerize-for-onprem-to-cloud-portability.md)), the
move to k3s — and later to managed cloud Kubernetes — is an infrastructure change, not a
rewrite. Manifests/Helm charts will land here when that work starts.
