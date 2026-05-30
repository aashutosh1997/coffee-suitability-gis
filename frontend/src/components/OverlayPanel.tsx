import {
  Alert,
  Badge,
  Checkbox,
  Group,
  Loader,
  Paper,
  Select,
  Slider,
  Stack,
  Text,
  Title,
} from "@mantine/core";

import { useOverlays, type OverlayLayer } from "../api/client";
import { ColorbarLegend } from "./ColorbarLegend";

export interface OverlayUiState {
  enabled: Set<string>;
  opacity: Record<string, number>;
  band: Record<string, number>;
}

interface Props {
  state: OverlayUiState;
  onToggle: (key: string) => void;
  onOpacity: (key: string, value: number) => void;
  onBand: (key: string, band: number) => void;
}

const MONTHS = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

export function defaultOverlayState(): OverlayUiState {
  return { enabled: new Set(), opacity: {}, band: {} };
}

export function getOpacity(state: OverlayUiState, key: string): number {
  return state.opacity[key] ?? 0.7;
}

export function getBand(state: OverlayUiState, key: string): number {
  return state.band[key] ?? 1;
}

export function OverlayPanel({ state, onToggle, onOpacity, onBand }: Props) {
  const { data, isLoading, isError } = useOverlays();

  if (isLoading) {
    return (
      <Paper shadow="sm" p="sm" data-testid="overlay-panel">
        <Group gap="xs">
          <Loader size="xs" />
          <Text size="sm">Loading map layers…</Text>
        </Group>
      </Paper>
    );
  }
  if (isError || !data || data.layers.length === 0) {
    return (
      <Paper shadow="sm" p="sm" data-testid="overlay-panel">
        <Alert color="gray" variant="light">
          No raster layers available.
        </Alert>
      </Paper>
    );
  }

  return (
    <Paper shadow="sm" p="sm" data-testid="overlay-panel" style={{ width: 260 }}>
      <Title order={6} mb="xs">
        Map layers
      </Title>
      <Stack gap="md">
        {data.layers.map((layer) => (
          <OverlayLayerControl
            key={layer.key}
            layer={layer}
            enabled={state.enabled.has(layer.key)}
            opacity={getOpacity(state, layer.key)}
            band={getBand(state, layer.key)}
            onToggle={() => onToggle(layer.key)}
            onOpacity={(v) => onOpacity(layer.key, v)}
            onBand={(b) => onBand(layer.key, b)}
          />
        ))}
      </Stack>
    </Paper>
  );
}

interface ControlProps {
  layer: OverlayLayer;
  enabled: boolean;
  opacity: number;
  band: number;
  onToggle: () => void;
  onOpacity: (value: number) => void;
  onBand: (band: number) => void;
}

function OverlayLayerControl({
  layer,
  enabled,
  opacity,
  band,
  onToggle,
  onOpacity,
  onBand,
}: ControlProps) {
  const multiBand = layer.band_count > 1;
  return (
    <div data-testid={`overlay-${layer.key}`}>
      <Group justify="space-between" align="flex-start" wrap="nowrap">
        <Checkbox
          label={
            <span>
              <Text component="span" size="sm" fw={500}>
                {layer.name}
              </Text>
            </span>
          }
          checked={enabled}
          onChange={onToggle}
        />
        {layer.source && (
          <Badge size="xs" variant="light" color="gray">
            {layer.resolution ?? "raster"}
          </Badge>
        )}
      </Group>
      {enabled && (
        <Stack gap={6} mt={6} pl={26}>
          {multiBand && (
            <Select
              size="xs"
              label="Month"
              value={String(band)}
              data={(layer.bands ?? []).map((b) => ({
                value: String(b.n),
                label: b.name,
              }))}
              onChange={(v) => v && onBand(Number(v))}
              allowDeselect={false}
              comboboxProps={{ withinPortal: false }}
              aria-label={`${layer.name} month selector`}
            />
          )}
          <div>
            <Text size="xs" c="dimmed" mb={2}>
              Opacity
            </Text>
            <Slider
              size="xs"
              min={0}
              max={1}
              step={0.05}
              value={opacity}
              onChange={onOpacity}
              label={(v) => `${Math.round(v * 100)}%`}
              aria-label={`${layer.name} opacity`}
            />
          </div>
          <ColorbarLegend
            colormap={layer.colormap}
            rescale={layer.rescale}
            units={multiBand ? `${MONTHS[band - 1]} ${layer.units}` : layer.units}
          />
          {layer.source && (
            <Text size="xs" c="dimmed">
              {layer.source}
            </Text>
          )}
        </Stack>
      )}
    </div>
  );
}
