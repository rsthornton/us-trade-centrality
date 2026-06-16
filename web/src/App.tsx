import { useState, useEffect, useMemo, lazy, Suspense } from "react";
import { loadAllCore, loadCommodityCentralities, loadCommodityEdges } from "./data/loader";
import { topoFeature } from "./lib/topo";
import { MEASURE_COLORS } from "./lib/colors";
import TradeMap from "./components/TradeMap";
import CentralityPills from "./components/CentralityPills";
import CommodityFilter from "./components/CommodityFilter";
import ColorLegend from "./components/ColorLegend";
import DivergenceView from "./components/rankings/DivergenceView";
import StateDrawer from "./components/drawer/StateDrawer";
import Wordmark from "./components/brand/Wordmark";
import Footer from "./components/Footer";
import { Button, SegmentedControl, Slider } from "./components/ui";
import OrientationHint from "./components/OrientationHint";
import { readInitialUrlState, useSyncUrlState } from "./hooks/useUrlState";
import type {
  BaseCentralityRow,
  CommodityCentralityRow,
  CoreData,
  Edge,
  Measure,
} from "./types";

// Interactive WASM notebook hosted on molab (marimo Cloud).
const NOTEBOOK_URL = "https://molab.marimo.io/notebooks/nb_ssAp6xhuFRsEaQKP2y7ZjH/app";
const REPO_URL = "https://github.com/rsthornton/us-trade-centrality";

// DEV-only component gallery (lazy: its chunk is never loaded in production).
const Gallery = import.meta.env.DEV ? lazy(() => import("./dev/Gallery")) : null;

type NetworkType = "51" | "52";
type FlowDirection = "both" | "in" | "out";
type View = "map" | "divergence";

