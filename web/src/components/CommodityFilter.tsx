import type { Metadata } from "../types";

const QUICK_PICKS = [
  { code: "all", label: "All" },
  { code: "01-05", label: "Agri" },
  { code: "15-19", label: "Energy" },
  { code: "35-38", label: "Mfg" },
];

interface CommodityFilterProps {
  selected: string;
  onSelect: (code: string) => void;
  metadata: Metadata | null;
}

export default function CommodityFilter({ selected, onSelect, metadata }: CommodityFilterProps) {
  const groups = metadata?.commodity_groups ?? {};
  const names = metadata?.sctg_names ?? {};

  const displayName = selected !== "all" && names[selected] ? names[selected] : null;

  return (
    <div className="flex flex-col gap-1.5">
      {/* Quick-select buttons */}
      <div className="flex gap-1.5">
        {QUICK_PICKS.map(({ code, label }) => {
          const active = selected === code;
          return (
            <button
              key={code}
              onClick={() => onSelect(code)}
              className="px-2.5 py-1 rounded text-xs font-medium cursor-pointer border transition-all duration-200"
              style={{
                backgroundColor: active ? "var(--accent-blue)" + "18" : "transparent",
                borderColor: active ? "var(--accent-blue)" : "var(--border)",
                color: active ? "var(--accent-blue)" : "var(--text-secondary)",
              }}
            >
              {label}
            </button>
          );
        })}
      </div>

      {/* Grouped commodity select */}
      <div className="flex items-center gap-2">
        <select
          value={selected}
          onChange={(e) => onSelect(e.target.value)}
          className="text-xs rounded border px-2 py-1 cursor-pointer min-w-[180px]"
          style={{
            backgroundColor: "var(--bg-surface)",
            borderColor: "var(--border)",
            color: "var(--text-primary)",
            outline: "none",
          }}
        >
          <option value="all">All Commodities</option>
          {Object.entries(groups).map(([groupName, codes]) => (
            <optgroup key={groupName} label={groupName}>
              {codes.map((code) => (
                <option key={code} value={code}>
                  {code} — {names[code] || code}
                </option>
              ))}
            </optgroup>
          ))}
        </select>

        {displayName && (
          <span
            className="text-xs font-medium truncate max-w-[160px]"
            style={{ color: "var(--accent-blue)" }}
            title={displayName}
          >
            {displayName}
          </span>
        )}
      </div>
    </div>
  );
}
