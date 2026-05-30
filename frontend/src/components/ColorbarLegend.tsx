interface Props {
  colormap: string;
  rescale: [number, number];
  units: string;
}

// Hand-tuned CSS approximations of the matplotlib colormaps served by TiTiler. They
// don't need to be pixel-perfect -- they just need to read the right direction.
const GRADIENTS: Record<string, string> = {
  terrain:
    "linear-gradient(to right, #333399 0%, #00a087 25%, #f7f7a5 60%, #a87444 85%, #ffffff 100%)",
  rdylbu_r:
    "linear-gradient(to right, #313695 0%, #74add1 25%, #ffffbf 50%, #f46d43 75%, #a50026 100%)",
  blues: "linear-gradient(to right, #f7fbff 0%, #6baed6 50%, #08306b 100%)",
};

function formatTick(value: number): string {
  if (Number.isInteger(value)) return value.toString();
  return value.toFixed(1);
}

export function ColorbarLegend({ colormap, rescale, units }: Props) {
  const gradient = GRADIENTS[colormap] ?? GRADIENTS.blues;
  const [lo, hi] = rescale;
  return (
    <div data-testid="colorbar-legend" style={{ width: "100%" }}>
      <div
        aria-label={`${colormap} colormap from ${lo} to ${hi} ${units}`}
        style={{
          height: 10,
          background: gradient,
          borderRadius: 2,
          border: "1px solid var(--mantine-color-gray-3)",
        }}
      />
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          fontSize: 11,
          color: "var(--mantine-color-dimmed)",
          marginTop: 2,
        }}
      >
        <span>{formatTick(lo)}</span>
        <span>{units}</span>
        <span>{formatTick(hi)}</span>
      </div>
    </div>
  );
}
