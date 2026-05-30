import { render } from "@testing-library/react";
import type maplibregl from "maplibre-gl";
import { describe, expect, it, vi } from "vitest";

import type { OverlayLayer } from "../../api/client";
import {
  RasterOverlayLayer,
  rasterLayerId,
  rasterSourceId,
} from "../RasterOverlayLayer";

function fakeMap() {
  const sources = new Set<string>();
  const layers = new Set<string>();
  const map = {
    addSource: vi.fn((...args: unknown[]) => {
      sources.add(args[0] as string);
    }),
    addLayer: vi.fn((...args: unknown[]) => {
      layers.add((args[0] as { id: string }).id);
    }),
    getSource: vi.fn((id: string) => (sources.has(id) ? {} : undefined)),
    getLayer: vi.fn((id: string) => (layers.has(id) ? {} : undefined)),
    removeLayer: vi.fn((id: string) => {
      layers.delete(id);
    }),
    removeSource: vi.fn((id: string) => {
      sources.delete(id);
    }),
    setPaintProperty: vi.fn(),
    setLayoutProperty: vi.fn(),
  };
  return map as unknown as maplibregl.Map & typeof map;
}

const SINGLE_BAND: OverlayLayer = {
  key: "altitude",
  name: "Altitude",
  units: "m",
  dataset: "copernicus-glo30",
  source: "local fixture",
  resolution: "local fixture",
  retrieved: "2026-05-30",
  version: "fixture",
  colormap: "terrain",
  rescale: [0, 3500],
  band_count: 1,
  bands: null,
  tile_url_template:
    "http://tiles.test/cog/tiles/{z}/{x}/{y}.png?url=s3://b/a.tif&rescale=0,3500&colormap_name=terrain",
};

const MULTI_BAND: OverlayLayer = {
  ...SINGLE_BAND,
  key: "precip-monthly",
  name: "Monthly precipitation",
  band_count: 12,
  bands: Array.from({ length: 12 }, (_, i) => ({ n: i + 1, name: "Jan" })),
  tile_url_template:
    "http://tiles.test/cog/tiles/{z}/{x}/{y}.png?url=s3://b/m.tif&rescale=0,800&colormap_name=blues",
};

describe("RasterOverlayLayer", () => {
  it("is a no-op without a map", () => {
    expect(() =>
      render(
        <RasterOverlayLayer
          map={null}
          layer={SINGLE_BAND}
          opacity={0.7}
          visible={true}
        />,
      ),
    ).not.toThrow();
  });

  it("adds source + layer on first mount and uses the template URL verbatim", () => {
    const map = fakeMap();
    render(
      <RasterOverlayLayer map={map} layer={SINGLE_BAND} opacity={0.7} visible={true} />,
    );
    expect(map.addSource).toHaveBeenCalledWith(
      rasterSourceId("altitude"),
      expect.objectContaining({
        type: "raster",
        tiles: [SINGLE_BAND.tile_url_template],
      }),
    );
    expect(map.addLayer).toHaveBeenCalledWith(
      expect.objectContaining({
        id: rasterLayerId("altitude"),
        type: "raster",
        paint: { "raster-opacity": 0.7 },
      }),
      undefined,
    );
  });

  it("appends &bidx={band} for a multi-band layer", () => {
    const map = fakeMap();
    render(
      <RasterOverlayLayer
        map={map}
        layer={MULTI_BAND}
        opacity={1}
        visible={true}
        band={6}
      />,
    );
    const call = map.addSource.mock.calls[0][1] as { tiles: string[] };
    expect(call.tiles[0]).toBe(`${MULTI_BAND.tile_url_template}&bidx=6`);
  });

  it("updates opacity via setPaintProperty when the opacity prop changes", () => {
    const map = fakeMap();
    const { rerender } = render(
      <RasterOverlayLayer map={map} layer={SINGLE_BAND} opacity={0.4} visible={true} />,
    );
    rerender(
      <RasterOverlayLayer map={map} layer={SINGLE_BAND} opacity={0.9} visible={true} />,
    );
    expect(map.setPaintProperty).toHaveBeenCalledWith(
      rasterLayerId("altitude"),
      "raster-opacity",
      0.9,
    );
  });

  it("toggles visibility via setLayoutProperty", () => {
    const map = fakeMap();
    const { rerender } = render(
      <RasterOverlayLayer map={map} layer={SINGLE_BAND} opacity={1} visible={true} />,
    );
    rerender(
      <RasterOverlayLayer map={map} layer={SINGLE_BAND} opacity={1} visible={false} />,
    );
    expect(map.setLayoutProperty).toHaveBeenCalledWith(
      rasterLayerId("altitude"),
      "visibility",
      "none",
    );
  });

  it("removes layer + source on unmount", () => {
    const map = fakeMap();
    const { unmount } = render(
      <RasterOverlayLayer map={map} layer={SINGLE_BAND} opacity={1} visible={true} />,
    );
    unmount();
    expect(map.removeLayer).toHaveBeenCalledWith(rasterLayerId("altitude"));
    expect(map.removeSource).toHaveBeenCalledWith(rasterSourceId("altitude"));
  });
});
