# ADR-0004: Use Mantine as the UI component library

## Status

Accepted

## Date

2026-05-28

## Deciders

Frontend Engineer, UX/UI Designer, Product Owner.

## Context

The web app is a **data-heavy internal tool** used by **non-GIS field officers**: it needs
forms, tables, modals, notifications, date inputs, and a coherent accessible look, on top of
the MapLibre map. The audience is not power users, so sensible defaults and accessibility
out of the box matter (NFR-17). The team is small and Phase 1+ frontend work is broad
([07-roadmap-and-phases.md](../07-roadmap-and-phases.md)), so we want to spend effort on the
map/result/override experience, not on rebuilding base components.

Alternatives considered:

- **shadcn/ui** — copy-in components you own and restyle; maximal control and a bespoke look,
  but **more maintenance**: each component (and its a11y/behavior) becomes our code to keep,
  and common pieces (data tables, form state, notifications) must be assembled ourselves.
- **Mantine** — batteries-included, accessible components with hooks, form handling, tables,
  modals, and notifications shipped and maintained upstream.

This is a non-branded internal tool, so the bespoke styling advantage of shadcn carries
little weight against its higher maintenance load.

## Decision

Adopt **Mantine** as the component library for the React/TypeScript frontend.

Mantine wins because it delivers accessible, ready-made components for exactly the data-entry
and data-display surfaces this tool is full of, letting a small team move quickly on the
parts that are actually differentiated (map, factor overlays, per-factor breakdown, override
UI).

## Consequences

### Positive

- Faster delivery of forms, tables, notifications, and modals with accessibility built in.
- Consistent theming across the app from a single source.
- Frontend effort concentrates on map/result/override UX, not base widgets.

### Negative

- A first-class dependency on Mantine and its theming model; design is shaped by its
  conventions and upgrade cadence.
- Heavier visual customization fights the framework more than owning copy-in components
  would — acceptable for a non-branded internal tool.

## Related

- Frontend stack and the Mantine-vs-shadcn open question: [05-tech-stack.md](../05-tech-stack.md).
- Usability requirement for non-GIS users: NFR-17, [02-requirements.md](../02-requirements.md).
- Web app responsibilities: [04-architecture.md](../04-architecture.md).
