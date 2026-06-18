/**
 * Albers USA projection — projects lon/lat to SVG coordinates
 * with Alaska and Hawaii insets. Pure math, no D3 dependency.
 *
 * Matches D3's geoAlbersUsa() output for a 975×610 viewport.
 */

import type { FeatureCollection, GeoPosition, GeoRing, StatePath } from "../types";

const WIDTH = 975;
const HEIGHT = 610;

const DEG = Math.PI / 180;

type RawProjection = (lambda: number, phi: number) => GeoPosition;
type Projection = (lon: number, lat: number) => GeoPosition;

function conicEqualArea(phi1Deg: number, phi2Deg: number): RawProjection {
  const phi1 = phi1Deg * DEG;
  const phi2 = phi2Deg * DEG;
  const sy0 = Math.sin(phi1);
  const n = (sy0 + Math.sin(phi2)) / 2;
  const c = 1 + sy0 * (2 * n - sy0);
  const r0 = Math.sqrt(c) / n;

  return (lambda, phi) => {
    const r = Math.sqrt(c - 2 * n * Math.sin(phi)) / n;
    const x = r * Math.sin(lambda * n);
    const y = r0 - r * Math.cos(lambda * n);
    return [x, y];
  };
}

function makeProjection(
  phi1: number,
  phi2: number,
  centerLon: number,
  centerLat: number,
  scale: number,
  tx: number,
  ty: number,
): Projection {
  const raw = conicEqualArea(phi1, phi2);
  const lambda0 = centerLon * DEG;
  const phi0 = centerLat * DEG;
  const [cx, cy] = raw(0, phi0);

  return (lon, lat) => {
    const [x, y] = raw(lon * DEG - lambda0, lat * DEG);
    return [(x - cx) * scale + tx, -(y - cy) * scale + ty];
  };
}

const lower48 = makeProjection(29.5, 45.5, -96, 37.5, 1070, 480, 250);

const alaska = makeProjection(55, 65, -154, 62, 350, 150, 440);

const hawaii = makeProjection(8, 18, -157, 20.5, 1070, 310, 440);

const ALASKA_FIPS = "02";
const HAWAII_FIPS = "15";

export function projectPoint(lon: number, lat: number, fips?: string | null): GeoPosition {
  if (fips === ALASKA_FIPS) return alaska(lon, lat);
  if (fips === HAWAII_FIPS) return hawaii(lon, lat);
  return lower48(lon, lat);
}

function ringToPath(ring: GeoRing, fips: string): string {
  if (ring.length === 0) return "";
  const points = ring.map(([lon, lat]) => {
    const [x, y] = projectPoint(lon, lat, fips);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  return `M${points.join("L")}Z`;
}

export function geoToSvgPaths(geojson: FeatureCollection): Record<string, StatePath> {
  const paths: Record<string, StatePath> = {};
  for (const feature of geojson.features) {
    const fips = feature.id;
    const name = feature.properties.name;
    const geo = feature.geometry;
    if (!geo) continue;

    let d: string;
    if (geo.type === "Polygon") {
      d = geo.coordinates.map((ring) => ringToPath(ring, fips)).join("");
    } else if (geo.type === "MultiPolygon") {
      d = geo.coordinates
        .map((polygon) => polygon.map((ring) => ringToPath(ring, fips)).join(""))
        .join("");
    } else {
      continue;
    }

    paths[fips] = { d, name, fips };
  }
  return paths;
}

export const MAP_WIDTH = WIDTH;
export const MAP_HEIGHT = HEIGHT;
