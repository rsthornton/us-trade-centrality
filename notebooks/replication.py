# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "pandas==2.3.1",
#     "numpy==2.3.2",
#     "altair==5.5.0",
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

    # Add toolkit to path for analysis functions
    _toolkit_path = str(Path(__file__).parent.parent / "cfs-network-toolkit")
    if _toolkit_path not in sys.path:
        sys.path.insert(0, _toolkit_path)

    from cfs_toolkit.analysis import (
        load_network_graph,
        extract_edge_weights,
        scan_filtration_range,
        filter_graph_by_percentile,
        load_gdp_data,
        compute_gdp_vs_centrality_comparison,
        identify_outliers,
        align_measures,
        rank_columns,
        compute_rank_correlations,
        compute_rank_changes,
        summarize_effect_sizes,
        calculate_distribution_stats,
    )
    from cfs_toolkit.core import compute_all_centralities
    import networkx as nx
    import marimo as mo

    FIPS_TO_STATE = {
        1: 'AL', 2: 'AK', 4: 'AZ', 5: 'AR', 6: 'CA', 8: 'CO', 9: 'CT', 10: 'DE',
        11: 'DC', 12: 'FL', 13: 'GA', 15: 'HI', 16: 'ID', 17: 'IL', 18: 'IN',
        19: 'IA', 20: 'KS', 21: 'KY', 22: 'LA', 23: 'ME', 24: 'MD', 25: 'MA',
        26: 'MI', 27: 'MN', 28: 'MS', 29: 'MO', 30: 'MT', 31: 'NE', 32: 'NV',
        33: 'NH', 34: 'NJ', 35: 'NM', 36: 'NY', 37: 'NC', 38: 'ND', 39: 'OH',
        40: 'OK', 41: 'OR', 42: 'PA', 44: 'RI', 45: 'SC', 46: 'SD', 47: 'TN',
        48: 'TX', 49: 'UT', 50: 'VT', 51: 'VA', 53: 'WA', 54: 'WV', 55: 'WI', 56: 'WY'
    }

    MEASURES = ['betweenness', 'eigenvector', 'out_degree']


@app.cell(hide_code=True)
def _():
    # REPLICATION NOTE: Domestic network produced by:
    #   python main.py --config configs/domestic.yaml
    # International network produced by:
    #   python main.py --config configs/international.yaml
    # Both runs dated 2025-11-29 with weight inversion fix applied.

    REPO_ROOT = Path(__file__).parent.parent

    DOMESTIC_RUN = REPO_ROOT / "results" / "51x51_domestic"
    INTL_RUN = REPO_ROOT / "results" / "52x52_international"

    # Load pre-computed centrality CSVs
    # Columns: state_id, label, betweenness, eigenvector, out_degree,
    #          rank_betweenness, rank_eigenvector, rank_out_degree
    domestic_df = pd.read_csv(DOMESTIC_RUN / "centralities_51x51_domestic.csv")
    intl_df = pd.read_csv(INTL_RUN / "centralities_52x52_intl.csv")

    # REPLICATION NOTE: Graphs can be rebuilt from raw CFS PUF via the pipeline.
    # Pre-computed gpickle files used here for speed.
    G_domestic = load_network_graph(DOMESTIC_RUN)
    G_intl = load_network_graph(INTL_RUN)

    # REPLICATION NOTE: GDP data from BEA Table SQGDP1, 2017 Q4 (millions).
    gdp_dict = load_gdp_data(REPO_ROOT / "data" / "state_gdp_2017.csv")

    # Verification: CA = #1 betweenness confirms weight inversion fix
    _top_betw = domestic_df.loc[domestic_df['rank_betweenness'] == 1, 'label'].iloc[0]
    assert _top_betw == 'CA', f"Expected CA as #1 betweenness, got {_top_betw}"

    mo.output.replace(
        mo.md(f"**Data loaded** — Domestic: {len(domestic_df)} states, "
              f"International: {len(intl_df)} entities, "
              f"GDP: {len(gdp_dict)} states")
    )
    return G_domestic, domestic_df, gdp_dict, intl_df


