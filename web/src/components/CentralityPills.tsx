import { MEASURE_COLORS } from "../lib/colors";
import type { Measure } from "../types";

const MEASURES: { key: Measure; label: string; description: string }[] = [
  { key: "eigenvector", label: "Trade prestige", description: "eigenvector" },
  { key: "betweenness", label: "Bridge position", description: "betweenness" },
  { key: "out_degree", label: "Export reach", description: "weighted out-degree" },
];

interface CentralityPillsProps {
  selected: Measure;
  onSelect: (measure: Measure) => void;
  /** Stack the three measures vertically (for the control rail). */
  vertical?: boolean;
}

/** Measure selector. Enclosed group; the measure's color rides as a small dot
 *  (tying it to the map ramp) rather than a full colored border. */
export default function CentralityPills({ selected, onSelect, vertical }: CentralityPillsProps) {
  return (
    <div
      className={`${vertical ? "flex flex-col w-full" : "inline-flex"} gap-0.5 p-0.5 rounded-lg`}
      style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--hairline)" }}
    >
      {MEASURES.map(({ key, label, description }) => {
        const active = selected === key;
        return (
          <button
            key={key}
            onClick={() => onSelect(key)}
            className={`text-left px-3 py-1.5 rounded-md cursor-pointer transition-all duration-200 ${vertical ? "w-full" : ""}`}
            style={{
              backgroundColor: active ? "var(--bg-secondary)" : "transparent",
              boxShadow: active ? "var(--shadow-card)" : "none",
            }}
          >
            <span className="flex items-center gap-2">
              <span
                className="inline-block w-2 h-2 rounded-full"
                style={{ backgroundColor: MEASURE_COLORS[key], opacity: active ? 1 : 0.45 }}
              />
              <span
                className="text-sm font-medium"
                style={{ color: active ? "var(--text-primary)" : "var(--text-secondary)" }}
              >
                {label}
              </span>
            </span>
            <span
              className="block font-mono text-[11px] mt-0.5 pl-4"
              style={{ color: "var(--text-muted)" }}
            >
              {description}
            </span>
          </button>
        );
      })}
    </div>
  );
}
