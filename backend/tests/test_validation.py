"""Phase 3 validation harness tests.

Pure-logic tests use a stub predictor (no COG/DB). A small integration test runs the
real engine against the committed fixtures (local-file COG mode via conftest).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.assess import AssessResponse, Overall
from app.validation import harness, report
from app.validation.plots import GroundTruthPlot, load_plots

SYNTHETIC_CSV = (
    Path(__file__).resolve().parents[2]
    / "config"
    / "ground-truth"
    / "synthetic_plots.csv"
)


def _response(cls: str, limiting: str = "temperature") -> AssessResponse:
    return AssessResponse(
        aoi={"geometry": {}},
        overall=Overall(class_=cls, score=0.5, limiting_factor=limiting),
        factors=[],
        model_config_version="test",
    )


def _plot(pid: str, status: str) -> GroundTruthPlot:
    return GroundTruthPlot(
        plot_id=pid,
        latitude=28.07,
        longitude=83.89,
        district="Gulmi",
        observed_status=status,  # type: ignore[arg-type]
    )


# --- loader ---------------------------------------------------------------------


def test_load_synthetic_plots_skips_comments_and_validates():
    plots = load_plots(SYNTHETIC_CSV)
    assert len(plots) == 40
    assert all(p.observed_status in {"thriving", "struggling", "failed"} for p in plots)
    assert {p.plot_id for p in plots} >= {"GUL-001", "KAV-001", "NAW-001"}


def test_load_plots_rejects_bad_status(tmp_path):
    csv_path = tmp_path / "bad.csv"
    csv_path.write_text(
        "plot_id,latitude,longitude,district,observed_status\n"
        "# a comment line\n"
        "X-1,28.0,83.9,Gulmi,flourishing\n"
    )
    with pytest.raises(ValidationError):
        load_plots(csv_path)


def test_load_plots_empty_optionals_become_none(tmp_path):
    csv_path = tmp_path / "ok.csv"
    csv_path.write_text(
        "plot_id,latitude,longitude,district,observed_status,planting_year,notes\n"
        "X-1,28.0,83.9,Gulmi,thriving,,\n"
    )
    (plot,) = load_plots(csv_path)
    assert plot.planting_year is None
    assert plot.notes is None


# --- pure harness ---------------------------------------------------------------


def _stub_result() -> harness.ValidationResult:
    predicted = {"P1": "S1", "P2": "S3", "P3": "N", "P4": "S2"}

    def predict(plot: GroundTruthPlot) -> AssessResponse:
        if plot.plot_id == "BOOM":
            raise RuntimeError("outside seeded region")
        return _response(predicted[plot.plot_id])

    plots = [
        _plot("P1", "thriving"),
        _plot("P2", "struggling"),
        _plot("P3", "failed"),
        _plot("P4", "failed"),  # predicted S2 -> thriving: optimistic disagreement
        _plot("BOOM", "thriving"),  # raises -> excluded
    ]
    return harness.evaluate(plots, predict, "2026.test")


def test_evaluate_agreement_and_exclusion():
    result = _stub_result()
    assert len(result.scored) == 4
    assert len(result.excluded) == 1
    assert result.matches == 3
    assert result.agreement == 0.75


def test_confusion_matrix_counts():
    matrix = harness.confusion_matrix(_stub_result())
    assert matrix["thriving"]["thriving"] == 1
    assert matrix["struggling"]["struggling"] == 1
    assert matrix["failed"]["failed"] == 1
    assert matrix["failed"]["thriving"] == 1  # the optimistic miss


def test_diagnose_and_direction():
    result = _stub_result()
    assert harness.diagnose(result) == {"temperature": 1}
    miss = next(r for r in result.scored if r.plot.plot_id == "P4")
    assert miss.direction == "optimistic"


def test_report_dict_reconciles():
    data = report.build_report(_stub_result())
    assert data["n_scored"] + data["n_excluded"] == data["n_plots"] == 5
    assert data["agreement"] == 0.75
    assert "SYNTHETIC" in report.render_markdown(_stub_result())


# --- integration: real engine over committed fixtures ---------------------------

pytest.importorskip("rasterio")
pytest.importorskip("geopandas")


def test_engine_validation_runs_over_fixtures(tmp_path):
    from app.suitability.config_loader import load_config
    from app.suitability.engine import assess_point
    from tests.conftest import CONFIG_PATH

    config = load_config(CONFIG_PATH)

    def predict(plot: GroundTruthPlot) -> AssessResponse:
        geometry = {"type": "Point", "coordinates": [plot.longitude, plot.latitude]}
        return assess_point(geometry, config)

    # Both inside the committed Gulmi fixture extent.
    plots = [_plot("FIX-1", "thriving"), _plot("FIX-2", "struggling")]
    result = harness.evaluate(plots, predict, config.model_config_version)

    assert len(result.scored) == 2
    assert all(r.predicted_class in {"S1", "S2", "S3", "N"} for r in result.scored)

    md_path, json_path = report.write_report(result, tmp_path)
    assert md_path.exists() and json_path.exists()
    assert "Validation report" in md_path.read_text()
