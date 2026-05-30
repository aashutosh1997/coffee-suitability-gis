import { describe, expect, it } from "vitest";

import type { Geometry } from "../../api/client";
import { aoiBounds, aoiSummary, formatArea, formatCoords } from "../geo";

describe("formatArea", () => {
  it("renders sub-hectare areas in m²", () => {
    expect(formatArea(2_300)).toBe("2,300 m²");
    expect(formatArea(9_999)).toBe("9,999 m²");
  });
  it("renders hectare-scale areas with the raw m² alongside", () => {
    expect(formatArea(23_418)).toBe("2.34 ha (23,418 m²)");
  });
  it("renders ≥ 1 km² areas in km² with ha", () => {
    expect(formatArea(1_250_000)).toBe("1.25 km² (125.0 ha)");
  });
});

describe("formatCoords", () => {
  it("uses 4-decimal degrees with N/E for positive coords", () => {
    expect(formatCoords(83.89, 28.07)).toBe("28.0700° N, 83.8900° E");
  });
  it("flips hemisphere tags for negative coords", () => {
    expect(formatCoords(-45.3, -12.5)).toBe("12.5000° S, 45.3000° W");
  });
});

describe("aoiSummary", () => {
  it("computes geodesic area for a polygon (within 2% of the lat-corrected reference)", () => {
    // 0.001° × 0.001° square at Gulmi (~28°N): reference ≈ 111.32 m × cos(28°) × 111.32 m
    // ≈ 10 940 m². turf's geodesic value should land within a few % of this.
    const polygon: Geometry = {
      type: "Polygon",
      coordinates: [
        [
          [83.89, 28.07],
          [83.891, 28.07],
          [83.891, 28.071],
          [83.89, 28.071],
          [83.89, 28.07],
        ],
      ],
    };
    const summary = aoiSummary(polygon);
    if (summary.kind !== "polygon") throw new Error("expected polygon summary");
    const ref = 111_320 * Math.cos((28 * Math.PI) / 180) * 0.001 * 111_320 * 0.001;
    expect(summary.area_m2).toBeGreaterThan(ref * 0.98);
    expect(summary.area_m2).toBeLessThan(ref * 1.02);
    expect(summary.label).toMatch(/^Area: /);
  });

  it("returns coordinates for a point AOI", () => {
    const point: Geometry = { type: "Point", coordinates: [83.89, 28.07] };
    const summary = aoiSummary(point);
    expect(summary).toEqual({
      kind: "point",
      lon: 83.89,
      lat: 28.07,
      label: "28.0700° N, 83.8900° E",
    });
  });
});

describe("aoiBounds", () => {
  it("returns the min/max corners of a polygon ring", () => {
    const polygon: Geometry = {
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
    expect(aoiBounds(polygon)).toEqual([83.89, 28.07, 83.91, 28.09]);
  });
  it("degenerates a point to a zero-width box", () => {
    expect(aoiBounds({ type: "Point", coordinates: [83.89, 28.07] })).toEqual([
      83.89, 28.07, 83.89, 28.07,
    ]);
  });
});
