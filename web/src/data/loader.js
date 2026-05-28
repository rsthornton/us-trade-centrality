const cache = new Map();

async function fetchJSON(path) {
  if (cache.has(path)) return cache.get(path);
  const res = await fetch(path);
  const data = await res.json();
  cache.set(path, data);
  return data;
}

export async function loadCentralities(networkType = "51") {
  return fetchJSON(`/data/centralities_${networkType}.json`);
}

export async function loadRankChanges() {
  return fetchJSON("/data/rank_changes.json");
}

export async function loadTopEdges() {
  return fetchJSON("/data/top_edges.json");
}

export async function loadNetworkStats() {
  return fetchJSON("/data/network_stats.json");
}

export async function loadMetadata() {
  return fetchJSON("/data/metadata.json");
}

export async function loadFiltration() {
  return fetchJSON("/data/filtration.json");
}

export async function loadCommodityCentralities() {
  return fetchJSON("/data/commodity_centralities.json");
}

export async function loadCommodityEdges(code) {
  return fetchJSON(`/data/commodity_edges/${code}.json`);
}

export async function loadTopoJSON() {
  return fetchJSON("/data/us-states-10m.json");
}

export async function loadAllCore() {
  const [centralities51, centralities52, rankChanges, topEdges, stats, metadata, topo] =
    await Promise.all([
      loadCentralities("51"),
      loadCentralities("52"),
      loadRankChanges(),
      loadTopEdges(),
      loadNetworkStats(),
      loadMetadata(),
      loadTopoJSON(),
    ]);

  return { centralities51, centralities52, rankChanges, topEdges, stats, metadata, topo };
}