@app.cell(hide_code=True)
def _(G_domestic):
    _weights = extract_edge_weights(G_domestic)
    _stats = calculate_distribution_stats(_weights, "51x51_domestic")

    _density = nx.density(G_domestic)
    _total_volume = _weights.sum()

    mo.output.replace(mo.md(f"""## Section 1: Data Exploration

    ### Network Descriptive Statistics (51×51 Domestic)

    | Metric | Value |
    |--------|-------|
    | Nodes | {G_domestic.number_of_nodes()} |
    | Edges | {G_domestic.number_of_edges():,} |
    | Density | {_density:.4f} |
    | Total volume | ${_total_volume / 1e9:,.1f}B |
    | Mean weight | ${_stats['mean'] / 1e6:,.1f}M |
    | Median weight | ${_stats['median'] / 1e6:,.1f}M |
    | Std dev | ${_stats['std'] / 1e6:,.1f}M |
    | Min | ${_stats['min'] / 1e6:,.2f}M |
    | Max | ${_stats['max'] / 1e6:,.1f}M |
    | IQR | ${_stats['iqr'] / 1e6:,.1f}M |
    """))
    return


@app.cell(hide_code=True)
def _(G_domestic):
    _weights = extract_edge_weights(G_domestic)
    _weight_df = pd.DataFrame({'weight_billions': _weights / 1e9})
    _mean_val = _weights.mean() / 1e9
    _median_val = np.median(_weights) / 1e9

    _base = alt.Chart(_weight_df).mark_bar(opacity=0.7).encode(
        alt.X('weight_billions:Q', bin=alt.Bin(maxbins=50), title='Edge Weight ($ Billions)'),
        alt.Y('count()', title='Frequency'),
    ).properties(title='Edge Weight Distribution (51×51 Domestic)', width=700, height=350)

    _mean_rule = alt.Chart(pd.DataFrame({'x': [_mean_val]})).mark_rule(
        color='red', strokeDash=[4, 4], strokeWidth=2
    ).encode(x='x:Q')

    _median_rule = alt.Chart(pd.DataFrame({'x': [_median_val]})).mark_rule(
        color='orange', strokeDash=[2, 2], strokeWidth=2
    ).encode(x='x:Q')

    _mean_label = alt.Chart(pd.DataFrame({'x': [_mean_val], 'text': [f'Mean: ${_mean_val:.1f}B']})).mark_text(
        align='left', dx=5, dy=-10, color='red', fontSize=11
    ).encode(x='x:Q', text='text:N')

    _median_label = alt.Chart(pd.DataFrame({'x': [_median_val], 'text': [f'Median: ${_median_val:.1f}B']})).mark_text(
        align='left', dx=5, dy=10, color='orange', fontSize=11
    ).encode(x='x:Q', text='text:N')

    weight_dist_chart = (_base + _mean_rule + _median_rule + _mean_label + _median_label)
    mo.output.replace(weight_dist_chart)
    return


@app.cell(hide_code=True)
def _(G_domestic):
    _edges = [
        {
            'origin': FIPS_TO_STATE.get(u, str(u)),
            'destination': FIPS_TO_STATE.get(v, str(v)),
            'weight_billions': d['weight'] / 1e9,
        }
        for u, v, d in G_domestic.edges(data=True)
    ]
    _edge_df = pd.DataFrame(_edges).sort_values('weight_billions', ascending=False).head(10).reset_index(drop=True)
    _edge_df.index = _edge_df.index + 1
    _edge_df.columns = ['Origin', 'Destination', 'Trade Volume ($B)']
    _edge_df['Trade Volume ($B)'] = _edge_df['Trade Volume ($B)'].round(2)

    mo.output.replace(mo.vstack([
        mo.md("### Top 10 Trade Corridors by Volume"),
        mo.ui.table(_edge_df, selection=None),
    ]))
    return


