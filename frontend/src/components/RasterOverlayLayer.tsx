import type maplibregl from "maplibre-gl";
import { useEffect, useRef } from "react";

import type { OverlayLayer } from "../api/client";
import { AOI_LAYERS } from "./AOILayer";

interface Props {
  map: maplibregl.Map | null;
  layer: OverlayLayer;
  opacity: number;
  visible: boolean;
  band?: number | null;
}

const SOURCE_PREFIX = "overlay-src:";
const LAYER_PREFIX = "overlay-lyr:";

export function rasterSourceId(key: string): string {
  return `${SOURCE_PREFIX}${key}`;
}

export function rasterLayerId(key: string): string {
  return `${LAYER_PREFIX}${key}`;
}

/** Append &bidx={band} to the multi-band template; single-band layers ignore band. */
function tileUrl(layer: OverlayLayer, band?: number | null): string {
  if (layer.band_count > 1 && band != null) {
    return `${layer.tile_url_template}&bidx=${band}`;
  }
  return layer.tile_url_template;
}

/** Mounts a TiTiler raster source + layer on the map. Mirrors AOILayer's lifecycle:
 * add on first mount, update paint/visibility on prop change, clean up on unmount.
 * The AOI vector outline always renders on top via the `beforeId` insertion point. */
export function RasterOverlayLayer({ map, layer, opacity, visible, band }: Props) {
  const lastUrlRef = useRef<string | null>(null);

  useEffect(() => {
    if (!map) return;
    const sourceId = rasterSourceId(layer.key);
    const layerId = rasterLayerId(layer.key);
    const url = tileUrl(layer, band);

    if (!map.getSource(sourceId)) {
      map.addSource(sourceId, {
        type: "raster",
        tiles: [url],
        tileSize: 256,
      });
      const aoiFill = map.getLayer(AOI_LAYERS.fill) ? AOI_LAYERS.fill : undefined;
      map.addLayer(
        {
          id: layerId,
          type: "raster",
          source: sourceId,
          paint: { "raster-opacity": opacity },
        },
        aoiFill,
      );
      lastUrlRef.current = url;
      return;
    }

    // URL changed (band switch): re-create the source so MapLibre re-fetches tiles.
    if (lastUrlRef.current !== url) {
      if (map.getLayer(layerId)) map.removeLayer(layerId);
      if (map.getSource(sourceId)) map.removeSource(sourceId);
      map.addSource(sourceId, {
        type: "raster",
        tiles: [url],
        tileSize: 256,
      });
      const aoiFill = map.getLayer(AOI_LAYERS.fill) ? AOI_LAYERS.fill : undefined;
      map.addLayer(
        {
          id: layerId,
          type: "raster",
          source: sourceId,
          paint: { "raster-opacity": opacity },
        },
        aoiFill,
      );
      lastUrlRef.current = url;
    }
  }, [map, layer, band, opacity]);

  useEffect(() => {
    if (!map) return;
    const layerId = rasterLayerId(layer.key);
    if (map.getLayer(layerId)) {
      map.setPaintProperty(layerId, "raster-opacity", opacity);
    }
  }, [map, layer.key, opacity]);

  useEffect(() => {
    if (!map) return;
    const layerId = rasterLayerId(layer.key);
    if (map.getLayer(layerId)) {
      map.setLayoutProperty(layerId, "visibility", visible ? "visible" : "none");
    }
  }, [map, layer.key, visible]);

  useEffect(() => {
    if (!map) return;
    const sourceId = rasterSourceId(layer.key);
    const layerId = rasterLayerId(layer.key);
    return () => {
      if (map.getLayer(layerId)) map.removeLayer(layerId);
      if (map.getSource(sourceId)) map.removeSource(sourceId);
      lastUrlRef.current = null;
    };
  }, [map, layer.key]);

  return null;
}
