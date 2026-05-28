import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { HealthBadge } from "../components/HealthBadge";

function renderWithQuery(ui: ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>);
}

describe("HealthBadge", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("shows healthy when the API returns ok", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => ({ status: "ok" }) }),
    );
    renderWithQuery(<HealthBadge />);
    await waitFor(() =>
      expect(screen.getByRole("status")).toHaveTextContent(/healthy/i),
    );
  });

  it("shows unreachable when the API errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 500, json: async () => ({}) }),
    );
    renderWithQuery(<HealthBadge />);
    await waitFor(() =>
      expect(screen.getByRole("status")).toHaveTextContent(/unreachable/i),
    );
  });
});
