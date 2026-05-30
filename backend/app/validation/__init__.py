"""Phase 3 validation harness: score labelled ground-truth plots and measure
agreement against the suitability model (docs/phase-0/ground-truth-plan.md).

Pure logic (mapping, confusion matrix, agreement, diagnosis) lives in `harness` and
takes a `predict` callable, so it is unit-testable without the COG/DB data layer. Only
`run` (the CLI) wires the real `app.suitability.engine`.
"""
