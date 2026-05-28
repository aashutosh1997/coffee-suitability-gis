import { AppShell, Box, Paper, Title } from "@mantine/core";
import maplibregl from "maplibre-gl";
import { useCallback, useEffect, useState } from "react";

import {
  isJob,
  useAssess,
  useAssessJob,
  type AssessResponse,
  type Geometry,
} from "./api/client";
import { AOIInput } from "./components/AOIInput";
import { HealthBadge } from "./components/HealthBadge";
import { PilotMap } from "./components/PilotMap";
import { ResultPanel } from "./components/ResultPanel";

export default function App() {
  const [map, setMap] = useState<maplibregl.Map | null>(null);
  const [geometry, setGeometry] = useState<Geometry | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [result, setResult] = useState<AssessResponse | null>(null);

  const assess = useAssess();
  const job = useAssessJob(jobId);

  useEffect(() => {
    if (job.data?.status === "SUCCESS" && job.data.result) {
      setResult(job.data.result);
      setJobId(null);
    }
  }, [job.data]);

  const onMapReady = useCallback((m: maplibregl.Map) => setMap(m), []);

  const runAssessment = () => {
    if (!geometry) return;
    setResult(null);
    setJobId(null);
    assess.mutate(geometry, {
      onSuccess: (r) => (isJob(r) ? setJobId(r.job_id) : setResult(r)),
    });
  };

  const busy = assess.isPending || !!jobId;

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
        <HealthBadge />
      </AppShell.Header>
      <AppShell.Main>
        <Box
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 380px",
            gap: 16,
            height: "calc(100vh - 88px)",
          }}
        >
          <div style={{ position: "relative" }}>
            <PilotMap onMapReady={onMapReady} />
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
          </div>
          <Paper shadow="sm" p="md" style={{ overflow: "auto" }}>
            <Title order={5} mb="sm">
              Result
            </Title>
            <ResultPanel result={result} loading={busy} />
          </Paper>
        </Box>
      </AppShell.Main>
    </AppShell>
  );
}
