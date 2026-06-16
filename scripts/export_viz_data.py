"""Export pre-computed pipeline data as JSON for the React frontend.

Reads from viz/data/ CSVs and the pickled NetworkX graph,
writes clean JSON to web/public/data/.
"""

import json
import pickle
import sys
from pathlib import Path

import networkx as nx
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VIZ_DATA = PROJECT_ROOT / "viz" / "data"
OUT_DIR = PROJECT_ROOT / "web" / "public" / "data"

COMMODITY_GROUPS = {
    "Agriculture & Food": [
        "01", "02", "03", "04", "05", "06", "07", "08", "09",
        "01-05", "06-09",
    ],
    "Mining & Extraction": [
        "10", "11", "12", "13", "14", "15", "16", "17", "18", "19",
        "10-14", "15-19",
    ],
    "Chemicals & Plastics": ["20", "21", "22", "23", "24", "20-24"],
    "Wood & Paper": ["25", "26", "27", "28", "29", "25-30"],
    "Metals & Minerals": ["30", "31", "32", "33", "31-34"],
    "Machinery & Equipment": ["34", "35", "36", "37", "38", "35-38"],
    "Consumer & Other": ["39", "40", "41", "43", "39-43", "00"],
}

SCTG_NAMES = {
    "00": "Unknown/Unclassified",
    "01": "Live Animals and Fish", "02": "Cereal Grains",
    "03": "Other Agricultural Products", "04": "Animal Feed",
    "05": "Meat/Seafood", "06": "Milled Grain Products",
    "07": "Other Foodstuffs", "08": "Alcoholic Beverages",
    "09": "Tobacco Products", "10": "Building Stone",
    "11": "Natural Sands", "12": "Gravel and Crushed Stone",
    "13": "Nonmetallic Minerals", "14": "Metallic Ores",
    "15": "Coal", "16": "Crude Petroleum",
    "17": "Gasoline", "18": "Fuel Oils",
    "19": "Coal and Petroleum Products", "20": "Basic Chemicals",
    "21": "Pharmaceutical Products", "22": "Fertilizers",
    "23": "Chemical Products", "24": "Plastics/Rubber",
    "25": "Logs and Wood", "26": "Wood Products",
    "27": "Newsprint/Paper", "28": "Paper Articles",
    "29": "Printed Products", "30": "Textiles/Leather",
    "31": "Nonmetallic Mineral Products", "32": "Base Metals",
    "33": "Articles of Base Metal", "34": "Machinery",
    "35": "Electronic Equipment", "36": "Motorized Vehicles",
    "37": "Transportation Equipment", "38": "Precision Instruments",
    "39": "Furniture", "40": "Misc. Manufactured Products",
    "41": "Waste/Scrap", "43": "Mixed Freight",
    "01-05": "Agriculture (Grouped)", "06-09": "Food Products (Grouped)",
    "10-14": "Mining (Grouped)", "15-19": "Energy (Grouped)",
    "20-24": "Chemicals (Grouped)", "25-30": "Wood/Paper/Textiles (Grouped)",
    "31-34": "Metals/Machinery (Grouped)", "35-38": "Electronics/Vehicles (Grouped)",
    "39-43": "Consumer/Other (Grouped)",
}


def load_and_merge():
    """Load all source data and prepare merged dataframes."""
    coords = pd.read_csv(VIZ_DATA / "state_coords.csv")
    gdp = pd.read_csv(VIZ_DATA / "state_gdp_2017.csv")
    gdp["gdp_billions"] = gdp["gdp_2017_q4_millions"] / 1000
    gdp["gdp_rank"] = gdp["gdp_billions"].rank(ascending=False, method="min").astype(int)

    c51 = pd.read_csv(VIZ_DATA / "centralities_51x51.csv").rename(columns={"label": "state"})
    c52 = pd.read_csv(VIZ_DATA / "centralities_52x52.csv").rename(columns={"label": "state"})

    def merge_meta(df):
        df = df.merge(
            gdp[["state_abbrev", "gdp_billions", "gdp_rank"]],
            left_on="state", right_on="state_abbrev", how="left",
        ).drop(columns=["state_abbrev"])
        df = df.merge(
            coords[["state_abbr", "state_name", "lat", "lon"]],
            left_on="state", right_on="state_abbr", how="left",
        ).drop(columns=["state_abbr"])
        return df

    c51 = merge_meta(c51)
    c52 = merge_meta(c52)

    return coords, gdp, c51, c52


def export_centralities(c51, c52):
    """Export centralities with GDP and coords merged."""
    c51.to_json(OUT_DIR / "centralities_51.json", orient="records", double_precision=6)
    c52.to_json(OUT_DIR / "centralities_52.json", orient="records", double_precision=6)
    print(f"  centralities_51.json: {len(c51)} states")
    print(f"  centralities_52.json: {len(c52)} states")


