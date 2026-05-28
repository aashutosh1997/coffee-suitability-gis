import type { StyleSpecification } from "maplibre-gl";

// Pilot region: Nepal mid-hills (Gulmi / Syangja / Kavre). Center ~ Gulmi/Syangja.
export const PILOT_CENTER: [number, number] = [83.8, 28.0];
export const PILOT_ZOOM = 11;

// Esri World Imagery satellite basemap: free raster tiles, no API token — keeps the
// "no vendor lock-in" posture (doc 05). Attribution is required. A fully self-hosted
// Sentinel-2 basemap via TiTiler is the longer-term, on-prem-aligned option (Phase 2/3).
export const BASEMAP_STYLE: StyleSpecification = {
  version: 8,
  sources: {
    "esri-world-imagery": {
      type: "raster",
      tiles: [
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      ],
      tileSize: 256,
      maxzoom: 19,
      attribution:
        "Imagery (c) Esri, Maxar, Earthstar Geographics, and the GIS User Community",
    },
  },
  layers: [
    {
      id: "esri-world-imagery",
      type: "raster",
      source: "esri-world-imagery",
    },
  ],
};
