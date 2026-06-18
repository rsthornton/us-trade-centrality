/** Shared data models for the Interstate Power Observatory.
 *  Shapes mirror the JSON in web/public/data/ produced by scripts/export_viz_data.py.
 *  See web/DESIGN.md for the data contract. */

export type Measure = "betweenness" | "eigenvector" | "out_degree";
export type RankKey = `rank_${Measure}`;

/** Fields shared by national and commodity centrality rows.
 *  state_name is optional here: national rows carry it, commodity rows do not. */
export interface BaseCentralityRow {
  state_id: number;
  state: string;
  state_name?: string;
  betweenness: number;
  eigenvector: number;
  out_degree: number;
  rank_betweenness: number;
  rank_eigenvector: number;
  rank_out_degree: number;
  gdp_billions: number;
  gdp_rank: number;
}

/** National network rows (centralities_51.json / centralities_52.json) carry coords + name. */
export interface CentralityRow extends BaseCentralityRow {
  state_name: string;
  lat: number;
  lon: number;
}

/** Per-commodity rows (commodity_centralities.json) carry the commodity, not coords. */
export interface CommodityCentralityRow extends BaseCentralityRow {
  commodity_code: string;
  commodity_name: string;
}

/** A directed trade flow with pre-resolved endpoint coordinates. */
export interface Edge {
  source: string;
  target: string;
  weight: number;
  source_lat: number;
  source_lon: number;
  target_lat: number;
  target_lon: number;
}

export interface PartnerFlow {
  partner: string;
  weight: number;
}

/** A state's true total trade + top partners (full bilateral matrix, not the display backbone). */
export interface StateTotals {
  state: string;
  out_total: number;
  in_total: number;
  top_out: PartnerFlow[];
  top_in: PartnerFlow[];
}

export interface RankChange {
  state: string;
  betweenness_change: number;
  eigenvector_change: number;
  out_degree_change: number;
}

export interface NetworkStats {
  nodes: number;
  edges: number;
  density: number;
  clustering_coefficient: number;
  reciprocity: number;
}

export interface Metadata {
  commodity_groups: Record<string, string[]>;
  sctg_names: Record<string, string>;
}

/* ── GeoJSON (minimal — what lib/geo.ts consumes) ─────────────────────── */

export type GeoPosition = [number, number];
export type GeoRing = GeoPosition[];

export interface PolygonGeometry {
  type: "Polygon";
  coordinates: GeoRing[];
}
export interface MultiPolygonGeometry {
  type: "MultiPolygon";
  coordinates: GeoRing[][];
}
export type GeoGeometry = PolygonGeometry | MultiPolygonGeometry;

export interface GeoFeature {
  type: "Feature";
  id: string;
  properties: { name?: string } & Record<string, unknown>;
  geometry: GeoGeometry | null;
}

export interface FeatureCollection {
  type: "FeatureCollection";
  features: GeoFeature[];
}

/** Resolved SVG path for one state, keyed by FIPS in geoToSvgPaths(). */
export interface StatePath {
  d: string;
  name?: string;
  fips: string;
}

/* ── TopoJSON (minimal — what lib/topo.ts consumes) ───────────────────── */

export interface TopoTransform {
  scale: [number, number];
  translate: [number, number];
}

export interface TopoGeometry {
  type: GeoGeometry["type"] | string;
  id: string;
  properties?: Record<string, unknown>;
  arcs: unknown;
}

export interface TopoObject {
  type: "GeometryCollection";
  geometries: TopoGeometry[];
}

export interface TopoTopology {
  type: "Topology";
  transform?: TopoTransform;
  arcs: GeoPosition[][];
  objects: Record<string, TopoObject>;
}

/** Everything loadAllCore() resolves. */
export interface CoreData {
  centralities51: CentralityRow[];
  centralities52: CentralityRow[];
  rankChanges: RankChange[];
  topEdges: Edge[];
  stats: NetworkStats;
  metadata: Metadata;
  topo: TopoTopology;
  stateTotals: StateTotals[];
}
