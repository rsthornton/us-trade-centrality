"""
Year-aware loading for the three-survey evolution study.

Wraps the cfs_toolkit pipeline (load -> preprocess -> aggregate -> graph)
and adds the cross-year comparability handling the 2012/2017/2022
comparison requires: SCTG 16 exclusion, grouped-code accounting, and
truncation accounting for the 2022 PUMS.
"""

import logging
from pathlib import Path

import pandas as pd
import yaml

from cfs_toolkit.core.data_loader import load_cfs_data
from cfs_toolkit.core.preprocessor import preprocess_cfs_data, aggregate_cfs_to_edges
from cfs_toolkit.core.network_builder import build_trade_network
from cfs_toolkit.core.centralities import compute_all_centralities

log = logging.getLogger(__name__)

EVOLUTION_DIR = Path(__file__).resolve().parent.parent


def sctg_includes_16(code):
    """True if an SCTG code or grouped range (e.g. '15-19') covers crude petroleum (16)."""
    code = str(code).strip()
    if "-" in code:
        try:
            lo, hi = code.split("-")
            return int(lo) <= 16 <= int(hi)
        except ValueError:
            return False
    try:
        return int(code) == 16
    except ValueError:
        return False


def load_year_config(year):
    path = EVOLUTION_DIR / "configs" / f"cfs_{year}.yaml"
    with open(path) as f:
        config = yaml.safe_load(f)
    return config


def load_year(year, sample_size=None, truncation_value=30_000_000):
    """
    Build one survey year's network bundle.

    Returns a dict with the aggregate edge list, per-commodity edge list,
    graph, centrality table, and the stats the go/no-go gates consume.
    SCTG 16 (and grouped codes covering it) is excluded from every year
    for cross-year parity: it is out of scope in the 2022 survey.
    """
    config = load_year_config(year)
    source = config["source_file"]

    df = load_cfs_data(source, sample_size=sample_size)

    sctg_str = df["SCTG"].astype("string").fillna("")
    grouped_mask = sctg_str.str.contains("-")
    sctg16_mask = sctg_str.map(sctg_includes_16)

    raw_total = float((df["SHIPMT_VALUE"].astype("float64") * df["WGT_FACTOR"].astype("float64")).sum())
    stats = {
        "year": year,
        "source_file": source,
        "sample_size": sample_size,
        "raw_records": int(len(df)),
        "raw_weighted_total": raw_total,
        "grouped_sctg_share": float(grouped_mask.mean()),
        "sctg16_records_dropped": int(sctg16_mask.sum()),
        "truncation_share": float((df["SHIPMT_VALUE"] >= truncation_value).mean()),
    }

    df = df[~sctg16_mask]
    df = preprocess_cfs_data(df, interstate_only=True)

    commodity_edges = (
        df.groupby(["ORIG_STATE", "DEST_STATE", "SCTG"], observed=True, as_index=False)
        ["weighted_value"].sum()
    )

    edges = aggregate_cfs_to_edges(df)
    stats["interstate_records"] = int(len(df))
    stats["interstate_weighted_total"] = float(edges["SHIPMT_VALUE"].sum())
    stats["edge_count"] = int(len(edges))

    G = build_trade_network(edges)
    centralities = compute_all_centralities(G)

    return {
        "year": year,
        "config": config,
        "edges": edges,
        "commodity_edges": commodity_edges,
        "graph": G,
        "centralities": centralities,
        "stats": stats,
    }
