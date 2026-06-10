"""
H1-H5 tests for a 2017-anchored year pair.

Each test returns the measured values plus a verdict against the
pre-registered thresholds in thresholds.yaml. Rank machinery is reused
from cfs_toolkit.analysis.comparison_utils (the functions are generic
over any two centrality tables, originally written for 51x51 vs 52x52).
"""

import numpy as np
import pandas as pd
import networkx as nx
from scipy.stats import skew
from sklearn.metrics import normalized_mutual_info_score

from cfs_toolkit.analysis.comparison_utils import (
    compute_rank_correlations,
    compute_topk_overlap,
)

MEASURES = ["betweenness", "eigenvector", "out_degree"]

OPS = {">=": lambda v, t: v >= t, ">": lambda v, t: v > t,
       "<=": lambda v, t: v <= t, "<": lambda v, t: v < t}


def h1_hub_centrality(base, target, spec):
    correlations = compute_rank_correlations(
        base["centralities"], target["centralities"], MEASURES
    )
    overlap = compute_topk_overlap(
        base["centralities"], target["centralities"], ["eigenvector"], [10]
    )
    top10 = overlap["eigenvector"][10]["overlap_count"]

    per_measure = {}
    for measure, forecast in spec["forecasts"].items():
        rho = correlations[measure]["spearman"]
        holds = OPS[forecast["op"]](rho, forecast["value"])
        per_measure[measure] = {
            "spearman": rho,
            "kendall": correlations[measure]["kendall"],
            "forecast": f"rho {forecast['op']} {forecast['value']}",
            "holds": bool(holds),
        }

    top10_holds = top10 >= spec["top10_overlap_min"]
    return {
        "hypothesis": "H1",
        "measures": per_measure,
        "top10_overlap": {"count": top10, "min": spec["top10_overlap_min"], "holds": bool(top10_holds)},
        "holds": bool(all(m["holds"] for m in per_measure.values()) and top10_holds),
    }


def _backbone_edges(edges, percentile):
    cutoff = np.percentile(edges["SHIPMT_VALUE"], percentile)
    backbone = edges[edges["SHIPMT_VALUE"] >= cutoff]
    return set(zip(backbone["ORIG_STATE"], backbone["DEST_STATE"]))


def h2_backbone(base, target, spec):
    set_base = _backbone_edges(base["edges"], spec["top_weight_percentile"])
    set_target = _backbone_edges(target["edges"], spec["top_weight_percentile"])
    union = set_base | set_target
    jaccard = len(set_base & set_target) / len(union) if union else 0.0
    return {
        "hypothesis": "H2",
        "jaccard": jaccard,
        "backbone_sizes": {"base": len(set_base), "target": len(set_target)},
        "forecast": f"jaccard >= {spec['jaccard_min']}",
        "holds": bool(jaccard >= spec["jaccard_min"]),
    }


def _commodity_vector(commodity_edges, codes=None, prefix=None):
    sctg = commodity_edges["SCTG"].astype("string")
    if prefix is not None:
        mask = sctg.str.startswith(prefix)
    else:
        mask = sctg.isin(codes)
    sub = commodity_edges[mask]
    return sub.groupby(["ORIG_STATE", "DEST_STATE"])["weighted_value"].sum()


def _cosine_delta(vec_a, vec_b):
    aligned = pd.concat([vec_a, vec_b], axis=1, keys=["a", "b"]).fillna(0.0)
    a, b = aligned["a"].to_numpy(), aligned["b"].to_numpy()
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return None
    return float(1.0 - np.dot(a, b) / denom)


