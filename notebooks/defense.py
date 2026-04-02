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
app = marimo.App(width="full")

with app.setup(hide_code=True):
    import pandas as pd
    import numpy as np
    import altair as alt
    import sys
    from pathlib import Path
    from scipy.stats import spearmanr
    import plotly.express as px
    import marimo as mo

    _toolkit_path = str(Path(__file__).parent.parent / "cfs-network-toolkit")
    if _toolkit_path not in sys.path:
        sys.path.insert(0, _toolkit_path)

    from cfs_toolkit.analysis import (
        load_network_graph,
        count_components_at_filtration,
        scan_filtration_range,
        filter_graph_by_percentile,
        load_gdp_data,
    )
    from cfs_toolkit.core import compute_all_centralities
    import networkx as nx

    FIPS_TO_STATE = {
        1: 'AL', 2: 'AK', 4: 'AZ', 5: 'AR', 6: 'CA', 8: 'CO', 9: 'CT', 10: 'DE',
        11: 'DC', 12: 'FL', 13: 'GA', 15: 'HI', 16: 'ID', 17: 'IL', 18: 'IN',
        19: 'IA', 20: 'KS', 21: 'KY', 22: 'LA', 23: 'ME', 24: 'MD', 25: 'MA',
        26: 'MI', 27: 'MN', 28: 'MS', 29: 'MO', 30: 'MT', 31: 'NE', 32: 'NV',
        33: 'NH', 34: 'NJ', 35: 'NM', 36: 'NY', 37: 'NC', 38: 'ND', 39: 'OH',
        40: 'OK', 41: 'OR', 42: 'PA', 44: 'RI', 45: 'SC', 46: 'SD', 47: 'TN',
        48: 'TX', 49: 'UT', 50: 'VT', 51: 'VA', 53: 'WA', 54: 'WV', 55: 'WI', 56: 'WY'
    }

    STATE_NAMES = {
        'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
        'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
        'DC': 'District of Columbia', 'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii',
        'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
        'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine',
        'MD': 'Maryland', 'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota',
        'MS': 'Mississippi', 'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska',
        'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico',
        'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
        'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island',
        'SC': 'South Carolina', 'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas',
        'UT': 'Utah', 'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington',
        'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming'
    }

    alt.theme.enable('dark')

    # === LOAD ALL DATA ===
    REPO_ROOT = Path(__file__).parent.parent
    DOMESTIC_RUN = REPO_ROOT / "results" / "51x51_domestic"
    INTL_RUN = REPO_ROOT / "results" / "52x52_international"

    domestic_df = pd.read_csv(DOMESTIC_RUN / "centralities_51x51_domestic.csv")
    intl_df = pd.read_csv(INTL_RUN / "centralities_52x52_intl.csv")
    G_domestic = load_network_graph(DOMESTIC_RUN)

    top_betw = domestic_df.loc[domestic_df['rank_betweenness'] == 1, 'label'].iloc[0]
    assert top_betw == 'CA', f"Weight inversion error: expected CA #1 betweenness, got {top_betw}"

    # Master state dataframe
    gdp_df = pd.read_csv(REPO_ROOT / "data" / "state_gdp_2017.csv")
    pop_df = pd.read_csv(REPO_ROOT / "data" / "state_population_2017.csv")

    master = domestic_df.copy().rename(columns={'label': 'state_abbrev', 'state_id': 'fips'})
    master['state_name'] = master['state_abbrev'].map(STATE_NAMES)
    master = master.merge(gdp_df[['state_abbrev', 'gdp_2017_q4_millions']], on='state_abbrev', how='left')
    master['gdp_billions'] = master['gdp_2017_q4_millions'] / 1000
    master['rank_gdp'] = master['gdp_2017_q4_millions'].rank(ascending=False, method='min').astype(int)
    master = master.merge(pop_df[['state_abbrev', 'pop_2017_acs']], on='state_abbrev', how='left')
    master['div_eigenvector'] = master['rank_gdp'] - master['rank_eigenvector']

    # GDP-centrality merge for scatter plots
    gdp_cent = domestic_df.merge(gdp_df, left_on='label', right_on='state_abbrev')
    gdp_cent['gdp_billions'] = gdp_cent['gdp_2017_q4_millions'] / 1000
    gdp_cent['gdp_rank'] = gdp_cent['gdp_billions'].rank(ascending=False).astype(int)
    gdp_cent['eig_rank'] = gdp_cent['rank_eigenvector'].astype(int)
    gdp_cent['divergence'] = gdp_cent['gdp_rank'] - gdp_cent['eig_rank']


