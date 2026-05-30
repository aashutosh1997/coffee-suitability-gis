import { render } from "@testing-library/react";
import type maplibregl from "maplibre-gl";
import { describe, expect, it, vi } from "vitest";

import type { Geometry } from "../../api/client";
import { AOILayer, AOI_LAYERS, AOI_SOURCE } from "../AOILayer";

function fakeMap(initialHasSource = true) {
  let hasSource = initialHasSource;
  const source = { setData: vi.fn() };
  const map = {
    addSource: vi.fn(() => {
      hasSource = true;
    }),
    addLayer: vi.fn(),
    getSource: vi.fn(() => (hasSource ? source : undefined)),
    getLayer: vi.fn(() => true),
    removeLayer: vi.fn(),
    removeSource: vi.fn(),
  };
  return { map: map as unknown as maplibregl.Map, source };
}

const POLYGON: Geometry = {
  type: "Polygon",
  coordinates: [
    [
      [83.89, 28.07],
      [83.91, 28.07],
      [83.91, 28.09],
      [83.89, 28.09],
      [83.89, 28.07],
    ],
  ],
};

describe("AOILayer", () => {
  it("is a no-op when no map is available", () => {
    expect(() => render(<AOILayer map={null} geometry={null} />)).not.toThrow();
  });

  it("adds the AOI source + three layers on first mount and feeds the polygon in", () => {
    const { map, source } = fakeMap(false);
    render(<AOILayer map={map} geometry={POLYGON} />);
    expect(map.addSource).toHaveBeenCalledWith(AOI_SOURCE, expect.any(Object));
    expect(map.addLayer).toHaveBeenCalledTimes(3);
    const layerIds = (map.addLayer as ReturnType<typeof vi.fn>).mock.calls.map(
      (c) => (c[0] as { id: string }).id,
    );
    expect(layerIds).toEqual([AOI_LAYERS.fill, AOI_LAYERS.outline, AOI_LAYERS.point]);
    expect(source.setData).toHaveBeenCalledWith(
      expect.objectContaining({ type: "Feature", geometry: POLYGON }),
    );
  });

  it("clears the source data when geometry becomes null", () => {
    const { map, source } = fakeMap();
    render(<AOILayer map={map} geometry={null} />);
    expect(source.setData).toHaveBeenCalledWith(
      expect.objectContaining({ type: "FeatureCollection", features: [] }),
    );
  });

  it("removes layers + source on unmount", () => {
    const { map } = fakeMap();
    const { unmount } = render(<AOILayer map={map} geometry={null} />);
    unmount();
    expect(map.removeLayer).toHaveBeenCalledTimes(3);
    expect(map.removeSource).toHaveBeenCalledWith(AOI_SOURCE);
  });
});
