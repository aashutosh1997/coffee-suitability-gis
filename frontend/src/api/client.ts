import { useMutation, useQuery } from "@tanstack/react-query";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export interface Health {
  status: string;
}

export function useHealth() {
  return useQuery<Health>({
    queryKey: ["health"],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/health`);
      if (!res.ok) throw new Error(`health request failed: ${res.status}`);
      return (await res.json()) as Health;
    },
    refetchInterval: 10000,
  });
}

// --- assessment ----------------------------------------------------------------

export interface Geometry {
  type: "Point" | "Polygon";
  coordinates: number[] | number[][][];
}

export interface FactorResult {
  name: string;
  raw_value: number | null;
  unit: string | null;
  band: string | null;
  sub_score: number;
  weight: number;
  explanation: string;
  source: Record<string, unknown>;
}

export interface Overall {
  class: string;
  score: number;
  limiting_factor: string | null;
}

export interface AssessResponse {
  aoi: Record<string, unknown>;
  overall: Overall;
  factors: FactorResult[];
  model_config_version: string;
  uncertainty_notes: string[];
}

export interface JobAccepted {
  job_id: string;
  status: string;
}

export type AssessResult = AssessResponse | JobAccepted;

export function isJob(result: AssessResult): result is JobAccepted {
  return (result as JobAccepted).job_id !== undefined;
}

export function useAssess() {
  return useMutation<AssessResult, Error, Geometry>({
    mutationFn: async (geometry) => {
      const res = await fetch(`${API_BASE}/assess`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ geometry }),
      });
      if (!res.ok && res.status !== 202) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail.detail ?? `Assessment failed (${res.status})`);
      }
      return (await res.json()) as AssessResult;
    },
  });
}

export interface JobStatus {
  job_id: string;
  status: string;
  result: AssessResponse | null;
}

export function useAssessJob(jobId: string | null) {
  return useQuery<JobStatus>({
    queryKey: ["assess-job", jobId],
    enabled: !!jobId,
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/assess/${jobId}`);
      return (await res.json()) as JobStatus;
    },
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "SUCCESS" || status === "FAILURE" ? false : 1500;
    },
  });
}

// --- recent-conditions context (non-scoring) -----------------------------------

export interface RecentClimate {
  source: string | null;
  annual_mean_temp_c: number | null;
  annual_precip_mm: number | null;
  period: string | null;
  note: string | null;
  available: boolean;
}

// --- raster overlays (FR-13) ----------------------------------------------------

export interface OverlayBand {
  n: number;
  name: string;
}

export interface OverlayLayer {
  key: string;
  name: string;
  units: string;
  dataset: string;
  source: string | null;
  resolution: string | null;
  retrieved: string | null;
  version: string | null;
  colormap: string;
  rescale: [number, number];
  band_count: number;
  bands: OverlayBand[] | null;
  tile_url_template: string;
}

export interface OverlaysResponse {
  layers: OverlayLayer[];
}

export function useOverlays() {
  return useQuery<OverlaysResponse>({
    queryKey: ["overlays"],
    staleTime: Infinity, // provenance flips only on re-seed; manual refresh if needed
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/overlays`);
      if (!res.ok) throw new Error(`overlays request failed: ${res.status}`);
      return (await res.json()) as OverlaysResponse;
    },
  });
}

export function useRecentClimate(lon: number | null, lat: number | null) {
  return useQuery<RecentClimate>({
    queryKey: ["recent-climate", lon, lat],
    enabled: lon != null && lat != null,
    staleTime: 1000 * 60 * 60, // climatology is stable; cache for an hour
    queryFn: async () => {
      const res = await fetch(
        `${API_BASE}/context/recent-climate?lon=${lon}&lat=${lat}`,
      );
      return (await res.json()) as RecentClimate;
    },
  });
}
