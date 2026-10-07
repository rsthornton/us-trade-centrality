import { useMemo } from "react";
import { MEASURE_COLORS } from "../../lib/colors";
import { hasRank, rankGap } from "../../lib/ranks";
import { formatScore } from "../../lib/format";
import TradeCard from "./TradeCard";
import PartnersList from "./PartnersList";
import { formatDollars, type Partner } from "./format";
import type { BaseCentralityRow, Edge, Measure, StateTotals } from "../../types";

const MEASURES: { key: Measure; label: string }[] = [
  { key: "eigenvector", label: "Trade prestige" },
  { key: "betweenness", label: "Bridge position" },
  { key: "out_degree", label: "Export reach" },
];

function interpret(name: string, key: Measure, diff: number): string {
  const label = MEASURES.find((m) => m.key === key)?.label.toLowerCase() ?? key;
  const direction = diff > 0 ? "higher" : "lower";
  return `${name}'s ${label} rank is ${Math.abs(diff)} places ${direction} than its GDP rank.`;
}

interface RankPillProps {
  label: string;
  value: string;
  rank: number | null;
  color?: string;
  delta?: number;
}

function RankPill({ label, value, rank, color, delta }: RankPillProps) {
  return (
    <div className="min-w-[112px]">
      <div
        className="text-[11px] font-medium mb-1 flex items-center gap-1.5"
        style={{ color: "var(--text-secondary)" }}
      >
        {color && (
          <span className="inline-block w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
        )}
        {label}
      </div>
      {rank === null ? (
        <div className="text-sm" style={{ color: "var(--text-muted)" }}>
          {label === "Bridge position" ? "No brokerage" : "None"}
        </div>
      ) : (
        <div className="flex items-baseline gap-2 font-mono tabular-nums">
          <span className="text-sm" style={{ color: "var(--text-primary)" }}>
            #{rank}
          </span>
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>
            {value}
          </span>
          {delta !== undefined && delta !== 0 && (
            <span
              className="text-xs font-semibold"
              style={{ color: delta > 0 ? "var(--gap-above)" : "var(--gap-below)" }}
            >
              {delta > 0 ? `+${delta}` : `−${Math.abs(delta)}`}
            </span>
          )}
        </div>
      )}
    </div>
  );
}

interface StateDossierProps {
  state: string;
  /** Full state name (commodity rows carry only the code). */
  stateName: string;
  /** The measure selected in the rail; the interpretation follows it. */
  measure: Measure;
  data: BaseCentralityRow;
  edges: Edge[];
  totals?: StateTotals | null;
  /** Caveat shown under trade volume when the data cannot see part of this commodity. */
  scopeNote?: string;
  onClose: () => void;
}

/** Horizontal state detail panel that sits below the stage (map/divergence). */
export default function StateDossier({
  state,
  stateName,
  measure,
  data,
  edges,
  totals,
  scopeNote,
  onClose,
}: StateDossierProps) {
  const fromEdges = useMemo(() => {
    if (!edges || edges.length === 0) {
      return { outbound: 0, inbound: 0, topOutbound: [] as Partner[], topInbound: [] as Partner[] };
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

  const outbound = totals ? totals.out_total : fromEdges.outbound;
  const inbound = totals ? totals.in_total : fromEdges.inbound;
  const topOutbound = totals ? totals.top_out.slice(0, 5) : fromEdges.topOutbound;
  const topInbound = totals ? totals.top_in.slice(0, 5) : fromEdges.topInbound;

  const gap = hasRank(data, measure) ? rankGap(data, measure) : 0;
  const hasVolume = totals != null || edges.length > 0;

  return (
    <div
      key={state}
      className="mt-3 p-5 relative overflow-hidden"
      style={{
        background: "linear-gradient(180deg, var(--canvas-from), var(--canvas-to))",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-card)",
        boxShadow: "0 1px 2px rgba(0, 0, 0, 0.05)",
        animation: "ipo-finding-in 0.3s ease",
      }}
    >
      <div className="relative flex flex-wrap items-start gap-x-8 gap-y-5">
        {/* Identity + interpretation */}
        <div className="min-w-[200px] max-w-[260px]">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h3 className="text-xl font-semibold truncate" style={{ color: "var(--text-primary)" }}>
                {stateName}
              </h3>
            </div>
            <button
              onClick={onClose}
              aria-label="Close"
              className="text-lg cursor-pointer leading-none flex-shrink-0"
              style={{ color: "var(--text-muted)" }}
            >
              ✕
            </button>
          </div>
          {Math.abs(gap) >= 5 && (
            <p className="text-sm mt-2 leading-snug" style={{ color: "var(--text-secondary)" }}>
              {interpret(stateName, measure, gap)}
            </p>
          )}
        </div>

        {/* Trade volume */}
        {hasVolume && (
          <div>
            {scopeNote && (
              <p
                className="text-xs mb-3 max-w-[300px] leading-snug px-3 py-2 rounded-md"
                role="note"
                style={{
                  color: "var(--text-primary)",
                  background: "var(--bg-surface)",
                  border: "1px solid var(--border)",
                }}
              >
                <span className="font-semibold">Coverage limit. </span>
                {scopeNote}
              </p>
            )}
            <div
              className="text-[11px] font-medium mb-2"
              style={{ color: "var(--text-secondary)" }}
            >
              Shipment value
            </div>
            <div className="flex gap-2">
              <TradeCard label="Outbound" value={outbound} />
              <TradeCard label="Inbound" value={inbound} />
            </div>
            {Math.abs(inbound - outbound) > 0 && (
              <p className="text-xs mt-2" style={{ color: "var(--text-secondary)" }}>
                {inbound > outbound ? "Net importer" : "Net exporter"}{" "}
                <span className="font-mono">{formatDollars(Math.abs(inbound - outbound))}</span>
              </p>
            )}
          </div>
        )}

        {/* GDP + network ranks */}
        <div>
          <div
            className="text-[11px] font-medium mb-2"
            style={{ color: "var(--text-secondary)" }}
          >
            GDP rank and network ranks
          </div>
          <div className="flex gap-4 flex-wrap">
            <RankPill label="GDP" value={formatDollars(data.gdp_billions * 1e9)} rank={data.gdp_rank} />
            {MEASURES.map(({ key, label }) => (
              <RankPill
                key={key}
                label={label}
                value={formatScore(data[key])}
                rank={hasRank(data, key) ? data[`rank_${key}`] : null}
                color={MEASURE_COLORS[key]}
                delta={rankGap(data, key)}
              />
            ))}
          </div>
        </div>

        {/* Top partners */}
        {(topOutbound.length > 0 || topInbound.length > 0) && (
          <div className="flex gap-6">
            <div className="-mt-4">
              <PartnersList title="Top destinations" partners={topOutbound} />
            </div>
            <div className="-mt-4">
              <PartnersList title="Top origins" partners={topInbound} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
