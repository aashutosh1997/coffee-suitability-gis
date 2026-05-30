"""Render a ValidationResult to a machine-readable dict (JSON) and a human report
(markdown). The report leads with a SYNTHETIC-data warning so an agreement % from the
example set is never mistaken for a real accuracy claim.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.validation.harness import (
    PREDICTED_TO_STATUS,
    STATUSES,
    ValidationResult,
    confusion_matrix,
    diagnose,
)

SYNTHETIC_WARNING = (
    "> **SYNTHETIC DATA — NOT AN ACCURACY CLAIM.** This exercises the validation "
    "harness against a synthetic, stratified plot set with no agronomic meaning. The "
    "agreement % proves the mechanism works; the >=80% launch target (doc 01) is only "
    "meaningful against real co-op-labelled plots (ground-truth-plan.md §5)."
)


def build_report(result: ValidationResult) -> dict[str, object]:
    """Machine-readable summary for the JSON sidecar."""
    return {
        "config_version": result.config_version,
        "mapping": PREDICTED_TO_STATUS,
        "n_plots": len(result.results),
        "n_scored": len(result.scored),
        "n_excluded": len(result.excluded),
        "matches": result.matches,
        "agreement": result.agreement,
        "confusion_matrix": confusion_matrix(result),
        "limiting_factor_in_disagreements": diagnose(result),
        "plots": [
            {
                "plot_id": r.plot.plot_id,
                "district": r.plot.district,
                "observed_status": r.observed_status,
                "predicted_class": r.predicted_class,
                "expected_status": r.expected_status,
                "score": r.score,
                "limiting_factor": r.limiting_factor,
                "agree": r.agree,
                "direction": r.direction,
                "error": r.error,
            }
            for r in result.results
        ],
    }


def _matrix_table(result: ValidationResult) -> list[str]:
    matrix = confusion_matrix(result)
    header = "| observed \\ predicted | " + " | ".join(STATUSES) + " |"
    sep = "|" + "---|" * (len(STATUSES) + 1)
    rows = [header, sep]
    for obs in STATUSES:
        cells = " | ".join(str(matrix[obs][pred]) for pred in STATUSES)
        rows.append(f"| **{obs}** | {cells} |")
    return rows


def _plot_table(result: ValidationResult) -> list[str]:
    rows = [
        "| plot | district | observed | predicted | score | expected | agree | "
        "limiting |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in result.results:
        if r.excluded:
            rows.append(
                f"| {r.plot.plot_id} | {r.plot.district} | {r.observed_status} | "
                f"— | — | — | excluded | {r.error} |"
            )
            continue
        mark = "✓" if r.agree else f"✗ ({r.direction})"
        score = f"{r.score:.2f}" if r.score is not None else "—"
        rows.append(
            f"| {r.plot.plot_id} | {r.plot.district} | {r.observed_status} | "
            f"{r.predicted_class} | {score} | {r.expected_status} | {mark} | "
            f"{r.limiting_factor or '—'} |"
        )
    return rows


def render_markdown(result: ValidationResult) -> str:
    pct = result.agreement * 100
    gate = "MET" if result.agreement >= 0.80 else "NOT met"
    mapping = ", ".join(f"{k}→{v}" for k, v in PREDICTED_TO_STATUS.items())
    diag = diagnose(result)
    diag_line = ", ".join(f"{k} ({n})" for k, n in diag.items()) if diag else "none"

    lines = [
        f"# Validation report — config {result.config_version}",
        "",
        SYNTHETIC_WARNING,
        "",
        "## Summary",
        f"- Plots: {len(result.results)} "
        f"(scored {len(result.scored)}, excluded {len(result.excluded)})",
        f"- Agreement: **{result.matches}/{len(result.scored)} = {pct:.1f}%** "
        f"(≥80% target {gate} — synthetic)",
        f"- Class→status mapping: {mapping}",
        f"- Limiting factor in disagreements: {diag_line}",
        "",
        "## Confusion matrix (rows = observed, columns = mapped prediction)",
        *_matrix_table(result),
        "",
        "## Per-plot results",
        *_plot_table(result),
        "",
    ]
    return "\n".join(lines)


def write_report(result: ValidationResult, out_dir: str | Path) -> tuple[Path, Path]:
    """Write `validation-<version>.md` + `.json`; return both paths."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stem = f"validation-{result.config_version}"
    md_path = out / f"{stem}.md"
    json_path = out / f"{stem}.json"
    md_path.write_text(render_markdown(result))
    json_path.write_text(json.dumps(build_report(result), indent=2))
    return md_path, json_path
