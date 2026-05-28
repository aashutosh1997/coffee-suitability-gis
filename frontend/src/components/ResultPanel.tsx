import { Alert, Badge, Group, List, Loader, Stack, Table, Text } from "@mantine/core";

import type { AssessResponse } from "../api/client";

const CLASS_COLOR: Record<string, string> = {
  S1: "green",
  S2: "teal",
  S3: "yellow",
  N: "red",
};

const CLASS_LABEL: Record<string, string> = {
  S1: "Highly suitable",
  S2: "Moderately suitable",
  S3: "Marginally suitable",
  N: "Not suitable",
};

interface Props {
  result: AssessResponse | null;
  loading: boolean;
  error?: string | null;
}

export function ResultPanel({ result, loading, error }: Props) {
  if (error) {
    return (
      <Alert color="red" title="Could not assess this area">
        {error}
      </Alert>
    );
  }
  if (loading) {
    return (
      <Group gap="xs">
        <Loader size="sm" />
        <Text>Assessing…</Text>
      </Group>
    );
  }
  if (!result) {
    return <Text c="dimmed">Pick an area and run an assessment to see results.</Text>;
  }

  const cls = result.overall.class;
  return (
    <Stack gap="sm">
      <Group gap="sm">
        <Badge color={CLASS_COLOR[cls] ?? "gray"} size="lg">
          {cls}
        </Badge>
        <Text fw={600}>{CLASS_LABEL[cls] ?? cls}</Text>
        <Text c="dimmed" size="sm">
          score {result.overall.score}
        </Text>
      </Group>

      {result.overall.limiting_factor && (
        <Text size="sm">
          Biggest limitation: <b>{result.overall.limiting_factor}</b>
        </Text>
      )}

      <Table withTableBorder withRowBorders verticalSpacing="xs">
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Factor</Table.Th>
            <Table.Th>Value</Table.Th>
            <Table.Th>Band</Table.Th>
            <Table.Th>Explanation</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {result.factors.map((f) => {
            const notAssessed = f.band === "not_assessed";
            const value =
              f.raw_value == null ? "—" : `${f.raw_value}${f.unit ? ` ${f.unit}` : ""}`;
            return (
              <Table.Tr key={f.name} c={notAssessed ? "dimmed" : undefined}>
                <Table.Td>{f.name}</Table.Td>
                <Table.Td>{value}</Table.Td>
                <Table.Td>{notAssessed ? "Not assessed" : f.band}</Table.Td>
                <Table.Td>{f.explanation}</Table.Td>
              </Table.Tr>
            );
          })}
        </Table.Tbody>
      </Table>

      {result.uncertainty_notes.length > 0 && (
        <List size="xs" c="dimmed">
          {result.uncertainty_notes.map((note, i) => (
            <List.Item key={i}>{note}</List.Item>
          ))}
        </List>
      )}

      <Text size="xs" c="dimmed">
        Model config {result.model_config_version}
      </Text>
    </Stack>
  );
}
