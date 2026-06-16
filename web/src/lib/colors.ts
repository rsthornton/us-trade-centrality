/**
 * Color scales for centrality visualization.
 * Viridis is perceptually uniform and colorblind-safe; PRGn is the divergence scale.
 */

import type { Measure } from "../types";

const VIRIDIS = [
  "#440154", "#46085c", "#471164", "#481a6c", "#482273", "#472a7a",
  "#453282", "#433a83", "#404387", "#3d4d8a", "#39558c", "#355e8d",
  "#31688e", "#2d708e", "#29798e", "#26818e", "#228a8d", "#1f938c",
  "#1f9d89", "#20a486", "#25ab82", "#2eb37c", "#3bbb75", "#4cc26c",
  "#5ec962", "#73d056", "#88d44a", "#9dd93a", "#b5de2b", "#cce11f",
  "#e5e419", "#fde725",
];

const PRGN = [
  "#40004b", "#5e0066", "#762a83", "#8e4ca0", "#9f73ab", "#b8a5c9",
  "#d2c7df", "#e8e0ef", "#f7f7f7",
  "#d5ecd4", "#a6dba0", "#73c378", "#4dac26", "#2d8e00", "#1b7837",
  "#00641a", "#005000",
];

export function interpolateViridis(t: number): string {
  const i = Math.max(0, Math.min(VIRIDIS.length - 1, Math.floor(t * (VIRIDIS.length - 1))));
  return VIRIDIS[i];
}

export function interpolateDivergence(t: number): string {
  const i = Math.max(0, Math.min(PRGN.length - 1, Math.floor(t * (PRGN.length - 1))));
  return PRGN[i];
}

export function centralityToColor(value: number, min: number, max: number): string {
  if (max === min) return VIRIDIS[VIRIDIS.length >> 1];
  const t = (value - min) / (max - min);
  return interpolateViridis(t);
}

export function divergenceToColor(rankDiff: number, maxAbs: number): string {
  if (maxAbs === 0) return PRGN[PRGN.length >> 1];
  const t = (rankDiff / maxAbs + 1) / 2;
  return interpolateDivergence(t);
}

export const MEASURE_COLORS: Record<Measure, string> = {
  eigenvector: "#44cc88",
  betweenness: "#4488ff",
  out_degree: "#ff9944",
};
