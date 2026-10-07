import { useMemo, useState } from "react";
import type { BaseCentralityRow, Measure } from "../../types";
import { MEASURES } from "./constants";
import { tint } from "../ui/style";
import { hasRank } from "../../lib/ranks";

export interface DivergenceTableProps {
  centralities: BaseCentralityRow[];
  measure: Measure;
  selectedState: string | null;
  onSelectState: (state: string | null) => void;
}

export default function DivergenceTable({
  centralities,
  measure,
  selectedState,
  onSelectState,
}: DivergenceTableProps) {
  const rankKey = `rank_${measure}` as const;
  const [ascending, setAscending] = useState(false);

  const rows = useMemo(() => {
    return centralities
      .map((r) => ({
        state: r.state,
        name: r.state_name,
        gdp: r.gdp_rank,
        rank: r[rankKey],
        delta: r.gdp_rank - r[rankKey],
        isZero: !hasRank(r, measure),
        value: r[measure],
      }))
      .sort((a, b) => (ascending ? a.delta - b.delta : b.delta - a.delta));
  }, [centralities, rankKey, measure, ascending]);

  const measureLabel = MEASURES.find((m) => m.key === measure)?.label || measure;

  return (
    <div className="mt-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
          {measureLabel} rank and GDP rank, all states
        </span>
        <button
          onClick={() => setAscending(!ascending)}
          className="text-xs cursor-pointer px-2 py-0.5 rounded border"
          style={{ borderColor: "var(--border)", color: "var(--text-secondary)", background: "transparent" }}
        >
          {ascending ? "Lower than GDP first" : "Higher than GDP first"}
        </button>
      </div>
      <div style={{ maxHeight: 480, overflowY: "auto" }}>
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
                Network
              </th>
              <th className="text-right text-xs py-1.5 pl-2 sticky top-0 font-mono" style={{ color: "var(--text-muted)", background: "var(--bg-primary)", fontWeight: 500 }}>
                Gap
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => {
              const isSelected = r.state === selectedState;
              const deltaColor =
                r.delta >= 5
                  ? "var(--gap-above)"
                  : r.delta <= -5
                    ? "var(--gap-below)"
                    : "var(--text-muted)";
              const rowBg = isSelected
                ? "rgba(255, 169, 77, 0.14)"
                : r.delta >= 5
                  ? tint("var(--gap-above)", 10)
                  : r.delta <= -5
                    ? tint("var(--gap-below)", 10)
                    : "transparent";
              return (
                <tr
                  key={r.state}
                  className="cursor-pointer"
                  onClick={() => onSelectState(isSelected ? null : r.state)}
                  style={{ backgroundColor: rowBg }}
                  onMouseEnter={(e) => {
                    if (!isSelected) e.currentTarget.style.backgroundColor = "var(--bg-surface)";
                  }}
                  onMouseLeave={(e) => {
                    if (!isSelected) e.currentTarget.style.backgroundColor = rowBg;
                  }}
                >
                  <td className="text-sm py-1 pr-3" style={{ color: "var(--text-primary)" }}>
                    {r.name}
                    <span className="font-mono text-xs ml-1.5" style={{ color: "var(--text-muted)" }}>
                      {r.state}
                    </span>
                  </td>
                  <td className="text-right font-mono text-sm py-1 px-2" style={{ color: "var(--text-secondary)" }}>
                    {r.gdp}
                  </td>
                  <td
                    className="text-right font-mono text-sm py-1 px-2"
                    style={{ color: r.isZero ? "var(--text-muted)" : "var(--text-secondary)" }}
                  >
                    {r.isZero ? "none" : r.rank}
                  </td>
                  <td className="text-right font-mono text-sm font-semibold py-1 pl-2" style={{ color: deltaColor }}>
                    {r.isZero ? "\u2013" : r.delta > 0 ? `+${r.delta}` : `\u2212${Math.abs(r.delta)}`}
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
