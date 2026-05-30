# Validation report — config 2026.2

> **SYNTHETIC DATA — NOT AN ACCURACY CLAIM.** This exercises the validation harness against a synthetic, stratified plot set with no agronomic meaning. The agreement % proves the mechanism works; the >=80% launch target (doc 01) is only meaningful against real co-op-labelled plots (ground-truth-plan.md §5).

## Summary
- Plots: 40 (scored 40, excluded 0)
- Agreement: **19/40 = 47.5%** (≥80% target NOT met — synthetic)
- Class→status mapping: S1→thriving, S2→thriving, S3→struggling, N→failed
- Limiting factor in disagreements: slope (10), altitude (7), shading (4)

## Confusion matrix (rows = observed, columns = mapped prediction)
| observed \ predicted | thriving | struggling | failed |
|---|---|---|---|
| **thriving** | 14 | 0 | 1 |
| **struggling** | 9 | 1 | 2 |
| **failed** | 8 | 1 | 4 |

## Per-plot results
| plot | district | observed | predicted | score | expected | agree | limiting |
|---|---|---|---|---|---|---|---|
| GUL-001 | Gulmi | thriving | S1 | 0.94 | thriving | ✓ | slope |
| GUL-002 | Gulmi | thriving | S1 | 0.83 | thriving | ✓ | shading |
| GUL-003 | Gulmi | thriving | S2 | 0.72 | thriving | ✓ | slope |
| GUL-004 | Gulmi | thriving | S1 | 1.00 | thriving | ✓ | altitude |
| GUL-005 | Gulmi | struggling | S1 | 0.95 | thriving | ✗ (optimistic) | slope |
| GUL-006 | Gulmi | struggling | N | 0.51 | failed | ✗ (pessimistic) | altitude |
| GUL-007 | Gulmi | failed | S1 | 0.83 | thriving | ✗ (optimistic) | shading |
| GUL-008 | Gulmi | struggling | S1 | 0.84 | thriving | ✗ (optimistic) | slope |
| GUL-009 | Gulmi | struggling | S1 | 1.00 | thriving | ✗ (optimistic) | altitude |
| GUL-010 | Gulmi | failed | S1 | 0.91 | thriving | ✗ (optimistic) | slope |
| GUL-011 | Gulmi | failed | S2 | 0.77 | thriving | ✗ (optimistic) | slope |
| GUL-012 | Gulmi | struggling | S2 | 0.78 | thriving | ✗ (optimistic) | shading |
| GUL-013 | Gulmi | thriving | S2 | 0.79 | thriving | ✓ | slope |
| SYA-001 | Syangja | thriving | S1 | 0.85 | thriving | ✓ | slope |
| SYA-002 | Syangja | thriving | S2 | 0.75 | thriving | ✓ | slope |
| SYA-003 | Syangja | thriving | S2 | 0.77 | thriving | ✓ | slope |
| SYA-004 | Syangja | struggling | S3 | 0.66 | struggling | ✓ | altitude |
| SYA-005 | Syangja | struggling | S1 | 0.94 | thriving | ✗ (optimistic) | slope |
| SYA-006 | Syangja | thriving | N | 0.56 | failed | ✗ (pessimistic) | altitude |
| SYA-007 | Syangja | struggling | N | 0.49 | failed | ✗ (pessimistic) | altitude |
| SYA-008 | Syangja | failed | S2 | 0.72 | thriving | ✗ (optimistic) | slope |
| SYA-009 | Syangja | thriving | S1 | 0.98 | thriving | ✓ | shading |
| SYA-010 | Syangja | failed | S3 | 0.66 | struggling | ✗ (optimistic) | altitude |
| SYA-011 | Syangja | thriving | S2 | 0.76 | thriving | ✓ | altitude |
| KAV-001 | Kavre | struggling | S1 | 0.98 | thriving | ✗ (optimistic) | shading |
| KAV-002 | Kavre | failed | S2 | 0.79 | thriving | ✗ (optimistic) | slope |
| KAV-003 | Kavre | thriving | S2 | 0.78 | thriving | ✓ | shading |
| KAV-004 | Kavre | thriving | S2 | 0.78 | thriving | ✓ | slope |
| KAV-005 | Kavre | thriving | S1 | 0.94 | thriving | ✓ | slope |
| KAV-006 | Kavre | struggling | S1 | 0.94 | thriving | ✗ (optimistic) | slope |
| KAV-007 | Kavre | failed | S2 | 0.78 | thriving | ✗ (optimistic) | slope |
| KAV-008 | Kavre | failed | S1 | 0.89 | thriving | ✗ (optimistic) | altitude |
| KAV-009 | Kavre | thriving | S1 | 0.93 | thriving | ✓ | shading |
| KAV-010 | Kavre | struggling | S1 | 0.88 | thriving | ✗ (optimistic) | shading |
| KAV-011 | Kavre | struggling | S2 | 0.72 | thriving | ✗ (optimistic) | slope |
| KAV-012 | Kavre | failed | S1 | 0.89 | thriving | ✗ (optimistic) | altitude |
| NAW-001 | Nawalparasi | failed | N | 0.40 | failed | ✓ | altitude |
| NAW-002 | Nawalparasi | failed | N | 0.40 | failed | ✓ | altitude |
| CHI-001 | Chitwan | failed | N | 0.46 | failed | ✓ | altitude |
| CHI-002 | Chitwan | failed | N | 0.40 | failed | ✓ | altitude |
