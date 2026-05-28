import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("maplibre-gl", () => ({
  default: {
    Map: vi.fn(),
    Marker: vi.fn(() => ({ setLngLat: () => ({ addTo: vi.fn() }), remove: vi.fn() })),
  },
}));

import { AOIInput } from "../AOIInput";
import { renderWithProviders } from "../../test-utils";

describe("AOIInput", () => {
  it("defaults to point mode with the run button disabled", () => {
    renderWithProviders(
      <AOIInput map={null} onGeometry={vi.fn()} onRun={vi.fn()} busy={false} />,
    );
    expect(screen.getByText(/click the map to drop a pin/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /run assessment/i })).toBeDisabled();
  });

  it("switches to upload mode and reveals the upload control", () => {
    renderWithProviders(
      <AOIInput map={null} onGeometry={vi.fn()} onRun={vi.fn()} busy={false} />,
    );
    fireEvent.click(screen.getByText("Upload"));
    expect(screen.getByRole("button", { name: /upload geojson/i })).toBeInTheDocument();
  });
});
