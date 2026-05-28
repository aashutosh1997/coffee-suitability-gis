import { Button, FileButton, SegmentedControl, Stack, Text } from "@mantine/core";
import maplibregl from "maplibre-gl";
import { useEffect, useRef, useState } from "react";

import type { Geometry } from "../api/client";

type Mode = "point" | "polygon" | "upload";

interface Props {
  map: maplibregl.Map | null;
  onGeometry: (geometry: Geometry | null) => void;
  onRun: () => void;
  busy: boolean;
}

interface DrawHandle {
  stop: () => void;
}

export function AOIInput({ map, onGeometry, onRun, busy }: Props) {
  const [mode, setMode] = useState<Mode>("point");
  const [hasGeometry, setHasGeometry] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const markerRef = useRef<maplibregl.Marker | null>(null);
  const drawRef = useRef<DrawHandle | null>(null);

  // Point mode: click the map to drop a pin.
  useEffect(() => {
    if (!map || mode !== "point") return;
    const onClick = (e: maplibregl.MapMouseEvent) => {
      const coords: [number, number] = [e.lngLat.lng, e.lngLat.lat];
      markerRef.current?.remove();
      markerRef.current = new maplibregl.Marker().setLngLat(coords).addTo(map);
      onGeometry({ type: "Point", coordinates: coords });
      setHasGeometry(true);
    };
    map.on("click", onClick);
    return () => {
      map.off("click", onClick);
    };
  }, [map, mode, onGeometry]);

  // Polygon mode: Terra Draw bound to the live MapLibre map (dynamically imported).
  useEffect(() => {
    if (!map || mode !== "polygon") return;
    let cancelled = false;
    (async () => {
      /* eslint-disable @typescript-eslint/no-explicit-any */
      const td: any = await import("terra-draw");
      const adapterMod: any = await import("terra-draw-maplibre-gl-adapter");
      if (cancelled) return;
      const draw = new td.TerraDraw({
        adapter: new adapterMod.TerraDrawMapLibreGLAdapter({ map }),
        modes: [new td.TerraDrawPolygonMode()],
      });
      draw.start();
      draw.setMode("polygon");
      draw.on("finish", () => {
        const polygons = draw
          .getSnapshot()
          .filter((f: any) => f.geometry?.type === "Polygon");
        const last = polygons[polygons.length - 1];
        if (last) {
          onGeometry({ type: "Polygon", coordinates: last.geometry.coordinates });
          setHasGeometry(true);
        }
      });
      drawRef.current = draw;
      /* eslint-enable @typescript-eslint/no-explicit-any */
    })();
    return () => {
      cancelled = true;
      try {
        drawRef.current?.stop();
      } catch {
        /* ignore */
      }
      drawRef.current = null;
    };
  }, [map, mode, onGeometry]);

  const handleUpload = (file: File | null) => {
    setError(null);
    if (!file) return;
    file
      .text()
      .then((text) => {
        const json = JSON.parse(text);
        const geom =
          json.type === "FeatureCollection"
            ? json.features?.[0]?.geometry
            : json.type === "Feature"
              ? json.geometry
              : json;
        if (!geom || (geom.type !== "Point" && geom.type !== "Polygon")) {
          throw new Error("Expected a Point or Polygon geometry.");
        }
        onGeometry({ type: geom.type, coordinates: geom.coordinates });
        setHasGeometry(true);
      })
      .catch((err: Error) => setError(`Could not read GeoJSON: ${err.message}`));
  };

  const changeMode = (value: string) => {
    setMode(value as Mode);
    onGeometry(null);
    setHasGeometry(false);
    setError(null);
    markerRef.current?.remove();
  };

  return (
    <Stack gap="xs">
      <SegmentedControl
        size="xs"
        value={mode}
        onChange={changeMode}
        data={[
          { label: "Point", value: "point" },
          { label: "Draw", value: "polygon" },
          { label: "Upload", value: "upload" },
        ]}
      />
      {mode === "point" && <Text size="sm">Click the map to drop a pin.</Text>}
      {mode === "polygon" && (
        <Text size="sm">Draw a polygon on the map; double-click to finish.</Text>
      )}
      {mode === "upload" && (
        <FileButton
          onChange={handleUpload}
          accept=".geojson,.json,application/geo+json"
        >
          {(props) => (
            <Button variant="light" size="xs" {...props}>
              Upload GeoJSON
            </Button>
          )}
        </FileButton>
      )}
      {error && (
        <Text size="xs" c="red">
          {error}
        </Text>
      )}
      <Button onClick={onRun} disabled={!hasGeometry || busy} loading={busy}>
        Run assessment
      </Button>
    </Stack>
  );
}
