import type maplibregl from "maplibre-gl";
import { useEffect } from "react";

import type { Geometry } from "../api/client";

interface Props {
  map: maplibregl.Map | null;
  geometry: Geometry | null;
}

/** A persistent map layer for the AOI (polygon outline + fill, or a point marker). The
 * Terra Draw visual is ephemeral and the Marker is point-only; this renders the AOI as a
 * real MapLibre layer so it stays visible after the draw is committed and is captured by
 * the print snapshot. */
export const AOI_SOURCE = "aoi";
export const AOI_LAYERS = {
  fill: "aoi-fill",
  outline: "aoi-outline",
  point: "aoi-point",
} as const;

const EMPTY_FC: GeoJSON.FeatureCollection = { type: "FeatureCollection", features: [] };

export function AOILayer({ map, geometry }: Props) {
  useEffect(() => {
    if (!map) return;

    if (!map.getSource(AOI_SOURCE)) {
      map.addSource(AOI_SOURCE, { type: "geojson", data: EMPTY_FC });
      map.addLayer({
        id: AOI_LAYERS.fill,
        type: "fill",
        source: AOI_SOURCE,
        filter: ["==", ["geometry-type"], "Polygon"],
        paint: { "fill-color": "#f0c20a", "fill-opacity": 0.2 },
      });
      map.addLayer({
        id: AOI_LAYERS.outline,
        type: "line",
        source: AOI_SOURCE,
        filter: ["==", ["geometry-type"], "Polygon"],
        paint: { "line-color": "#f0c20a", "line-width": 2 },
      });
      map.addLayer({
        id: AOI_LAYERS.point,
        type: "circle",
        source: AOI_SOURCE,
        filter: ["==", ["geometry-type"], "Point"],
        paint: {
          "circle-radius": 7,
          "circle-color": "#f0c20a",
          "circle-stroke-color": "#ffffff",
          "circle-stroke-width": 2,
        },
      });
    }

    const src = map.getSource(AOI_SOURCE) as maplibregl.GeoJSONSource | undefined;
    if (!src) return;
    if (!geometry) {
      src.setData(EMPTY_FC);
      return;
    }
    src.setData({
      type: "Feature",
      geometry: geometry as GeoJSON.Geometry,
      properties: {},
    });
  }, [map, geometry]);

  useEffect(() => {
    if (!map) return;
    return () => {
      for (const id of Object.values(AOI_LAYERS)) {
        if (map.getLayer(id)) map.removeLayer(id);
      }
      if (map.getSource(AOI_SOURCE)) map.removeSource(AOI_SOURCE);
    };
  }, [map]);

  return null;
}
