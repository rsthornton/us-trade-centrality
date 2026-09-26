/**
 * Color scales for centrality visualization.
 * Cividis is perceptually uniform and colorblind-safe; BrBG is the divergence scale.
 */

import type { Measure } from "../types";

const CIVIDIS = [
  "#00224e", "#00285b", "#002e6a", "#053371", "#1c396f", "#293f6e",
  "#33446d", "#3c4a6c", "#45506c", "#4d556c", "#555b6d", "#5c616e",
  "#646770", "#6b6d72", "#727274", "#787877", "#807f78", "#888578",
  "#908b78", "#979177", "#a09875", "#a89e73", "#b0a571", "#b9ab6d",
  "#c2b369", "#cbb965", "#d3c05f", "#dcc859", "#e6d051", "#efd748",
  "#f8df3c", "#fee838",
];

const BRBG = [
  "#543005", "#774508", "#995d13", "#b97b29", "#cfa256", "#e2c787",
  "#f1dfb3", "#f6edd7",
  "#f4f5f5",
  "#d7eeeb", "#b4e2db", "#87d0c5", "#58b0a7", "#2d8f87", "#0c7169",
  "#01554b", "#003c30",
];

export function interpolateSequential(t: number): string {
  const i = Math.max(0, Math.min(CIVIDIS.length - 1, Math.floor(t * (CIVIDIS.length - 1))));
  return CIVIDIS[i];
}

export function interpolateDivergence(t: number): string {
  const i = Math.max(0, Math.min(BRBG.length - 1, Math.floor(t * (BRBG.length - 1))));
  return BRBG[i];
}

export function centralityToColor(value: number, min: number, max: number): string {
  if (max === min) return CIVIDIS[CIVIDIS.length >> 1];
  const t = (value - min) / (max - min);
  return interpolateSequential(t);
}

export function divergenceToColor(rankDiff: number, maxAbs: number): string {
  if (maxAbs === 0) return BRBG[BRBG.length >> 1];
  const t = (rankDiff / maxAbs + 1) / 2;
  return interpolateDivergence(t);
}

export const MEASURE_COLORS: Record<Measure, string> = {
  eigenvector: "#44cc88",
  betweenness: "#4488ff",
  out_degree: "#ff9944",
};
