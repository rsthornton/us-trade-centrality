/**
 * Minimal TopoJSON → GeoJSON decoder.
 * Replaces topojson-client dependency (~3KB savings, zero npm deps).
 */

function decodeArc(topology, arc) {
  let x = 0, y = 0;
  return arc.map(([dx, dy]) => {
    x += dx;
    y += dy;
    const [lon, lat] = topology.transform
      ? [x * topology.transform.scale[0] + topology.transform.translate[0],
         y * topology.transform.scale[1] + topology.transform.translate[1]]
      : [x, y];
    return [lon, lat];
  });
}

function decodeArcs(topology) {
  return topology.arcs.map((arc) => decodeArc(topology, arc));
}

function resolveRing(arcs, decodedArcs) {
  const coords = [];
  for (const idx of arcs) {
    const arc = idx >= 0 ? decodedArcs[idx] : decodedArcs[~idx].slice().reverse();
    if (coords.length > 0) arc.shift();
    coords.push(...arc);
  }
  return coords;
}

function resolveGeometry(geom, decodedArcs) {
  if (geom.type === "Polygon") {
    return {
      type: "Polygon",
      coordinates: geom.arcs.map((ring) => resolveRing(ring, decodedArcs)),
    };
  }
  if (geom.type === "MultiPolygon") {
    return {
      type: "MultiPolygon",
      coordinates: geom.arcs.map((polygon) =>
        polygon.map((ring) => resolveRing(ring, decodedArcs)),
      ),
    };
  }
  return geom;
}

export function topoFeature(topology, objectName) {
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
