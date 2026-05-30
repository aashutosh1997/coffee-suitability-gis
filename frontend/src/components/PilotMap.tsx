import maplibregl from "maplibre-gl";
import { useEffect, useRef } from "react";

import { BASEMAP_STYLE, PILOT_CENTER, PILOT_ZOOM } from "../config/mapStyle";

interface Props {
  onMapReady?: (map: maplibregl.Map) => void;
}

export function PilotMap({ onMapReady }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: BASEMAP_STYLE,
      center: PILOT_CENTER,
      zoom: PILOT_ZOOM,
      // Required so map.getCanvas().toDataURL() returns the rendered pixels for the
      // print-report snapshot; WebGL canvases otherwise read back blank.
      preserveDrawingBuffer: true,
    });
    mapRef.current = map;
    map.on("load", () => onMapReady?.(map));
    return () => {
      map.remove();
      mapRef.current = null;
    };
    // onMapReady is stable (useCallback in the parent); init must run once.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div
      ref={containerRef}
      data-testid="pilot-map"
      style={{ width: "100%", height: "100%" }}
    />
  );
}
