# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "pandas==2.3.1",
#     "numpy==2.3.2",
#     "altair==5.5.0",
#     "plotly==5.24.1",
#     "scipy==1.16.1",
# ]
# [tool.marimo.display]
# theme = "system"
# ///

import marimo

__generated_with = "0.19.11"
app = marimo.App(width="full", auto_download=["html"])

with app.setup(hide_code=True):
    import pandas as pd
    import numpy as np
    import altair as alt
    import sys
    from pathlib import Path
    from scipy.stats import spearmanr
    import plotly.express as px

    _toolkit_path = str(Path(__file__).parent.parent / "cfs-network-toolkit")
    if _toolkit_path not in sys.path:
        sys.path.insert(0, _toolkit_path)

    from cfs_toolkit.analysis import load_network_graph
    from cfs_toolkit.core import compute_all_centralities
    from cfs_toolkit.core.normalizations import gdp_sender, gdp_geometric


@app.cell
def intro():
    import marimo as mo

    mo.md("""
    # Pre-Normalization Sensitivity Analysis

    The thesis computes centrality on **raw dollar-weighted** trade flows.
    This notebook asks: **do the rankings change if we normalize edge weights
    by GDP before computing centrality?**

    Two GDP-based normalizations are tested against the baseline (raw) results:

    | Variant | Formula | What it asks |
    |---------|---------|-------------|
    | **GDP-Sender** | A'[i][j] = A[i][j] / GDPᵢ | "Relative to the size of its economy, how much does state i trade with j?" |
    | **GDP-Geometric** | A'[i][j] = A[i][j] / √(GDPᵢ × GDPⱼ) | "Controlling for economic size of both endpoints, how strong is this trade link?" |

    GDP-Sender is the conservative test — it directly addresses whether
    rankings are an artifact of large economies producing large flows.
    GDP-Geometric is more aggressive — it also penalizes flows *to* large economies.

    Both use the same `compute_all_centralities()` function from the toolkit.
    The only thing that changes is the edge weights fed into it.
    """)


@app.cell
def load_data():
    REPO_ROOT = Path(__file__).parent.parent
    DOMESTIC_RUN = REPO_ROOT / "results" / "51x51_domestic"

    G_raw = load_network_graph(DOMESTIC_RUN)
    baseline = pd.read_csv(DOMESTIC_RUN / "centralities_51x51_domestic.csv")
    gdp_df = pd.read_csv(REPO_ROOT / "data" / "state_gdp_2017.csv")

    assert G_raw.number_of_nodes() == 51
    assert len(baseline) == 51

    weights = [d["weight"] for _, _, d in G_raw.edges(data=True)]

    import marimo as mo
    mo.md(f"""
    ## Data Loaded

    - **Network**: {G_raw.number_of_nodes()} nodes, {G_raw.number_of_edges()} edges
    - **Edge weight range**: ${min(weights)/1e9:.2f}B – ${max(weights)/1e9:.2f}B
    - **Density**: {G_raw.number_of_edges() / (51 * 50) * 100:.1f}%
    """)

    return G_raw, baseline, gdp_df, REPO_ROOT


@app.cell
def compute_variants(G_raw, baseline, gdp_df):
    variants = {
        "GDP-Sender": gdp_sender(G_raw, gdp_df),
        "GDP-Geometric": gdp_geometric(G_raw, gdp_df),
    }

    measures = ["betweenness", "eigenvector", "out_degree"]

    norm_results = {}
    for name, G_norm in variants.items():
        df = compute_all_centralities(G_norm)
        for col in measures:
            df[f"rank_{col}"] = df[col].rank(ascending=False, method="min").astype(int)
        norm_results[name] = df

    return norm_results, measures


@app.cell
def spearman_table(baseline, norm_results, measures):
    import marimo as mo

    summary_rows = []
    for name, df in norm_results.items():
        merged = baseline.merge(
            df[["label"] + measures], on="label", suffixes=("_base", "_norm")
        )
        row = {"Normalization": name}
        for m in measures:
            rho, _ = spearmanr(merged[f"{m}_base"], merged[f"{m}_norm"])
            row[f"ρ ({m})"] = round(rho, 3)
        summary_rows.append(row)

    rho_df = pd.DataFrame(summary_rows)

    delta_rows = []
    for name, df in norm_results.items():
        merged = baseline[["label"] + [f"rank_{m}" for m in measures]].merge(
            df[["label"] + [f"rank_{m}" for m in measures]],
            on="label",
            suffixes=("_base", "_norm"),
        )
        row = {"Normalization": name}
        for m in measures:
            mean_delta = (
                (merged[f"rank_{m}_base"] - merged[f"rank_{m}_norm"]).abs().mean()
            )
            row[f"Mean |Δrank| ({m})"] = round(mean_delta, 1)
        delta_rows.append(row)

    delta_df = pd.DataFrame(delta_rows)

    mo.md(f"""
    ## Spearman Rank Correlation vs Baseline

    How much do rankings change under each normalization?
    ρ = 1.0 means identical rankings; ρ = 0 means no relationship.

    {rho_df.to_markdown(index=False)}

    ## Mean Absolute Rank Change

    Average number of rank positions each state moves.

    {delta_df.to_markdown(index=False)}
    """)

    return rho_df, delta_df