def export_rank_changes(c51, c52):
    """Export rank changes between 51x51 and 52x52 networks."""
    states_51 = set(c51["state"])
    c52_overlap = c52[c52["state"].isin(states_51)].copy()

    changes = c51[["state"]].copy()
    for measure in ["betweenness", "eigenvector", "out_degree"]:
        rank_51 = c51.set_index("state")[f"rank_{measure}"]
        rank_52 = c52_overlap.set_index("state")[f"rank_{measure}"]
        changes[f"{measure}_change"] = (rank_51 - rank_52).reindex(changes["state"]).values

    changes.to_json(OUT_DIR / "rank_changes.json", orient="records", double_precision=2)
    print(f"  rank_changes.json: {len(changes)} states")


def export_top_edges(top_n=100):
    """Export top aggregate edges from the pickled network graph."""
    graph_path = VIZ_DATA / "network_graph.gpickle"
    coords = pd.read_csv(VIZ_DATA / "state_coords.csv")
    c51 = pd.read_csv(VIZ_DATA / "centralities_51x51.csv").rename(columns={"label": "state"})

    coord_lookup = {
        row["state_abbr"]: {"lat": row["lat"], "lon": row["lon"]}
        for _, row in coords.iterrows()
    }
    id_to_label = dict(zip(c51["state_id"], c51["state"]))

    with open(graph_path, "rb") as f:
        G = pickle.load(f)

    edges_sorted = sorted(
        ((s, t, d["weight"]) for s, t, d in G.edges(data=True)),
        key=lambda x: x[2],
        reverse=True,
    )

    top_edges = []
    for src_id, tgt_id, weight in edges_sorted[:top_n]:
        src = id_to_label.get(src_id)
        tgt = id_to_label.get(tgt_id)
        if not src or not tgt or src not in coord_lookup or tgt not in coord_lookup:
            continue
        top_edges.append({
            "source": src,
            "target": tgt,
            "weight": round(weight, 2),
            "source_lat": coord_lookup[src]["lat"],
            "source_lon": coord_lookup[src]["lon"],
            "target_lat": coord_lookup[tgt]["lat"],
            "target_lon": coord_lookup[tgt]["lon"],
        })

    with open(OUT_DIR / "top_edges.json", "w") as f:
        json.dump(top_edges, f)
    print(f"  top_edges.json: {len(top_edges)} edges")


def export_commodity_data():
    """Export commodity centralities and top edges per commodity."""
    comm_cent = pd.read_csv(VIZ_DATA / "commodity_centralities.csv").rename(columns={"label": "state"})
    comm_edges = pd.read_csv(VIZ_DATA / "commodity_edges.csv", dtype={"commodity_code": str})

    gdp = pd.read_csv(VIZ_DATA / "state_gdp_2017.csv")
    gdp["gdp_billions"] = gdp["gdp_2017_q4_millions"] / 1000
    gdp["gdp_rank"] = gdp["gdp_billions"].rank(ascending=False, method="min").astype(int)

    coords = pd.read_csv(VIZ_DATA / "state_coords.csv")
    coord_lookup = {
        row["state_abbr"]: {"lat": row["lat"], "lon": row["lon"]}
        for _, row in coords.iterrows()
    }

    result_dfs = []
    for code in comm_cent["commodity_code"].unique():
        code_df = comm_cent[comm_cent["commodity_code"] == code].copy()
        code_df["rank_betweenness"] = code_df["betweenness"].rank(ascending=False, method="min").astype(int)
        code_df["rank_eigenvector"] = code_df["eigenvector"].rank(ascending=False, method="min").astype(int)
        code_df["rank_out_degree"] = code_df["out_degree"].rank(ascending=False, method="min").astype(int)
        code_df = code_df.merge(
            gdp[["state_abbrev", "gdp_billions", "gdp_rank"]],
            left_on="state", right_on="state_abbrev", how="left",
        ).drop(columns=["state_abbrev"], errors="ignore")
        result_dfs.append(code_df)

    all_comm = pd.concat(result_dfs, ignore_index=True)
    all_comm.to_json(OUT_DIR / "commodity_centralities.json", orient="records", double_precision=6)
    print(f"  commodity_centralities.json: {len(all_comm)} rows")

    edges_dir = OUT_DIR / "commodity_edges"
    edges_dir.mkdir(exist_ok=True)
    count = 0
    for code in sorted(comm_edges["commodity_code"].unique()):
        code_edges = comm_edges[comm_edges["commodity_code"] == code].nlargest(50, "weight")
        records = []
        for _, row in code_edges.iterrows():
            src, tgt = row["source"], row["target"]
            if src in coord_lookup and tgt in coord_lookup:
                records.append({
                    "source": src,
                    "target": tgt,
                    "weight": round(row["weight"], 2),
                    "source_lat": coord_lookup[src]["lat"],
                    "source_lon": coord_lookup[src]["lon"],
                    "target_lat": coord_lookup[tgt]["lat"],
                    "target_lon": coord_lookup[tgt]["lon"],
                })
        with open(edges_dir / f"{code}.json", "w") as f:
            json.dump(records, f)
        count += 1

    print(f"  commodity_edges/: {count} commodity files")


