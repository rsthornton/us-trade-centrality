"""
Edge-weight normalization functions for trade network analysis.

Each function takes a NetworkX DiGraph with 'weight' edge attributes
and returns a new DiGraph with modified weights. The original graph
is never mutated.

Usage:
    from cfs_toolkit.core.normalizations import gdp_sender
    from cfs_toolkit.core import compute_all_centralities

    G_norm = gdp_sender(G, gdp_df)
    df = compute_all_centralities(G_norm)
"""

import networkx as nx
import numpy as np
import pandas as pd


def gdp_sender(G: nx.DiGraph, gdp_df: pd.DataFrame) -> nx.DiGraph:
    """Normalize edge weights by sender's GDP.

    Controls for economic size of the exporting state. Answers:
    "relative to the size of its economy, how much does state i
    trade with state j?"

    This is the most direct pre-normalization for the "big states"
    concern — large economies naturally produce large flows, and
    this removes that scale effect.

    Expects gdp_df with columns: state_abbrev, gdp_2017_q4_millions.

    Formula: A'[i][j] = A[i][j] / GDP_i
    """
    G_out = G.copy()
    gdp_lookup = dict(zip(gdp_df["state_abbrev"], gdp_df["gdp_2017_q4_millions"]))

    for u, v, d in G_out.edges(data=True):
        label = G_out.nodes[u].get("label", str(u))
        gdp_u = gdp_lookup.get(label)
        if gdp_u:
            d["weight"] = d["weight"] / gdp_u
    return G_out


def gdp_geometric(G: nx.DiGraph, gdp_df: pd.DataFrame) -> nx.DiGraph:
    """Normalize edge weights by geometric mean of endpoint GDPs.

    Controls for economic size of both sender and receiver. A $10B flow
    between two large states is weighted less than a $10B flow between
    two small states. More aggressive than gdp_sender — also penalizes
    flows *to* large economies.

    Expects gdp_df with columns: state_abbrev, gdp_2017_q4_millions.

    Formula: A'[i][j] = A[i][j] / sqrt(GDP_i * GDP_j)
    """
    G_out = G.copy()
    gdp_lookup = dict(zip(gdp_df["state_abbrev"], gdp_df["gdp_2017_q4_millions"]))

    for u, v, d in G_out.edges(data=True):
        label_u = G_out.nodes[u].get("label", str(u))
        label_v = G_out.nodes[v].get("label", str(v))
        gdp_u = gdp_lookup.get(label_u)
        gdp_v = gdp_lookup.get(label_v)
        if gdp_u and gdp_v:
            d["weight"] = d["weight"] / np.sqrt(gdp_u * gdp_v)
    return G_out
