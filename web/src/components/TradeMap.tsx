import { useEffect, useMemo, useState } from "react";
import { geoToSvgPaths, projectPoint, MAP_WIDTH, MAP_HEIGHT } from "../lib/geo";
import { centralityToColor } from "../lib/colors";
import Tooltip from "./ui/Tooltip";
import { mapColors } from "../tokens";
import type { BaseCentralityRow, Edge, FeatureCollection, Measure } from "../types";

interface HoverInfo {
  name: string;
  rank: number | null;
  gdpRank: number | null;
  x: number;
  y: number;
}

const MEASURE_LABEL: Record<Measure, string> = {
  betweenness: "Bridge rank",
  eigenvector: "Prestige rank",
  out_degree: "Export rank",
};

const FIPS_TO_ABBR: Record<string, string> = {
  "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA",
  "08": "CO", "09": "CT", "10": "DE", "11": "DC", "12": "FL",
  "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN",
  "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME",
  "24": "MD", "25": "MA", "26": "MI", "27": "MN", "28": "MS",
  "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH",
  "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND",
  "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI",
  "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT",
  "50": "VT", "51": "VA", "53": "WA", "54": "WV", "55": "WI",
  "56": "WY",
};

const EXCLUDED_FIPS = new Set(["60", "66", "69", "72", "78"]);

type FlowDirection = "both" | "in" | "out";

interface TradeMapProps {
  geojson: FeatureCollection | null;
  centralities: BaseCentralityRow[];
  measure: Measure;
  selectedState: string | null;
  onSelectState: (state: string | null) => void;
  edges: Edge[];
  showEdges: boolean;
  flowDirection?: FlowDirection;
  /** Active measure hue (used for the hover outline). */
  accent: string;
}

