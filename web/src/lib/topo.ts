/**
 * Minimal TopoJSON → GeoJSON decoder.
 * Replaces topojson-client dependency (~3KB savings, zero npm deps).
 */

import type {
  FeatureCollection,
  GeoGeometry,
  GeoPosition,
  GeoRing,
  TopoGeometry,
  TopoTopology,
} from "../types";

function decodeArc(topology: TopoTopology, arc: GeoPosition[]): GeoRing {
  let x = 0;
  let y = 0;
  return arc.map(([dx, dy]) => {
    x += dx;
    y += dy;
    const point: GeoPosition = topology.transform
      ? [
          x * topology.transform.scale[0] + topology.transform.translate[0],
          y * topology.transform.scale[1] + topology.transform.translate[1],
        ]
      : [x, y];
    return point;
  });
}

function decodeArcs(topology: TopoTopology): GeoRing[] {
  return topology.arcs.map((arc) => decodeArc(topology, arc));
}

function resolveRing(arcs: number[], decodedArcs: GeoRing[]): GeoRing {
  const coords: GeoRing = [];
  for (const idx of arcs) {
    const arc = idx >= 0 ? decodedArcs[idx] : decodedArcs[~idx].slice().reverse();
    if (coords.length > 0) arc.shift();
    coords.push(...arc);
  }
  return coords;
}

function resolveGeometry(geom: TopoGeometry, decodedArcs: GeoRing[]): GeoGeometry | null {
  if (geom.type === "Polygon") {
    return {
      type: "Polygon",
      coordinates: (geom.arcs as number[][]).map((ring) => resolveRing(ring, decodedArcs)),
    };
  }
  if (geom.type === "MultiPolygon") {
    return {
      type: "MultiPolygon",
      coordinates: (geom.arcs as number[][][]).map((polygon) =>
        polygon.map((ring) => resolveRing(ring, decodedArcs)),
      ),
    };
  }
  return null;
}

export function topoFeature(topology: TopoTopology, objectName: string): FeatureCollection {
  const obj = topology.objects[objectName];
  const decoded = decodeArcs(topology);

  return {
    type: "FeatureCollection",
    features: obj.geometries.map((geom) => ({
      type: "Feature",
      id: geom.id,
      properties: geom.properties || {},
      geometry: resolveGeometry(geom, decoded),
    })),
  };
}
