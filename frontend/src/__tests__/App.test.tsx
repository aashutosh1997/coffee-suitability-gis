import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

// maplibre-gl needs WebGL, which jsdom lacks — mock it for the render test.
vi.mock("maplibre-gl", () => ({
  default: {
    Map: vi.fn(() => ({ remove: vi.fn(), addControl: vi.fn() })),
    Marker: vi.fn(() => ({ setLngLat: () => ({ addTo: vi.fn() }) })),
  },
}));

import App from "../App";

describe("App", () => {
  it("renders the header and the map container", () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => ({ status: "ok" }) }),
    );
    const qc = new QueryClient();
    render(
      <QueryClientProvider client={qc}>
        <App />
      </QueryClientProvider>,
    );
    expect(screen.getByText(/TerraBean/i)).toBeInTheDocument();
    expect(screen.getByTestId("pilot-map")).toBeInTheDocument();
  });
});
