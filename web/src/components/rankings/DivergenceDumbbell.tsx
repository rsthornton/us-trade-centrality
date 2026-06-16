import { useMemo } from "react";
import type { BaseCentralityRow, Measure } from "../../types";
import { MEASURES } from "./constants";

const W = 680;
const ROW_H = 26;
const TOP = 26; // axis label band
const LEFT = 70; // state label gutter
const RIGHT = 64; // delta gutter
const TOP_N = 14; // biggest movers shown

export interface DivergenceDumbbellProps {
  centralities: BaseCentralityRow[];
  measure: Measure;
  selectedState: string | null;
  onSelectState: (state: string | null) => void;
}

export default function DivergenceDumbbell({
  centralities,
  measure,
  selectedState,
  onSelectState,
}: DivergenceDumbbellProps) {
  const rankKey = `rank_${measure}` as const;
  const measureLabel = MEASURES.find((m) => m.key === measure)?.label ?? measure;

  const rows = useMemo(() => {
    const all = centralities.map((r) => ({
      state: r.state,
      name: r.state_name ?? r.state,
      gdp: r.gdp_rank,
      net: r[rankKey],
      delta: r.gdp_rank - r[rankKey], // > 0: network rank beats GDP rank (overperforms)
    }));
    // The N biggest movers, then ordered overperform → underperform.
    return all
      .slice()
      .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
      .slice(0, TOP_N)
      .sort((a, b) => b.delta - a.delta);
  }, [centralities, rankKey]);

  const H = TOP + rows.length * ROW_H + 6;
  const xScale = (rank: number) => LEFT + ((rank - 1) / 50) * (W - LEFT - RIGHT);
  const firstNeg = rows.findIndex((r) => r.delta < 0);

  const dirColor = (delta: number) =>
    delta > 0 ? "var(--accent-green)" : delta < 0 ? "var(--accent-red)" : "var(--text-muted)";

  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto">
        {/* rank axis hints */}
        <text x={xScale(1)} y={14} fontSize={9} fill="var(--text-muted)">
          rank #1
        </text>
        <text x={xScale(51)} y={14} fontSize={9} fill="var(--text-muted)" textAnchor="end">
          #51
        </text>
        <line
          x1={xScale(1)} y1={TOP - 6} x2={xScale(1)} y2={H - 4}
          stroke="var(--border)" strokeWidth={1} strokeDasharray="2,3"
        />
        <line
          x1={xScale(51)} y1={TOP - 6} x2={xScale(51)} y2={H - 4}
          stroke="var(--border)" strokeWidth={1} strokeDasharray="2,3"
        />

        {rows.map((r, i) => {
          const y = TOP + i * ROW_H + ROW_H / 2;
          const color = dirColor(r.delta);
          const isSel = r.state === selectedState;
          const gx = xScale(r.gdp);
          const nx = xScale(r.net);
          return (
            <g
              key={r.state}
              className="cursor-pointer"
              onClick={() => onSelectState(isSel ? null : r.state)}
            >
              <title>
                {r.name}: GDP #{r.gdp} → {measureLabel} #{r.net} ({r.delta > 0 ? "+" : ""}
                {r.delta})
              </title>
              {isSel && (
                <rect
                  x={0} y={y - ROW_H / 2} width={W} height={ROW_H}
                  fill="var(--map-selection)" opacity={0.12} rx={4}
                />
              )}
              <text
                x={LEFT - 10} y={y + 3} textAnchor="end" fontSize={11}
                fontWeight={isSel ? 700 : 500} fill="var(--text-primary)"
              >
                {r.state}
              </text>
              <line
                x1={gx} y1={y} x2={nx} y2={y}
                stroke={color} strokeWidth={2.5} strokeLinecap="round" opacity={0.5}
              />
              {/* GDP rank: hollow dot */}
              <circle cx={gx} cy={y} r={4} fill="var(--bg-secondary)" stroke="var(--text-muted)" strokeWidth={1.5} />
              {/* network rank: filled dot in the direction color */}
              <circle cx={nx} cy={y} r={4.5} fill={color} />
              <text
                x={W - RIGHT + 12} y={y + 3} fontSize={11} fontWeight={600} fill={color}
              >
                {r.delta > 0 ? `+${r.delta}` : r.delta}
              </text>
            </g>
          );
        })}

        {/* faint divider at the overperform / underperform crossover */}
        {firstNeg > 0 && (
          <line
            x1={LEFT - 30} y1={TOP + firstNeg * ROW_H} x2={W - RIGHT + 30} y2={TOP + firstNeg * ROW_H}
            stroke="var(--border)" strokeWidth={1}
          />
        )}
      </svg>

      <div
        className="flex items-center gap-4 mt-2 text-xs flex-wrap"
        style={{ color: "var(--text-muted)" }}
      >
        <span className="inline-flex items-center gap-1.5">
          <span
            className="inline-block w-2.5 h-2.5 rounded-full"
            style={{ background: "var(--bg-secondary)", border: "1.5px solid var(--text-muted)" }}
          />
          GDP rank
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="inline-block w-2.5 h-2.5 rounded-full" style={{ background: "var(--text-secondary)" }} />
          {measureLabel} rank
        </span>
        <span style={{ color: "var(--accent-green)" }}>▲ above GDP weight</span>
        <span style={{ color: "var(--accent-red)" }}>▼ below GDP weight</span>
      </div>
    </div>
  );
}
