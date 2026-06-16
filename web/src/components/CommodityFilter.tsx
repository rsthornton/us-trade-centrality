import { Select, SegmentedControl } from "./ui";
import type { SelectGroup, SegmentOption } from "./ui";
import type { Metadata } from "../types";

const QUICK_PICKS: SegmentOption<string>[] = [
  { value: "all", label: "All" },
  { value: "01-05", label: "Agri" },
  { value: "15-19", label: "Energy" },
  { value: "35-38", label: "Mfg" },
];

interface CommodityFilterProps {
  selected: string;
  onSelect: (code: string) => void;
  metadata: Metadata | null;
}

export default function CommodityFilter({ selected, onSelect, metadata }: CommodityFilterProps) {
  const groupsObj = metadata?.commodity_groups ?? {};
  const names = metadata?.sctg_names ?? {};

  const groups: SelectGroup[] = Object.entries(groupsObj).map(([groupName, codes]) => ({
    label: groupName,
    options: codes.map((code) => ({ value: code, label: `${code} — ${names[code] || code}` })),
  }));

  const displayName = selected !== "all" && names[selected] ? names[selected] : null;

  return (
    <div className="flex flex-col gap-1.5">
      <SegmentedControl options={QUICK_PICKS} value={selected} onChange={onSelect} />

      <div className="flex items-center gap-2">
        <Select
          value={selected}
          onChange={onSelect}
          leadingOption={{ value: "all", label: "All Commodities" }}
          groups={groups}
        />

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
