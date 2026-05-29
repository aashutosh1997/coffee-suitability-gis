import { describe, expect, it } from "vitest";

import { BASEMAP_STYLE } from "../mapStyle";

describe("BASEMAP_STYLE", () => {
  it("layers satellite imagery under the Esri reference overlays (place labels)", () => {
    const ids = BASEMAP_STYLE.layers.map((l) => l.id);
    expect(ids).toEqual([
      "esri-world-imagery",
      "esri-transportation",
      "esri-boundaries-places",
    ]);
    // Labels paint last so they sit on top of the imagery.
    expect(ids.indexOf("esri-boundaries-places")).toBeGreaterThan(
      ids.indexOf("esri-world-imagery"),
    );
  });
});