# ============================================================
# CELL 1: State Profile — "What about [state]?"
# ============================================================
@app.cell(hide_code=True)
def _(master, mo):
    _options = dict(zip(
        master['state_name'] + ' (' + master['state_abbrev'] + ')',
        master['state_abbrev']
    ))
    state_selector = mo.ui.dropdown(options=_options, value='Florida (FL)', label='Select a state')

    _s = master[master['state_abbrev'] == state_selector.value].iloc[0]
    _gdp_rank = int(_s['rank_gdp'])
    _eig_rank = int(_s['rank_eigenvector'])
    _btw_rank = int(_s['rank_betweenness'])
    _diff = _gdp_rank - _eig_rank

    if _diff >= 5:
        _status = f"Punches above weight (+{_diff})"
    elif _diff <= -5:
        _status = f"Punches below weight ({_diff})"
    else:
        _status = "Proportional"

    mo.vstack([
        mo.md("# State Profile"),
        state_selector,
        mo.md(f"""
| | Value | Rank |
|--|-------|------|
| **GDP** | ${_s['gdp_billions']:.1f}B | #{_gdp_rank} |
| **Eigenvector** | {_s['eigenvector']:.4f} | #{_eig_rank} |
| **Betweenness** | {_s['betweenness']:.4f} | #{_btw_rank} |
| **Out-Degree** | ${_s['out_degree']/1e9:.1f}B | #{int(_s['rank_out_degree'])} |

**{_status}**
        """)
    ])
    return (state_selector,)


# ============================================================
# CELL 2: Structural Undervaluation — "Show me who overperforms"
# ============================================================
@app.cell(hide_code=True)
def _(gdp_cent, mo):
    _df = gdp_cent.copy()

    _fig = px.choropleth(
        _df, locations='label', locationmode='USA-states',
        color='divergence', color_continuous_scale='PRGn',
        color_continuous_midpoint=0, range_color=[-12, 12], scope='usa',
        title='Structural Undervaluation: GDP Rank - Eigenvector Rank',
    )
    _fig.update_traces(hovertemplate='<b>%{location}</b><br>Divergence: %{z:+d}<extra></extra>')
    _fig.update_layout(
        geo=dict(showlakes=True, lakecolor='rgb(255,255,255)', bgcolor='rgba(0,0,0,0)'),
        margin=dict(l=0, r=0, t=50, b=0),
        coloraxis_colorbar=dict(title='GDP Rank −<br>Centrality Rank', thickness=15, len=0.7),
        paper_bgcolor='rgba(0,0,0,0)', title_font_size=18, title_x=0.5,
    )

    _over = _df.nlargest(5, 'divergence')
    _under = _df.nsmallest(5, 'divergence')
    _over_str = ' · '.join([f"**{r['label']}** (+{int(r['divergence'])})" for _, r in _over.iterrows()])
    _under_str = ' · '.join([f"**{r['label']}** ({int(r['divergence'])})" for _, r in _under.iterrows()])

    mo.vstack([
        mo.md("# Structural Undervaluation"),
        mo.md("GDP ranks by final output. Eigenvector reveals role in enabling output elsewhere. 40% of states diverge 5+ ranks."),
        _fig,
        mo.hstack([
            mo.callout(mo.md(f"**Overperformers** (green)\n\n{_over_str}\n\n*Manufacturing, energy, agriculture*"), kind='success'),
            mo.callout(mo.md(f"**Underperformers** (purple)\n\n{_under_str}\n\n*Service economies*"), kind='warn'),
        ], justify='center', gap=1),
        mo.md("*7 of 8 structurally undervalued states are now attracting $170B+ in AI data center investment. Same structural factors: cheap energy, water, grid capacity, logistics corridors.*")
    ])
    return


