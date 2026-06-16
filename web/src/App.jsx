import { useState, useEffect, useMemo } from "react";
import { loadAllCore, loadCommodityCentralities, loadCommodityEdges } from "./data/loader";
import { topoFeature } from "./lib/topo";
import TradeMap from "./components/TradeMap";
import CentralityPills from "./components/CentralityPills";
import CommodityFilter from "./components/CommodityFilter";
import ColorLegend from "./components/ColorLegend";
import RankingsTable from "./components/RankingsTable";
import StateDrawer from "./components/StateDrawer";

// Interactive WASM notebook hosted on molab (marimo Cloud).
const NOTEBOOK_URL =
  "https://molab.marimo.io/notebooks/nb_ssAp6xhuFRsEaQKP2y7ZjH/app";

export default function App() {
  const [data, setData] = useState(null);
  const [measure, setMeasure] = useState("eigenvector");
  const [selectedState, setSelectedState] = useState(null);
  const [networkType, setNetworkType] = useState("51");
  const [showEdges, setShowEdges] = useState(true);
  const [topN, setTopN] = useState(50);
  const [flowDirection, setFlowDirection] = useState("both");
  const [commodity, setCommodity] = useState("all");
  const [commodityCentralities, setCommodityCentralities] = useState(null);
  const [commodityEdges, setCommodityEdges] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAllCore().then((d) => {
      setData(d);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    if (commodity === "all") {
      setCommodityCentralities(null);
      setCommodityEdges(null);
      return;
    }
    loadCommodityCentralities().then((all) => {
      const filtered = all.filter((r) => r.commodity_code === commodity);
      setCommodityCentralities(filtered);
    });
    loadCommodityEdges(commodity).then(setCommodityEdges);
  }, [commodity]);

  const geojson = useMemo(() => {
    if (!data?.topo) return null;
    return topoFeature(data.topo, "states");
  }, [data?.topo]);

  const centralities = useMemo(() => {
    if (!data) return [];
    if (commodity !== "all" && commodityCentralities) return commodityCentralities;
    return networkType === "51" ? data.centralities51 : data.centralities52;
  }, [data, networkType, commodity, commodityCentralities]);

  // Full weight-sorted edge set (topEdges is pre-sorted; sort commodity edges to be safe).
  const allEdges = useMemo(() => {
    const raw = (commodity !== "all" && commodityEdges) ? commodityEdges : (data?.topEdges || []);
    return [...raw].sort((a, b) => b.weight - a.weight);
  }, [data, commodity, commodityEdges]);

  // Top-N slice actually drawn / explored.
  const edges = useMemo(() => allEdges.slice(0, topN), [allEdges, topN]);

  const selectedData = useMemo(() => {
    if (!selectedState || !centralities.length) return null;
    return centralities.find((r) => r.state === selectedState);
  }, [selectedState, centralities]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div
          className="text-sm font-mono tracking-widest uppercase"
          style={{ color: "var(--text-muted)" }}
        >
          Loading network data...
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen relative">
      <header className="px-6 pt-6 pb-2">
        <h1
          className="text-3xl font-light tracking-tight"
          style={{ color: "var(--text-primary)" }}
        >
          US Interstate Trade Centrality
        </h1>
        <p
          className="text-sm mt-1 max-w-xl"
          style={{ color: "var(--text-secondary)" }}
        >
          The map shows what GDP cannot — which states hold structural power in
          the $4 trillion interstate trade network.
        </p>
        <a
          href={NOTEBOOK_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block text-sm mt-2 font-medium transition-opacity hover:opacity-70"
          style={{ color: "var(--accent-blue)" }}
        >
          Explore the Math →
        </a>
      </header>

      <div className="px-6 py-3 flex items-center gap-4 flex-wrap">
        <CentralityPills selected={measure} onSelect={setMeasure} />

        <CommodityFilter
          selected={commodity}
          onSelect={(code) => {
            setCommodity(code);
            if (code !== "all") setNetworkType("51");
          }}
          metadata={data.metadata}
        />

        <div className="flex items-center gap-2 ml-auto">
          <button
            onClick={() => setNetworkType(networkType === "51" ? "52" : "51")}
            disabled={commodity !== "all"}
            className="px-3 py-1.5 rounded text-xs font-mono cursor-pointer border transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            style={{
              borderColor: "var(--border)",
              color: "var(--text-secondary)",
              backgroundColor: "transparent",
            }}
          >
            {networkType === "51" ? "51×51 Domestic" : "52×52 + Intl"}
          </button>

          <button
            onClick={() => setShowEdges(!showEdges)}
            className="px-3 py-1.5 rounded text-xs font-mono cursor-pointer border transition-colors"
            style={{
              borderColor: showEdges ? "var(--accent-blue)" : "var(--border)",
              color: showEdges ? "var(--accent-blue)" : "var(--text-secondary)",
              backgroundColor: showEdges ? "var(--accent-blue)" + "15" : "transparent",
            }}
          >
            {showEdges ? "Flows On" : "Flows Off"}
          </button>
        </div>
      </div>

      {showEdges && (
        <div className="px-6 pb-3 flex items-center gap-5 flex-wrap text-xs" style={{ color: "var(--text-secondary)" }}>
          {/* Top-N slider */}
          <label className="flex items-center gap-2">
            <span className="font-mono uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
              Top flows
            </span>
            <input
              type="range"
              min={Math.min(10, allEdges.length || 10)}
              max={Math.max(allEdges.length, 10)}
              step={10}
              value={Math.min(topN, allEdges.length)}
              onChange={(e) => setTopN(Number(e.target.value))}
              className="cursor-pointer"
              style={{ accentColor: "var(--accent-blue)", width: "140px" }}
            />
            <span className="font-mono tabular-nums" style={{ color: "var(--accent-blue)" }}>
              {Math.min(topN, allEdges.length)}
            </span>
          </label>

          {/* Flow-direction filter (applies when a state is selected) */}
          <div className="flex items-center gap-1.5">
            <span className="font-mono uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
              Direction
            </span>
            {[
              { code: "both", label: "Both" },
              { code: "in", label: "Inbound" },
              { code: "out", label: "Outbound" },
            ].map(({ code, label }) => {
              const active = flowDirection === code;
              return (
                <button
                  key={code}
                  onClick={() => setFlowDirection(code)}
                  className="px-2.5 py-1 rounded text-xs font-medium cursor-pointer border transition-all duration-200"
                  style={{
                    backgroundColor: active ? "var(--accent-blue)" + "18" : "transparent",
                    borderColor: active ? "var(--accent-blue)" : "var(--border)",
                    color: active ? "var(--accent-blue)" : "var(--text-secondary)",
                  }}
                >
                  {label}
                </button>
              );
            })}
            {!selectedState && (
              <span className="ml-1" style={{ color: "var(--text-muted)" }}>
                — select a state to apply
              </span>
            )}
          </div>
        </div>
      )}

      <div className="px-6 relative">
        <TradeMap
          geojson={geojson}
          centralities={centralities}
          measure={measure}
          selectedState={selectedState}
          onSelectState={setSelectedState}
          edges={edges}
          showEdges={showEdges}
          flowDirection={flowDirection}
        />

        {selectedState && selectedData && (
          <div
            className="absolute right-6 top-0 w-80 overflow-y-auto rounded-lg"
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--border)",
              boxShadow: "-4px 0 24px rgba(0,0,0,0.12)",
              maxHeight: "62vh",
            }}
          >
            <StateDrawer
              state={selectedState}
              data={selectedData}
              edges={edges}
              onClose={() => setSelectedState(null)}
              inline
            />
          </div>
        )}
      </div>

      <div className="px-6 py-1 flex items-center justify-between">
        <ColorLegend
          label={measure.replace("_", " ")}
          min={centralities.length ? Math.min(...centralities.map((r) => r[measure])) : 0}
          max={centralities.length ? Math.max(...centralities.map((r) => r[measure])) : 1}
        />
        {data.stats && (
          <div className="flex gap-6 text-xs font-mono" style={{ color: "var(--text-muted)" }}>
            <span>{data.stats.nodes} nodes</span>
            <span>{data.stats.edges.toLocaleString()} edges</span>
            <span>density {data.stats.density}</span>
          </div>
        )}
      </div>

      <RankingsTable
        centralities={centralities}
        measure={measure}
        selectedState={selectedState}
        onSelectState={setSelectedState}
      />

    </div>
  );
}
