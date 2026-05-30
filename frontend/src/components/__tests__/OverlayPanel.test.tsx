import { fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { renderWithProviders } from "../../test-utils";
import {
  OverlayPanel,
  defaultOverlayState,
  type OverlayUiState,
} from "../OverlayPanel";

afterEach(() => vi.unstubAllGlobals());

const RESPONSE = {
  layers: [
    {
      key: "altitude",
      name: "Altitude",
      units: "m",
      dataset: "copernicus-glo30",
      source: "Copernicus GLO-30",
      resolution: "~30 m",
      retrieved: "2026-05-30",
      version: "2026.1",
      colormap: "terrain",
      rescale: [0, 3500],
      band_count: 1,
      bands: null,
      tile_url_template: "http://t/cog/tiles/{z}/{x}/{y}.png?url=s3://b/a.tif",
    },
    {
      key: "precip-monthly",
      name: "Monthly precipitation",
      units: "mm/month",
      dataset: "chelsa-pr-monthly",
      source: "CHELSA V2.1",
      resolution: "~1 km",
      retrieved: "2026-05-30",
      version: "2026.1",
      colormap: "blues",
      rescale: [0, 800],
      band_count: 12,
      bands: Array.from({ length: 12 }, (_, i) => ({
        n: i + 1,
        name: [
          "Jan",
          "Feb",
          "Mar",
          "Apr",
          "May",
          "Jun",
          "Jul",
          "Aug",
          "Sep",
          "Oct",
          "Nov",
          "Dec",
        ][i],
      })),
      tile_url_template: "http://t/cog/tiles/{z}/{x}/{y}.png?url=s3://b/m.tif",
    },
  ],
};

function mockFetch(body: unknown) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok: true, json: async () => body }),
  );
}

function noopHandlers() {
  return {
    onToggle: vi.fn(),
    onOpacity: vi.fn(),
    onBand: vi.fn(),
  };
}

describe("OverlayPanel", () => {
  it("renders one checkbox per layer", async () => {
    mockFetch(RESPONSE);
    const handlers = noopHandlers();
    renderWithProviders(<OverlayPanel state={defaultOverlayState()} {...handlers} />);
    expect(await screen.findByLabelText(/Altitude/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Monthly precipitation/)).toBeInTheDocument();
  });

  it("clicking a checkbox fires onToggle with the layer key", async () => {
    mockFetch(RESPONSE);
    const handlers = noopHandlers();
    renderWithProviders(<OverlayPanel state={defaultOverlayState()} {...handlers} />);
    const checkbox = await screen.findByLabelText(/Altitude/);
    fireEvent.click(checkbox);
    expect(handlers.onToggle).toHaveBeenCalledWith("altitude");
  });

  it("does not render a month picker for single-band layers", async () => {
    mockFetch(RESPONSE);
    const enabled: OverlayUiState = {
      enabled: new Set(["altitude"]),
      opacity: {},
      band: {},
    };
    const handlers = noopHandlers();
    renderWithProviders(<OverlayPanel state={enabled} {...handlers} />);
    await waitFor(() => expect(screen.getByText(/Opacity/)).toBeInTheDocument());
    expect(screen.queryByLabelText(/month selector/i)).not.toBeInTheDocument();
  });

  it("renders a month picker for multi-band layers when enabled", async () => {
    mockFetch(RESPONSE);
    const enabled: OverlayUiState = {
      enabled: new Set(["precip-monthly"]),
      opacity: {},
      band: { "precip-monthly": 6 },
    };
    const handlers = noopHandlers();
    renderWithProviders(<OverlayPanel state={enabled} {...handlers} />);
    await waitFor(() =>
      expect(screen.getByText(/Monthly precipitation/)).toBeInTheDocument(),
    );
    const picker = screen.getByLabelText(/month selector/i);
    expect(picker).toHaveValue("Jun");
  });

  it("renders a colorbar legend for each enabled layer", async () => {
    mockFetch(RESPONSE);
    const enabled: OverlayUiState = {
      enabled: new Set(["altitude"]),
      opacity: {},
      band: {},
    };
    const handlers = noopHandlers();
    renderWithProviders(<OverlayPanel state={enabled} {...handlers} />);
    await waitFor(() =>
      expect(screen.getByTestId("colorbar-legend")).toBeInTheDocument(),
    );
  });
});