def export_filtration():
    """Export filtration results."""
    df = pd.read_csv(VIZ_DATA / "filtration_results_51x51.csv").rename(columns={"label": "state"})

    filtration = {}
    for label in df["threshold_label"].unique():
        subset = df[df["threshold_label"] == label].copy()
        subset["rank_betweenness"] = subset["betweenness"].rank(ascending=False, method="min").astype(int)
        subset["rank_eigenvector"] = subset["eigenvector"].rank(ascending=False, method="min").astype(int)
        subset["rank_out_degree"] = subset["out_degree"].rank(ascending=False, method="min").astype(int)
        filtration[label] = subset[
            ["state_id", "state", "betweenness", "eigenvector", "out_degree",
             "rank_betweenness", "rank_eigenvector", "rank_out_degree", "threshold"]
        ].to_dict(orient="records")

    with open(OUT_DIR / "filtration.json", "w") as f:
        json.dump(filtration, f)
    print(f"  filtration.json: {len(filtration)} thresholds")


def export_network_stats():
    """Export network-level summary statistics."""
    graph_path = VIZ_DATA / "network_graph.gpickle"
    c51 = pd.read_csv(VIZ_DATA / "centralities_51x51.csv")

    with open(graph_path, "rb") as f:
        G = pickle.load(f)

    stats = {
        "nodes": len(c51),
        "edges": G.number_of_edges(),
        "density": round(nx.density(G), 4),
        "clustering_coefficient": round(nx.average_clustering(G, weight="weight"), 4),
        "reciprocity": round(nx.reciprocity(G), 4),
    }

    with open(OUT_DIR / "network_stats.json", "w") as f:
        json.dump(stats, f, indent=2)
    print(f"  network_stats.json: {stats}")


def export_metadata():
    """Export commodity groups, SCTG names, and other reference data."""
    metadata = {
        "commodity_groups": COMMODITY_GROUPS,
        "sctg_names": SCTG_NAMES,
    }
    with open(OUT_DIR / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    print("  metadata.json: commodity groups + SCTG names")


def export_state_trade_totals(top_n=8):
    """Export each state's TRUE total inbound/outbound trade and top partners.

    Reads the full bilateral flow matrix (all 2,534 interstate edges), not the
    top-N display backbone, so the dashboard's state panel reflects real totals
    instead of only the corridors currently drawn on the map.
    """
    df = pd.read_csv(PROJECT_ROOT / "data" / "bilateral_flows_51x51.csv")
    states = sorted(set(df["origin"]) | set(df["destination"]))
    records = []
    for st in states:
        out_df = df[df["origin"] == st]
        in_df = df[df["destination"] == st]
        top_out = out_df.sort_values("trade_value_usd", ascending=False).head(top_n)
        top_in = in_df.sort_values("trade_value_usd", ascending=False).head(top_n)
        records.append({
            "state": st,
            "out_total": round(float(out_df["trade_value_usd"].sum()), 2),
            "in_total": round(float(in_df["trade_value_usd"].sum()), 2),
            "top_out": [
                {"partner": r.destination, "weight": round(float(r.trade_value_usd), 2)}
                for r in top_out.itertuples()
            ],
            "top_in": [
                {"partner": r.origin, "weight": round(float(r.trade_value_usd), 2)}
                for r in top_in.itertuples()
            ],
        })
    with open(OUT_DIR / "state_trade_totals.json", "w") as f:
        json.dump(records, f)
    print(f"  state_trade_totals.json: {len(records)} states")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "commodity_edges").mkdir(exist_ok=True)

    print("Exporting viz data to JSON...")
    coords, gdp, c51, c52 = load_and_merge()
    export_centralities(c51, c52)
    export_rank_changes(c51, c52)
    export_top_edges()
    export_commodity_data()
    export_filtration()
    export_network_stats()
    export_metadata()
    export_state_trade_totals()
    print(f"\nDone. Output: {OUT_DIR}")


if __name__ == "__main__":
    main()