# ============================================================
# CELL 3: Three Measures Compared — "How do they differ?"
# ============================================================
@app.cell(hide_code=True)
def _(domestic_df, mo):
    _measures = ['betweenness', 'eigenvector', 'out_degree']
    _labels = {'betweenness': 'Betweenness (Bridge)', 'eigenvector': 'Eigenvector (Prestige)', 'out_degree': 'Out-Degree (Capacity)'}

    _viz_data = []
    for _m in _measures:
        _top10 = domestic_df.nsmallest(10, f'rank_{_m}')[['label', _m, f'rank_{_m}']].copy()
        _top10['measure'] = _labels[_m]
        _top10['score'] = _top10[_m]
        _top10['rank'] = _top10[f'rank_{_m}'].astype(int)
        _viz_data.append(_top10[['label', 'measure', 'score', 'rank']])

    _viz_df = pd.concat(_viz_data, ignore_index=True)

    _chart = alt.Chart(_viz_df).mark_bar().encode(
        x=alt.X('score:Q', title='Centrality Score'),
        y=alt.Y('label:N', sort='-x', title=None),
        color=alt.Color('measure:N', legend=None, scale=alt.Scale(
            domain=list(_labels.values()), range=['#1f77b4', '#2ca02c', '#ff7f0e']
        )),
        tooltip=['label', alt.Tooltip('rank:Q', title='Rank'), alt.Tooltip('score:Q', format='.4f')]
    ).properties(width=250, height=300).facet(
        column=alt.Column('measure:N', title=None, header=alt.Header(labelFontSize=14, labelFontWeight='bold'))
    )

    _fl = domestic_df[domestic_df['label'] == 'FL'].iloc[0]

    mo.vstack([
        mo.md("# Three Measures Compared"),
        mo.md(f"Florida: **4th in GDP**, **#{int(_fl['rank_betweenness'])} in betweenness** (zero). A peninsula, not a bridge. 31 states (61%) have zero betweenness."),
        _chart,
    ])
    return


# ============================================================
# CELL 4: Boundary Sensitivity — "What changes with intl trade?"
# ============================================================
@app.cell(hide_code=True)
def _(domestic_df, intl_df, mo):
    # Eigenvector rank change choropleth
    _dom = domestic_df[['label', 'rank_eigenvector']].copy()
    _dom.columns = ['label', 'domestic_rank']
    _intl = intl_df[['label', 'rank_eigenvector']].copy()
    _intl.columns = ['label', 'intl_rank']
    _df = _dom.merge(_intl, on='label')
    _df['rank_change'] = _df['domestic_rank'] - _df['intl_rank']

    _fig = px.choropleth(
        _df, locations='label', locationmode='USA-states',
        color='rank_change', color_continuous_scale='PRGn',
        color_continuous_midpoint=0, range_color=[-10, 10], scope='usa',
        title='Boundary Effect: Eigenvector Rank Change (Domestic → International)',
    )
    _fig.update_traces(hovertemplate='<b>%{location}</b><br>Rank Change: %{z:+d}<extra></extra>')
    _fig.update_layout(
        geo=dict(showlakes=True, lakecolor='rgb(255,255,255)', bgcolor='rgba(0,0,0,0)'),
        margin=dict(l=0, r=0, t=50, b=0),
        coloraxis_colorbar=dict(title='Rank Change', thickness=15, len=0.7),
        paper_bgcolor='rgba(0,0,0,0)', title_font_size=18, title_x=0.5,
    )

    # Rank scatter for all three measures
    _measure_order = [
        ('out_degree', 'Out-Degree (ρ=0.994)', '#ff7f0e'),
        ('eigenvector', 'Eigenvector (ρ=0.982)', '#2ca02c'),
        ('betweenness', 'Betweenness (ρ=0.816)', '#1f77b4')
    ]

    def _make_scatter(_measure, _title, _color):
        _d = domestic_df[['label', f'rank_{_measure}']].copy()
        _d.columns = ['state', 'domestic_rank']
        _i = intl_df[['label', f'rank_{_measure}']].copy()
        _i.columns = ['state', 'intl_rank']
        _merged = _d.merge(_i, on='state')

        _diag = pd.DataFrame({'x': [1, 51], 'y': [1, 51]})
        _line = alt.Chart(_diag).mark_line(strokeDash=[4, 4], color='gray', opacity=0.5).encode(x='x:Q', y='y:Q')
        _points = alt.Chart(_merged).mark_circle(size=60, opacity=0.8, color=_color).encode(
            x=alt.X('domestic_rank:Q', title='Domestic', scale=alt.Scale(domain=[1, 51])),
            y=alt.Y('intl_rank:Q', title='International', scale=alt.Scale(domain=[1, 51])),
            tooltip=['state', 'domestic_rank', 'intl_rank']
        )
        return alt.layer(_line, _points).properties(width=200, height=200, title=_title)

    _charts = alt.hconcat(*[_make_scatter(m, t, c) for m, t, c in _measure_order])

    mo.vstack([
        mo.md("# Boundary Sensitivity"),
        mo.md("Treating U.S. commodity trade as the open system it actually is. The more a measure depends on global network structure, the more boundary specification matters."),
        _fig,
        mo.md("---"),
        _charts,
        mo.md("*Out-degree clusters on diagonal. Betweenness scatters. Gateway states (WA, HI, NJ) gain; interior bridges (OH, MO) lose.*"),
    ])
    return


