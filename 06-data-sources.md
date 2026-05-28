# 06 — Data Sources

All sources below are **open / freely usable**. Exact licenses and the final selection
must be confirmed during the **Phase 0 data spike** — verify the current terms of each
before relying on it, and record the decision in an ADR.

## Elevation (DEM) — drives altitude, slope, aspect, terrain shading

| Source | Resolution | Notes |
|--------|-----------|-------|
| **Copernicus DEM (GLO-30)** | ~30 m | Modern, global, open; strong default |
| **SRTM** | ~30 m | Long-standing, widely used, well-documented |
| **NASADEM** | ~30 m | Reprocessed SRTM, improved voids |
| **ASTER GDEM** | ~30 m | Wider latitude coverage; noisier |

> Resolution caveat: ~30 m smooths small terraced plots. If the co-op needs finer
> terrain detail, evaluate national/regional LiDAR or higher-res DEMs for the operating
> area in Phase 0.

## Climate — drives temperature & rainfall factors

### Long-term normals (baseline suitability)
| Source | Resolution | Notes |
|--------|-----------|-------|
| **WorldClim v2.1** | ~1 km | Bioclimatic variables (temp, precip), monthly normals; common default |
| **CHELSA** | ~1 km | High-res climatologies, often better in complex terrain |

### Reanalysis & observations (recent conditions / trends)
| Source | Access | Notes |
|--------|--------|-------|
| **ERA5 (Copernicus CDS)** | API (registration) | Hourly reanalysis back decades |
| **NASA POWER** | Free API, no key | Agro-climatology point queries; great for on-demand temp/rainfall |
| **Open-Meteo** | Free API (non-commercial tiers) | Historical archive + forecast point queries; easy caching |

The point weather APIs (NASA POWER, Open-Meteo) are the on-demand source for "recent
conditions"; the gridded normals (WorldClim/CHELSA) are pre-ingested for the baseline
suitability score.

## Land cover & canopy — drives canopy-shading estimate

| Source | Resolution | Notes |
|--------|-----------|-------|
| **ESA WorldCover** | ~10 m | Global land-cover classes |
| **Global canopy-height datasets** | ~10 m–1 km | Estimate existing tree cover for shade context |

## Soil (Phase 3+) — advisory soil factor

| Source | Resolution | Notes |
|--------|-----------|-------|
| **SoilGrids (ISRIC)** | ~250 m | pH, texture, organic carbon, depth — global, modeled (validate locally) |

## Solar position / insolation (computed, not downloaded)
Solar geometry for the shading/insolation model is **computed** from the DEM + sun
position using **pvlib** and **GRASS `r.sun`** — no external dataset required, only the
DEM and the location/date.

## Ingestion approach
For each supported region:
1. Fetch source rasters once.
2. Reproject to a common CRS, clip to the region of interest.
3. Convert to **Cloud-Optimized GeoTIFF (COG)** and store in object storage.
4. Register extents/metadata (including dataset version + retrieval date) in PostGIS so
   every assessment can report **provenance** (FR-15).
5. Schedule refreshes where sources update; weather caches expire on a short TTL.

## Provenance & reproducibility
Every assessment records, per factor, the dataset name, resolution, and retrieval date,
plus the model-config version. This satisfies the explainability goal (Vision) and
reproducibility requirement (NFR-16), and lets agronomists judge how much to trust a
result given data resolution.