@app.cell(hide_code=True)
def _():
    mo.output.replace(mo.md("""## Section 2: Centrality Computation

    ### Three-Measure Framework

    The analysis employs three centrality measures capturing distinct structural roles:

    1. **Betweenness centrality** — Brokerage: fraction of shortest paths passing through a state.
       Higher values indicate gateway/bridge positions in the trade network.

    2. **Eigenvector centrality** — Prestige: importance weighted by the importance of trading partners.
       Higher values indicate connection to other high-volume states.

    3. **Out-degree centrality** (weighted) — Activity: normalized total outbound trade volume.
       Higher values indicate broad distribution of exports across many partners.

    **Weight inversion**: Edge weights represent trade volume (higher = stronger connection).
    For shortest-path computation, weights are inverted: `distance = max_weight / weight`.
    This ensures high-volume corridors are treated as "short" paths.

    Canonical implementation: `cfs_toolkit.core.compute_all_centralities()`
    """))
    return


@app.cell(hide_code=True)
def _(domestic_df):
    _charts = []
    _titles = {
        'betweenness': 'Betweenness (Brokerage)',
        'eigenvector': 'Eigenvector (Prestige)',
        'out_degree': 'Out-Degree (Activity)',
    }
    for _measure in MEASURES:
        _top10 = domestic_df.nlargest(10, _measure)[['label', _measure]].copy()
        _chart = alt.Chart(_top10).mark_bar().encode(
            x=alt.X(f'{_measure}:Q', title=_titles[_measure]),
            y=alt.Y('label:N', sort='-x', title=''),
            tooltip=[alt.Tooltip('label:N', title='State'),
                     alt.Tooltip(f'{_measure}:Q', format='.4f', title='Score')],
        ).properties(title=f'Top 10: {_titles[_measure]}', width=250, height=250)
        _charts.append(_chart)

    domestic_centrality_chart = alt.hconcat(*_charts).properties(
        title='51×51 Domestic Network — Top 10 by Centrality Measure'
    )
    mo.output.replace(domestic_centrality_chart)
    return


@app.cell(hide_code=True)
def _(intl_df):
    # Note: RoW (Rest of World, node 52) dominates all measures in the international network.
    # Display includes RoW to show its effect.
    _charts = []
    _titles = {
        'betweenness': 'Betweenness (Brokerage)',
        'eigenvector': 'Eigenvector (Prestige)',
        'out_degree': 'Out-Degree (Activity)',
    }
    for _measure in MEASURES:
        _top10 = intl_df.nlargest(10, _measure)[['label', _measure]].copy()
        _chart = alt.Chart(_top10).mark_bar().encode(
            x=alt.X(f'{_measure}:Q', title=_titles[_measure]),
            y=alt.Y('label:N', sort='-x', title=''),
            color=alt.condition(
                alt.datum.label == 'RoW',
                alt.value('#e45756'),
                alt.value('#4c78a8'),
            ),
            tooltip=[alt.Tooltip('label:N', title='State'),
                     alt.Tooltip(f'{_measure}:Q', format='.4f', title='Score')],
        ).properties(title=f'Top 10: {_titles[_measure]}', width=250, height=250)
        _charts.append(_chart)

    intl_centrality_chart = alt.hconcat(*_charts).properties(
        title='52×52 International Network — Top 10 by Centrality Measure (RoW in red)'
    )
    mo.output.replace(intl_centrality_chart)
    return


@app.cell(hide_code=True)
def _(G_domestic):
    # REPLICATION NOTE: scan_filtration_range checks SCC count at each percentile.
    # Breaking point expected around 33% based on prior pipeline runs.
    _scan_df = scan_filtration_range(G_domestic, 0, 50)

    _break_row = _scan_df[_scan_df['is_connected'] == False]
    _break_pct = int(_break_row.iloc[0]['percentile']) if len(_break_row) > 0 else None

    _chart = alt.Chart(_scan_df).mark_line(point=True).encode(
        x=alt.X('percentile:Q', title='Filtration Percentile (%)'),
        y=alt.Y('n_scc:Q', title='Strongly Connected Components'),
        tooltip=[
            alt.Tooltip('percentile:Q', title='Percentile'),
            alt.Tooltip('n_scc:Q', title='SCCs'),
            alt.Tooltip('edges:Q', title='Edges remaining'),
        ],
    ).properties(
        title='Network Connectivity Under Filtration (51×51 Domestic)',
        width=700, height=350,
    )

    # Annotation for breaking point
    _annotation_parts = [_chart]
    if _break_pct is not None:
        _break_rule = alt.Chart(pd.DataFrame({'x': [_break_pct]})).mark_rule(
            color='red', strokeDash=[4, 4], strokeWidth=2
        ).encode(x='x:Q')
        _break_label = alt.Chart(pd.DataFrame({
            'x': [_break_pct], 'y': [3],
            'text': [f'Breaks at {_break_pct}%']
        })).mark_text(align='left', dx=5, color='red', fontSize=12).encode(
            x='x:Q', y='y:Q', text='text:N'
        )
        _annotation_parts += [_break_rule, _break_label]

    filtration_chart = alt.layer(*_annotation_parts)
    mo.output.replace(mo.vstack([
        mo.md("## Section 3: Filtration Validation"),
        filtration_chart,
    ]))
    return


