# ADR-0001: Record architecture decisions

## Status

Accepted

## Date

2026-05-28

## Deciders

Delivery/PM, GIS Specialist, DevOps/Platform, Product Owner (the Phase 0 design table).

## Context

TerraBean is built by a **cross-functional team** (agronomy, GIS, backend, frontend,
data, DevOps, product — see [08-team-and-roles.md](../08-team-and-roles.md)) over a
multi-phase lifecycle ([07-roadmap-and-phases.md](../07-roadmap-and-phases.md)). Decisions
made in Phase 0 — queue, datasets, deployment shape — will be questioned months later by
people who were not in the room, including a possible cloud team in Phase 5.

The design docs already explain *what* was chosen, but the project's stated principle is
that **the why matters more than the what** ([05-tech-stack.md](../05-tech-stack.md)). We
need a durable, low-ceremony decision trail that survives team turnover and captures the
alternatives we rejected, so we do not re-litigate settled questions or silently reverse
them.

We considered: (a) no formal record (relies on tribal memory — fails the moment someone
leaves); (b) decisions buried in PR descriptions and chat (unsearchable, ephemeral);
(c) a single growing "decisions" page (no immutability, no clear supersession). None give
a stable, citable, per-decision artifact.

## Decision

We will capture each significant architectural decision as an **Architecture Decision
Record** using the Michael Nygard template (Status, Context, Decision, Consequences).

- ADRs live in `docs/adr/` as markdown, numbered sequentially (`NNNN-kebab-title.md`).
- An ADR is **immutable once Accepted**. To change a decision we write a new ADR that
  **supersedes** the old one, and mark the old one `Superseded by ADR-XXXX` — we do not
  edit history. Trivial fixes (typos, broken links) are the only allowed edits.
- Each ADR records the alternatives considered and why the chosen option won.
- ADRs are reviewed in the same PR flow as code.

## Consequences

### Positive

- A searchable, citable trail of *why* each choice was made; new joiners ramp faster.
- Immutability + supersession makes reversals explicit and auditable.
- Forces alternatives to be written down before a decision is locked.

### Negative

- A small, ongoing authoring cost per significant decision.
- The team must agree on what counts as "significant" to avoid both over- and
  under-documenting; this is left to author judgment plus PR review.

## Related

- Template/process applies to all ADRs in this directory.
- Decision-rationale principle: [05-tech-stack.md](../05-tech-stack.md),
  [04-architecture.md](../04-architecture.md).
