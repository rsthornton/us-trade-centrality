import { useMemo } from "react";
import { MEASURE_COLORS } from "../../lib/colors";
import type { BaseCentralityRow, Edge, Measure } from "../../types";
import TradeCard from "./TradeCard";
import MeasureCard from "./MeasureCard";
import PartnersList from "./PartnersList";
import { type Partner } from "./format";

interface DivergenceChipProps {
  label: string;
  diff: number;
  color: string;
}

function DivergenceChip({ label, diff, color }: DivergenceChipProps) {
  const absDiff = Math.abs(diff);
  if (absDiff < 3) {
    return (
      <span
        className="text-xs font-medium px-2 py-0.5 rounded-full inline-flex items-center gap-1"
        style={{ color: "var(--text-muted)", backgroundColor: "var(--text-muted)" + "15" }}
      >
        <span style={{ color }}>{label}</span>
        <span>•</span>
        <span>
          {diff >= 0 ? "+" : ""}
          {diff}
        </span>
      </span>
    );
  }
  const positive = diff > 0;
  const chipColor = positive ? "var(--accent-green)" : "var(--accent-red)";
  return (
    <span
      className="text-xs font-medium px-2 py-0.5 rounded-full inline-flex items-center gap-1"
      style={{ color: chipColor, backgroundColor: chipColor + "15" }}
    >
      <span style={{ color }}>{label}</span>
      <span>{positive ? "▲" : "▼"}</span>
      <span>
        {positive ? "+" : ""}
        {diff}
      </span>
    </span>
  );
}

const MEASURES: { key: Measure; label: string }[] = [
  { key: "eigenvector", label: "Eigenvector" },
  { key: "betweenness", label: "Betweenness" },
  { key: "out_degree", label: "Out-Degree" },
];

interface StateDrawerProps {
  state: string | null;
  data: BaseCentralityRow | null;
  edges: Edge[];
  onClose: () => void;
  inline?: boolean;
}

export default function StateDrawer({ state, data, edges, onClose, inline }: StateDrawerProps) {
  const { outbound, inbound, topOutbound, topInbound } = useMemo(() => {
    if (!edges || edges.length === 0) {
      return {
        outbound: 0,
        inbound: 0,
        topOutbound: [] as Partner[],
        topInbound: [] as Partner[],
      };
    }

    let out = 0;
    let inb = 0;
    const outMap = new Map<string, number>();
    const inMap = new Map<string, number>();

    for (const e of edges) {
      if (e.source === state) {
        out += e.weight;
        outMap.set(e.target, (outMap.get(e.target) || 0) + e.weight);
      }
      if (e.target === state) {
        inb += e.weight;
        inMap.set(e.source, (inMap.get(e.source) || 0) + e.weight);
      }
    }

    const sortTop = (m: Map<string, number>): Partner[] =>
      Array.from(m.entries())
        .map(([partner, weight]) => ({ partner, weight }))
        .sort((a, b) => b.weight - a.weight)
        .slice(0, 5);

    return { outbound: out, inbound: inb, topOutbound: sortTop(outMap), topInbound: sortTop(inMap) };
  }, [edges, state]);

  if (!state || !data) return null;

  const divergences = MEASURES.map(({ key, label }) => ({
    key,
    label,
    diff: (data.gdp_rank || 0) - (data[`rank_${key}`] || 0),
    color: MEASURE_COLORS[key],
  }));

  return (
    <div className={inline ? "p-4" : "p-5"}>
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div className="min-w-0 flex-1 mr-2">
          <h2 className="text-2xl font-bold truncate" style={{ color: "var(--text-primary)" }}>
            {data.state_name || state}
          </h2>
          <span className="text-sm font-mono" style={{ color: "var(--text-muted)" }}>
            {state}
          </span>
        </div>
        <button
          onClick={onClose}
          className="text-lg cursor-pointer px-2 py-1 rounded hover:bg-white/10 flex-shrink-0"
          style={{ color: "var(--text-muted)" }}
        >
          ✕
        </button>
      </div>

      {/* GDP divergence chips — all three measures */}
      <div className="flex flex-wrap gap-1.5 mb-5">
        {divergences.map(({ key, label, diff, color }) => (
          <DivergenceChip key={key} label={label.slice(0, 3)} diff={diff} color={color} />
        ))}
      </div>

      {/* Trade volume cards */}
      {edges && edges.length > 0 && (
        <div className="grid grid-cols-2 gap-2 mb-5">
          <TradeCard label="Outbound" value={outbound} />
          <TradeCard label="Inbound" value={inbound} />
        </div>
      )}

      {/* GDP + centrality measure cards */}
      <div className="space-y-3">
        <MeasureCard label="GDP (2017)" value={`$${data.gdp_billions?.toFixed(0)}B`} rank={data.gdp_rank} />
        {MEASURES.map(({ key, label }) => (
          <MeasureCard
            key={key}
            label={label}
            value={data[key]?.toFixed(4)}
            rank={data[`rank_${key}`]}
            valueColor={MEASURE_COLORS[key]}
          />
        ))}
      </div>

      <PartnersList title="Top Outbound →" partners={topOutbound} />
      <PartnersList title="Top Inbound ←" partners={topInbound} />
    </div>
  );
}