def h3_commodity(base, target, spec, pair_label):
    pharma_delta = _cosine_delta(
        _commodity_vector(base["commodity_edges"], prefix=spec["pharma_sctg_prefix"]),
        _commodity_vector(target["commodity_edges"], prefix=spec["pharma_sctg_prefix"]),
    )
    ag_delta = _cosine_delta(
        _commodity_vector(base["commodity_edges"], codes=spec["agriculture_sctg_codes"]),
        _commodity_vector(target["commodity_edges"], codes=spec["agriculture_sctg_codes"]),
    )
    if pharma_delta is None or ag_delta is None:
        return {"hypothesis": "H3", "holds": None, "note": "empty commodity vector (sample too small?)"}

    if pair_label == "retrodiction":
        gap = abs(pharma_delta - ag_delta)
        holds = gap <= spec["retrodiction_max_gap"]
        forecast = f"|delta_pharma - delta_ag| <= {spec['retrodiction_max_gap']}"
    else:
        gap = pharma_delta - ag_delta
        holds = pharma_delta > ag_delta
        forecast = "delta_pharma > delta_ag"

    return {
        "hypothesis": "H3",
        "pharma_delta": pharma_delta,
        "agriculture_delta": ag_delta,
        "gap": gap,
        "forecast": forecast,
        "holds": bool(holds),
    }


def _undirected_weighted(G):
    U = nx.Graph()
    U.add_nodes_from(G.nodes(data=True))
    for u, v, d in G.edges(data=True):
        w = d["weight"] + (U[u][v]["weight"] if U.has_edge(u, v) else 0.0)
        U.add_edge(u, v, weight=w)
    return U


def _louvain_labels(G, seed=42):
    communities = nx.community.louvain_communities(_undirected_weighted(G), weight="weight", seed=seed)
    labels = {}
    for i, community in enumerate(communities):
        for node in community:
            labels[node] = i
    return labels


def h4_community(base, target, spec):
    labels_base = _louvain_labels(base["graph"])
    labels_target = _louvain_labels(target["graph"])
    common = sorted(set(labels_base) & set(labels_target))
    nmi = normalized_mutual_info_score(
        [labels_base[n] for n in common], [labels_target[n] for n in common]
    )
    return {
        "hypothesis": "H4",
        "nmi": float(nmi),
        "communities": {"base": len(set(labels_base.values())), "target": len(set(labels_target.values()))},
        "forecast": f"nmi >= {spec['nmi_min']}",
        "holds": bool(nmi >= spec["nmi_min"]),
    }


def _gini(values):
    v = np.sort(np.asarray(values, dtype=float))
    if len(v) == 0 or v.sum() == 0:
        return 0.0
    n = len(v)
    return float((2 * np.arange(1, n + 1) - n - 1).dot(v) / (n * v.sum()))


def net_flow_stats(bundle):
    edges = bundle["edges"]
    w = {(r.ORIG_STATE, r.DEST_STATE): r.SHIPMT_VALUE for r in edges.itertuples(index=False)}
    pairs = {tuple(sorted(k)) for k in w}
    net = [abs(w.get((i, j), 0.0) - w.get((j, i), 0.0)) for i, j in pairs]
    return {"gini": _gini(net), "skewness": float(skew(edges["SHIPMT_VALUE"]))}


def h5_asymmetry(base, target, spec, pair_label):
    g_base = net_flow_stats(base)["gini"]
    g_target = net_flow_stats(target)["gini"]

    if pair_label == "retrodiction":
        shift = abs(g_target - g_base)
        holds = shift <= spec["retrodiction_max_gini_shift"]
        forecast = f"|gini shift| <= {spec['retrodiction_max_gini_shift']}"
    else:
        shift = g_target - g_base
        holds = shift >= spec["prediction_min_gini_growth"]
        forecast = f"gini growth >= {spec['prediction_min_gini_growth']}"

    return {
        "hypothesis": "H5",
        "gini_base": g_base,
        "gini_target": g_target,
        "shift": shift,
        "forecast": forecast,
        "holds": bool(holds),
    }


def run_pair(pair_label, base, target, thresholds):
    return {
        "pair": pair_label,
        "base_year": base["year"],
        "target_year": target["year"],
        "H1": h1_hub_centrality(base, target, thresholds["h1_hub_centrality"]),
        "H2": h2_backbone(base, target, thresholds["h2_backbone"]),
        "H3": h3_commodity(base, target, thresholds["h3_commodity"], pair_label),
        "H4": h4_community(base, target, thresholds["h4_community"]),
        "H5": h5_asymmetry(base, target, thresholds["h5_asymmetry"], pair_label),
    }
