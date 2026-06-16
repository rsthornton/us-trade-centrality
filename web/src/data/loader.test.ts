import { describe, it, expect, vi } from "vitest";
import { loadAllCore } from "./loader";

function bodyFor(path: string): unknown {
  if (path.includes("network_stats"))
    return { nodes: 51, edges: 2534, density: 0.99, clustering_coefficient: 0, reciprocity: 0 };
  if (path.includes("metadata")) return { commodity_groups: {}, sctg_names: {} };
  if (path.includes("us-states")) return { type: "Topology", arcs: [], objects: {} };
  return [];
}

describe("loadAllCore", () => {
  it("resolves the full CoreData shape and caches per path", async () => {
    const fetchMock = vi.fn(async (path: string) => ({
      ok: true,
      json: async () => bodyFor(path),
    }));
    vi.stubGlobal("fetch", fetchMock);

    const data = await loadAllCore();
    expect(Object.keys(data).sort()).toEqual(
      ["centralities51", "centralities52", "metadata", "rankChanges", "stats", "topEdges", "topo"].sort(),
    );

    const callsAfterFirst = fetchMock.mock.calls.length;
    expect(callsAfterFirst).toBe(7);

    // Second call hits the in-memory cache: no additional fetches.
    await loadAllCore();
    expect(fetchMock.mock.calls.length).toBe(callsAfterFirst);
  });
});
