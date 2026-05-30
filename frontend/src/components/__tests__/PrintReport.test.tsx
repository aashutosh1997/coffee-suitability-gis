import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { Geometry } from "../../api/client";
import { renderWithProviders } from "../../test-utils";
import { PrintReport } from "../PrintReport";

const POLYGON: Geometry = {
  type: "Polygon",
  coordinates: [
    [
      [83.89, 28.07],
      [83.891, 28.07],
      [83.891, 28.071],
      [83.89, 28.071],
      [83.89, 28.07],
    ],
  ],
};
const POINT: Geometry = { type: "Point", coordinates: [83.89, 28.07] };
const PNG = "data:image/png;base64,abc";

describe("PrintReport", () => {
  it("renders nothing when no geometry is set", () => {
    renderWithProviders(<PrintReport geometry={null} snapshot={null} />);
    expect(screen.queryByText("Plot")).not.toBeInTheDocument();
    expect(screen.queryByTestId("print-aoi-map")).not.toBeInTheDocument();
  });

  it("renders the snapshot + a formatted area for a polygon", () => {
    renderWithProviders(<PrintReport geometry={POLYGON} snapshot={PNG} />);
    expect(screen.getByTestId("print-aoi-map")).toHaveAttribute("src", PNG);
    expect(screen.getByText(/^Area: /)).toBeInTheDocument();
  });

  it("renders the snapshot + coordinates for a point", () => {
    renderWithProviders(<PrintReport geometry={POINT} snapshot={PNG} />);
    expect(screen.getByTestId("print-aoi-map")).toBeInTheDocument();
    expect(screen.getByText("28.0700° N, 83.8900° E")).toBeInTheDocument();
  });

  it("shows a fallback note when the snapshot is unavailable", () => {
    renderWithProviders(<PrintReport geometry={POLYGON} snapshot={null} />);
    expect(screen.queryByTestId("print-aoi-map")).not.toBeInTheDocument();
    expect(screen.getByText(/map preview unavailable/i)).toBeInTheDocument();
    expect(screen.getByText(/^Area: /)).toBeInTheDocument();
  });
});
