import { useHealth } from "../api/client";

export function HealthBadge() {
  const { data, isLoading } = useHealth();
  const ok = data?.status === "ok";

  const color = isLoading ? "#9e9e9e" : ok ? "#2e7d32" : "#c62828";
  const label = isLoading ? "API: checking…" : ok ? "API: healthy" : "API: unreachable";

  return (
    <span
      role="status"
      style={{
        background: color,
        color: "white",
        padding: "4px 10px",
        borderRadius: 12,
        fontSize: 13,
        fontFamily: "system-ui, sans-serif",
      }}
    >
      {label}
    </span>
  );
}
