import { useMemo } from "react";
import { MEASURE_COLORS } from "../lib/colors";

function RankBadge({ rank, total = 51 }) {
  const pct = rank / total;
  const color = pct <= 0.2 ? "var(--accent-green)" : pct <= 0.5 ? "var(--accent-blue)" : "var(--text-muted)";
  return (
    <span
      className="font-mono text-sm font-semibold px-1.5 py-0.5 rounded"
      style={{ color, backgroundColor: color + "15" }}
    >
      #{rank}
    </span>
  );
}

function DivergenceChip({ label, diff, color }) {
  const absDiff = Math.abs(diff);
  if (absDiff < 3) {
    return (
      <span
        className="text-xs font-medium px-2 py-0.5 rounded-full inline-flex items-center gap-1"
        style={{ color: "var(--text-muted)", backgroundColor: "var(--text-muted)" + "15" }}
      >
        <span style={{ color }}>{label}</span>
        <span>•</span>
        <span>{diff >= 0 ? "+" : ""}{diff}</span>
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
      <span>{positive ? "+" : ""}{diff}</span>
    </span>
  );
}

function formatDollars(raw) {
  const b = raw / 1e9;
  if (b >= 1000) return `$${(b / 1000).toFixed(1)}T`;
  if (b >= 1) return `$${b.toFixed(1)}B`;
  const m = raw / 1e6;
  if (m >= 1) return `$${m.toFixed(0)}M`;
  return `$${(raw / 1e3).toFixed(0)}K`;
}

const MEASURES = [
  { key: "eigenvector", label: "Eigenvector" },
  { key: "betweenness", label: "Betweenness" },
  { key: "out_degree", label: "Out-Degree" },
];

export default function StateDrawer({ state, data, edges, measure, onClose, inline }) {
  if (!state || !data) return null;

  const { outbound, inbound, topOutbound, topInbound } = useMemo(() => {
    if (!edges || edges.length === 0) {
      return { outbound: 0, inbound: 0, topOutbound: [], topInbound: [] };
    }

    let out = 0;
    let inb = 0;
    const outMap = new Map();
    const inMap = new Map();

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

    const topOut = Array.from(outMap.entries())
      .map(([partner, weight]) => ({ partner, weight }))
      .sort((a, b) => b.weight - a.weight)
      .slice(0, 5);

    const topIn = Array.from(inMap.entries())
      .map(([partner, weight]) => ({ partner, weight }))
      .sort((a, b) => b.weight - a.weight)
      .slice(0, 5);

    return { outbound: out, inbound: inb, topOutbound: topOut, topInbound: topIn };
  }, [edges, state]);

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
            <h2
              className="text-2xl font-bold truncate"
              style={{ color: "var(--text-primary)" }}
            >
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
            <div className="p-3 rounded-lg" style={{ backgroundColor: "var(--bg-surface)" }}>
              <div
                className="text-xs uppercase tracking-wider mb-1"
                style={{ color: "var(--text-muted)" }}
              >
                Outbound
              </div>
              <div className="font-mono text-lg" style={{ color: "var(--text-primary)" }}>
                {formatDollars(outbound)}
              </div>
            </div>
            <div className="p-3 rounded-lg" style={{ backgroundColor: "var(--bg-surface)" }}>
              <div
                className="text-xs uppercase tracking-wider mb-1"
                style={{ color: "var(--text-muted)" }}
              >
                Inbound
              </div>
              <div className="font-mono text-lg" style={{ color: "var(--text-primary)" }}>
                {formatDollars(inbound)}
              </div>
            </div>
          </div>
        )}

        {/* GDP + centrality measure cards */}
        <div className="space-y-3">
          <div className="p-3 rounded-lg" style={{ backgroundColor: "var(--bg-surface)" }}>
            <div
              className="text-xs uppercase tracking-wider mb-1"
              style={{ color: "var(--text-muted)" }}
            >
              GDP (2017)
            </div>
            <div className="flex justify-between items-center">
              <span className="font-mono text-lg" style={{ color: "var(--text-primary)" }}>
                ${data.gdp_billions?.toFixed(0)}B
              </span>
              <RankBadge rank={data.gdp_rank} />
            </div>
          </div>

          {MEASURES.map(({ key, label }) => (
            <div
              key={key}
              className="p-3 rounded-lg"
              style={{ backgroundColor: "var(--bg-surface)" }}
            >
              <div
                className="text-xs uppercase tracking-wider mb-1"
                style={{ color: "var(--text-muted)" }}
              >
                {label}
              </div>
              <div className="flex justify-between items-center">
                <span className="font-mono text-lg" style={{ color: MEASURE_COLORS[key] }}>
                  {data[key]?.toFixed(4)}
                </span>
                <RankBadge rank={data[`rank_${key}`]} />
              </div>
            </div>
          ))}
        </div>

        {/* Top Outbound Partners */}
        {topOutbound.length > 0 && (
          <div className="mt-5">
            <div
              className="text-xs uppercase tracking-wider mb-2"
              style={{ color: "var(--text-muted)" }}
            >
              Top Outbound →
            </div>
            <div
              className="rounded-lg overflow-hidden"
              style={{ border: "1px solid var(--border)" }}
            >
              {topOutbound.map((p, i) => (
                <div
                  key={p.partner}
                  className="flex items-center justify-between px-3 py-2"
                  style={{
                    backgroundColor: i % 2 === 0 ? "var(--bg-surface)" : "var(--bg-secondary)",
                    borderTop: i > 0 ? "1px solid var(--border)" : "none",
                  }}
                >
                  <div className="flex items-center gap-2 min-w-0 flex-1 mr-2">
                    <span
                      className="text-xs w-4 text-right flex-shrink-0"
                      style={{ color: "var(--text-muted)" }}
                    >
                      {i + 1}
                    </span>
                    <span
                      className="text-sm truncate"
                      style={{ color: "var(--text-primary)" }}
                    >
                      {p.partner}
                    </span>
                  </div>
                  <span
                    className="font-mono text-sm flex-shrink-0"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    {formatDollars(p.weight)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Top Inbound Partners */}
        {topInbound.length > 0 && (
          <div className="mt-4">
            <div
              className="text-xs uppercase tracking-wider mb-2"
              style={{ color: "var(--text-muted)" }}
            >
              Top Inbound ←
            </div>
            <div
              className="rounded-lg overflow-hidden"
              style={{ border: "1px solid var(--border)" }}
            >
              {topInbound.map((p, i) => (
                <div
                  key={p.partner}
                  className="flex items-center justify-between px-3 py-2"
                  style={{
                    backgroundColor: i % 2 === 0 ? "var(--bg-surface)" : "var(--bg-secondary)",
                    borderTop: i > 0 ? "1px solid var(--border)" : "none",
                  }}
                >
                  <div className="flex items-center gap-2 min-w-0 flex-1 mr-2">
                    <span
                      className="text-xs w-4 text-right flex-shrink-0"
                      style={{ color: "var(--text-muted)" }}
                    >
                      {i + 1}
                    </span>
                    <span
                      className="text-sm truncate"
                      style={{ color: "var(--text-primary)" }}
                    >
                      {p.partner}
                    </span>
                  </div>
                  <span
                    className="font-mono text-sm flex-shrink-0"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    {formatDollars(p.weight)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
    </div>
  );
}
