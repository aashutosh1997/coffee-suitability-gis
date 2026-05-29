import { screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { renderWithProviders } from "../../test-utils";
import { RecentClimate } from "../RecentClimate";

afterEach(() => vi.unstubAllGlobals());

function mockFetch(body: unknown) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok: true, json: async () => body }),
  );
}

describe("RecentClimate", () => {
  it("renders nothing without a point", () => {
    renderWithProviders(<RecentClimate lon={null} lat={null} />);
    expect(screen.queryByText(/recent conditions/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/unavailable/i)).not.toBeInTheDocument();
  });

  it("shows recent values when the service is available", async () => {
    mockFetch({
      source: "NASA POWER",
      annual_mean_temp_c: 18.5,
      annual_precip_mm: 1850,
      period: "multi-year climatology",
      note: null,
      available: true,
    });
    renderWithProviders(<RecentClimate lon={83.89} lat={28.07} />);
    await waitFor(() =>
      expect(screen.getByText(/Recent conditions \(NASA POWER\)/)).toBeInTheDocument(),
    );
    expect(screen.getByText(/not used in scoring/i)).toBeInTheDocument();
  });

  it("degrades gracefully when unavailable", async () => {
    mockFetch({
      source: null,
      annual_mean_temp_c: null,
      annual_precip_mm: null,
      period: null,
      note: "Live weather services are unreachable.",
      available: false,
    });
    renderWithProviders(<RecentClimate lon={83.89} lat={28.07} />);
    await waitFor(() => expect(screen.getByText(/unavailable/i)).toBeInTheDocument());
  });
});
