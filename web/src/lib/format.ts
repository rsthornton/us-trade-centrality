/** 1 → "1st", 22 → "22nd", 13 → "13th". */
export function ordinal(n: number): string {
  const tens = n % 100;
  if (tens >= 11 && tens <= 13) return `${n}th`;
  const suffix = { 1: "st", 2: "nd", 3: "rd" }[n % 10] ?? "th";
  return `${n}${suffix}`;
}

/** Centrality score to three decimals, without printing a positive score as zero. */
export function formatScore(value: number): string {
  if (value === 0) return "0";
  if (value < 0.001) return "<0.001";
  return value.toFixed(3);
}
