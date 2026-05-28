import { useState, useEffect, useMemo } from "react";
import { loadAllCore, loadCommodityCentralities, loadCommodityEdges } from "./data/loader";
import { topoFeature } from "./lib/topo";
import TradeMap from "./components/TradeMap";
import CentralityPills from "./components/CentralityPills";
import CommodityFilter from "./components/CommodityFilter";
import ColorLegend from "./components/ColorLegend";
import RankingsTable from "./components/RankingsTable";
import StateDrawer from "./components/StateDrawer";

export default function App() {
  const [data, setData] = useState(null);
  const [measure, setMeasure] = useState("eigenvector");
  const [selectedState, setSelectedState] = useState(null);
  const [networkType, setNetworkType] = useState("51");
  const [showEdges, setShowEdges] = useState(true);
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

  const edges = useMemo(() => {
    if (commodity !== "all" && commodityEdges) return commodityEdges;
    return data?.topEdges || [];
  }, [data, commodity, commodityEdges]);

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

      <div className="px-6 relative">
        <TradeMap
          geojson={geojson}
          centralities={centralities}
          measure={measure}
          selectedState={selectedState}
          onSelectState={setSelectedState}
          edges={edges}
          showEdges={showEdges}
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
              measure={measure}
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
