import { Select, SegmentedControl } from "./ui";
import type { SelectGroup } from "./ui";
import type { Metadata } from "../types";
import { QUICK_PICKS, quickPickFor } from "../lib/commodity";


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
    options: codes.map((code) => ({ value: code, label: `${names[code] || code} (${code})` })),
  }));

  return (
    <div className="flex flex-col gap-2">
      <SegmentedControl
        options={QUICK_PICKS}
        value={quickPickFor(selected)}
        onChange={onSelect}
        size="sm"
      />
      <Select
        value={selected}
        onChange={onSelect}
        leadingOption={{ value: "all", label: "All commodities" }}
        groups={groups}
        className="w-full"
      />
    </div>
  );
}
