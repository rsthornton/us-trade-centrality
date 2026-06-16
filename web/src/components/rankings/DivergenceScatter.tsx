import { useMemo, useState } from "react";
import { centralityToColor } from "../../lib/colors";
import type { BaseCentralityRow, Measure } from "../../types";

const CHART_W = 240;
const CHART_H = 240;
const PAD = { top: 24, right: 12, bottom: 28, left: 28 };
const INNER_W = CHART_W - PAD.left - PAD.right;
const INNER_H = CHART_H - PAD.top - PAD.bottom;
const LABEL_THRESHOLD = 7;

export interface DivergenceScatterProps {
  centralities: BaseCentralityRow[];
  measureKey: Measure;
  label: string;
  selectedState: string | null;
  onSelectState: (state: string | null) => void;
}

export default function DivergenceScatter({
  centralities,
  measureKey,
  label,
  selectedState,
  onSelectState,
}: DivergenceScatterProps) {
  const rankKey = `rank_${measureKey}` as const;

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

  const [hovered, setHovered] = useState<string | null>(null);

  const diagX1 = PAD.left;
  const diagY1 = PAD.top;
  const diagX2 = PAD.left + INNER_W;
  const diagY2 = PAD.top + INNER_H;

  return (
    <div className="flex-1 min-w-0">
      <div className="text-xs font-medium text-center mb-1" style={{ color: "var(--text-secondary)" }}>
        {label}
      </div>
      <svg viewBox={`0 0 ${CHART_W} ${CHART_H}`} className="w-full h-auto">
        <line
          x1={diagX1} y1={diagY1} x2={diagX2} y2={diagY2}
          stroke="#d0d0d8" strokeWidth={1} strokeDasharray="3,3"
        />

        <text x={PAD.left + INNER_W / 2} y={CHART_H - 4} textAnchor="middle" fontSize={9} fill="var(--text-muted)">
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

        {hovered &&
          (() => {
            const p = points.find((pt) => pt.state === hovered);
            if (!p) return null;
            const tx = Math.min(p.x + 8, CHART_W - 90);
            const ty = Math.max(p.y - 8, 30);
            return (
              <g pointerEvents="none">
                <rect
                  x={tx - 2} y={ty - 12} width={88} height={32} rx={4}
                  fill="white" stroke="var(--border)" strokeWidth={0.5} opacity={0.95}
                />
                <text x={tx + 2} y={ty} fontSize={8} fontWeight={600} fill="var(--text-primary)">
                  {p.name}
                </text>
                <text x={tx + 2} y={ty + 12} fontSize={7.5} fill="var(--text-secondary)">
                  GDP #{p.gdp} → Net #{p.rank} ({p.delta > 0 ? "+" : ""}
                  {p.delta})
                </text>
              </g>
            );
          })()}
      </svg>
    </div>
  );
}
