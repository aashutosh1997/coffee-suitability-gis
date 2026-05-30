import { Stack, Text, Title } from "@mantine/core";

import type { Geometry } from "../api/client";
import { aoiSummary } from "../utils/geo";

interface Props {
  geometry: Geometry | null;
  snapshot: string | null;
}

/** Print-only AOI block: a map snapshot + the polygon area or point coordinates. Mounted
 * inside `.print-area` and hidden on-screen via `.print-only` so it shows only in the
 * print preview / saved PDF. */
export function PrintReport({ geometry, snapshot }: Props) {
  if (!geometry) return null;
  const summary = aoiSummary(geometry);
  return (
    <div className="print-only">
      <Stack gap="xs">
        <Title order={5}>Plot</Title>
        {snapshot ? (
          <img
            src={snapshot}
            alt="AOI on map"
            className="print-aoi-map"
            data-testid="print-aoi-map"
          />
        ) : (
          <Text size="sm" c="dimmed">
            Map preview unavailable.
          </Text>
        )}
        <Text size="sm">{summary.label}</Text>
      </Stack>
    </div>
  );
}