@app.cell
def biggest_movers(baseline, norm_results, measures):
    import marimo as mo

    sections = []
    for name, df in norm_results.items():
        for m in measures:
            merged = baseline[["label", f"rank_{m}"]].merge(
                df[["label", f"rank_{m}"]], on="label", suffixes=("_raw", "_norm")
            )
            merged["delta"] = merged[f"rank_{m}_raw"] - merged[f"rank_{m}_norm"]
            merged["abs_delta"] = merged["delta"].abs()
            top5 = merged.nlargest(5, "abs_delta")

            m_label = m.replace("_", " ").title()
            lines = [f"**{name} — {m_label}**\n"]
            for _, row in top5.iterrows():
                d = int(row["delta"])
                sign = "+" if d > 0 else ""
                lines.append(
                    f"- {row['label']}: {int(row[f'rank_{m}_raw'])} → "
                    f"{int(row[f'rank_{m}_norm'])} ({sign}{d})"
                )
            sections.append("\n".join(lines))

    mo.md("## Biggest Movers\n\n" + "\n\n".join(sections))


@app.cell
def eigenvector_comparison_chart(baseline, norm_results):
    import marimo as mo

    chart_rows = []
    for name, df in norm_results.items():
        merged = baseline[["label", "rank_eigenvector"]].merge(
            df[["label", "rank_eigenvector"]], on="label", suffixes=("_raw", "_norm")
        )
        merged["normalization"] = name
        chart_rows.append(merged)

    chart_df = pd.concat(chart_rows, ignore_index=True)

    scatter = (
        alt.Chart(chart_df)
        .mark_circle(size=60)
        .encode(
            x=alt.X(
                "rank_eigenvector_raw:Q",
                title="Raw Eigenvector Rank",
                scale=alt.Scale(domain=[1, 51]),
            ),
            y=alt.Y(
                "rank_eigenvector_norm:Q",
                title="GDP-Normalized Eigenvector Rank",
                scale=alt.Scale(domain=[1, 51]),
            ),
            color=alt.Color("normalization:N", title="Normalization"),
            tooltip=["label", "rank_eigenvector_raw", "rank_eigenvector_norm", "normalization"],
        )
        .properties(width=500, height=500, title="Eigenvector Rank Stability Under GDP Pre-Normalization")
    )

    diagonal = (
        alt.Chart(pd.DataFrame({"x": [1, 51], "y": [1, 51]}))
        .mark_line(strokeDash=[5, 5], color="gray")
        .encode(x="x:Q", y="y:Q")
    )

    mo.ui.altair_chart(scatter + diagonal)


@app.cell
def interpretation():
    import marimo as mo

    mo.md("""
    ## Key Findings

    **GDP-sender normalization (ρ = 0.980) directly addresses the "big states" concern.**
    Dividing each edge by the sender's GDP asks: "relative to its economy,
    how much does state i trade with j?" The top 5 barely change (TX, CA, IL, OH, FL).
    The biggest movers are mid-tier: MN rises 7 positions, AZ and HI drop 6.
    This confirms that the raw-weight eigenvector rankings are not merely
    an artifact of economic size.

    **GDP-geometric normalization (ρ = 0.886) is a more aggressive test.**
    Controlling for both sender and receiver GDP amplifies divergences:
    CA drops from rank 2 to 19, MS rises from 27 to 11, TN rises to rank 1.
    This is consistent with the structural undervaluation finding —
    the same states the thesis identifies as "punching above their weight"
    rise further when GDP scale effects are removed from both endpoints.

    **Betweenness is moderately sensitive to both normalizations.**
    ρ = 0.601 (sender) and 0.736 (geometric). Path-based measures respond
    non-linearly to weight transformations because shortest-path calculations
    depend on relative edge magnitudes across the entire network.

    ## Defense Implication

    The core thesis finding — that centrality reveals structural patterns
    invisible to GDP — holds under GDP pre-normalization. The conservative test
    (GDP-sender, ρ = 0.980) shows eigenvector rankings are not a "big states"
    artifact. The aggressive test (GDP-geometric, ρ = 0.886) amplifies the
    structural undervaluation pattern the thesis already identifies.
    Pre-normalization refines the finding — it does not overturn it.
    """)


@app.cell
def export_results(norm_results, baseline, measures, REPO_ROOT):
    import marimo as mo

    output_dir = REPO_ROOT / "results" / "normalization_comparison"
    output_dir.mkdir(exist_ok=True)

    all_dfs = []
    baseline_copy = baseline.copy()
    baseline_copy["normalization"] = "Raw (baseline)"
    all_dfs.append(baseline_copy)
    for name, df in norm_results.items():
        df_copy = df.copy()
        df_copy["normalization"] = name
        all_dfs.append(df_copy)

    full = pd.concat(all_dfs, ignore_index=True)
    full.to_csv(output_dir / "all_centralities.csv", index=False)

    summary_rows = []
    for name, df in norm_results.items():
        merged = baseline.merge(
            df[["label"] + measures], on="label", suffixes=("_base", "_norm")
        )
        row = {"normalization": name}
        for m in measures:
            rho, _ = spearmanr(merged[f"{m}_base"], merged[f"{m}_norm"])
            merged_ranks = baseline[["label", f"rank_{m}"]].merge(
                df[["label", f"rank_{m}"]], on="label", suffixes=("_base", "_norm")
            )
            mean_delta = (
                (merged_ranks[f"rank_{m}_base"] - merged_ranks[f"rank_{m}_norm"])
                .abs()
                .mean()
            )
            row[f"rho_{m}"] = round(rho, 3)
            row[f"mean_delta_{m}"] = round(mean_delta, 1)
        summary_rows.append(row)

    pd.DataFrame(summary_rows).to_csv(output_dir / "summary.csv", index=False)

    mo.md(f"Results exported to `{output_dir.relative_to(REPO_ROOT)}/`")


if __name__ == "__main__":
    app.run()
