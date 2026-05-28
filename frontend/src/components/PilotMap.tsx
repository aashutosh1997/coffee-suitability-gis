import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef } from "react";

import { BASEMAP_STYLE, PILOT_CENTER, PILOT_ZOOM } from "../config/mapStyle";

export function PilotMap() {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: BASEMAP_STYLE,
      center: PILOT_CENTER,
      zoom: PILOT_ZOOM,
    });
    new maplibregl.Marker().setLngLat(PILOT_CENTER).addTo(map);
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  return (
    <div
      ref={containerRef}
      data-testid="pilot-map"
      style={{ width: "100%", height: "100%" }}
    />
  );
}
