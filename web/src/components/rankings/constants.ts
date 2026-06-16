import type { Measure } from "../../types";

export const MEASURES: { key: Measure; label: string; short: string }[] = [
  { key: "eigenvector", label: "Eigenvector", short: "Eig" },
  { key: "betweenness", label: "Betweenness", short: "Bet" },
  { key: "out_degree", label: "Out-Degree", short: "Out" },
];
