import { useMemo } from "react";
import { MEASURE_COLORS } from "../../lib/colors";
import Badge from "../ui/Badge";
import TradeCard from "./TradeCard";
import PartnersList from "./PartnersList";
import { type Partner } from "./format";
import type { BaseCentralityRow, Edge, Measure, StateTotals } from "../../types";

const MEASURES: { key: Measure; label: string }[] = [
  { key: "eigenvector", label: "Eigenvector" },
  { key: "betweenness", label: "Betweenness" },
  { key: "out_degree", label: "Out-Degree" },
];

function interpret(key: Measure, diff: number): string {
  if (diff > 0) {
    const phrase =
      key === "betweenness"
        ? "a critical bridge"
        : key === "eigenvector"
          ? "trades with powerful partners"
          : "an outsized exporter";
    return `Punches above its weight: ${phrase}, ${diff} ranks more central than its economy.`;
  }
  const plain =
    key === "betweenness"
      ? "bridge position"
      : key === "eigenvector"
        ? "trade prestige"
        : "export reach";
  return `Below its economic weight: ${Math.abs(diff)} ranks lower in ${plain} than its size.`;
}

function rankColor(rank: number, total = 51): string {
  const pct = rank / total;
  return pct <= 0.2
    ? "var(--accent-green)"
    : pct <= 0.5
      ? "var(--accent-blue)"
      : "var(--text-muted)";
}

interface RankPillProps {
  label: string;
  value: string;
  rank: number;
  color?: string;
  delta?: number;
}

function RankPill({ label, value, rank, color, delta }: RankPillProps) {
  return (
    <div className="min-w-[104px]">
      <div
        className="text-[10px] uppercase tracking-wider mb-1 flex items-center gap-1.5"
        style={{ color: "var(--text-muted)" }}
      >
        {color && (
          <span className="inline-block w-1.5 h-1.5 rounded-full" style={{ backgroundColor: color }} />
        )}
        {label}
      </div>
      <div className="flex items-baseline gap-2">
        <span className="font-mono text-sm" style={{ color: color ?? "var(--text-primary)" }}>
          {value}
        </span>
        <Badge color={rankColor(rank)}>#{rank}</Badge>
        {delta !== undefined && delta !== 0 && (
          <span
            className="text-xs font-medium"
            style={{ color: delta > 0 ? "var(--accent-green)" : "var(--accent-red)" }}
          >
            {delta > 0 ? "▲+" : "▼"}
            {delta > 0 ? delta : delta}
          </span>
        )}
      </div>
    </div>
  );
}

interface StateDossierProps {
  state: string;
  data: BaseCentralityRow;
  edges: Edge[];
  totals?: StateTotals | null;
  /** Active measure hue for the top accent + watermark. */
  accent: string;
  onClose: () => void;
}

/** Horizontal state detail panel that sits below the stage (map/divergence). */
export default function StateDossier({
  state,
  data,
  edges,
  totals,
  accent,
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

  const divergences = MEASURES.map(({ key }) => ({
    key,
    diff: (data.gdp_rank || 0) - (data[`rank_${key}`] || 0),
  }));
  const standout = divergences.reduce((a, b) => (Math.abs(b.diff) > Math.abs(a.diff) ? b : a));
  const hasVolume = totals != null || edges.length > 0;

  return (
    <div
      key={state}
      className="mt-3 p-5 relative overflow-hidden"
      style={{
        background: "linear-gradient(180deg, var(--canvas-from), var(--canvas-to))",
        border: "1px solid var(--hairline)",
        borderTop: `2.5px solid ${accent}`,
        borderRadius: "var(--radius-card)",
        boxShadow: "0 1px 2px rgba(26, 26, 46, 0.05)",
        animation: "ipo-finding-in 0.3s ease",
      }}
    >
      <span
        aria-hidden
        className="absolute pointer-events-none select-none font-bold tracking-tighter"
        style={{ right: 18, top: -18, fontSize: 130, lineHeight: 1, color: accent, opacity: 0.07 }}
      >
        {state}
      </span>
      <div className="relative flex flex-wrap items-start gap-x-8 gap-y-5">
        {/* Identity + interpretation */}
        <div className="min-w-[200px] max-w-[260px]">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h3 className="text-xl font-bold truncate" style={{ color: "var(--text-primary)" }}>
                {data.state_name || state}
              </h3>
              <span className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>
                {state}
              </span>
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
          {Math.abs(standout.diff) >= 5 && (
            <p
              className="text-xs mt-2 leading-snug"
              style={{ color: MEASURE_COLORS[standout.key] }}
            >
              {interpret(standout.key, standout.diff)}
            </p>
          )}
        </div>

        {/* Trade volume */}
        {hasVolume && (
          <div>
            <div
              className="text-[10px] uppercase tracking-wider mb-2"
              style={{ color: "var(--text-muted)" }}
            >
              Trade volume
            </div>
            <div className="flex gap-2">
              <TradeCard label="Outbound" value={outbound} />
              <TradeCard label="Inbound" value={inbound} />
            </div>
          </div>
        )}

        {/* GDP + network ranks */}
        <div>
          <div
            className="text-[10px] uppercase tracking-wider mb-2"
            style={{ color: "var(--text-muted)" }}
          >
            GDP vs network rank
          </div>
          <div className="flex gap-4 flex-wrap">
            <RankPill label="GDP" value={`$${data.gdp_billions?.toFixed(0)}B`} rank={data.gdp_rank} />
            {MEASURES.map(({ key, label }) => (
              <RankPill
                key={key}
                label={label}
                value={data[key]?.toFixed(3)}
                rank={data[`rank_${key}`]}
                color={MEASURE_COLORS[key]}
                delta={data.gdp_rank - data[`rank_${key}`]}
              />
            ))}
          </div>
        </div>

        {/* Top partners */}
        {(topOutbound.length > 0 || topInbound.length > 0) && (
          <div className="flex gap-6">
            <div className="-mt-4">
              <PartnersList title="Top Outbound →" partners={topOutbound} />
            </div>
            <div className="-mt-4">
              <PartnersList title="Top Inbound ←" partners={topInbound} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