@app.cell(hide_code=True)
def _(G_domestic, domestic_df):
    # Compute centralities on filtered networks and compare via Spearman rho
    _thresholds = [10, 20, 30]
    _rows = []

    for _pct in _thresholds:
        _G_filt, _ = filter_graph_by_percentile(G_domestic, _pct)
        _filt_df = compute_all_centralities(_G_filt)

        for _measure in MEASURES:
            # Align on state_id for consistent comparison
            _baseline = domestic_df.set_index('state_id')[_measure]
            _filtered = _filt_df.set_index('state_id')[_measure]
            _common = _baseline.index.intersection(_filtered.index)
            _rho, _p = spearmanr(_baseline.loc[_common], _filtered.loc[_common])
            _rows.append({'Filtration %': f'{_pct}%', 'Measure': _measure, 'Spearman ρ': f'{_rho:.4f}'})

    _stability_df = pd.DataFrame(_rows).pivot(index='Filtration %', columns='Measure', values='Spearman ρ')
    _stability_df = _stability_df[MEASURES]

    # Format as markdown table
    _header = "| Filtration | " + " | ".join(MEASURES) + " |"
    _sep = "|" + "|".join(["---"] * (len(MEASURES) + 1)) + "|"
    _body = []
    for _idx in _stability_df.index:
        _vals = " | ".join(str(_stability_df.loc[_idx, m]) for m in MEASURES)
        _body.append(f"| {_idx} | {_vals} |")

    mo.output.replace(mo.md(f"""### Rank Stability Under Filtration

    Spearman rank correlation (ρ) between baseline and filtered centralities:

    {_header}
    {_sep}
    {chr(10).join(_body)}

    Higher ρ → rankings are robust to removal of low-weight edges.
    """))
    return


@app.cell(hide_code=True)
def _(G_domestic, domestic_df):
    # Compute 30% filtration rho for each measure
    _G_30, _ = filter_graph_by_percentile(G_domestic, 30)
    _df_30 = compute_all_centralities(_G_30)
    _summary_parts = []

    for _m in MEASURES:
        _baseline = domestic_df.set_index('state_id')[_m]
        _filtered = _df_30.set_index('state_id')[_m]
        _common = _baseline.index.intersection(_filtered.index)
        _rho, _ = spearmanr(_baseline.loc[_common], _filtered.loc[_common])
        _summary_parts.append(f"**{_m}** ρ = {_rho:.3f}")

    mo.output.replace(mo.md(
        f"**Filtration summary (30%):** At 30% filtration — removing the weakest "
        f"30% of trade corridors — rank correlations remain high: "
        f"{', '.join(_summary_parts)}. "
        f"This confirms that centrality rankings are driven by the high-volume backbone, "
        f"not noise from minor trade flows."
    ))
    return


@app.cell(hide_code=True)
def _(domestic_df, gdp_dict):
    _gdp_df = pd.DataFrame([
        {'label': k, 'gdp': v} for k, v in gdp_dict.items()
    ])
    _merged = domestic_df.merge(_gdp_df, on='label')
    _gdp_rank = _merged['gdp'].rank(ascending=False, method='min')

    _rows = []
    for _m in MEASURES:
        _rank_col = f'rank_{_m}'
        _rho, _p = spearmanr(_merged[_rank_col], _gdp_rank)
        _rows.append({'Measure': _m, 'Spearman ρ': f'{_rho:.4f}', 'p-value': f'{_p:.2e}'})

    _corr_df = pd.DataFrame(_rows)

    _header = "| Measure | Spearman ρ | p-value |"
    _sep = "|---|---|---|"
    _body = [f"| {r['Measure']} | {r['Spearman ρ']} | {r['p-value']} |" for _, r in _corr_df.iterrows()]

    mo.output.replace(mo.md(f"""## Section 4: GDP Divergence

    ### GDP-Centrality Rank Correlations

    {_header}
    {_sep}
    {chr(10).join(_body)}

    Measures how well economic size (GDP) predicts structural position in the trade network.
    """))
    return


