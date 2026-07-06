import marimo

__generated_with = "0.19.11"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    import pandas as pd
    import altair as alt

    return (alt, pd)


@app.cell
def _(pd):
    cols = ["ORIG_STATE", "DEST_STATE", "SHIPMT_VALUE", "WGT_FACTOR", "SCTG"]
    df = pd.read_csv(
        "/Users/home/Desktop/halcyonic-projects/active/cfs-network-analysis/data/cfs_2017_puf.csv",
        usecols=cols,
    )
    df
    return (df,)


@app.cell
def _(df, mo):
    mo.md(f"""
    **{df.shape[0]:,} rows × {df.shape[1]} columns**
    """)
    return


@app.cell
def _(pd):
    # Load centralities and GDP
    cent = pd.read_csv(
        "/Users/home/Desktop/halcyonic-projects/active/us-trade-centrality/results/51x51_domestic/centralities_51x51_domestic.csv"
    )
    gdp = pd.read_csv(
        "/Users/home/Desktop/halcyonic-projects/active/us-trade-centrality/data/state_gdp_2017.csv"
    )

    fips = {
        1: "AL", 2: "AK", 4: "AZ", 5: "AR", 6: "CA", 8: "CO", 9: "CT",
        10: "DE", 11: "DC", 12: "FL", 13: "GA", 15: "HI", 16: "ID",
        17: "IL", 18: "IN", 19: "IA", 20: "KS", 21: "KY", 22: "LA",
        23: "ME", 24: "MD", 25: "MA", 26: "MI", 27: "MN", 28: "MS",
        29: "MO", 30: "MT", 31: "NE", 32: "NV", 33: "NH", 34: "NJ",
        35: "NM", 36: "NY", 37: "NC", 38: "ND", 39: "OH", 40: "OK",
        41: "OR", 42: "PA", 44: "RI", 45: "SC", 46: "SD", 47: "TN",
        48: "TX", 49: "UT", 50: "VT", 51: "VA", 53: "WA", 54: "WV",
        55: "WI", 56: "WY",
    }
    cent["state_abbrev"] = cent["state_id"].map(fips)

    merged = cent.merge(gdp[["state_abbrev", "gdp_2017_q4_millions"]], on="state_abbrev")
    merged["rank_gdp"] = merged["gdp_2017_q4_millions"].rank(ascending=False).astype(int)
    merged["delta_eigenvector"] = merged["rank_gdp"] - merged["rank_eigenvector"]

    display_df = merged[["state_abbrev", "rank_gdp", "rank_eigenvector", "delta_eigenvector"]].copy()
    display_df.columns = ["State", "GDP Rank", "Eigenvector Rank", "Δ (GDP − Eigenvector)"]
    display_df = display_df.reindex(
        display_df["Δ (GDP − Eigenvector)"].abs().sort_values(ascending=False).index
    )

    top_over = display_df[display_df["Δ (GDP − Eigenvector)"] > 0].head(5)
    top_under = display_df[display_df["Δ (GDP − Eigenvector)"] < 0].head(5)
    result = pd.concat([top_over, top_under]).reset_index(drop=True)
    return (display_df, result)


@app.cell
def _(display_df, mo, result):
    divergent = (display_df["Δ (GDP − Eigenvector)"].abs() >= 5).sum()
    mo.vstack([
        mo.md("### Eigenvector Centrality vs GDP: Largest Divergences"),
        result,
        mo.md(f"**{divergent} of {len(display_df)} states** diverge by 5+ rank positions"),
    ])
    return


