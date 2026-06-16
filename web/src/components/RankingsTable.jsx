import { useState, useMemo, useRef, useEffect } from "react";
import { centralityToColor } from "../lib/colors";

const MEASURE_FILLS = {
  eigenvector: { bg: "#ECFDF5", text: "#065F46", shadow: "rgba(6, 95, 70, 0.12)" },
  betweenness: { bg: "#EFF6FF", text: "#1E40AF", shadow: "rgba(30, 64, 175, 0.12)" },
  out_degree: { bg: "#FFF7ED", text: "#9A3412", shadow: "rgba(154, 52, 18, 0.12)" },
};

const MEASURES = [
  { key: "eigenvector", label: "Eigenvector", short: "Eig" },
  { key: "betweenness", label: "Betweenness", short: "Bet" },
  { key: "out_degree", label: "Out-Degree", short: "Out" },
];

const CHART_W = 240;
const CHART_H = 240;
const PAD = { top: 24, right: 12, bottom: 28, left: 28 };
const INNER_W = CHART_W - PAD.left - PAD.right;
const INNER_H = CHART_H - PAD.top - PAD.bottom;
const LABEL_THRESHOLD = 7;

function DivergenceScatter({ centralities, measureKey, label, selectedState, onSelectState }) {
  const rankKey = `rank_${measureKey}`;

  const { points, minVal, maxVal } = useMemo(() => {
    if (!centralities.length) return { points: [], minVal: 0, maxVal: 1 };
    const vals = centralities.map((r) => r[measureKey]);
    const mn = Math.min(...vals);
    const mx = Math.max(...vals);
    const pts = centralities.map((r) => {
      const gdp = r.gdp_rank;
      const rank = r[rankKey];
      const delta = gdp - rank;
      const x = PAD.left + ((gdp - 1) / 50) * INNER_W;
      const y = PAD.top + ((rank - 1) / 50) * INNER_H;
      return {
        x, y, gdp, rank, delta,
        state: r.state,
        name: r.state_name,
        value: r[measureKey],
        isZero: r[measureKey] === 0,
        showLabel: Math.abs(delta) >= LABEL_THRESHOLD,
      };
    });
    return { points: pts, minVal: mn, maxVal: mx };
  }, [centralities, measureKey, rankKey]);

  const [hovered, setHovered] = useState(null);

  const diagX1 = PAD.left;
  const diagY1 = PAD.top;
  const diagX2 = PAD.left + INNER_W;
  const diagY2 = PAD.top + INNER_H;

  return (
    <div className="flex-1 min-w-0">
      <div
        className="text-xs font-medium text-center mb-1"
        style={{ color: "var(--text-secondary)" }}
      >
        {label}
      </div>
      <svg viewBox={`0 0 ${CHART_W} ${CHART_H}`} className="w-full h-auto">
        <line
          x1={diagX1} y1={diagY1} x2={diagX2} y2={diagY2}
          stroke="#d0d0d8" strokeWidth={1} strokeDasharray="3,3"
        />

        <text
          x={PAD.left + INNER_W / 2} y={CHART_H - 4}
          textAnchor="middle" fontSize={9} fill="var(--text-muted)"
        >
          GDP Rank →
        </text>
        <text
          x={6} y={PAD.top + INNER_H / 2}
          textAnchor="middle" fontSize={9} fill="var(--text-muted)"
          transform={`rotate(-90, 6, ${PAD.top + INNER_H / 2})`}
        >
          Network Rank →
        </text>

        <text x={PAD.left} y={PAD.top - 6} fontSize={8} fill="var(--text-muted)">1</text>
        <text x={PAD.left + INNER_W} y={PAD.top - 6} fontSize={8} fill="var(--text-muted)" textAnchor="end">51</text>
        <text x={PAD.left - 4} y={PAD.top + 3} fontSize={8} fill="var(--text-muted)" textAnchor="end">1</text>
        <text x={PAD.left - 4} y={PAD.top + INNER_H + 3} fontSize={8} fill="var(--text-muted)" textAnchor="end">51</text>

        {/* "above weight" / "below weight" zone labels */}
        <text
          x={PAD.left + INNER_W * 0.75} y={PAD.top + INNER_H * 0.25}
          fontSize={8} fill="var(--accent-green)" opacity={0.5} textAnchor="middle"
        >
          ↑ above weight
        </text>
        <text
          x={PAD.left + INNER_W * 0.25} y={PAD.top + INNER_H * 0.75}
          fontSize={8} fill="var(--accent-red)" opacity={0.5} textAnchor="middle"
        >
          ↓ below weight
        </text>

        {points.map((p) => {
          const isSelected = p.state === selectedState;
          const isHov = p.state === hovered;
          const color = p.isZero ? "#ccc" : centralityToColor(p.value, minVal, maxVal);
          return (
            <g key={p.state}>
              <circle
                cx={p.x} cy={p.y}
                r={isSelected ? 5 : isHov ? 4.5 : 3.5}
                fill={color}
                stroke={isSelected ? "#FFA94D" : isHov ? "#666" : "white"}
                strokeWidth={isSelected ? 2 : 1}
                opacity={p.isZero ? 0.4 : 1}
                className="cursor-pointer"
                onMouseEnter={() => setHovered(p.state)}
                onMouseLeave={() => setHovered(null)}
                onClick={() => onSelectState(isSelected ? null : p.state)}
              />
              {(p.showLabel || isHov || isSelected) && (
                <text
                  x={p.x + 5} y={p.y - 5}
                  fontSize={isHov || isSelected ? 9 : 7.5}
                  fontWeight={isSelected ? 700 : 500}
                  fill={p.delta > 0 ? "var(--accent-green)" : "var(--accent-red)"}
                  opacity={isHov || isSelected ? 1 : 0.8}
                >
                  {p.state}
                </text>
              )}
            </g>
          );
        })}

        {hovered && (() => {
          const p = points.find((pt) => pt.state === hovered);
          if (!p) return null;
          const tx = Math.min(p.x + 8, CHART_W - 90);
          const ty = Math.max(p.y - 8, 30);
          return (
            <g pointerEvents="none">
              <rect
                x={tx - 2} y={ty - 12} width={88} height={32} rx={4}
                fill="white" stroke="var(--border)" strokeWidth={0.5}
                opacity={0.95}
              />
              <text x={tx + 2} y={ty} fontSize={8} fontWeight={600} fill="var(--text-primary)">
                {p.name}
              </text>
              <text x={tx + 2} y={ty + 12} fontSize={7.5} fill="var(--text-secondary)">
                GDP #{p.gdp} → Net #{p.rank} ({p.delta > 0 ? "+" : ""}{p.delta})
              </text>
            </g>
          );
        })()}
      </svg>
    </div>
  );
}

