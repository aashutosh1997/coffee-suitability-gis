# Validation report — config 2026.1

> **SYNTHETIC DATA — NOT AN ACCURACY CLAIM.** This exercises the validation harness against a synthetic, stratified plot set with no agronomic meaning. The agreement % proves the mechanism works; the >=80% launch target (doc 01) is only meaningful against real co-op-labelled plots (ground-truth-plan.md §5).

## Summary
- Plots: 40 (scored 40, excluded 0)
- Agreement: **17/40 = 42.5%** (≥80% target NOT met — synthetic)
- Class→status mapping: S1→thriving, S2→thriving, S3→struggling, N→failed
- Limiting factor in disagreements: slope (8), altitude (7), precipitation (6), temperature (1), shading (1)

## Confusion matrix (rows = observed, columns = mapped prediction)
| observed \ predicted | thriving | struggling | failed |
|---|---|---|---|
| **thriving** | 13 | 1 | 1 |
| **struggling** | 10 | 0 | 2 |
| **failed** | 7 | 2 | 4 |

## Per-plot results
| plot | district | observed | predicted | score | expected | agree | limiting |
|---|---|---|---|---|---|---|---|
| GUL-001 | Gulmi | thriving | S2 | 0.71 | thriving | ✓ | precipitation |
| GUL-002 | Gulmi | thriving | S2 | 0.71 | thriving | ✓ | precipitation |
| GUL-003 | Gulmi | thriving | S2 | 0.60 | thriving | ✓ | slope |
| GUL-004 | Gulmi | thriving | S2 | 0.76 | thriving | ✓ | precipitation |
| GUL-005 | Gulmi | struggling | S2 | 0.76 | thriving | ✗ (optimistic) | precipitation |
| GUL-006 | Gulmi | struggling | N | 0.26 | failed | ✗ (pessimistic) | altitude |
| GUL-007 | Gulmi | failed | S3 | 0.55 | struggling | ✗ (optimistic) | precipitation |
| GUL-008 | Gulmi | struggling | S2 | 0.65 | thriving | ✗ (optimistic) | precipitation |
| GUL-009 | Gulmi | struggling | S1 | 0.81 | thriving | ✗ (optimistic) | precipitation |
| GUL-010 | Gulmi | failed | S1 | 0.85 | thriving | ✗ (optimistic) | slope |
| GUL-011 | Gulmi | failed | S3 | 0.59 | struggling | ✗ (optimistic) | precipitation |
| GUL-012 | Gulmi | struggling | S2 | 0.71 | thriving | ✗ (optimistic) | precipitation |
| GUL-013 | Gulmi | thriving | S3 | 0.56 | struggling | ✗ (pessimistic) | slope |
| SYA-001 | Syangja | thriving | S2 | 0.80 | thriving | ✓ | slope |
| SYA-002 | Syangja | thriving | S2 | 0.76 | thriving | ✓ | slope |
| SYA-003 | Syangja | thriving | S2 | 0.73 | thriving | ✓ | slope |
| SYA-004 | Syangja | struggling | S2 | 0.71 | thriving | ✗ (optimistic) | altitude |
| SYA-005 | Syangja | struggling | S1 | 0.85 | thriving | ✗ (optimistic) | slope |
| SYA-006 | Syangja | thriving | N | 0.61 | failed | ✗ (pessimistic) | altitude |
| SYA-007 | Syangja | struggling | N | 0.56 | failed | ✗ (pessimistic) | altitude |
| SYA-008 | Syangja | failed | S2 | 0.69 | thriving | ✗ (optimistic) | slope |
| SYA-009 | Syangja | thriving | S1 | 0.90 | thriving | ✓ | temperature |
| SYA-010 | Syangja | failed | S2 | 0.77 | thriving | ✗ (optimistic) | altitude |
| SYA-011 | Syangja | thriving | S2 | 0.77 | thriving | ✓ | altitude |
| KAV-001 | Kavre | struggling | S1 | 0.94 | thriving | ✗ (optimistic) | temperature |
| KAV-002 | Kavre | failed | S2 | 0.73 | thriving | ✗ (optimistic) | slope |
| KAV-003 | Kavre | thriving | S2 | 0.78 | thriving | ✓ | shading |
| KAV-004 | Kavre | thriving | S2 | 0.72 | thriving | ✓ | slope |
| KAV-005 | Kavre | thriving | S1 | 0.89 | thriving | ✓ | slope |
| KAV-006 | Kavre | struggling | S1 | 0.94 | thriving | ✗ (optimistic) | slope |
| KAV-007 | Kavre | failed | S2 | 0.78 | thriving | ✗ (optimistic) | slope |
| KAV-008 | Kavre | failed | S1 | 0.89 | thriving | ✗ (optimistic) | altitude |
| KAV-009 | Kavre | thriving | S1 | 0.93 | thriving | ✓ | shading |
| KAV-010 | Kavre | struggling | S1 | 0.88 | thriving | ✗ (optimistic) | shading |
| KAV-011 | Kavre | struggling | S2 | 0.62 | thriving | ✗ (optimistic) | slope |
| KAV-012 | Kavre | failed | S1 | 0.89 | thriving | ✗ (optimistic) | altitude |
| NAW-001 | Nawalparasi | failed | N | 0.46 | failed | ✓ | altitude |
| NAW-002 | Nawalparasi | failed | N | 0.49 | failed | ✓ | altitude |
| CHI-001 | Chitwan | failed | N | 0.52 | failed | ✓ | altitude |
| CHI-002 | Chitwan | failed | N | 0.46 | failed | ✓ | altitude |
