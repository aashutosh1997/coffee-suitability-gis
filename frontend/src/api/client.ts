import { useQuery } from "@tanstack/react-query";

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
