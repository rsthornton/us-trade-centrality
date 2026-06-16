import { MEASURE_COLORS } from "../lib/colors";
import type { Measure } from "../types";

const MEASURES: { key: Measure; label: string; description: string }[] = [
  { key: "eigenvector", label: "Eigenvector", description: "Trade prestige" },
  { key: "betweenness", label: "Betweenness", description: "Bridge position" },
  { key: "out_degree", label: "Out-Degree", description: "Export reach" },
];

interface CentralityPillsProps {
  selected: Measure;
  onSelect: (measure: Measure) => void;
}

export default function CentralityPills({ selected, onSelect }: CentralityPillsProps) {
  return (
    <div className="flex gap-2">
      {MEASURES.map(({ key, label, description }) => {
        const active = selected === key;
        const color = MEASURE_COLORS[key];
        return (
          <button
            key={key}
            onClick={() => onSelect(key)}
            className="px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-200 cursor-pointer border"
            style={{
              backgroundColor: active ? color + "22" : "transparent",
              borderColor: active ? color : "var(--border)",
              color: active ? color : "var(--text-secondary)",
            }}
          >
            <span className="block text-xs opacity-60">{description}</span>
            {label}
          </button>
        );
      })}
    </div>
  );
}
