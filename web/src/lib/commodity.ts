import type { SegmentOption } from "../components/ui";

export const QUICK_PICKS: SegmentOption<string>[] = [
  { value: "all", label: "All" },
  { value: "01-05", label: "Agriculture" },
  { value: "15-19", label: "Energy" },
  { value: "35-38", label: "Machinery" },
];

/** The quick-pick that covers a commodity, so a single code chosen in the
 *  dropdown still lights its group (e.g. 02 lights Agriculture). */
export function quickPickFor(code: string): string {
  if (QUICK_PICKS.some((q) => q.value === code)) return code;
  const n = Number(code);
  if (!Number.isFinite(n) || code.includes("-")) return "";
  for (const { value } of QUICK_PICKS) {
    const [lo, hi] = value.split("-").map(Number);
    if (hi !== undefined && n >= lo && n <= hi) return value;
  }
  return "";
}
