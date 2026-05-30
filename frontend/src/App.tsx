import { AppShell, Box, Button, Group, Paper, Stack, Title } from "@mantine/core";
import maplibregl from "maplibre-gl";
import { useCallback, useEffect, useState } from "react";

import {
  isJob,
  useAssess,
  useAssessJob,
  useOverlays,
  type AssessResponse,
  type Geometry,
} from "./api/client";
import { AOIInput } from "./components/AOIInput";
import { AOILayer } from "./components/AOILayer";
import { HealthBadge } from "./components/HealthBadge";
import {
  OverlayPanel,
  defaultOverlayState,
  getBand,
  getOpacity,
  type OverlayUiState,
} from "./components/OverlayPanel";
import { PilotMap } from "./components/PilotMap";
import { PrintReport } from "./components/PrintReport";
import { RasterOverlayLayer } from "./components/RasterOverlayLayer";
import { RecentClimate } from "./components/RecentClimate";
import { ResultPanel } from "./components/ResultPanel";
import { aoiBounds } from "./utils/geo";

export default function App() {
  const [map, setMap] = useState<maplibregl.Map | null>(null);
  const [geometry, setGeometry] = useState<Geometry | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [result, setResult] = useState<AssessResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [printSnapshot, setPrintSnapshot] = useState<string | null>(null);
  const [overlayState, setOverlayState] = useState<OverlayUiState>(defaultOverlayState);

  const assess = useAssess();
  const job = useAssessJob(jobId);
  const overlays = useOverlays();

  useEffect(() => {
    if (!job.data) return;
    if (job.data.status === "SUCCESS" && job.data.result) {
      setResult(job.data.result);
      setJobId(null);
    } else if (job.data.status === "FAILURE") {
      setError("Assessment failed for this area. Try a different or larger area.");
      setJobId(null);
    }
  }, [job.data]);

  const onMapReady = useCallback((m: maplibregl.Map) => setMap(m), []);

  const runAssessment = () => {
    if (!geometry) return;
    setError(null);
    setResult(null);
    setJobId(null);
    assess.mutate(geometry, {
      onSuccess: (r) => (isJob(r) ? setJobId(r.job_id) : setResult(r)),
      onError: (e) => setError(e.message),
    });
  };

  const busy = assess.isPending || !!jobId;
  const point = geometry?.type === "Point" ? (geometry.coordinates as number[]) : null;

  const toggleOverlay = useCallback((key: string) => {
    setOverlayState((prev) => {
      const enabled = new Set(prev.enabled);
      if (enabled.has(key)) enabled.delete(key);
      else enabled.add(key);
      return { ...prev, enabled };
    });
  }, []);
  const setOverlayOpacity = useCallback((key: string, value: number) => {
    setOverlayState((prev) => ({
      ...prev,
      opacity: { ...prev.opacity, [key]: value },
    }));
  }, []);
  const setOverlayBand = useCallback((key: string, band: number) => {
    setOverlayState((prev) => ({
      ...prev,
      band: { ...prev.band, [key]: band },
    }));
  }, []);

  const printReport = async () => {
    if (!result || !geometry || !map) {
      window.print();
      return;
    }
    const camera = {
      center: map.getCenter(),
      zoom: map.getZoom(),
      bearing: map.getBearing(),
      pitch: map.getPitch(),
    };
    const bounds = aoiBounds(geometry);
    if (geometry.type === "Polygon" && bounds) {
      const [w, s, e, n] = bounds;
      map.fitBounds(
        [
          [w, s],
          [e, n],
        ],
        { padding: 50, duration: 0 },
      );
    } else if (geometry.type === "Point") {
      const [lon, lat] = geometry.coordinates as number[];
      map.jumpTo({ center: [lon, lat], zoom: 14 });
    }
    await new Promise<void>((resolve) => map.once("idle", () => resolve()));
    let snapshot: string | null = null;
    try {
      snapshot = map.getCanvas().toDataURL("image/png");
    } catch (err) {
      // tainted-canvas (cross-origin tiles without ACAO) — print without the image.
      console.warn("Map snapshot unavailable for print", err);
    }
    setPrintSnapshot(snapshot);
    // Let React paint the snapshot before opening the print dialog.
    await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()));
    window.print();
    map.jumpTo(camera);
  };

  return (
    <AppShell header={{ height: 56 }} padding="md">
      <AppShell.Header
        px="md"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <Title order={4}>TerraBean — Arabica Suitability (Nepal mid-hills pilot)</Title>
        <Group gap="sm" className="no-print">
          <Button
            size="xs"
            variant="default"
            disabled={!result}
            onClick={() => void printReport()}
          >
            Print / Save as PDF
          </Button>
          <HealthBadge />
        </Group>
      </AppShell.Header>
      <AppShell.Main>
        <Box
          className="print-full"
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 380px",
            gap: 16,
            height: "calc(100vh - 88px)",
          }}
        >
          <div className="no-print" style={{ position: "relative" }}>
            <PilotMap onMapReady={onMapReady} />
            <AOILayer map={map} geometry={geometry} />
            {(overlays.data?.layers ?? [])
              .filter((layer) => overlayState.enabled.has(layer.key))
              .map((layer) => (
                <RasterOverlayLayer
                  key={layer.key}
                  map={map}
                  layer={layer}
                  opacity={getOpacity(overlayState, layer.key)}
                  visible={true}
                  band={layer.band_count > 1 ? getBand(overlayState, layer.key) : null}
                />
              ))}
            <Paper
              shadow="sm"
              p="sm"
              style={{ position: "absolute", top: 12, left: 12, width: 260, zIndex: 1 }}
            >
              <AOIInput
                map={map}
                onGeometry={setGeometry}
                onRun={runAssessment}
                busy={busy}
              />
            </Paper>
            <div style={{ position: "absolute", top: 12, right: 12, zIndex: 1 }}>
              <OverlayPanel
                state={overlayState}
                onToggle={toggleOverlay}
                onOpacity={setOverlayOpacity}
                onBand={setOverlayBand}
              />
            </div>
          </div>
          <Paper className="print-area" shadow="sm" p="md" style={{ overflow: "auto" }}>
            <Stack gap="md">
              <PrintReport geometry={geometry} snapshot={printSnapshot} />
              <div>
                <Title order={5} mb="sm">
                  Result
                </Title>
                <ResultPanel result={result} loading={busy} error={error} />
              </div>
              <RecentClimate lon={point?.[0] ?? null} lat={point?.[1] ?? null} />
            </Stack>
          </Paper>
        </Box>
      </AppShell.Main>
    </AppShell>
  );
}
