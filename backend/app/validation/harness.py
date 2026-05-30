"""Pure validation logic: map predicted class -> observed status, build a confusion
matrix, measure agreement, and diagnose disagreements.

`evaluate` takes a `predict` callable so this module never imports the COG/DB data
layer and is fully unit-testable with a stub. A per-plot prediction error (e.g. a plot
outside the seeded region) is recorded as *excluded* and never aborts the run.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from app.schemas.assess import AssessResponse
from app.validation.plots import GroundTruthPlot

# Predicted suitability class -> expected observed status (ground-truth-plan.md §4.2).
# Recorded in the report because the mapping is itself a reviewable modeling choice.
PREDICTED_TO_STATUS: dict[str, str] = {
    "S1": "thriving",
    "S2": "thriving",
    "S3": "struggling",
    "N": "failed",
}
# Ordinal rank (best -> worst) used to label a disagreement's direction.
STATUS_RANK: dict[str, int] = {"thriving": 2, "struggling": 1, "failed": 0}
STATUSES: list[str] = ["thriving", "struggling", "failed"]

Predictor = Callable[[GroundTruthPlot], AssessResponse]


@dataclass
class PlotResult:
    plot: GroundTruthPlot
    observed_status: str
    predicted_class: str | None = None
    expected_status: str | None = None
    score: float | None = None
    limiting_factor: str | None = None
    agree: bool = False
    error: str | None = None

    @property
    def excluded(self) -> bool:
        return self.error is not None

    @property
    def direction(self) -> str:
        """How the model erred relative to the observed outcome."""
        if self.expected_status is None or self.agree:
            return "ok"
        delta = STATUS_RANK[self.expected_status] - STATUS_RANK[self.observed_status]
        return "optimistic" if delta > 0 else "pessimistic"


@dataclass
class ValidationResult:
    config_version: str
    results: list[PlotResult] = field(default_factory=list)

    @property
    def scored(self) -> list[PlotResult]:
        return [r for r in self.results if not r.excluded]

    @property
    def excluded(self) -> list[PlotResult]:
        return [r for r in self.results if r.excluded]

    @property
    def agreement(self) -> float:
        scored = self.scored
        if not scored:
            return 0.0
        matches = sum(1 for r in scored if r.agree)
        return round(matches / len(scored), 4)

    @property
    def matches(self) -> int:
        return sum(1 for r in self.scored if r.agree)


def evaluate(
    plots: list[GroundTruthPlot], predict: Predictor, config_version: str
) -> ValidationResult:
    """Run `predict` for each plot and score it against the observed label."""
    results: list[PlotResult] = []
    for plot in plots:
        try:
            response = predict(plot)
        except Exception as exc:  # one bad plot must not abort the batch
            results.append(
                PlotResult(
                    plot=plot,
                    observed_status=plot.observed_status,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
            continue
        predicted = response.overall.class_
        expected = PREDICTED_TO_STATUS.get(predicted)
        results.append(
            PlotResult(
                plot=plot,
                observed_status=plot.observed_status,
                predicted_class=predicted,
                expected_status=expected,
                score=response.overall.score,
                limiting_factor=response.overall.limiting_factor,
                agree=(expected == plot.observed_status),
            )
        )
    return ValidationResult(config_version=config_version, results=results)


def confusion_matrix(result: ValidationResult) -> dict[str, dict[str, int]]:
    """Rows = observed status, columns = expected status (mapped prediction)."""
    matrix = {obs: {pred: 0 for pred in STATUSES} for obs in STATUSES}
    for r in result.scored:
        if r.expected_status is not None:
            matrix[r.observed_status][r.expected_status] += 1
    return matrix


def diagnose(result: ValidationResult) -> dict[str, int]:
    """Tally the limiting factor across disagreements (most-implicated first)."""
    tally: dict[str, int] = {}
    for r in result.scored:
        if not r.agree and r.limiting_factor is not None:
            tally[r.limiting_factor] = tally.get(r.limiting_factor, 0) + 1
    return dict(sorted(tally.items(), key=lambda kv: kv[1], reverse=True))
