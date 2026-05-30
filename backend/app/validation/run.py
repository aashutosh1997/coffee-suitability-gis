"""CLI: validate the suitability model against a labelled ground-truth set.

Loads a pinned config version, runs the real engine at each plot's coordinates, and
writes a confusion-matrix report (markdown + JSON). Run inside the seeded stack so the
engine has national DEM + climate to read (see `make validate`).

Usage:
    python -m app.validation.run \
        --plots /config/ground-truth/synthetic_plots.csv \
        --config /config/suitability/arabica-2026.1.yaml \
        --out /config/../docs/phase-3
"""

from __future__ import annotations

import argparse
from pathlib import Path

from app.schemas.assess import AssessResponse
from app.suitability.config_loader import load_config
from app.suitability.engine import assess_point
from app.validation import harness, report
from app.validation.plots import GroundTruthPlot, load_plots


def _make_predictor(config_path: str) -> harness.Predictor:
    config = load_config(config_path)

    def predict(plot: GroundTruthPlot) -> AssessResponse:
        geometry = {"type": "Point", "coordinates": [plot.longitude, plot.latitude]}
        return assess_point(geometry, config)

    return predict


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the model vs ground truth")
    parser.add_argument("--plots", required=True, help="ground-truth CSV path")
    parser.add_argument("--config", required=True, help="suitability config YAML path")
    parser.add_argument("--out", default="docs/phase-3", help="report output directory")
    args = parser.parse_args()

    config = load_config(args.config)
    plots = load_plots(args.plots)
    predict = _make_predictor(args.config)

    result = harness.evaluate(plots, predict, config.model_config_version)
    md_path, json_path = report.write_report(result, args.out)

    pct = result.agreement * 100
    print(
        f"validation: {result.matches}/{len(result.scored)} agree = {pct:.1f}% "
        f"({len(result.excluded)} excluded) at config {result.config_version}"
    )
    print(f"validation: wrote {Path(md_path)} and {Path(json_path)}")


if __name__ == "__main__":
    main()