# ============================================================
# CELL 5: Filtration Validation — "Is this robust?"
# ============================================================
@app.cell(hide_code=True)
def _(G_domestic, domestic_df, mo):
    filtration_slider = mo.ui.slider(start=0, stop=50, value=0, step=5, label="Filtration %", show_value=True)

    if filtration_slider.value == 0:
        _result = mo.md("**Baseline**: All 2,534 edges. Move the slider to remove weak edges.")
    else:
        _pct = filtration_slider.value
        _comp = count_components_at_filtration(G_domestic, _pct)

        if _comp['is_connected']:
            _G_f, _ = filter_graph_by_percentile(G_domestic, _pct)
            _f_df = compute_all_centralities(_G_f)

            _rows = []
            for _m, _col in [('Betweenness', 'betweenness'), ('Eigenvector', 'eigenvector'), ('Out-Degree', 'out_degree')]:
                _b = domestic_df.set_index('state_id')[_col]
                _f = _f_df.set_index('state_id')[_col]
                _c = _b.index.intersection(_f.index)
                _rho, _ = spearmanr(_b.loc[_c], _f.loc[_c])
                _rows.append(f"| {_m} | ρ = {_rho:.4f} | {'Stable' if _rho > 0.95 else 'Changed'} |")

            _result = mo.md(f"""**Filtration at {_pct}%** — Connected ({_comp['edges_remaining']} edges)

| Measure | Spearman ρ | Status |
|---------|-----------|--------|
{chr(10).join(_rows)}""")
        else:
            _result = mo.md(f"**Filtration at {_pct}%** — Fragmented ({_comp['n_strongly_connected']} components). Rankings no longer comparable.")

    mo.vstack([
        mo.md("# Filtration Validation"),
        mo.md("At 99.4% density, are centrality results artifacts? Remove weak edges and watch. Network stays connected up to 33%. Rankings: ρ=1.000 at 33% for all three measures."),
        filtration_slider,
        _result,
    ])
    return (filtration_slider,)


# ============================================================
# CELL 6: Key Numbers — Quick reference for Q&A
# ============================================================
@app.cell(hide_code=True)
def _(mo):
    mo.md("""
# Quick Reference

| Finding | Number | Source |
|---------|--------|--------|
| States diverging 5+ ranks from GDP | 40% (20/51) | §4.3 |
| States with zero betweenness | 31 (61%) | §4.3 |
| FL GDP rank / betweenness rank | #4 / zero | §4.3 |
| Filtration stability (all measures) | ρ = 1.000 | §4.2 |
| Betweenness boundary sensitivity | ρ = 0.816 | §4.4 |
| Eigenvector boundary sensitivity | ρ = 0.982 | §4.4 |
| Out-degree boundary sensitivity | ρ = 0.994 | §4.4 |
| KY GDP rank / eigenvector rank | #28 / #14 | §5.4 |
| MS GDP-normalized centrality | #1 | §4.3 |
| Data center investment in undervalued states | $170B+ | §7 |
| Without DC: divergence | 36% (18/50) | §4.3 |
| Betweenness-GDP correlation | ρ = 0.763 | §4.3 |
| Eigenvector-GDP correlation | ρ = 0.934 | §4.3 |
    """)
    return


if __name__ == "__main__":
    app.run()