@app.cell
def _(pd):
    from scipy.stats import spearmanr

    fips_map = {
        1: "AL", 2: "AK", 4: "AZ", 5: "AR", 6: "CA", 8: "CO", 9: "CT",
        10: "DE", 11: "DC", 12: "FL", 13: "GA", 15: "HI", 16: "ID",
        17: "IL", 18: "IN", 19: "IA", 20: "KS", 21: "KY", 22: "LA",
        23: "ME", 24: "MD", 25: "MA", 26: "MI", 27: "MN", 28: "MS",
        29: "MO", 30: "MT", 31: "NE", 32: "NV", 33: "NH", 34: "NJ",
        35: "NM", 36: "NY", 37: "NC", 38: "ND", 39: "OH", 40: "OK",
        41: "OR", 42: "PA", 44: "RI", 45: "SC", 46: "SD", 47: "TN",
        48: "TX", 49: "UT", 50: "VT", 51: "VA", 53: "WA", 54: "WV",
        55: "WI", 56: "WY",
    }

    dom_raw = pd.read_csv(
        "/Users/home/Desktop/halcyonic-projects/active/us-trade-centrality/results/51x51_domestic/centralities_51x51_domestic.csv"
    )
    intl_raw = pd.read_csv(
        "/Users/home/Desktop/halcyonic-projects/active/us-trade-centrality/results/52x52_international/centralities_52x52_intl.csv"
    )

    common_ids = set(dom_raw["state_id"]) & set(intl_raw["state_id"])
    dom_c = dom_raw[dom_raw["state_id"].isin(common_ids)].set_index("state_id").sort_index()
    intl_c = intl_raw[intl_raw["state_id"].isin(common_ids)].set_index("state_id").sort_index()

    # Re-rank within 51 common states (not using pre-computed ranks from 52-state set)
    # Use method="first" to break ties and spread zero-betweenness states across unique ranks
    dom_c["btw_rank_51"] = dom_c["betweenness"].rank(ascending=False, method="first").astype(int)
    intl_c["btw_rank_51"] = intl_c["betweenness"].rank(ascending=False, method="first").astype(int)
    dom_c["label"] = dom_c.index.map(fips_map)
    intl_c["label"] = intl_c.index.map(fips_map)

    # Boundary stats for bar chart
    boundary_stats = []
    for m in ["betweenness", "eigenvector", "out_degree"]:
        d = dom_c[m].rank(ascending=False, method="min").astype(int)
        i = intl_c[m].rank(ascending=False, method="min").astype(int)
        shift = (d - i).abs()
        rho, _ = spearmanr(dom_c[m], intl_c[m])
        boundary_stats.append({
            "Measure": m.replace("_", " ").title(),
            "rho": rho,
            "avg_shift": shift.mean(),
            "max_shift": int(shift.max()),
        })

    boundary_df = pd.DataFrame(boundary_stats)

    # Scatter: all 51 states, method='first' for visual spread (matches thesis figure code)
    # ρ computed on raw values within 51 common states (matches thesis TEXT: 0.816)
    btw_rho, _ = spearmanr(dom_c["betweenness"], intl_c["betweenness"])

    # Rank domestic within 51 states
    dom_btw_rank = dom_c["betweenness"].rank(ascending=False, method="first").astype(int)

    # Rank international within ALL 52 states (including RoW) — matches thesis figure code
    # Then filter to 51 common states for the scatter
    intl_all = intl_raw.copy()
    intl_all["label"] = intl_all["state_id"].map(fips_map)
    intl_all["btw_rank_52"] = intl_all["betweenness"].rank(ascending=False, method="first").astype(int)
    intl_52_ranks = intl_all.set_index("state_id")["btw_rank_52"]
    intl_btw_rank = intl_52_ranks.loc[dom_c.index]

    scatter_df = pd.DataFrame({
        "label": dom_c["label"].values,
        "dom_rank": dom_btw_rank.values,
        "intl_rank": intl_btw_rank.values,
    })
    scatter_df["rank_change"] = scatter_df["intl_rank"] - scatter_df["dom_rank"]
    scatter_df["abs_change"] = scatter_df["rank_change"].abs()
    scatter_df["status"] = scatter_df["rank_change"].apply(
        lambda x: "Rank Improved" if x < 0 else ("Rank Declined" if x > 0 else "Unchanged")
    )

    return (boundary_df, btw_rho, scatter_df)