@app.cell(hide_code=True)
def _(domestic_df, gdp_dict):
    _comparison_df = compute_gdp_vs_centrality_comparison(domestic_df, gdp_dict)
    _over, _under = identify_outliers(_comparison_df, threshold=5)

    # Top 5 overperformers
    _over_rows = []
    for _s, _rd, _gr, _er, _narr in _over[:5]:
        _over_rows.append(f"| {_s} | +{_rd} | {_gr} | {_er} | {_narr} |")

    # Top 5 underperformers
    _under_rows = []
    for _s, _rd, _gr, _er, _narr in _under[:5]:
        _under_rows.append(f"| {_s} | {_rd} | {_gr} | {_er} | {_narr} |")

    _header = "| State | Rank Diff | GDP Rank | Eig Rank | Narrative |"
    _sep = "|---|---|---|---|---|"

    mo.output.replace(mo.md(f"""### GDP vs Eigenvector Centrality: Rank Divergence

    **Overperformers** (structurally central beyond GDP):

    {_header}
    {_sep}
    {chr(10).join(_over_rows)}

    **Underperformers** (structurally peripheral despite GDP):

    {_header}
    {_sep}
    {chr(10).join(_under_rows)}

    Total outliers (|rank diff| ≥ 5): {len(_over)} overperformers, {len(_under)} underperformers.
    """))
    return


@app.cell(hide_code=True)
def _(domestic_df, gdp_dict):
    _comparison_df = compute_gdp_vs_centrality_comparison(domestic_df, gdp_dict)

    # Color by divergence direction
    _comparison_df['divergence'] = _comparison_df['rank_diff'].apply(
        lambda x: 'Overperformer' if x > 0 else ('Underperformer' if x < 0 else 'Neutral')
    )

    _diagonal = pd.DataFrame({'x': [0, 52], 'y': [0, 52]})

    _scatter = alt.Chart(_comparison_df).mark_circle(size=80, opacity=0.7).encode(
        x=alt.X('gdp_rank:Q', title='GDP Rank (1 = largest)', scale=alt.Scale(domain=[0, 52])),
        y=alt.Y('eigenvector_rank:Q', title='Eigenvector Centrality Rank (1 = most central)', scale=alt.Scale(domain=[0, 52])),
        color=alt.Color('divergence:N', scale=alt.Scale(
            domain=['Overperformer', 'Neutral', 'Underperformer'],
            range=['#d62728', '#999999', '#1f77b4']
        ), title='Divergence'),
        tooltip=[
            alt.Tooltip('state_abbrev:N', title='State'),
            alt.Tooltip('gdp_rank:Q', title='GDP Rank'),
            alt.Tooltip('eigenvector_rank:Q', title='Eigenvector Rank'),
            alt.Tooltip('rank_diff:Q', title='Rank Difference'),
        ],
    )

    _labels = alt.Chart(
        _comparison_df[_comparison_df['rank_diff'].abs() >= 8]
    ).mark_text(dx=7, dy=-7, fontSize=10).encode(
        x='gdp_rank:Q',
        y='eigenvector_rank:Q',
        text='state_abbrev:N',
    )

    _line = alt.Chart(_diagonal).mark_line(
        strokeDash=[4, 4], color='black', opacity=0.4
    ).encode(x='x:Q', y='y:Q')

    gdp_scatter = (_scatter + _line + _labels).properties(
        title='Economic Size vs Structural Position (51×51 Domestic)',
        width=500, height=500,
    )
    mo.output.replace(gdp_scatter)
    return