export default function App() {
  const [data, setData] = useState<CoreData | null>(null);
  const [view, setView] = useState<View>("map");
  const [measure, setMeasure] = useState<Measure>(
    () => readInitialUrlState().measure ?? "eigenvector",
  );
  const [selectedState, setSelectedState] = useState<string | null>(
    () => readInitialUrlState().state,
  );
  const [networkType, setNetworkType] = useState<NetworkType>("51");
  const [showEdges, setShowEdges] = useState(true);
  const [topN, setTopN] = useState(50);
  const [flowDirection, setFlowDirection] = useState<FlowDirection>("both");
  const [commodity, setCommodity] = useState("all");
  const [commodityCentralities, setCommodityCentralities] = useState<
    CommodityCentralityRow[] | null
  >(null);
  const [commodityEdges, setCommodityEdges] = useState<Edge[] | null>(null);
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

  const centralities = useMemo<BaseCentralityRow[]>(() => {
    if (!data) return [];
    if (commodity !== "all" && commodityCentralities) return commodityCentralities;
    return networkType === "51" ? data.centralities51 : data.centralities52;
  }, [data, networkType, commodity, commodityCentralities]);

  // Full weight-sorted edge set (topEdges is pre-sorted; sort commodity edges to be safe).
  const allEdges = useMemo<Edge[]>(() => {
    const raw = commodity !== "all" && commodityEdges ? commodityEdges : (data?.topEdges ?? []);
    return [...raw].sort((a, b) => b.weight - a.weight);
  }, [data, commodity, commodityEdges]);

  // Top-N slice actually drawn / explored.
  const edges = useMemo(() => allEdges.slice(0, topN), [allEdges, topN]);

  const selectedData = useMemo(() => {
    if (!selectedState || !centralities.length) return null;
    return centralities.find((r) => r.state === selectedState) ?? null;
  }, [selectedState, centralities]);

  // True per-state totals (all-commodity view only); commodity view falls back to
  // the visible commodity edges inside the drawer.
  const selectedTotals = useMemo(() => {
    if (!selectedState || commodity !== "all" || !data) return null;
    return data.stateTotals.find((t) => t.state === selectedState) ?? null;
  }, [selectedState, commodity, data]);

  useSyncUrlState(selectedState, measure);

  // The active measure's hue threads through the UI (canvas top accent, etc.).
  const measureColor = MEASURE_COLORS[measure];
  const stageStyle: React.CSSProperties = {
    background: "linear-gradient(180deg, var(--canvas-from), var(--canvas-to))",
    border: "1px solid var(--hairline)",
    borderTop: `2.5px solid ${measureColor}`,
    borderRadius: "var(--radius-card)",
    boxShadow: "0 1px 2px rgba(26, 26, 46, 0.05)",
  };

  if (Gallery && location.hash === "#/components") {
    return (
      <Suspense fallback={null}>
        <Gallery />
      </Suspense>
    );
  }

  if (loading || !data) {
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
    <div className="min-h-screen">
     <div className="mx-auto w-full max-w-[1240px]">
      <header className="px-6 pt-5">
        <div
          className="flex items-center justify-between gap-4 pb-4"
          style={{ borderBottom: "1px solid var(--border)" }}
        >
          <Wordmark />
          <nav className="flex items-center gap-5 text-sm">
            <a
              href={NOTEBOOK_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium transition-opacity hover:opacity-70"
              style={{ color: "var(--accent-blue)" }}
            >
              Explore the math →
            </a>
            <a
              href={REPO_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="transition-opacity hover:opacity-70"
              style={{ color: "var(--text-secondary)" }}
            >
              Source
            </a>
          </nav>
        </div>

        <div className="pt-6 pb-1">
          <div
            className="text-xs font-mono uppercase tracking-[0.18em] mb-2"
            style={{ color: "var(--text-muted)" }}
          >
            Structural power in U.S. interstate trade · CFS 2017
          </div>
          <h1
            className="text-3xl sm:text-4xl font-light tracking-tight"
            style={{
              backgroundImage: "linear-gradient(115deg, #1a1a2e 30%, #463080 75%, #6a3aa8 100%)",
              WebkitBackgroundClip: "text",
              backgroundClip: "text",
              color: "transparent",
              width: "fit-content",
            }}
          >
            The Interstate Power Observatory
          </h1>
          <p
            className="text-sm sm:text-base mt-2 max-w-2xl leading-relaxed"
            style={{ color: "var(--text-secondary)" }}
          >
            GDP measures what a state produces. Network centrality reveals the leverage it holds.
            Explore which states are the true hubs, bridges, and exporters of America's $4 trillion
            interstate commerce network.
          </p>
        </div>
      </header>

      <div className="px-6 pt-5">
        <SegmentedControl
          size="lg"
          options={[
            { value: "map", label: "Map" },
            { value: "divergence", label: "Divergence" },
          ]}
          value={view}
          onChange={setView}
        />
      </div>

      <div className="px-6 pt-4 pb-3 flex items-center gap-3 flex-wrap">
        <CentralityPills selected={measure} onSelect={setMeasure} />

        <CommodityFilter
          selected={commodity}
          onSelect={(code) => {
            setCommodity(code);
            if (code !== "all") setNetworkType("51");
          }}
          metadata={data.metadata}
        />

        {view === "map" && (
          <div className="flex items-center gap-1 ml-auto">
            <Button
              variant="ghost"
              size="sm"
              mono
              disabled={commodity !== "all"}
              onClick={() => setNetworkType(networkType === "51" ? "52" : "51")}
            >
              {networkType === "51" ? "51×51 Domestic" : "52×52 + Intl"}
            </Button>

            <Button
              variant="ghost"
              size="sm"
              mono
              active={showEdges}
              onClick={() => setShowEdges(!showEdges)}
            >
              {showEdges ? "Flows On" : "Flows Off"}
            </Button>
          </div>
        )}
      </div>

      {view === "map" && showEdges && (
        <div
          className="px-6 pb-3 flex items-center gap-5 flex-wrap text-xs"
          style={{ color: "var(--text-secondary)" }}
        >
          {/* Top-N slider */}
          <label className="flex items-center gap-2">
            <span className="font-mono uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
              Top flows
            </span>
            <Slider
              min={Math.min(10, allEdges.length || 10)}
              max={Math.max(allEdges.length, 10)}
              step={10}
              value={Math.min(topN, allEdges.length)}
              onChange={setTopN}
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
            <SegmentedControl
              size="sm"
              options={[
                { value: "both", label: "Both" },
                { value: "in", label: "Inbound" },
                { value: "out", label: "Outbound" },
              ]}
              value={flowDirection}
              onChange={setFlowDirection}
            />
            {!selectedState && (
              <span className="ml-1" style={{ color: "var(--text-muted)" }}>
                select a state to apply
              </span>
            )}
          </div>
        </div>
      )}

      {view === "map" ? (
        <div className="px-6">
          <div className="px-4 pt-4 pb-3" style={stageStyle}>
            <div className="relative">
              {!selectedState && <OrientationHint />}
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
                  className="absolute right-0 top-0 w-80 overflow-y-auto"
                  style={{
                    backgroundColor: "var(--bg-secondary)",
                    border: "1px solid var(--border)",
                    borderRadius: "var(--radius-card)",
                    boxShadow: "var(--shadow-drawer)",
                    maxHeight: "62vh",
                  }}
                >
                  <StateDrawer
                    state={selectedState}
                    data={selectedData}
                    edges={edges}
                    totals={selectedTotals}
                    onClose={() => setSelectedState(null)}
                    inline
                  />
                </div>
              )}
            </div>

            <div
              className="flex items-center justify-between mt-2 pt-2"
              style={{ borderTop: "1px solid var(--hairline)" }}
            >
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
          </div>
        </div>
      ) : (
        <DivergenceView
          centralities={centralities}
          measure={measure}
          selectedState={selectedState}
          onSelectState={setSelectedState}
          accent={measureColor}
        />
      )}

      <Footer />
     </div>
    </div>
  );
}
