import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { renderWithProviders } from "../test-utils";

// maplibre-gl needs WebGL (absent in jsdom) — mock it.
vi.mock("maplibre-gl", () => ({
  default: {
    Map: vi.fn(() => ({
      on: vi.fn(),
      off: vi.fn(),
      remove: vi.fn(),
      addControl: vi.fn(),
    })),
    Marker: vi.fn(() => ({
      setLngLat: () => ({ addTo: vi.fn() }),
      remove: vi.fn(),
    })),
  },
}));

import App from "../App";

describe("App", () => {
  it("renders the header and the map container", () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => ({ status: "ok" }) }),
    );
    renderWithProviders(<App />);
    expect(screen.getByText(/TerraBean/i)).toBeInTheDocument();
    expect(screen.getByTestId("pilot-map")).toBeInTheDocument();
  });
});
