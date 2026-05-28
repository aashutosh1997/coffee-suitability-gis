import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { AssessResponse } from "../../api/client";
import { renderWithProviders } from "../../test-utils";
import { ResultPanel } from "../ResultPanel";

const RESULT: AssessResponse = {
  aoi: {},
  overall: { class: "S2", score: 0.82, limiting_factor: "slope" },
  factors: [
    {
      name: "altitude",
      raw_value: 1320,
      unit: "m",
      band: "optimal",
      sub_score: 1.0,
      weight: 0.25,
      explanation: "Altitude 1320 m is in the optimal band (1000–1500 m).",
      source: { dataset: "Copernicus GLO-30" },
    },
    {
      name: "temperature",
      raw_value: null,
      unit: "degC",
      band: "not_assessed",
      sub_score: 0.0,
      weight: 0.25,
      explanation: "Temperature is not assessed in this phase.",
      source: {},
    },
  ],
  model_config_version: "2026.1",
  uncertainty_notes: ["Terrain-only assessment."],
};

describe("ResultPanel", () => {
  it("shows a prompt when there is no result", () => {
    renderWithProviders(<ResultPanel result={null} loading={false} />);
    expect(screen.getByText(/run an assessment/i)).toBeInTheDocument();
  });

  it("renders class, limiting factor, assessed and not-assessed factors", () => {
    renderWithProviders(<ResultPanel result={RESULT} loading={false} />);
    expect(screen.getByText("S2")).toBeInTheDocument();
    expect(screen.getByText(/Moderately suitable/i)).toBeInTheDocument();
    expect(screen.getByText(/Biggest limitation/i)).toBeInTheDocument();
    expect(screen.getByText("altitude")).toBeInTheDocument();
    // Climate factor rendered as not assessed.
    expect(screen.getByText("Not assessed")).toBeInTheDocument();
  });
});
