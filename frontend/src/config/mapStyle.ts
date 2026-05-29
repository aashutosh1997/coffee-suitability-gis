import type { StyleSpecification } from "maplibre-gl";

// Pilot region: Nepal mid-hills (Gulmi / Syangja / Kavre). Center ~ Gulmi/Syangja.
export const PILOT_CENTER: [number, number] = [83.8, 28.0];
export const PILOT_ZOOM = 11;

// Esri World Imagery satellite basemap + matching reference overlays (place names, admin
// boundaries, roads): all free raster tiles, no API token — keeps the "no vendor lock-in"
// posture (doc 05). The reference layers paint on top of the imagery so the otherwise
// label-less satellite view is navigable. Attribution is required. A fully self-hosted
// Sentinel-2 basemap via TiTiler is the longer-term, on-prem-aligned option (Phase 3).
const ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services";

export const BASEMAP_STYLE: StyleSpecification = {
  version: 8,
  sources: {
    "esri-world-imagery": {
      type: "raster",
      tiles: [`${ESRI}/World_Imagery/MapServer/tile/{z}/{y}/{x}`],
      tileSize: 256,
      maxzoom: 19,
      attribution:
        "Imagery (c) Esri, Maxar, Earthstar Geographics, and the GIS User Community",
    },
    "esri-transportation": {
      type: "raster",
      tiles: [`${ESRI}/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}`],
      tileSize: 256,
      maxzoom: 19,
      attribution: "Transportation (c) Esri",
    },
    "esri-boundaries-places": {
      type: "raster",
      tiles: [
        `${ESRI}/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}`,
      ],
      tileSize: 256,
      maxzoom: 19,
      attribution: "Labels (c) Esri",
    },
  },
  // Order = paint order: imagery first, then roads, then place/boundary labels on top.
  layers: [
    { id: "esri-world-imagery", type: "raster", source: "esri-world-imagery" },
    { id: "esri-transportation", type: "raster", source: "esri-transportation" },
    {
      id: "esri-boundaries-places",
      type: "raster",
      source: "esri-boundaries-places",
    },
  ],
};
