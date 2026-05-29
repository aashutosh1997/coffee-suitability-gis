import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { AssessResponse } from "../../api/client";
import { renderWithProviders } from "../../test-utils";
import { ResultPanel } from "../ResultPanel";

const RESULT: AssessResponse = {
  aoi: {},
  overall: { class: "S1", score: 0.83, limiting_factor: "shading" },
  factors: [
    {
      name: "altitude",
      raw_value: 1320,
      unit: "m",
      band: "optimal",
      sub_score: 1.0,
      weight: 0.25,
      explanation: "Altitude 1320 m is in the optimal band (1000–1500 m).",
      source: { dataset: "Copernicus GLO-30", resolution: "~30 m" },
    },
    {
      name: "temperature",
      raw_value: 20.1,
      unit: "degC",
      band: "optimal",
      sub_score: 1.0,
      weight: 0.25,
      explanation: "Temperature 20.1 °C is in the optimal band (18–22 °C).",
      source: { dataset: "CHELSA", resolution: "~1 km" },
    },
    {
      name: "shading",
      raw_value: null,
      unit: null,
      band: "moderate_shade_warm_site",
      sub_score: 1.0,
      weight: 0.15,
      explanation: "Shading classified as moderate_shade_warm_site.",
      source: { dataset: "terrain shading model" },
    },
  ],
  model_config_version: "2026.1",
  uncertainty_notes: ["Climate factors come from ~1 km normals."],
};

describe("ResultPanel", () => {
  it("shows a prompt when there is no result", () => {
    renderWithProviders(<ResultPanel result={null} loading={false} />);
    expect(screen.getByText(/run an assessment/i)).toBeInTheDocument();
  });

  it("renders class, limiting factor, and all five factors as assessed", () => {
    renderWithProviders(<ResultPanel result={RESULT} loading={false} />);
    expect(screen.getByText("S1")).toBeInTheDocument();
    expect(screen.getByText(/Highly suitable/i)).toBeInTheDocument();
    expect(screen.getByText(/Biggest limitation/i)).toBeInTheDocument();
    expect(screen.getByText("temperature")).toBeInTheDocument();
    // Categorical shading renders its band label, not "Not assessed".
    expect(screen.getByText("moderate_shade_warm_site")).toBeInTheDocument();
    expect(screen.queryByText("Not assessed")).not.toBeInTheDocument();
  });

  it("shows per-factor provenance in the Source column (FR-15)", () => {
    renderWithProviders(<ResultPanel result={RESULT} loading={false} />);
    expect(screen.getByText(/Copernicus GLO-30 · ~30 m/)).toBeInTheDocument();
    expect(screen.getByText(/CHELSA · ~1 km/)).toBeInTheDocument();
  });
});
