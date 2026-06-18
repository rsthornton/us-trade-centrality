import { interpolateViridis } from "../lib/colors";

const STEPS = 32;

interface ColorLegendProps {
  label?: string;
  min?: number;
  max?: number;
  /** Active measure hue for the label + dot. */
  color?: string;
}

export default function ColorLegend({
  label = "Centrality",
  min = 0,
  max = 1,
  color,
}: ColorLegendProps) {
  const stops = Array.from({ length: STEPS }, (_, i) => {
    const t = i / (STEPS - 1);
    return interpolateViridis(t);
  });

  return (
    <div className="flex items-center gap-3">
      <span className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>
        {min.toFixed(2)}
      </span>
      <div className="flex h-2.5 rounded-full overflow-hidden" style={{ width: 160 }}>
        {stops.map((color, i) => (
          <div key={i} style={{ flex: 1, backgroundColor: color }} />
        ))}
      </div>
      <span className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>
        {max.toFixed(2)}
      </span>
      <span className="inline-flex items-center gap-1.5 text-xs font-medium">
        {color && (
          <span
            className="inline-block w-1.5 h-1.5 rounded-full"
            style={{ backgroundColor: color }}
          />
        )}
        <span style={{ color: color ?? "var(--text-muted)" }}>{label}</span>
      </span>
    </div>
  );
}