@app.cell(hide_code=True)
def _(domestic_df, intl_df):
    # Align 51×51 and 52×52 data, excluding RoW
    domestic_aligned, intl_aligned = align_measures(domestic_df, intl_df, MEASURES)

    mo.output.replace(mo.md(
        f"## Section 5: Boundary Sensitivity (51×51 vs 52×52)\n\n"
        f"Aligned {len(domestic_aligned)} states across both network specifications "
        f"(RoW excluded from 52×52)."
    ))
    return domestic_aligned, intl_aligned


@app.cell(hide_code=True)
def _(domestic_aligned, intl_aligned):
    _corrs = compute_rank_correlations(domestic_aligned, intl_aligned, MEASURES)

    _header = "| Measure | Spearman ρ | p-value | Kendall τ | p-value |"
    _sep = "|---|---|---|---|---|"
    _rows = []
    for _m in MEASURES:
        _c = _corrs[_m]
        _rows.append(
            f"| {_m} | {_c['spearman']:.4f} | {_c['spearman_p']:.2e} | "
            f"{_c['kendall']:.4f} | {_c['kendall_p']:.2e} |"
        )

    mo.output.replace(mo.md(f"""### Rank Correlations: 51×51 Domestic vs 52×52 International

    {_header}
    {_sep}
    {chr(10).join(_rows)}

    High correlations indicate rankings are robust to inclusion of international trade flows (RoW node).
    """))
    return


@app.cell(hide_code=True)
def _(domestic_aligned, intl_aligned):
    _rank_changes = compute_rank_changes(domestic_aligned, intl_aligned, MEASURES)
    _effects = summarize_effect_sizes(_rank_changes)

    _header = "| Measure | Mean |Δ| | Max |Δ| | Median |Δ| | States Changed | Total |"
    _sep = "|---|---|---|---|---|---|"
    _rows = []
    for _m in MEASURES:
        _e = _effects[_m]
        _rows.append(
            f"| {_m} | {_e['mean_abs_change']:.1f} | {_e['max_abs_change']} | "
            f"{_e['median_abs_change']:.1f} | {_e['states_changed']}/{_e['total_states']} | "
            f"{_e['total_states']} |"
        )

    mo.output.replace(mo.md(f"""### Per-State Rank Change Effect Sizes

    {_header}
    {_sep}
    {chr(10).join(_rows)}

    Low mean absolute rank changes indicate that adding the RoW node has minimal effect on
    relative state rankings.
    """))
    return


@app.cell(hide_code=True)
def _(domestic_aligned, intl_aligned):
    _dom_ranked = rank_columns(domestic_aligned, MEASURES)
    _intl_ranked = rank_columns(intl_aligned, MEASURES)

    _merged = _dom_ranked[['label'] + [f'rank_{m}' for m in MEASURES]].merge(
        _intl_ranked[['label'] + [f'rank_{m}' for m in MEASURES]],
        on='label', suffixes=('_51', '_52')
    )

    _titles = {
        'betweenness': 'Betweenness',
        'eigenvector': 'Eigenvector',
        'out_degree': 'Out-Degree',
    }

    _charts = []
    _diagonal = pd.DataFrame({'x': [0, 52], 'y': [0, 52]})

    for _m in MEASURES:
        _scatter = alt.Chart(_merged).mark_circle(size=60, opacity=0.7).encode(
            x=alt.X(f'rank_{_m}_51:Q', title='51×51 Rank', scale=alt.Scale(domain=[0, 52])),
            y=alt.Y(f'rank_{_m}_52:Q', title='52×52 Rank', scale=alt.Scale(domain=[0, 52])),
            tooltip=[
                alt.Tooltip('label:N', title='State'),
                alt.Tooltip(f'rank_{_m}_51:Q', title='51×51 Rank'),
                alt.Tooltip(f'rank_{_m}_52:Q', title='52×52 Rank'),
            ],
        ).properties(title=_titles[_m], width=250, height=250)

        _line = alt.Chart(_diagonal).mark_line(
            strokeDash=[4, 4], color='black', opacity=0.4
        ).encode(x='x:Q', y='y:Q')

        _charts.append(_scatter + _line)

    boundary_chart = alt.hconcat(*_charts).properties(
        title='Boundary Sensitivity: Domestic vs International Rankings'
    )
    mo.output.replace(boundary_chart)
    return


if __name__ == "__main__":
    app.run()