function DivergenceTable({ centralities, measure, selectedState, onSelectState }) {
  const rankKey = `rank_${measure}`;
  const [ascending, setAscending] = useState(false);

  const rows = useMemo(() => {
    return centralities
      .map((r) => ({
        state: r.state,
        name: r.state_name,
        gdp: r.gdp_rank,
        rank: r[rankKey],
        delta: r.gdp_rank - r[rankKey],
        isZero: r[measure] === 0,
        value: r[measure],
      }))
      .sort((a, b) => ascending ? a.delta - b.delta : b.delta - a.delta);
  }, [centralities, rankKey, measure, ascending]);

  const measureLabel = MEASURES.find((m) => m.key === measure)?.label || measure;

  return (
    <div className="mt-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
          {measureLabel} vs GDP — divergence ranking
        </span>
        <button
          onClick={() => setAscending(!ascending)}
          className="text-xs cursor-pointer px-2 py-0.5 rounded border"
          style={{ borderColor: "var(--border)", color: "var(--text-secondary)", background: "transparent" }}
        >
          {ascending ? "Below weight ↓" : "Above weight ↑"}
        </button>
      </div>
      <div style={{ maxHeight: 220, overflowY: "auto" }}>
        <table className="w-full" style={{ borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th className="text-left text-xs py-1.5 pr-3 sticky top-0" style={{ color: "var(--text-muted)", background: "var(--bg-primary)", fontWeight: 500 }}>
                State
              </th>
              <th className="text-right text-xs py-1.5 px-2 sticky top-0 font-mono" style={{ color: "var(--text-muted)", background: "var(--bg-primary)", fontWeight: 500 }}>
                GDP
              </th>
              <th className="text-right text-xs py-1.5 px-2 sticky top-0 font-mono" style={{ color: "var(--text-muted)", background: "var(--bg-primary)", fontWeight: 500 }}>
                Net
              </th>
              <th className="text-right text-xs py-1.5 pl-2 sticky top-0 font-mono" style={{ color: "var(--text-muted)", background: "var(--bg-primary)", fontWeight: 500 }}>
                Δ
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => {
              const isSelected = r.state === selectedState;
              const deltaColor = r.delta >= 5
                ? "var(--accent-green)"
                : r.delta <= -5
                  ? "var(--accent-red)"
                  : "var(--text-muted)";
              return (
                <tr
                  key={r.state}
                  className="cursor-pointer"
                  onClick={() => onSelectState(isSelected ? null : r.state)}
                  style={{
                    backgroundColor: isSelected ? "rgba(255, 169, 77, 0.12)" : "transparent",
                  }}
                  onMouseEnter={(e) => { if (!isSelected) e.currentTarget.style.backgroundColor = "var(--bg-surface)"; }}
                  onMouseLeave={(e) => { if (!isSelected) e.currentTarget.style.backgroundColor = "transparent"; }}
                >
                  <td className="text-sm py-1 pr-3" style={{ color: "var(--text-primary)" }}>
                    {r.name}
                    <span className="font-mono text-xs ml-1.5" style={{ color: "var(--text-muted)" }}>{r.state}</span>
                  </td>
                  <td className="text-right font-mono text-sm py-1 px-2" style={{ color: "var(--text-secondary)" }}>
                    {r.gdp}
                  </td>
                  <td className="text-right font-mono text-sm py-1 px-2" style={{ color: r.isZero ? "var(--text-muted)" : "var(--text-secondary)" }}>
                    {r.isZero ? "—" : r.rank}
                  </td>
                  <td className="text-right font-mono text-sm font-semibold py-1 pl-2" style={{ color: deltaColor }}>
                    {r.isZero ? "—" : (r.delta > 0 ? `+${r.delta}` : r.delta)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function RankingsTable({ centralities, measure, selectedState, onSelectState }) {
  const [expanded, setExpanded] = useState(false);
  const [bounced, setBounced] = useState(false);
  const contentRef = useRef(null);
  const buttonRef = useRef(null);

  useEffect(() => {
    if (expanded && contentRef.current) {
      contentRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [expanded]);

  useEffect(() => {
    const timer = setTimeout(() => setBounced(true), 2000);
    return () => clearTimeout(timer);
  }, []);

  if (!centralities || !centralities.length) return null;

  const fill = MEASURE_FILLS[measure] || MEASURE_FILLS.eigenvector;

  return (
    <div
      className="mx-6 mt-2 rounded-t-lg overflow-hidden"
      style={{
        backgroundColor: "var(--bg-secondary)",
        border: "1px solid var(--border)",
        borderBottom: "none",
      }}
    >
      <div className="flex justify-center py-3">
        <button
          ref={buttonRef}
          onClick={() => setExpanded(!expanded)}
          className="cursor-pointer transition-all duration-200"
          style={{
            background: expanded ? "var(--bg-surface)" : fill.bg,
            color: expanded ? "var(--text-secondary)" : fill.text,
            border: "none",
            borderRadius: 24,
            padding: "10px 24px",
            fontSize: 15,
            fontWeight: 500,
            boxShadow: expanded ? "none" : `0 4px 14px ${fill.shadow}`,
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            animation: bounced && !expanded ? "nudge 0.6s ease-in-out 1" : "none",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.boxShadow = expanded ? "none" : `0 6px 20px ${fill.shadow}`;
            e.currentTarget.style.transform = "translateY(-1px)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.boxShadow = expanded ? "none" : `0 4px 14px ${fill.shadow}`;
            e.currentTarget.style.transform = "none";
          }}
        >
          <span
            className="inline-block transition-transform duration-200"
            style={{ transform: expanded ? "rotate(180deg)" : "none", fontSize: 11 }}
          >
            ▼
          </span>
          {expanded ? "Collapse" : "See where GDP and network power diverge"}
        </button>
      </div>

      <style>{`
        @keyframes nudge {
          0%, 100% { transform: translateY(0); }
          40% { transform: translateY(6px); }
          70% { transform: translateY(-2px); }
        }
      `}</style>

      {expanded && (
        <div ref={contentRef} className="px-5 pb-5">
          <div className="flex gap-2">
            {MEASURES.map(({ key, label }) => (
              <DivergenceScatter
                key={key}
                centralities={centralities}
                measureKey={key}
                label={label}
                selectedState={selectedState}
                onSelectState={onSelectState}
              />
            ))}
          </div>

          <DivergenceTable
            centralities={centralities}
            measure={measure}
            selectedState={selectedState}
            onSelectState={onSelectState}
          />
        </div>
      )}
    </div>
  );
}