@app.cell
def _(alt, boundary_df, mo):
    chart = alt.Chart(boundary_df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        x=alt.X("Measure:N", sort=["Betweenness", "Eigenvector", "Out Degree"], axis=alt.Axis(labelFontSize=14, titleFontSize=14)),
        y=alt.Y("avg_shift:Q", title="Average Rank Shift (positions)", scale=alt.Scale(domain=[0, 7]), axis=alt.Axis(labelFontSize=13, titleFontSize=14)),
        color=alt.Color("Measure:N", scale=alt.Scale(
            domain=["Betweenness", "Eigenvector", "Out Degree"],
            range=["#6a994e", "#7b2d8e", "#e07a5f"]
        ), legend=None),
    ).properties(
        width=400,
        height=300,
        title=alt.TitleParams("Average Rank Shift: 51x51 vs 52x52", fontSize=16),
    )

    text = chart.mark_text(dy=-12, fontSize=14, fontWeight="bold").encode(
        text=alt.Text("avg_shift:Q", format=".1f"),
    )

    mo.vstack([
        chart + text,
        mo.md("*Betweenness states shift 5.3 positions on average vs 2.4 (eigenvector) and 1.5 (out-degree)*"),
    ])
    return


@app.cell
def _(alt, btw_rho, mo, scatter_df):
    # Thesis-style scatter: all 51 states, axes inverted (rank 1 = top-left)
    # ρ from raw values (0.816), change count from re-ranked within 51

    color_scale = alt.Scale(
        domain=["Rank Improved", "Rank Declined", "Unchanged"],
        range=["#27AE60", "#E74C3C", "#95A5A6"]
    )

    max_rank = 52
    diag = alt.Chart(
        {"values": [{"x": 0, "y": 0}, {"x": max_rank, "y": max_rank}]}
    ).mark_line(strokeDash=[6, 4], color="black", opacity=0.5, strokeWidth=2).encode(
        x="x:Q", y="y:Q"
    )

    points = alt.Chart(scatter_df).mark_circle(
        size=120, opacity=0.7, stroke="white", strokeWidth=1.5
    ).encode(
        x=alt.X("dom_rank:Q",
                 title="Rank in 51x51 Domestic Network (1 = Highest Betweenness)",
                 scale=alt.Scale(domain=[max_rank, 0]),
                 axis=alt.Axis(labelFontSize=12, titleFontSize=13)),
        y=alt.Y("intl_rank:Q",
                 title="Rank in 52x52 International Network (1 = Highest Betweenness)",
                 scale=alt.Scale(domain=[max_rank, 0]),
                 axis=alt.Axis(labelFontSize=12, titleFontSize=13)),
        color=alt.Color("status:N", scale=color_scale,
                         legend=alt.Legend(title=None, orient="top-left", labelFontSize=12)),
        tooltip=["label:N", "dom_rank:Q", "intl_rank:Q", "rank_change:Q"],
    )

    # Bold labels for big movers, small for rest
    big_movers = scatter_df[scatter_df["abs_change"] >= 5]
    small_movers = scatter_df[scatter_df["abs_change"] < 5]

    big_labels = alt.Chart(big_movers).mark_text(
        dx=8, dy=-8, fontSize=11, fontWeight="bold"
    ).encode(
        x="dom_rank:Q", y="intl_rank:Q", text="label:N",
        color=alt.Color("status:N", scale=color_scale, legend=None),
    )

    small_labels = alt.Chart(small_movers).mark_text(
        dx=7, dy=-7, fontSize=9
    ).encode(
        x="dom_rank:Q", y="intl_rank:Q", text="label:N",
        color=alt.value("#666666"),
    )

    n_changed = (scatter_df["abs_change"] > 0).sum()
    n_total = len(scatter_df)

    scatter_chart = (diag + points + big_labels + small_labels).properties(
        width=500,
        height=500,
        title=alt.TitleParams("Betweenness Rank Stability", fontSize=18),
    )

    mo.vstack([
        scatter_chart,
        mo.md(f"**ρ = {btw_rho:.3f}  |  Changed: {n_changed}/{n_total} ({100*n_changed/n_total:.0f}%)**"),
    ])
    return


if __name__ == "__main__":
    app.run()
