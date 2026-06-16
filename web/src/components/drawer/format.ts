/** Compact USD formatting shared across drawer cards and partner lists. */
export function formatDollars(raw: number): string {
  const b = raw / 1e9;
  if (b >= 1000) return `$${(b / 1000).toFixed(1)}T`;
  if (b >= 1) return `$${b.toFixed(1)}B`;
  const m = raw / 1e6;
  if (m >= 1) return `$${m.toFixed(0)}M`;
  return `$${(raw / 1e3).toFixed(0)}K`;
}

export interface Partner {
  partner: string;
  weight: number;
}