export default function TradeMap({
  geojson,
  centralities,
  measure,
  selectedState,
  onSelectState,
  edges,
  showEdges,
  flowDirection = "both",
  accent,
}: TradeMapProps) {
  const [hoveredState, setHoveredState] = useState<string | null>(null);
  const [hoverInfo, setHoverInfo] = useState<HoverInfo | null>(null);

  // ESC key dismisses selection
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape" && selectedState) {
        onSelectState(null);
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [selectedState, onSelectState]);

  const paths = useMemo(() => {
    if (!geojson) return {};
    return geoToSvgPaths(geojson);
  }, [geojson]);

  const centralityMap = useMemo(() => {
    const map: Record<string, BaseCentralityRow> = {};
    if (!centralities) return map;
    for (const row of centralities) {
      map[row.state] = row;
    }
    return map;
  }, [centralities]);

  const { min, max } = useMemo(() => {
    if (!centralities || !measure) return { min: 0, max: 1 };
    const vals = centralities.map((r) => r[measure]);
    return { min: Math.min(...vals), max: Math.max(...vals) };
  }, [centralities, measure]);

  const edgeLines = useMemo(() => {
    if (!edges || !showEdges) return [];
    const maxWeight = Math.max(...edges.map((e) => e.weight));
    const totalWeight = edges.reduce((sum, e) => sum + e.weight, 0);
    return edges.map((e) => {
      const [x1, y1] = projectPoint(e.source_lon, e.source_lat, null);
      const [x2, y2] = projectPoint(e.target_lon, e.target_lat, null);
      const mx = (x1 + x2) / 2;
      const dx = x2 - x1;
      const dy = y2 - y1;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const my = (y1 + y2) / 2 - dist * 0.18;
      const weightRatio = e.weight / maxWeight;
      const pct = totalWeight ? (e.weight / totalWeight) * 100 : 0;

      // Direction-aware emphasis: when a state is selected, the In/Out/Both
      // filter decides which incident edges light up.
      const touchesSelected =
        flowDirection === "out"
          ? e.source === selectedState
          : flowDirection === "in"
            ? e.target === selectedState
            : e.source === selectedState || e.target === selectedState;
      const isConnectedToSelected = selectedState && touchesSelected;
      const isConnectedToHovered =
        hoveredState && (e.source === hoveredState || e.target === hoveredState);

      let opacity: number;
      let stroke: string;
      let width: number;
      let glow: boolean;

      if (selectedState) {
        if (isConnectedToSelected) {
          stroke = mapColors.selection;
          opacity = 0.95;
          width = 0.75 + weightRatio * 3.5;
          glow = true;
        } else {
          stroke = mapColors.dim;
          opacity = 0.1;
          width = 0.5;
          glow = false;
        }
      } else if (isConnectedToHovered) {
        stroke = mapColors.selection;
        opacity = 0.7;
        width = 0.75 + weightRatio * 2.5;
        glow = true;
      } else {
        stroke = mapColors.dim;
        opacity = 0.35;
        width = 0.75;
        glow = false;
      }

      return {
        x1, y1, x2, y2, mx, my, opacity, width, stroke, glow,
        source: e.source, target: e.target, weight: e.weight, pct,
        key: `${e.source}-${e.target}`,
      };
    });
  }, [edges, showEdges, selectedState, hoveredState, flowDirection]);

  return (
    <>
    <svg
      viewBox={`0 0 ${MAP_WIDTH} ${MAP_HEIGHT}`}
      className="w-full h-auto"
      style={{ maxHeight: "62vh" }}
    >
      <defs>
        <filter id="glow">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <filter id="edge-glow">
          <feDropShadow dx="0" dy="0" stdDeviation="1.5" floodColor="white" floodOpacity="0.8" />
        </filter>
      </defs>

      {/* invisible background rect for click-outside dismiss */}
      <rect
        x="0"
        y="0"
        width={MAP_WIDTH}
        height={MAP_HEIGHT}
        fill="transparent"
        onClick={() => onSelectState(null)}
      />

      {Object.entries(paths).map(([fips, { d, name }]) => {
        if (EXCLUDED_FIPS.has(fips)) return null;
        const abbr = FIPS_TO_ABBR[fips];
        const data = abbr ? centralityMap[abbr] : null;
        const value = data ? data[measure] : 0;
        const fill = data ? centralityToColor(value, min, max) : mapColors.empty;
        const isSelected = abbr === selectedState;
        const isHovered = abbr === hoveredState;
        const dimmed = selectedState && !isSelected;
        const washed = dimmed ? mapColors.wash : null;

        // selection uses white outline + glow, not fill change; hover uses medium outline
        let stroke: string = mapColors.stroke;
        let strokeWidth = 0.5;
        if (isSelected) {
          stroke = "#ffffff";
          strokeWidth = 2.5;
        } else if (isHovered) {
          stroke = accent;
          strokeWidth = 2;
        }

        return (
          <path
            key={fips}
            d={d}
            opacity={1}
            filter={isSelected ? "url(#glow)" : undefined}
            className="cursor-pointer"
            style={{
              fill: washed || fill,
              stroke,
              strokeWidth,
              transition: "fill 450ms ease, stroke 250ms ease, stroke-width 250ms ease",
            }}
            onMouseEnter={() => setHoveredState(abbr ?? null)}
            onMouseMove={(e) => {
              if (!abbr) return;
              setHoverInfo({
                name: name ?? abbr,
                rank: data ? data[`rank_${measure}`] : null,
                gdpRank: data ? data.gdp_rank : null,
                x: e.clientX,
                y: e.clientY,
              });
            }}
            onMouseLeave={() => {
              setHoveredState(null);
              setHoverInfo(null);
            }}
            onClick={(e) => {
              e.stopPropagation();
              onSelectState(isSelected ? null : (abbr ?? null));
            }}
          >
            <title>
              {name}
              {data ? ` — ${measure.replace("_", " ")}: #${data[`rank_${measure}`]}` : ""}
            </title>
          </path>
        );
      })}

      {showEdges &&
        edgeLines.map((e) => {
          const arcPath = `M${e.x1},${e.y1} Q${e.mx},${e.my} ${e.x2},${e.y2}`;
          return (
            <g key={e.key}>
              {/* Visible flow arc (no pointer events — the hit-path below captures hover) */}
              <path
                d={arcPath}
                fill="none"
                stroke={e.stroke}
                strokeWidth={e.width}
                opacity={e.opacity}
                filter={e.glow ? "url(#edge-glow)" : undefined}
                pointerEvents="none"
                className="transition-opacity duration-200"
              />
              {/* Transparent wide hit-path carries the native tooltip */}
              <path
                d={arcPath}
                fill="none"
                stroke="transparent"
                strokeWidth={8}
                pointerEvents="stroke"
                style={{ cursor: "crosshair" }}
              >
                <title>
                  {e.source} → {e.target}: $
                  {e.weight.toLocaleString("en-US", { maximumFractionDigits: 0 })} (
                  {e.pct.toFixed(1)}% of shown flows)
                </title>
              </path>
            </g>
          );
        })}
    </svg>
      <Tooltip x={hoverInfo?.x ?? 0} y={hoverInfo?.y ?? 0} visible={!!hoverInfo}>
        {hoverInfo && (
          <>
            <div className="font-semibold">{hoverInfo.name}</div>
            <div style={{ color: "var(--text-secondary)" }}>
              {hoverInfo.rank != null
                ? `${MEASURE_LABEL[measure]} #${hoverInfo.rank} · GDP #${hoverInfo.gdpRank}`
                : "No data for this commodity"}
            </div>
          </>
        )}
      </Tooltip>
    </>
  );
}
