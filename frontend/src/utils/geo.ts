import area from "@turf/area";

import type { Geometry } from "../api/client";

/** Polygon area (geodesic, m²) or point coordinates — for the printed AOI summary. */
export type AOISummary =
  | { kind: "polygon"; area_m2: number; label: string }
  | { kind: "point"; lon: number; lat: number; label: string };

export function aoiSummary(geometry: Geometry): AOISummary {
  if (geometry.type === "Polygon") {
    const polygon: GeoJSON.Polygon = {
      type: "Polygon",
      coordinates: geometry.coordinates as number[][][],
    };
    const m2 = area(polygon);
    return { kind: "polygon", area_m2: m2, label: `Area: ${formatArea(m2)}` };
  }
  const [lon, lat] = geometry.coordinates as number[];
  return { kind: "point", lon, lat, label: formatCoords(lon, lat) };
}

/** Human-readable area: m² under 1 ha, ha under 1 km², km² above — with the raw m². */
export function formatArea(m2: number): string {
  const rounded = Math.round(m2).toLocaleString("en-US");
  if (m2 < 10_000) return `${rounded} m²`;
  const ha = m2 / 10_000;
  if (m2 < 1_000_000) return `${ha.toFixed(2)} ha (${rounded} m²)`;
  const km2 = m2 / 1_000_000;
  return `${km2.toFixed(2)} km² (${ha.toFixed(1)} ha)`;
}

/** "28.0700° N, 83.8900° E" — 4-decimal degrees with hemisphere tags. */
export function formatCoords(lon: number, lat: number): string {
  const latDir = lat >= 0 ? "N" : "S";
  const lonDir = lon >= 0 ? "E" : "W";
  return `${Math.abs(lat).toFixed(4)}° ${latDir}, ${Math.abs(lon).toFixed(4)}° ${lonDir}`;
}

/** [west, south, east, north] bounding box; points degenerate to a zero-width box. */
export function aoiBounds(geometry: Geometry): [number, number, number, number] | null {
  if (geometry.type === "Point") {
    const [lon, lat] = geometry.coordinates as number[];
    return [lon, lat, lon, lat];
  }
  const ring = (geometry.coordinates as number[][][])[0];
  if (!ring?.length) return null;
  let west = ring[0][0],
    east = ring[0][0],
    south = ring[0][1],
    north = ring[0][1];
  for (const [lon, lat] of ring) {
    if (lon < west) west = lon;
    if (lon > east) east = lon;
    if (lat < south) south = lat;
    if (lat > north) north = lat;
  }
  return [west, south, east, north];
}
