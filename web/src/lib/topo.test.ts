import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { topoFeature } from "./topo";
import type { TopoTopology } from "../types";

const topology = JSON.parse(
  readFileSync("public/data/us-states-10m.json", "utf-8"),
) as TopoTopology;

describe("topoFeature", () => {
  const fc = topoFeature(topology, "states");

  it("decodes the states object into a FeatureCollection", () => {
    expect(fc.type).toBe("FeatureCollection");
    expect(fc.features.length).toBeGreaterThan(50);
  });

  it("produces Polygon/MultiPolygon geometries with coordinates", () => {
    const withGeom = fc.features.filter((f) => f.geometry);
    expect(withGeom.length).toBe(fc.features.length);
    const sample = withGeom[0].geometry!;
    expect(["Polygon", "MultiPolygon"]).toContain(sample.type);
    expect(sample.coordinates.length).toBeGreaterThan(0);
  });
});
