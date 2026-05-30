"""Load labelled ground-truth plots from the CSV schema in ground-truth-plan.md.

The CSV is the agronomist-owned label set (one row per observed plot). Comment lines
(`#`) are skipped so the file can carry provenance/warnings inline. `observed_status` is
validated against the three allowed labels so a typo fails loudly rather than silently
dropping a row from the agreement metric.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

ObservedStatus = Literal["thriving", "struggling", "failed"]

_OPTIONAL_EMPTY = (
    "elevation_m_observed",
    "cultivar",
    "planting_year",
    "notes",
    "labelled_by",
    "label_date",
)


class GroundTruthPlot(BaseModel):
    plot_id: str
    latitude: float
    longitude: float
    district: str
    observed_status: ObservedStatus
    elevation_m_observed: float | None = None
    cultivar: str | None = None
    planting_year: int | None = None
    notes: str | None = None
    labelled_by: str | None = None
    label_date: str | None = None


def _clean(row: dict[str, str]) -> dict[str, str | None]:
    """Empty CSV cells become None so optional fields validate cleanly."""
    return {
        key: (None if key in _OPTIONAL_EMPTY and value.strip() == "" else value)
        for key, value in row.items()
    }


def load_plots(csv_path: str | Path) -> list[GroundTruthPlot]:
    """Parse the ground-truth CSV into validated plots (skipping `#` comment lines)."""
    with open(csv_path, newline="") as handle:
        data_lines = (line for line in handle if not line.lstrip().startswith("#"))
        reader = csv.DictReader(data_lines)
        return [GroundTruthPlot.model_validate(_clean(row)) for row in reader]
