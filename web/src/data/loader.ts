import type {
  CentralityRow,
  CommodityCentralityRow,
  CoreData,
  Edge,
  Metadata,
  NetworkStats,
  RankChange,
  StateTotals,
  TopoTopology,
} from "../types";

const cache = new Map<string, unknown>();

async function fetchJSON<T>(path: string): Promise<T> {
  if (cache.has(path)) return cache.get(path) as T;
  const res = await fetch(path);
  const data = (await res.json()) as T;
  cache.set(path, data);
  return data;
}

export function loadCentralities(networkType: "51" | "52" = "51"): Promise<CentralityRow[]> {
  return fetchJSON(`/data/centralities_${networkType}.json`);
}

export function loadRankChanges(): Promise<RankChange[]> {
  return fetchJSON("/data/rank_changes.json");
}

export function loadTopEdges(): Promise<Edge[]> {
  return fetchJSON("/data/top_edges.json");
}

export function loadNetworkStats(): Promise<NetworkStats> {
  return fetchJSON("/data/network_stats.json");
}

export function loadMetadata(): Promise<Metadata> {
  return fetchJSON("/data/metadata.json");
}

export function loadFiltration(): Promise<unknown> {
  return fetchJSON("/data/filtration.json");
}

export function loadCommodityCentralities(): Promise<CommodityCentralityRow[]> {
  return fetchJSON("/data/commodity_centralities.json");
}

export function loadCommodityEdges(code: string): Promise<Edge[]> {
  return fetchJSON(`/data/commodity_edges/${code}.json`);
}

export function loadTopoJSON(): Promise<TopoTopology> {
  return fetchJSON("/data/us-states-10m.json");
}

export function loadStateTotals(): Promise<StateTotals[]> {
  return fetchJSON("/data/state_trade_totals.json");
}

export async function loadAllCore(): Promise<CoreData> {
  const [centralities51, centralities52, rankChanges, topEdges, stats, metadata, topo, stateTotals] =
    await Promise.all([
      loadCentralities("51"),
      loadCentralities("52"),
      loadRankChanges(),
      loadTopEdges(),
      loadNetworkStats(),
      loadMetadata(),
      loadTopoJSON(),
      loadStateTotals(),
    ]);

  return {
    centralities51,
    centralities52,
    rankChanges,
    topEdges,
    stats,
    metadata,
    topo,
    stateTotals,
  };
}
