"""
Which direction is the eigenvector centrality in this repo? (post-hoc check)

On a directed network there are two eigenvector centralities. With A[i, j] the
flow from state i to state j, the in-flow version scores a state by the scores
of the states that ship to it (x = A^T x / lambda, the left eigenvector of A);
the out-flow version scores it by the states it ships to (x = A x / lambda, the
right eigenvector). NetworkX's eigenvector_centrality_numpy on a DiGraph
returns the in-flow version, and that is what cfs_toolkit computes.

This script recomputes both versions from the thesis flows and from the three
evolution caches (read only), checks which one matches the stored values, and
records where the two disagree. Writes output/direction.json.
"""

import json
import pickle
from pathlib import Path

import networkx as nx
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CACHE = ROOT / "evolution" / "cache"
WATCH = ["TX", "CA", "FL", "KY", "MS", "IN", "LA", "TN", "MI", "DC"]


def both_versions(edges):
    g = nx.DiGraph()
    for src, dst, w in edges.itertuples(index=False):
        g.add_edge(src, dst, weight=w)
    in_flow = pd.Series(nx.eigenvector_centrality_numpy(g, weight="weight"))
    out_flow = pd.Series(nx.eigenvector_centrality_numpy(g.reverse(), weight="weight"))
    return in_flow, out_flow


def compare(name, edges, stored):
    in_flow, out_flow = both_versions(edges)
    df = pd.DataFrame({"stored": stored, "in_flow": in_flow, "out_flow": out_flow}).dropna()
    ranks = df.rank(ascending=False, method="min").astype(int)
    moved = (ranks.in_flow - ranks.out_flow).abs()
    return {
        "source": name,
        "states": len(df),
        "stored_matches": "in_flow"
        if (df.stored - df.in_flow).abs().max() < 1e-6
        else "out_flow"
        if (df.stored - df.out_flow).abs().max() < 1e-6
        else "neither",
        "max_abs_diff_stored_vs_in_flow": float((df.stored - df.in_flow).abs().max()),
        "spearman_in_vs_out": round(float(df.in_flow.corr(df.out_flow, method="spearman")), 3),
        "states_moving_5plus_ranks": int((moved >= 5).sum()),
        "largest_moves": {
            s: {"in_flow": int(ranks.in_flow[s]), "out_flow": int(ranks.out_flow[s])}
            for s in moved.sort_values(ascending=False).head(8).index
        },
        "watch": {
            s: {"in_flow": int(ranks.in_flow[s]), "out_flow": int(ranks.out_flow[s])}
            for s in WATCH
            if s in ranks.index
        },
    }


def main():
    results = []
    flows = pd.read_csv(ROOT / "data" / "bilateral_flows_51x51.csv")
    site = pd.DataFrame(json.loads((ROOT / "web/public/data/centralities_51.json").read_text()))
    results.append(
        compare(
            "thesis 2017 (data/bilateral_flows_51x51.csv vs dashboard)",
            flows[["origin", "destination", "trade_value_usd"]],
            site.set_index("state")["eigenvector"],
        )
    )
    for year in (2012, 2017, 2022):
        path = CACHE / f"cfs_{year}_full.pkl"
        if not path.exists():
            continue
        with open(path, "rb") as f:
            bundle = pickle.load(f)
        cent = bundle["centralities"]
        labels = cent.set_index("state_id")["label"]
        e = bundle["edges"]
        edges = pd.DataFrame(
            {
                "src": e.ORIG_STATE.map(labels),
                "dst": e.DEST_STATE.map(labels),
                "w": e.SHIPMT_VALUE,
            }
        ).dropna()
        edges = edges[edges.src != edges.dst].groupby(["src", "dst"], as_index=False).w.sum()
        results.append(
            compare(f"evolution cache {year}", edges, cent.set_index("label")["eigenvector"])
        )

    out = HERE / "output" / "direction.json"
    out.write_text(
        json.dumps({"note": "Post-hoc check. See README.md.", "results": results}, indent=1) + "\n"
    )
    for r in results:
        print(
            r["source"],
            "| stored =",
            r["stored_matches"],
            "| rho in/out =",
            r["spearman_in_vs_out"],
            "| 5+ rank moves:",
            r["states_moving_5plus_ranks"],
        )


if __name__ == "__main__":
    main()
