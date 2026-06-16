import { MEASURE_COLORS } from "../lib/colors";
import Pill from "./ui/Pill";
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
      {MEASURES.map(({ key, label, description }) => (
        <Pill
          key={key}
          active={selected === key}
          color={MEASURE_COLORS[key]}
          subtitle={description}
          onClick={() => onSelect(key)}
        >
          {label}
        </Pill>
      ))}
    </div>
  );
}
