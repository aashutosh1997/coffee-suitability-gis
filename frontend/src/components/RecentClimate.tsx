import { Alert, Group, Loader, Paper, Text } from "@mantine/core";

import { useRecentClimate } from "../api/client";

interface Props {
  lon: number | null;
  lat: number | null;
}

// Non-scoring "recent conditions" context (NASA POWER / Open-Meteo). Shown beside the
// suitability result purely as a cross-check; it never feeds the score.
export function RecentClimate({ lon, lat }: Props) {
  const { data, isLoading } = useRecentClimate(lon, lat);

  if (lon == null || lat == null) return null;
  if (isLoading) {
    return (
      <Group gap="xs">
        <Loader size="xs" />
        <Text size="sm" c="dimmed">
          Fetching recent conditions…
        </Text>
      </Group>
    );
  }
  if (!data || !data.available) {
    return (
      <Alert color="gray" variant="light" title="Recent conditions unavailable">
        {data?.note ?? "Live weather services are unreachable."}
      </Alert>
    );
  }

  return (
    <Paper withBorder p="sm">
      <Text size="sm" fw={600}>
        Recent conditions ({data.source})
      </Text>
      <Text size="sm">
        Mean temperature {data.annual_mean_temp_c}°C · precipitation{" "}
        {data.annual_precip_mm} mm
      </Text>
      <Text size="xs" c="dimmed">
        {data.period} · context only, not used in scoring
      </Text>
    </Paper>
  );
}
