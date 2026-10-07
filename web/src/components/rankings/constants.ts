import type { Measure } from "../../types";

export const MEASURES: { key: Measure; label: string; short: string }[] = [
  { key: "eigenvector", label: "Trade prestige", short: "Eig" },
  { key: "betweenness", label: "Bridge position", short: "Bet" },
  { key: "out_degree", label: "Export reach", short: "Out" },
];
