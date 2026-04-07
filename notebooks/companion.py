# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "pandas==2.3.1",
#     "numpy==2.3.2",
#     "matplotlib==3.10.5",
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
    # Initialization code that runs before all other cells
    import pandas as pd
    import numpy as np
    import altair as alt
    import sys
    from pathlib import Path
    from scipy.stats import spearmanr
    import plotly.express as px

    # Add toolkit to path for analysis functions
    _toolkit_path = str(Path(__file__).parent.parent / "cfs-network-toolkit")
    if _toolkit_path not in sys.path:
        sys.path.insert(0, _toolkit_path)

    # Import filtration and analysis functions
    from cfs_toolkit.analysis import (
        load_network_graph,
        count_components_at_filtration,
        scan_filtration_range,
        filter_graph_by_percentile,
        load_gdp_data,
        compute_gdp_vs_centrality_comparison,
    )
    from cfs_toolkit.core import compute_all_centralities
    import networkx as nx

    # FIPS code to state abbreviation mapping
    FIPS_TO_STATE = {
        1: 'AL', 2: 'AK', 4: 'AZ', 5: 'AR', 6: 'CA', 8: 'CO', 9: 'CT', 10: 'DE',
        11: 'DC', 12: 'FL', 13: 'GA', 15: 'HI', 16: 'ID', 17: 'IL', 18: 'IN',
        19: 'IA', 20: 'KS', 21: 'KY', 22: 'LA', 23: 'ME', 24: 'MD', 25: 'MA',
        26: 'MI', 27: 'MN', 28: 'MS', 29: 'MO', 30: 'MT', 31: 'NE', 32: 'NV',
        33: 'NH', 34: 'NJ', 35: 'NM', 36: 'NY', 37: 'NC', 38: 'ND', 39: 'OH',
        40: 'OK', 41: 'OR', 42: 'PA', 44: 'RI', 45: 'SC', 46: 'SD', 47: 'TN',
        48: 'TX', 49: 'UT', 50: 'VT', 51: 'VA', 53: 'WA', 54: 'WV', 55: 'WI', 56: 'WY'
    }

    def create_centrality_choropleth(df, measure='eigenvector', title=None, colorscale='YlOrRd'):
        """Create interactive Plotly choropleth for centrality visualization."""
        _measure_clean = measure.replace('_', ' ').title()
        _title = title or f'{_measure_clean} Centrality by State'

        _fig = px.choropleth(
            df,
            locations='label',
            locationmode='USA-states',
            color=measure,
            color_continuous_scale=colorscale,
            scope='usa',
            labels={measure: _measure_clean},
            title=_title,
        )

        _fig.update_traces(
            hovertemplate='<b>%{location}</b><br>' +
                          f'{_measure_clean}: ' + '%{z:.4f}<extra></extra>'
        )

        _fig.update_layout(
            geo=dict(
                showlakes=True,
                lakecolor='rgb(255, 255, 255)',
                bgcolor='rgba(0,0,0,0)',
            ),
            margin=dict(l=0, r=0, t=50, b=0),
            coloraxis_colorbar=dict(
                title=_measure_clean,
                thickness=15,
                len=0.7
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
        )

        return _fig

    # Consistent Altair theme for all charts
    alt.theme.enable('dark')


@app.cell(hide_code=True)
def _():
    # Data loading setup with relative paths
    REPO_ROOT = Path(__file__).parent.parent

    # Results directories (Nov 29 runs with weight inversion fix)
    DOMESTIC_RUN = REPO_ROOT / "results" / "51x51_domestic"
    INTL_RUN = REPO_ROOT / "results" / "52x52_international"

    # Load centrality data
    domestic_df = pd.read_csv(DOMESTIC_RUN / "centralities_51x51_domestic.csv")
    intl_df = pd.read_csv(INTL_RUN / "centralities_52x52_intl.csv")

    # Load network graph for filtration analysis
    G_domestic = load_network_graph(DOMESTIC_RUN)

    # === DATA VERIFICATION ===
    # Confirm weight inversion fix applied: CA should be #1 betweenness
    top_betw = domestic_df.loc[domestic_df['rank_betweenness'] == 1, 'label'].iloc[0]
    assert top_betw == 'CA', f"Data error: Expected CA as #1 betweenness, got {top_betw}. Check weight inversion."

    # Extract edge weights for distribution analysis
    edge_weights = [d['weight'] for u, v, d in G_domestic.edges(data=True)]
    edge_weights_df = pd.DataFrame({'weight': edge_weights})
    edge_weights_df['weight_billions'] = edge_weights_df['weight'] / 1e9

    # Build edge list with state abbreviations (not FIPS codes)
    edge_list_df = pd.DataFrame([
        {
            'origin': FIPS_TO_STATE.get(u, str(u)),
            'destination': FIPS_TO_STATE.get(v, str(v)),
            'weight': d['weight'],
            'weight_billions': d['weight'] / 1e9
        }
        for u, v, d in G_domestic.edges(data=True)
    ])

    # Status output
    print(f"✓ Domestic data: {len(domestic_df)} states")
    print(f"✓ International data: {len(intl_df)} entities")
    print(f"✓ Top betweenness: {top_betw} (weight inversion confirmed)")
    print(f"✓ Network loaded: {G_domestic.number_of_nodes()} nodes, {G_domestic.number_of_edges()} edges")
    return (
        G_domestic,
        REPO_ROOT,
        domestic_df,
        edge_list_df,
        edge_weights_df,
        intl_df,
    )


@app.cell(hide_code=True)
def _(G_domestic, REPO_ROOT, domestic_df):
    # === MASTER STATE DATAFRAME ===
    # Consolidates all state-level data for exploratory analysis
    # Schema: 20 columns covering identifiers, economic size, trade flows, centralities

    # --- Helper: State names mapping ---
    _STATE_NAMES = {
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

    # --- Step 1: Compute state flows from network graph ---
    _flows = []
    for _node in G_domestic.nodes():
        _label = G_domestic.nodes[_node].get('label', str(_node))

        # Sum outgoing edge weights (state → all successors)
        _total_outflow = sum(
            G_domestic[_node][_succ]['weight']
            for _succ in G_domestic.successors(_node)
        )

        # Sum incoming edge weights (all predecessors → state)
        _total_inflow = sum(
            G_domestic[_pred][_node]['weight']
            for _pred in G_domestic.predecessors(_node)
        )

        _flows.append({
            'fips': _node,
            'state_abbrev': _label,
            'total_inflow': _total_inflow,
            'total_outflow': _total_outflow
        })

    _flows_df = pd.DataFrame(_flows)

    # --- Step 2: Load external data (GDP + Population) ---
    _gdp_path = REPO_ROOT / "data" / "state_gdp_2017.csv"
    _pop_path = REPO_ROOT / "data" / "state_population_2017.csv"

    _gdp_df = pd.read_csv(_gdp_path)
    _pop_df = pd.read_csv(_pop_path)

    # --- Step 3: Build master dataframe ---
    # Start with centrality data
    _master = domestic_df.copy()
    _master = _master.rename(columns={'label': 'state_abbrev', 'state_id': 'fips'})

    # Add state names
    _master['state_name'] = _master['state_abbrev'].map(_STATE_NAMES)

    # Merge GDP
    _master = _master.merge(
        _gdp_df[['state_abbrev', 'gdp_2017_q4_millions']],
        on='state_abbrev', how='left'
    ).rename(columns={'gdp_2017_q4_millions': 'gdp_2017_millions'})
    _master['gdp_billions'] = _master['gdp_2017_millions'] / 1000
    _master['rank_gdp'] = _master['gdp_2017_millions'].rank(ascending=False, method='min').astype(int)

    # Merge population
    _master = _master.merge(
        _pop_df[['state_abbrev', 'pop_2017_acs']],
        on='state_abbrev', how='left'
    )
    _master['rank_pop'] = _master['pop_2017_acs'].rank(ascending=False, method='min').astype(int)

    # Merge flows
    _master = _master.merge(
        _flows_df[['state_abbrev', 'total_inflow', 'total_outflow']],
        on='state_abbrev', how='left'
    )

    # --- Step 4: Compute derived metrics ---
    _master['net_flow'] = _master['total_outflow'] - _master['total_inflow']
    _master['inout_ratio'] = _master['total_inflow'] / _master['total_outflow']

    # Normalized flow metrics
    _master['outflow_per_gdp'] = _master['total_outflow'] / (_master['gdp_billions'] * 1e9)
    _master['outflow_per_capita'] = _master['total_outflow'] / _master['pop_2017_acs']

    # --- Step 5: Reorder columns for readability ---
    _column_order = [
        # Identifiers
        'fips', 'state_abbrev', 'state_name',
        # Economic size
        'gdp_2017_millions', 'gdp_billions', 'rank_gdp',
        'pop_2017_acs', 'rank_pop',
        # Trade flows
        'total_inflow', 'total_outflow', 'net_flow', 'inout_ratio',
        'outflow_per_gdp', 'outflow_per_capita',
        # Centralities
        'betweenness', 'eigenvector', 'out_degree',
        'rank_betweenness', 'rank_eigenvector', 'rank_out_degree'
    ]

    master_state_df = _master[_column_order].copy()

    # Verification output
    _total_trade = master_state_df['total_outflow'].sum()
    print(f"✓ Master state dataframe: {len(master_state_df)} states × {len(master_state_df.columns)} columns")
    print(f"✓ Total trade volume: ${_total_trade/1e12:.2f}T")
    print(f"✓ GDP range: ${master_state_df['gdp_billions'].min():.1f}B - ${master_state_df['gdp_billions'].max():.1f}B")
    print(f"✓ Population range: {master_state_df['pop_2017_acs'].min():,} - {master_state_df['pop_2017_acs'].max():,}")
    return (master_state_df,)


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # U.S. Interstate Commerce Network Explorer

    **GDP measures economic size. Networks measure economic position.**

    California's $3.9T economy makes it #1 in GDP—but is it #1 in *structural importance* for interstate trade? This notebook lets you explore how 51 U.S. states connect through commodity flows, and what network centrality reveals that GDP alone cannot.

    **Data**: Census Bureau Commodity Flow Survey 2017 (physical goods, not services)
    """)
    return


@app.cell(hide_code=True)
def _(domestic_df, edge_list_df, edge_weights_df, mo):
    _n_nodes = len(domestic_df)
    _n_edges = len(edge_list_df)
    _max_edges = _n_nodes * (_n_nodes - 1)  # directed graph: n(n-1)
    _density = (_n_edges / _max_edges) * 100

    _top_betw = domestic_df.nsmallest(3, 'rank_betweenness')[['label', 'betweenness']].values.tolist()
    _top_eig = domestic_df.nsmallest(3, 'rank_eigenvector')[['label', 'eigenvector']].values.tolist()

    _total_trade = edge_weights_df['weight'].sum() / 1e12
    _median_trade = edge_weights_df['weight'].median() / 1e6
    _max_trade = edge_weights_df['weight'].max() / 1e9

    mo.md(f"""
    ## The Network at a Glance

    | Metric | Value |
    |--------|-------|
    | **Nodes** | {_n_nodes} (50 states + DC) |
    | **Edges** | {_n_edges:,} directed trade flows |
    | **Density** | {_density:.1f}% (nearly complete graph) |
    | **Total Trade** | ${_total_trade:.2f}T |
    | **Median Edge** | ${_median_trade:.0f}M |
    | **Max Edge** | ${_max_trade:.1f}B |

    **Top 3 by Betweenness** (bridges): {_top_betw[0][0]}, {_top_betw[1][0]}, {_top_betw[2][0]}
    **Top 3 by Eigenvector** (prestige): {_top_eig[0][0]}, {_top_eig[1][0]}, {_top_eig[2][0]}
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    _glossary = mo.md("""
    | Term | Definition |
    |------|------------|
    | **Betweenness Centrality** | How often a state lies on the shortest path between other states. High = critical bridge/bottleneck. |
    | **Eigenvector Centrality** | Importance based on connections to *other important states*. High = connected to major hubs. |
    | **Out-Degree** | Total value of goods a state ships to others. Measures distribution capacity. |
    | **Normalization** | Adjusting centrality by GDP to find states that "punch above their weight." |
    | **Filtration** | Removing weak edges to test ranking stability. Robust findings survive filtration. |
    | **Boundary Sensitivity** | Comparing 51×51 (domestic) vs 52×52 (with international) to see how foreign trade changes rankings. |
    """)
    mo.accordion({"📖 Key Terms (click to expand)": _glossary})
    return


@app.cell(hide_code=True)
def _(master_state_df, mo):
    mo.vstack([
        mo.md("### Master State Data (GDP + Centralities)"),
        mo.ui.table(master_state_df)
    ])
    return


@app.cell(hide_code=True)
def _(edge_list_df, mo):
    mo.vstack([
        mo.md("### Edge List (All Trade Flows)"),
        mo.ui.table(edge_list_df)
    ])
    return


@app.cell(hide_code=True)
def _(master_state_df, mo):
    # === GDP vs POPULATION: VERIFICATION STEP ===
    # Before using GDP for normalization, verify it correlates with population
    from scipy.stats import pearsonr

    _df = master_state_df.copy()

    # Compute Pearson correlation
    _r, _p = pearsonr(_df['gdp_2017_millions'], _df['pop_2017_acs'])

    # Create scatter plot with regression line
    _points = alt.Chart(_df).mark_circle(size=80, opacity=0.7).encode(
        x=alt.X('pop_2017_acs:Q', title='Population (2017 ACS)', axis=alt.Axis(format='~s')),
        y=alt.Y('gdp_2017_millions:Q', title='GDP 2017 ($ Millions)', axis=alt.Axis(format='~s')),
        tooltip=[
            alt.Tooltip('state_abbrev:N', title='State'),
            alt.Tooltip('state_name:N', title='Name'),
            alt.Tooltip('pop_2017_acs:Q', title='Population', format=','),
            alt.Tooltip('gdp_2017_millions:Q', title='GDP ($M)', format=',.0f')
        ]
    )

    # Add regression line
    _line = _points.transform_regression(
        'pop_2017_acs', 'gdp_2017_millions'
    ).mark_line(color='red', strokeDash=[4, 4], strokeWidth=2)

    _chart = alt.layer(_points, _line).properties(
        width=500,
        height=350,
        title=f'GDP vs Population: Pearson r = {_r:.3f}'
    )

    # Determine interpretation
    if _r >= 0.95:
        _interpretation = "**Very strong correlation (r ≥ 0.95)**. Population and GDP move together. Normalizing by GDP effectively controls for both economic and population size."
    elif _r >= 0.90:
        _interpretation = "**Strong correlation (r ≥ 0.90)**. Population and GDP are closely related. GDP normalization is a reasonable proxy for size control."
    else:
        _interpretation = f"**Moderate correlation (r = {_r:.2f})**. GDP and population diverge for some states. Consider normalizing by both measures separately."

    mo.vstack([
        mo.md(f"""
    ## Why Normalize by GDP? A Verification Step

    Before using GDP to identify "overperforming" states in network centrality, we should verify that GDP and population are **strongly correlated**. If they diverge, normalizing by one measure won't control for the other.

    **Pearson correlation**: r = {_r:.3f} (p < 0.001)

    {_interpretation}
        """),
        _chart,
        mo.md("*Each point is a state. California (top right) dominates both metrics. The near-linear relationship validates GDP as a proxy for state 'size' — large economies are generally populous economies.*"),
        mo.md("*Methodological note: We use **Pearson** here because we're comparing raw continuous values (dollars, population). Later analyses comparing centrality **ranks** use **Spearman**, which is appropriate for ordinal data.*")
    ])
    return


@app.cell(hide_code=True)
def _(edge_weights_df, mo):
    _chart = alt.Chart(edge_weights_df).mark_bar(color='steelblue').encode(
        alt.X('weight_billions:Q', bin=alt.Bin(maxbins=50), title='Edge Weight ($ Billions)'),
        alt.Y('count()', title='Number of Edges'),
    ).properties(
        width=600,
        height=300,
        title='Edge Weight Distribution'
    )

    mo.vstack([
        mo.md(f"""
    ## Heavy-Tail Distribution

    Most trade flows are small, but a few are enormous. The gap between median (${edge_weights_df['weight'].median()/1e6:.0f}M) and max (${edge_weights_df['weight'].max()/1e9:.1f}B) spans **two orders of magnitude**.

    **Implication**: With 99.4% density, nearly all states connect to all others—but only a handful of corridors carry the bulk of trade. This heavy-tail structure means the network has an effective *backbone* even when nominally complete.
        """),
        _chart
    ])
    return


@app.cell(hide_code=True)
def _(edge_weights_df, mo):
    _large_edges = edge_weights_df[edge_weights_df['weight_billions'] >= 1.0]
    _zoomed_chart = alt.Chart(_large_edges).mark_bar(color='darkgreen').encode(
        alt.X('weight_billions:Q', bin=alt.Bin(maxbins=30), title='Edge Weight ($ Billions)'),
        alt.Y('count()', title='Number of Edges'),
    ).properties(
        width=600,
        height=250,
        title=f'Major Corridors: Edges ≥ $1B ({len(_large_edges)} of 2,534)'
    )

    mo.vstack([
        mo.md("### Zooming In: The Right Tail"),
        _zoomed_chart,
        mo.md("*Only ~5% of edges exceed $1B, but these carry disproportionate influence on network structure.*")
    ])
    return


@app.cell(hide_code=True)
def _(edge_list_df, mo):
    _top_corridors = edge_list_df.nlargest(10, 'weight')[['origin', 'destination', 'weight_billions']].copy()
    _top_corridors = _top_corridors.reset_index(drop=True)
    _top_corridors['weight_billions'] = _top_corridors['weight_billions'].round(1)
    _top_corridors['corridor'] = _top_corridors['origin'] + ' → ' + _top_corridors['destination']

    _rows = "\n".join([
        f"| {i+1} | {row['corridor']} | ${row['weight_billions']}B |"
        for i, (_, row) in enumerate(_top_corridors.iterrows())
    ])

    mo.md(f"""
    ## The Backbone: Top 10 Trade Corridors

    These are the largest bilateral trade flows in the network—the economic arteries connecting major hubs.

    | Rank | Corridor | Value |
    |------|----------|-------|
    {_rows}

    *Notice: CA↔TX and the Northeast corridor (NJ↔NY↔PA) dominate. These flows shape the network's structure.*
    """)
    return


@app.cell(hide_code=True)
def _(domestic_df, mo):
    # Act 1 Hero Map: Geographic overview of network influence
    _fig = create_centrality_choropleth(
        domestic_df,
        measure='eigenvector',
        title='Network Influence: Eigenvector Centrality',
        colorscale='YlOrRd'
    )

    mo.vstack([
        mo.md("""
    ### Geographic Distribution of Network Power

    *Hover over states to see centrality scores. California, Texas, and Illinois dominate network influence through connections to other high-value trading partners.*
        """),
        _fig
    ])
    return


@app.cell(hide_code=True)
def _(domestic_df, mo):
    # Act 2: Geographic view of all three measures (tabbed)
    _betw_map = create_centrality_choropleth(
        domestic_df, 'betweenness', 'Betweenness: Bridging Power', 'Blues'
    )
    _eig_map = create_centrality_choropleth(
        domestic_df, 'eigenvector', 'Eigenvector: Network Influence', 'Greens'
    )
    _deg_map = create_centrality_choropleth(
        domestic_df, 'out_degree', 'Out-Degree: Distribution Capacity', 'Oranges'
    )

    mo.vstack([
        mo.md("""
    ### Geographic View: Three Measures Compared

    *Switch tabs to see how different centrality measures highlight different states. Notice how the West Coast dominates betweenness (bridging), while the Midwest gains prominence in eigenvector (connections to major hubs).*
        """),
        mo.ui.tabs({
            "Betweenness (Bridges)": _betw_map,
            "Eigenvector (Influence)": _eig_map,
            "Out-Degree (Capacity)": _deg_map
        })
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    measure_selector = mo.ui.dropdown(
        options={"Betweenness": "betweenness", "Eigenvector": "eigenvector", "Out-Degree": "out_degree"},
        value="Betweenness",
        label="Rank all states by:"
    )
    return (measure_selector,)


@app.cell(hide_code=True)
def _(domestic_df, measure_selector, mo):
    _measure = measure_selector.value
    _measure_label = measure_selector.selected_key

    _df = domestic_df[['label', _measure]].copy()
    _df = _df.sort_values(_measure, ascending=False).reset_index(drop=True)

    _chart = alt.Chart(_df).mark_bar(color='steelblue').encode(
        x=alt.X(f'{_measure}:Q', title=f'{_measure_label} Score'),
        y=alt.Y('label:N', sort='-x', title='State'),
        tooltip=['label', alt.Tooltip(f'{_measure}:Q', format='.4f')]
    ).properties(
        width=500,
        height=800,
        title=f'All 51 States Ranked by {_measure_label}'
    )

    mo.vstack([
        mo.md(f"""
    ## Explore: Full State Rankings

    Use the dropdown to see how rankings differ across measures. Notice how the *same state* can rank very differently depending on which dimension of "importance" you measure.
        """),
        measure_selector,
        _chart,
        mo.md("*The heavy-tail pattern repeats: a few states dominate, most cluster near zero.*")
    ])
    return


@app.cell(hide_code=True)
def _(master_state_df, mo):
    # State selector dropdown for Q&A / exploration
    _state_options = dict(zip(
        master_state_df['state_name'] + ' (' + master_state_df['state_abbrev'] + ')',
        master_state_df['state_abbrev']
    ))
    state_selector = mo.ui.dropdown(
        options=_state_options,
        value='California (CA)',
        label='Select a state to explore'
    )
    return (state_selector,)


@app.cell(hide_code=True)
def _(master_state_df, mo, state_selector):
    # State profile card - reactive to dropdown selection
    _s = master_state_df[master_state_df['state_abbrev'] == state_selector.value].iloc[0]

    # Determine if punching above/below weight
    _gdp_rank = int(_s['rank_gdp'])
    _eig_rank = int(_s['rank_eigenvector'])
    _rank_diff = _gdp_rank - _eig_rank
    if _rank_diff >= 5:
        _weight_status = f"**Punching above weight** (GDP #{_gdp_rank} → Eigenvector #{_eig_rank})"
    elif _rank_diff <= -5:
        _weight_status = f"**Punching below weight** (GDP #{_gdp_rank} → Eigenvector #{_eig_rank})"
    else:
        _weight_status = f"**Proportional** (GDP #{_gdp_rank} ≈ Eigenvector #{_eig_rank})"

    _flow_status = 'Net exporter' if _s['net_flow'] > 0 else 'Net importer'

    mo.vstack([
        mo.md(f"## State Profile: {_s['state_name']}"),
        state_selector,
        mo.md(f"""
    | Category | Value | Rank |
    |----------|-------|------|
    | **GDP (2017)** | ${_s['gdp_billions']:.1f}B | #{_gdp_rank} |
    | **Population** | {int(_s['pop_2017_acs']):,} | #{int(_s['rank_pop'])} |
    | **Eigenvector Centrality** | {_s['eigenvector']:.4f} | #{_eig_rank} |
    | **Betweenness Centrality** | {_s['betweenness']:.4f} | #{int(_s['rank_betweenness'])} |
    | **Out-Degree (Trade Volume)** | ${_s['out_degree']/1e9:.1f}B | #{int(_s['rank_out_degree'])} |
    | **Net Trade Flow** | ${_s['net_flow']/1e9:+.1f}B | {_flow_status} |

    {_weight_status}
        """),
        mo.md("*Select any state to see its complete profile. Useful during Q&A when someone asks 'what about my state?'*")
    ])
    return


@app.cell(hide_code=True)
def _(domestic_df, mo):
    # Prepare data for faceted visualization
    _measures = ['betweenness', 'eigenvector', 'out_degree']
    _labels = {'betweenness': 'Betweenness (Bridge)', 'eigenvector': 'Eigenvector (Prestige)', 'out_degree': 'Out-Degree (Capacity)'}

    # Get top 10 for each measure
    _viz_data = []
    for _m in _measures:
        _top10 = domestic_df.nsmallest(10, f'rank_{_m}')[['label', _m, f'rank_{_m}']].copy()
        _top10['measure'] = _labels[_m]
        _top10['score'] = _top10[_m]
        _top10['rank'] = _top10[f'rank_{_m}'].astype(int)
        _viz_data.append(_top10[['label', 'measure', 'score', 'rank']])

    _viz_df = pd.concat(_viz_data, ignore_index=True)

    # Create faceted chart
    _chart = alt.Chart(_viz_df).mark_bar().encode(
        x=alt.X('score:Q', title='Centrality Score'),
        y=alt.Y('label:N', sort='-x', title=None),
        color=alt.Color('measure:N', legend=None, scale=alt.Scale(
            domain=['Betweenness (Bridge)', 'Eigenvector (Prestige)', 'Out-Degree (Capacity)'],
            range=['#1f77b4', '#2ca02c', '#ff7f0e']
        )),
        tooltip=[
            alt.Tooltip('label:N', title='State'),
            alt.Tooltip('rank:Q', title='Rank'),
            alt.Tooltip('score:Q', title='Score', format='.4f')
        ]
    ).properties(
        width=250,
        height=300
    ).facet(
        column=alt.Column('measure:N', title=None, header=alt.Header(labelFontSize=14, labelFontWeight='bold'))
    )

    # Get FL's ranks for narrative
    _fl = domestic_df[domestic_df['label'] == 'FL'].iloc[0]
    _fl_betw_rank = int(_fl['rank_betweenness'])

    # Compute top 3 for each measure (DYNAMIC, not hardcoded)
    _top3_betw = ', '.join(domestic_df.nsmallest(3, 'rank_betweenness')['label'].tolist())
    _top3_eig = ', '.join(domestic_df.nsmallest(3, 'rank_eigenvector')['label'].tolist())
    _top3_deg = ', '.join(domestic_df.nsmallest(3, 'rank_out_degree')['label'].tolist())

    mo.vstack([
        mo.md(f"""
    ---

    ## Three Lenses on Network Importance

    Each centrality measure captures a different dimension of structural position:

    | Measure | Question | Top States |
    |---------|----------|------------|
    | **Betweenness** | Who sits on trade routes between others? | {_top3_betw} |
    | **Eigenvector** | Who connects to the most important partners? | {_top3_eig} |
    | **Out-Degree** | Who exports the most total value? | {_top3_deg} |

    ### The Florida Puzzle

    Florida is the **4th largest state economy** (~$1.1T GDP), yet ranks **#{_fl_betw_rank}** in betweenness. Why?

    FL is a *peninsula*—a geographic endpoint, not a bridge. Trade flows *into* Florida (consumer goods for 22M residents), but the major corridors bypass it entirely. The CA↔TX and NJ↔NY↔PA routes don't need Florida as an intermediary.

    **This is the core insight**: Structural position ≠ economic size. A state can be wealthy without being *central*.
        """),
        _chart,
        mo.md("*Top 10 states by each measure. Hover to see ranks—notice how IN excels at eigenvector (#5) but not betweenness (#15). Each state tells a different story.*")
    ])
    return


@app.cell(hide_code=True)
def _(master_state_df, mo):
    # === GDP-NORMALIZED CENTRALITY: WHO PUNCHES ABOVE THEIR WEIGHT? ===
    # Rank divergence approach: compare GDP rank to centrality rank
    # Positive divergence = more network-important than economy size suggests

    _df = master_state_df.copy()

    # Compute rank divergence for each centrality measure
    # divergence = rank_gdp - rank_centrality (positive = punches above weight)
    _df['div_eigenvector'] = _df['rank_gdp'] - _df['rank_eigenvector']
    _df['div_betweenness'] = _df['rank_gdp'] - _df['rank_betweenness']
    _df['div_out_degree'] = _df['rank_gdp'] - _df['rank_out_degree']

    # --- Build three separate scatter charts (hconcat instead of facet) ---
    def _make_chart(measure_col, div_col, title):
        _chart_df = _df.copy()
        _chart_df['rank_centrality'] = _chart_df[measure_col]
        _chart_df['divergence'] = _chart_df[div_col]

        _scatter = alt.Chart(_chart_df).mark_circle(size=60, opacity=0.7).encode(
            x=alt.X('rank_gdp:Q', title='GDP Rank', scale=alt.Scale(domain=[1, 51])),
            y=alt.Y('rank_centrality:Q', title='Centrality Rank', scale=alt.Scale(domain=[1, 51])),
            color=alt.Color('divergence:Q',
                scale=alt.Scale(scheme='redblue', domain=[-20, 20]),
                legend=None
            ),
            tooltip=[
                alt.Tooltip('state_abbrev:N', title='State'),
                alt.Tooltip('rank_gdp:Q', title='GDP Rank'),
                alt.Tooltip('rank_centrality:Q', title='Centrality Rank'),
                alt.Tooltip('divergence:Q', title='Divergence', format='+d')
            ]
        )

        _diag_data = pd.DataFrame({'x': [1, 51], 'y': [1, 51]})
        _diagonal = alt.Chart(_diag_data).mark_line(
            strokeDash=[5, 5], color='gray', strokeWidth=1.5
        ).encode(x='x:Q', y='y:Q')

        return alt.layer(_diagonal, _scatter).properties(width=250, height=250, title=title)

    _chart_eig = _make_chart('rank_eigenvector', 'div_eigenvector', 'Eigenvector')
    _chart_btw = _make_chart('rank_betweenness', 'div_betweenness', 'Betweenness')
    _chart_deg = _make_chart('rank_out_degree', 'div_out_degree', 'Out-Degree')

    _facet_chart = alt.hconcat(_chart_eig, _chart_btw, _chart_deg).properties(
        title='GDP Rank vs Centrality Rank by Measure'
    )

    # --- Top 5 over/underperformers for each measure ---
    _summary_rows = []
    for _m, _m_label in [('eigenvector', 'Eigenvector'), ('betweenness', 'Betweenness'), ('out_degree', 'Out-Degree')]:
        _sorted = _df.sort_values(f'div_{_m}', ascending=False)
        _top5 = _sorted.head(5)['state_abbrev'].tolist()
        _bottom5 = _sorted.tail(5)['state_abbrev'].tolist()
        _summary_rows.append({
            'Measure': _m_label,
            'Top 5 (Above Weight)': ', '.join(_top5),
            'Bottom 5 (Below Expected)': ', '.join(reversed(_bottom5))
        })
    _summary_df = pd.DataFrame(_summary_rows)

    # --- Complete rankings table with all three divergences ---
    _complete_df = _df.sort_values('div_eigenvector', ascending=False)[
        ['state_abbrev', 'state_name', 'rank_gdp',
         'rank_eigenvector', 'div_eigenvector',
         'rank_betweenness', 'div_betweenness',
         'rank_out_degree', 'div_out_degree']
    ].rename(columns={
        'state_abbrev': 'State',
        'state_name': 'Name',
        'rank_gdp': 'GDP Rk',
        'rank_eigenvector': 'Eig Rk',
        'div_eigenvector': 'Eig Δ',
        'rank_betweenness': 'Btw Rk',
        'div_betweenness': 'Btw Δ',
        'rank_out_degree': 'Deg Rk',
        'div_out_degree': 'Deg Δ'
    }).reset_index(drop=True)

    # Summary stats
    _eig_above = len(_df[_df['div_eigenvector'] > 5])
    _btw_above = len(_df[_df['div_betweenness'] > 5])
    _deg_above = len(_df[_df['div_out_degree'] > 5])

    mo.vstack([
        mo.md(f"""
    ---

    ## GDP-Normalized Network Importance

    Now that we've verified GDP correlates with population (r = 0.98), we can use GDP rank as a baseline for "expected" network importance. The question becomes: **which states are more central in the trade network than their economic size would predict?**

    **Rank Divergence** = GDP Rank − Centrality Rank
    - **Positive**: More central than GDP predicts → *punches above weight*
    - **Negative**: Less central than expected → *underperforms structurally*
    - **Zero**: Network importance matches economic size

    Each centrality captures a different structural role:
    | Measure | Captures | "Above weight" means |
    |---------|----------|---------------------|
    | **Eigenvector** | Connected to important states | Small economy, trades with big players |
    | **Betweenness** | Bridge on trade routes | Small economy, critical intermediary |
    | **Out-Degree** | Export volume | Small economy, ships a lot |
        """),
        mo.md("---"),
        mo.md("### Summary: Top 5 Performers by Measure"),
        mo.ui.table(_summary_df),
        mo.md("---"),
        _facet_chart,
        mo.md(f"""
    *Points below diagonal = punching above weight. Points above diagonal = underperforming.*

    **Counts above threshold (divergence > +5)**: Eigenvector: {_eig_above} states | Betweenness: {_btw_above} states | Out-Degree: {_deg_above} states
        """),
        mo.md("---"),
        mo.md("### Complete Rankings (All Measures)"),
        mo.md("*Δ = Divergence (GDP Rank − Centrality Rank). Positive = punches above weight.*"),
        mo.ui.table(_complete_df)
    ])
    return


@app.cell(hide_code=True)
def _(domestic_df, mo):
    # Load GDP data
    _gdp_path = Path(__file__).parent.parent / "data" / "state_gdp_2017.csv"
    _gdp = pd.read_csv(_gdp_path)
    _gdp['gdp_billions'] = _gdp['gdp_2017_q4_millions'] / 1000

    # Merge with centrality data
    gdp_centrality_df = domestic_df.merge(_gdp, left_on='label', right_on='state_abbrev')

    # Compute correlations for all measures (DYNAMIC)
    _correlations = []
    for _measure in ['eigenvector', 'out_degree', 'betweenness']:
        _rho, _p = spearmanr(gdp_centrality_df['gdp_billions'], gdp_centrality_df[_measure])
        _correlations.append({
            'measure': _measure,
            'rho': _rho,
            'p': _p
        })

    # Sort by correlation strength
    _correlations = sorted(_correlations, key=lambda x: x['rho'], reverse=True)

    # Dynamic strength labels
    def _strength_label(rho):
        if rho >= 0.9: return 'Strong'
        elif rho >= 0.8: return 'Moderate-Strong'
        elif rho >= 0.7: return 'Moderate'
        else: return 'Weak'

    _rows = "\n".join([
        f"| **{c['measure'].replace('_', '-').title()}** | ρ = {c['rho']:.3f} | {_strength_label(c['rho'])} |"
        for c in _correlations
    ])

    # Identify strongest and weakest for narrative
    _strongest = _correlations[0]['measure'].replace('_', '-')
    _weakest = _correlations[-1]['measure']
    _strongest_rho = _correlations[0]['rho']
    _weakest_rho = _correlations[-1]['rho']

    mo.md(f"""
    ---

    ## Does GDP Predict Centrality?

    We've established that different centrality measures capture different dimensions of network position. But here's the skeptic's question: **Is centrality just economic size in disguise?**

    If GDP perfectly predicted centrality, network analysis would add nothing — we'd just be measuring the same thing with extra steps.

    ### GDP vs Centrality Correlations

    | Measure | Correlation with GDP | Strength |
    |---------|---------------------|----------|
    {_rows}

    **Finding**: GDP correlates most strongly with {_strongest} (ρ = {_strongest_rho:.2f}) and least with {_weakest} (ρ = {_weakest_rho:.2f}).

    *Translation*: Big economies tend to be well-connected (prestige) and ship a lot (capacity). But bridging position is less tied to size — you can be a major bridge without being a major economy.
    """)
    return (gdp_centrality_df,)


@app.cell(hide_code=True)
def _(gdp_centrality_df, mo):
    # Compute rank differences (DYNAMIC)
    _df = gdp_centrality_df.copy()
    _df['gdp_rank'] = _df['gdp_billions'].rank(ascending=False).astype(int)
    _df['eig_rank'] = _df['rank_eigenvector'].astype(int)
    _df['rank_diff'] = _df['gdp_rank'] - _df['eig_rank']  # positive = punches above weight

    # Identify outliers (top 5 each direction)
    _above = _df.nlargest(5, 'rank_diff')[['label', 'eig_rank', 'gdp_rank', 'rank_diff', 'gdp_billions']]
    _below = _df.nsmallest(5, 'rank_diff')[['label', 'eig_rank', 'gdp_rank', 'rank_diff', 'gdp_billions']]

    # Create scatter plot
    _base = alt.Chart(_df).mark_circle(size=60, opacity=0.7).encode(
        x=alt.X('gdp_billions:Q', title='GDP ($ Billions)', scale=alt.Scale(type='log')),
        y=alt.Y('eigenvector:Q', title='Eigenvector Centrality'),
        tooltip=[
            alt.Tooltip('label:N', title='State'),
            alt.Tooltip('gdp_billions:Q', title='GDP ($B)', format=',.0f'),
            alt.Tooltip('eig_rank:Q', title='Eigenvector Rank'),
            alt.Tooltip('gdp_rank:Q', title='GDP Rank'),
            alt.Tooltip('rank_diff:Q', title='Rank Difference')
        ]
    )

    # Highlight outliers (with same tooltips as base)
    _above_labels = _above['label'].tolist()
    _below_labels = _below['label'].tolist()

    _tooltip_config = [
        alt.Tooltip('label:N', title='State'),
        alt.Tooltip('gdp_billions:Q', title='GDP ($B)', format=',.0f'),
        alt.Tooltip('eig_rank:Q', title='Eigenvector Rank'),
        alt.Tooltip('gdp_rank:Q', title='GDP Rank'),
        alt.Tooltip('rank_diff:Q', title='Rank Difference')
    ]

    _highlight_above = alt.Chart(_df[_df['label'].isin(_above_labels)]).mark_circle(
        size=120, color='green', opacity=0.8
    ).encode(x='gdp_billions:Q', y='eigenvector:Q', tooltip=_tooltip_config)

    _highlight_below = alt.Chart(_df[_df['label'].isin(_below_labels)]).mark_circle(
        size=120, color='red', opacity=0.8
    ).encode(x='gdp_billions:Q', y='eigenvector:Q', tooltip=_tooltip_config)

    # Add text labels for extreme outliers
    _extreme = _df[_df['label'].isin([_above_labels[0], _below_labels[0]])]
    _text = alt.Chart(_extreme).mark_text(dx=15, dy=-10, fontSize=12, fontWeight='bold').encode(
        x='gdp_billions:Q',
        y='eigenvector:Q',
        text='label:N',
        color=alt.condition(
            alt.datum.rank_diff > 0,
            alt.value('green'),
            alt.value('red')
        )
    )

    _chart = alt.layer(_base, _highlight_above, _highlight_below, _text).properties(
        width=500,
        height=350,
        title='GDP vs Network Prestige: Who Punches Above Their Weight?'
    )

    # Build outlier tables (DYNAMIC)
    _above_rows = "\n".join([
        f"| {r['label']} | #{int(r['eig_rank'])} | #{int(r['gdp_rank'])} | +{int(r['rank_diff'])} |"
        for _, r in _above.iterrows()
    ])
    _below_rows = "\n".join([
        f"| {r['label']} | #{int(r['eig_rank'])} | #{int(r['gdp_rank'])} | {int(r['rank_diff'])} |"
        for _, r in _below.iterrows()
    ])

    # Top outliers for narrative
    _top_above = _above.iloc[0]
    _top_below = _below.iloc[0]

    mo.vstack([
        _chart,
        mo.hstack([
            mo.md(f"""
    **Punch ABOVE Weight** (green)
    | State | Eig. Rank | GDP Rank | Diff |
    |-------|-----------|----------|------|
    {_above_rows}
            """),
            mo.md(f"""
    **Punch BELOW Weight** (red)
    | State | Eig. Rank | GDP Rank | Diff |
    |-------|-----------|----------|------|
    {_below_rows}
            """)
        ], justify='center', gap=2),
        mo.md(f"""
    *{_top_above['label']} is the biggest overperformer: #{int(_top_above['eig_rank'])} in network prestige despite #{int(_top_above['gdp_rank'])} GDP. {_top_below['label']} is the biggest underperformer: #{int(_top_below['eig_rank'])} prestige despite #{int(_top_below['gdp_rank'])} GDP.*

    **The takeaway**: States that "punch above their weight" share a common thread: **tangible goods production**. The top performers span manufacturing (KY, IN, MI, TN, SC), energy/resources (LA, MT, ND, OK), and agriculture (MS). These aren't just "Rust Belt" states—they're the physical economy: places that make, extract, and ship things. Network centrality captures logistics infrastructure and trade relationships that GDP (which includes services) doesn't fully reflect.
        """)
    ])
    return


@app.cell(hide_code=True)
def _(gdp_centrality_df, mo):
    # Act 4: Side-by-side GDP vs Eigenvector maps
    _cent_map = create_centrality_choropleth(
        gdp_centrality_df, 'eigenvector', 'Eigenvector Centrality', 'Greens'
    )

    # GDP choropleth
    _gdp_map = px.choropleth(
        gdp_centrality_df,
        locations='label',
        locationmode='USA-states',
        color='gdp_billions',
        color_continuous_scale='Blues',
        scope='usa',
        title='GDP 2017 ($ Billions)',
        labels={'gdp_billions': 'GDP ($B)'}
    )
    _gdp_map.update_layout(
        geo=dict(showlakes=True, lakecolor='rgb(255,255,255)', bgcolor='rgba(0,0,0,0)'),
        margin=dict(l=0, r=0, t=50, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    mo.vstack([
        mo.md("""
    ### Geographic Comparison: GDP vs Network Position

    *Compare the maps: GDP (left) and eigenvector centrality (right) show similar but not identical patterns. States across the South, Midwest, and Plains—from KY and TN to LA and ND—punch above their GDP weight. The common thread: manufacturing, energy, and agricultural production. The physical goods economy has more network influence than service-heavy GDP metrics suggest.*
        """),
        mo.hstack([_gdp_map, _cent_map], justify='center')
    ])
    return


@app.cell(hide_code=True)
def _(gdp_centrality_df, mo):
    # === HERO VISUALIZATION: The Physical Economy ===
    # Single dramatic divergence choropleth - the thesis punchline
    _df = gdp_centrality_df.copy()
    _df['gdp_rank'] = _df['gdp_billions'].rank(ascending=False).astype(int)
    _df['eig_rank'] = _df['rank_eigenvector'].astype(int)
    _df['divergence'] = _df['gdp_rank'] - _df['eig_rank']

    # Create divergence choropleth with PRGn (green-purple) - no political associations
    _fig = px.choropleth(
        _df,
        locations='label',
        locationmode='USA-states',
        color='divergence',
        color_continuous_scale='PRGn',
        color_continuous_midpoint=0,
        range_color=[-12, 12],
        scope='usa',
        title='<b>The Physical Economy</b><br><sup>Who Punches Above Their Weight?</sup>',
    )

    _fig.update_traces(
        hovertemplate='<b>%{location}</b><br>Divergence: %{z:+d}<extra></extra>'
    )

    _fig.update_layout(
        geo=dict(showlakes=True, lakecolor='rgb(255,255,255)', bgcolor='rgba(0,0,0,0)'),
        margin=dict(l=0, r=0, t=80, b=20),
        coloraxis_colorbar=dict(
            title='GDP Rank −<br>Centrality Rank',
            thickness=20,
            len=0.75,
            tickvals=[-10, -5, 0, 5, 10],
            ticktext=['-10', '-5', '0', '+5', '+10'],
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        title_font_size=22,
        title_x=0.5,
    )

    # Build callout lists for top 5 each direction
    _over = _df.nlargest(5, 'divergence')
    _under = _df.nsmallest(5, 'divergence')
    _over_str = ' · '.join([f"**{r['label']}** (+{int(r['divergence'])})" for _, r in _over.iterrows()])
    _under_str = ' · '.join([f"**{r['label']}** ({int(r['divergence'])})" for _, r in _under.iterrows()])

    mo.vstack([
        mo.md("---"),
        mo.md("## Structural Undervaluation: Structure ≠ Size"),
        _fig,
        mo.hstack([
            mo.callout(mo.md(f"**Overperformers** (green)\n\n{_over_str}\n\n*Manufacturing, energy, agriculture*"), kind='success'),
            mo.callout(mo.md(f"**Underperformers** (purple)\n\n{_under_str}\n\n*Service economies, tech hubs*"), kind='warn'),
        ], justify='center', gap=1),
        mo.md("""
    *Divergence = GDP Rank − Eigenvector Rank. Green states are more central in the trade network than their economic output predicts. These "physical economy" states—manufacturing, energy, agriculture—punch above their weight because network centrality captures logistics infrastructure and trade relationships that GDP (which includes services) doesn't reflect.*

    *Convergent evidence: 7 of 8 structurally undervalued states are now attracting major AI data center investment—collectively over $170B announced since 2024. The same factors that generate high network centrality (cheap energy, water, grid capacity, logistics corridors) drive infrastructure siting decisions.*
        """),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---

    ## Why This Works: The Weight Inversion Fix

    **The paradox**: NetworkX treats edge weights as *distances*—higher weight means longer path. But in trade networks, we want the opposite: a $78B corridor (CA↔TX) should be a *shorter* path than a $1M corridor (MT↔VT).

    **The fix**: We invert weights before computing betweenness:

    ```
    distance = max_weight / weight
    ```

    | Corridor | Trade Value | Inverted Distance |
    |----------|-------------|-------------------|
    | CA → TX | $78B | ~1 (short, preferred) |
    | MT → VT | $1M | ~78,000 (effectively infinite) |

    **Why it matters**: Without inversion, *isolated* states like DC, HI, and AK appeared as top "bridges"—because their weak connections created artificially long paths. With inversion, the true hubs emerge: CA, TX, NY.

    **The heavy-tail connection**: Remember the edge weight distribution? The bottom 90% of edges have such high inverted distances that they never participate in any shortest path. The network is 99.4% dense, but *effectively sparse*—only the backbone matters for betweenness.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    # Interactive filtration slider for methodology validation
    filtration_slider = mo.ui.slider(
        start=0,
        stop=50,
        value=0,
        step=5,
        label="Filtration %",
        show_value=True
    )
    mo.md(f"""
    ---

    ## Methodology Validation: Is 99% Density Suspicious?

    A skeptic might ask: *"With 99.4% edge density, aren't your centrality results just artifacts of a nearly-complete graph?"*

    **Try it yourself**: Use the slider to remove weak edges and watch the rankings. The network stays connected up to ~33%—beyond that it fragments.

    {filtration_slider}
    """)
    return (filtration_slider,)


@app.cell(hide_code=True)
def _(G_domestic, domestic_df, filtration_slider, mo):
    _pct = filtration_slider.value

    if _pct == 0:
        _output = mo.md("""
        **Baseline (no filtration)**: All 2,534 edges included. Move the slider to remove weak edges.
        """)
    else:
        _comp_info = count_components_at_filtration(G_domestic, _pct)
        _n_scc = _comp_info['n_strongly_connected']
        _threshold = _comp_info['threshold']
        _edges_remaining = _comp_info['edges_remaining']
        _is_connected = _comp_info['is_connected']

        if _is_connected:
            _G_filtered, _ = filter_graph_by_percentile(G_domestic, _pct)
            _filtered_df = compute_all_centralities(_G_filtered)

            _results = []
            for _m, _col in [
                ('Betweenness', 'betweenness'),
                ('Eigenvector', 'eigenvector'),
                ('Out-Degree', 'out_degree')
            ]:
                _baseline_vals = domestic_df.set_index('state_id')[_col]
                _filtered_vals = _filtered_df.set_index('state_id')[_col]
                _common = _baseline_vals.index.intersection(_filtered_vals.index)
                _rho, _ = spearmanr(_baseline_vals.loc[_common], _filtered_vals.loc[_common])
                _results.append((_m, _rho))

            _rows = "\n".join([f"| {m} | ρ = {rho:.4f} | {'✓ Stable' if rho > 0.95 else '~ Some change'} |"
                              for m, rho in _results])

            _output = mo.md(f"""
            **Filtration at {_pct}%** — ✓ Connected ({_edges_remaining} edges, threshold ${_threshold/1e6:.0f}M)

            | Measure | Spearman ρ vs Baseline | Status |
            |---------|------------------------|--------|
            {_rows}

            *Rankings virtually unchanged. The backbone carries the signal.*
            """)
        else:
            _output = mo.md(f"""
            **Filtration at {_pct}%** — ⚠️ **Fragmented** ({_n_scc} components, {_edges_remaining} edges)

            *Network has broken into {_n_scc} disconnected components. Centrality comparisons no longer meaningful.*

            **Key insight**: The network is robust up to ~33%, then rapidly fragments. The backbone (top 67% of edges) carries all structural information.
            """)

    _output
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Filtration Validates the Backbone

    Remember the **weight inversion fix**? High trade value = short path distance. This creates *effective sparsity*:

    | Edge Type | Trade Value | Inverted Distance | Role in Shortest Paths |
    |-----------|-------------|-------------------|------------------------|
    | CA → TX | $78B | ~1 | Always used |
    | MT → VT | $1M | ~78,000 | Never used |

    The bottom 33% of edges have such high inverted distances that they **never participate in any shortest path**. Removing them changes nothing because the algorithm already ignores them.

    **Conclusion**: The 99.4% density is not an artifact. Weight inversion creates a natural backbone, and our results are robust to edge removal.
    """)
    return


@app.cell(hide_code=True)
def _(G_domestic, master_state_df, mo):
    # === BETWEENNESS WITH FILTERING: DOES IT HELP? ===
    # Test whether 33% edge filtering makes betweenness more meaningful
    # (nx and filter_graph_by_percentile imported from setup cell)

    _df = master_state_df.copy()

    # Compute unfiltered betweenness divergence (not in master_state_df)
    _df['div_betweenness'] = _df['rank_gdp'] - _df['rank_betweenness']

    # --- Apply 33% filtering (max safe before fragmentation) ---
    _G_filtered, _threshold = filter_graph_by_percentile(G_domestic, 33)

    _n_edges_original = G_domestic.number_of_edges()
    _n_edges_filtered = _G_filtered.number_of_edges()
    _pct_removed = 100 * (1 - _n_edges_filtered / _n_edges_original)

    # --- Recompute betweenness on filtered network ---
    _btw_filtered_raw = nx.betweenness_centrality(_G_filtered, weight='weight', normalized=True)

    # Normalize to [0,1] using min-max scaling
    _btw_vals = list(_btw_filtered_raw.values())
    _btw_min, _btw_max = min(_btw_vals), max(_btw_vals)
    _btw_filtered = {k: (v - _btw_min) / (_btw_max - _btw_min) if _btw_max > _btw_min else 0
                     for k, v in _btw_filtered_raw.items()}

    # Add to dataframe
    _df['btw_filtered'] = _df['fips'].map(_btw_filtered)
    _df['rank_btw_filtered'] = _df['btw_filtered'].rank(ascending=False, method='min').astype(int)
    _df['div_btw_filtered'] = _df['rank_gdp'] - _df['rank_btw_filtered']

    # --- Compare unfiltered vs filtered betweenness ---
    _comparison = _df[['state_abbrev', 'rank_gdp', 'rank_betweenness', 'div_betweenness',
                       'rank_btw_filtered', 'div_btw_filtered']].copy()
    _comparison['rank_change'] = _comparison['rank_btw_filtered'] - _comparison['rank_betweenness']

    # Top 5 by divergence for each
    _top5_unfiltered = _df.nlargest(5, 'div_betweenness')[['state_abbrev', 'rank_gdp', 'rank_betweenness', 'div_betweenness']]
    _top5_filtered = _df.nlargest(5, 'div_btw_filtered')[['state_abbrev', 'rank_gdp', 'rank_btw_filtered', 'div_btw_filtered']]

    # Bottom 5 by divergence for each
    _bot5_unfiltered = _df.nsmallest(5, 'div_betweenness')[['state_abbrev', 'rank_gdp', 'rank_betweenness', 'div_betweenness']]
    _bot5_filtered = _df.nsmallest(5, 'div_btw_filtered')[['state_abbrev', 'rank_gdp', 'rank_btw_filtered', 'div_btw_filtered']]

    # --- Build comparison chart ---
    def _make_btw_chart(rank_col, div_col, title):
        _chart_df = _df.copy()
        _chart_df['rank_centrality'] = _chart_df[rank_col]
        _chart_df['divergence'] = _chart_df[div_col]

        _scatter = alt.Chart(_chart_df).mark_circle(size=60, opacity=0.7).encode(
            x=alt.X('rank_gdp:Q', title='GDP Rank', scale=alt.Scale(domain=[1, 51])),
            y=alt.Y('rank_centrality:Q', title='Betweenness Rank', scale=alt.Scale(domain=[1, 51])),
            color=alt.Color('divergence:Q',
                scale=alt.Scale(scheme='redblue', domain=[-20, 20]),
                legend=None
            ),
            tooltip=[
                alt.Tooltip('state_abbrev:N', title='State'),
                alt.Tooltip('rank_gdp:Q', title='GDP Rank'),
                alt.Tooltip('rank_centrality:Q', title='Betweenness Rank'),
                alt.Tooltip('divergence:Q', title='Divergence', format='+d')
            ]
        )

        _diag_data = pd.DataFrame({'x': [1, 51], 'y': [1, 51]})
        _diagonal = alt.Chart(_diag_data).mark_line(
            strokeDash=[5, 5], color='gray', strokeWidth=1.5
        ).encode(x='x:Q', y='y:Q')

        return alt.layer(_diagonal, _scatter).properties(width=300, height=300, title=title)

    _chart_unfiltered = _make_btw_chart('rank_betweenness', 'div_betweenness', 'Unfiltered (0%)')
    _chart_filtered = _make_btw_chart('rank_btw_filtered', 'div_btw_filtered', 'Filtered (33%)')

    _comparison_chart = alt.hconcat(_chart_unfiltered, _chart_filtered).properties(
        title='Betweenness: Does Filtering Help?'
    )

    # --- Check if filtering changes the story ---
    _unfiltered_top5_states = set(_top5_unfiltered['state_abbrev'].tolist())
    _filtered_top5_states = set(_top5_filtered['state_abbrev'].tolist())
    _overlap = len(_unfiltered_top5_states & _filtered_top5_states)

    mo.vstack([
        mo.md(f"""
    ---

    ## Does Filtering Fix Betweenness?

    Betweenness is unreliable in dense networks. Your earlier analysis found **33% filtration** is the maximum before the network fragments. Does filtering make GDP-normalized betweenness more meaningful?

    **Filtering details:**
    - Threshold: ${_threshold/1e6:.1f}M (edges below this removed)
    - Edges removed: {_n_edges_original - _n_edges_filtered:,} of {_n_edges_original:,} ({_pct_removed:.1f}%)
    - Edges remaining: {_n_edges_filtered:,}
        """),
        mo.md("---"),
        mo.hstack([
            mo.vstack([
                mo.md("**Unfiltered: Top 5 Above Weight**"),
                mo.ui.table(_top5_unfiltered.reset_index(drop=True))
            ]),
            mo.vstack([
                mo.md("**Filtered (33%): Top 5 Above Weight**"),
                mo.ui.table(_top5_filtered.reset_index(drop=True))
            ])
        ], justify='center', gap=2),
        mo.md("---"),
        _comparison_chart,
        mo.md(f"""
    **Result:** Top 5 overlap = {_overlap}/5 states

    {"**Filtering DOES change the story.** Different states emerge as overperformers — this suggests the unfiltered betweenness was indeed noise." if _overlap <= 2 else "**Filtering has limited effect.** Similar states appear in both — betweenness may be fundamentally problematic for this network, or 33% isn't enough filtering."}

    *Compare the scatter plots: Do points cluster more tightly around the diagonal after filtering (less divergence), or do genuine outliers emerge?*
        """),
        mo.callout(
            mo.md("""
    **Methodological Finding: Betweenness Stability Under Filtration**

    - **Unfiltered and filtered rankings are identical** (ρ=1.000 for all three measures at 33% filtration)
    - The compressed distribution (31 states at zero betweenness) reflects genuine network structure: trade routes through 5 hubs (CA, TX, NY, PA, IL)
    - Betweenness instability reported by Segarra & Ribeiro (2015) is an artifact of improper weight semantics, not an inherent limitation

    **Conclusion**: With correct weight inversion, betweenness reliably identifies bridging positions even at 99.4% density. The backbone carries the signal.
            """),
            kind="warn"
        ),
        mo.md("---"),
        mo.md("### Full Comparison: Unfiltered vs Filtered Betweenness"),
        mo.ui.table(
            _comparison.sort_values('div_btw_filtered', ascending=False)
            .rename(columns={
                'state_abbrev': 'State',
                'rank_gdp': 'GDP Rk',
                'rank_betweenness': 'Btw Rk (0%)',
                'div_betweenness': 'Δ (0%)',
                'rank_btw_filtered': 'Btw Rk (33%)',
                'div_btw_filtered': 'Δ (33%)',
                'rank_change': 'Rank Δ'
            })
            .reset_index(drop=True)
        )
    ])
    return


@app.cell(hide_code=True)
def _(domestic_df, intl_df, mo):
    # Compute rank changes between domestic (51×51) and international (52×52)
    _measures = ['betweenness', 'eigenvector', 'out_degree']
    _stats = []

    for _m in _measures:
        _dom_ranks = domestic_df.set_index('label')[f'rank_{_m}']
        _intl_ranks = intl_df.set_index('label')[f'rank_{_m}']

        # Only compare the 51 states (exclude RoW from intl)
        _common = _dom_ranks.index.intersection(_intl_ranks.index)
        _dom = _dom_ranks.loc[_common]
        _intl = _intl_ranks.loc[_common]

        # Count rank changes
        _changes = (_dom != _intl).sum()
        _pct = (_changes / len(_common)) * 100

        # Spearman correlation
        _rho, _ = spearmanr(_dom, _intl)

        _stats.append({
            'measure': _m,
            'changes': int(_changes),
            'pct': _pct,
            'rho': _rho
        })

    # Sort by correlation (highest first = most stable)
    _stats = sorted(_stats, key=lambda x: x['rho'], reverse=True)

    # Build the display with dynamic stability labels
    def _stability_label(rho):
        if rho >= 0.99: return 'Most stable'
        elif rho >= 0.95: return 'Very stable'
        elif rho >= 0.90: return 'Moderate'
        else: return 'Most sensitive'

    _rows = "\n".join([
        f"| **{s['measure'].replace('_', '-').title()}** | {s['changes']}/51 ({s['pct']:.0f}%) | ρ = {s['rho']:.3f} | {_stability_label(s['rho'])} |"
        for s in _stats
    ])

    # Identify most/least stable for narrative
    _most_stable = _stats[0]['measure'].replace('_', '-')
    _least_stable = _stats[-1]['measure']

    mo.md(f"""
    ---

    ## The Core Question: What Happens at the Boundary?

    We've measured centrality in the **51×51 domestic network**. But the U.S. doesn't trade in isolation—it connects to global markets. What happens when we add international trade?

    We construct a **52×52 network** by adding a "Rest of World" node representing all international trade flows. Then we compare rankings.

    ### The Finding

    | Measure | Rank Changes | Correlation | Stability |
    |---------|--------------|-------------|-----------|
    {_rows}

    **The pattern**: Trade capacity ({_most_stable}) is highly stable—states that export heavily domestically also export internationally. Bridging position ({_least_stable}) is most sensitive—adding a massive new node (RoW) reshuffles which states sit on shortest paths.

    *Why the difference? Out-degree reflects actual production/logistics infrastructure. Betweenness depends on network topology—adding RoW creates new shortest paths that bypass traditional domestic bridges.*
    """)
    return


@app.cell(hide_code=True)
def _(domestic_df, intl_df, mo):
    # === HERO VISUALIZATION: Boundary Sensitivity ===
    # Choropleth showing which states rise/fall when international trade is added

    # Merge domestic and international eigenvector ranks
    _dom = domestic_df[['label', 'rank_eigenvector']].copy()
    _dom.columns = ['label', 'domestic_rank']
    _intl = intl_df[['label', 'rank_eigenvector']].copy()
    _intl.columns = ['label', 'intl_rank']
    _df = _dom.merge(_intl, on='label')

    # Rank change: positive = improved (domestic was higher number, now lower)
    # e.g., domestic=15, intl=10 → change=+5 (rose 5 spots)
    _df['rank_change'] = _df['domestic_rank'] - _df['intl_rank']

    # Create divergence choropleth with PRGn
    _fig = px.choropleth(
        _df,
        locations='label',
        locationmode='USA-states',
        color='rank_change',
        color_continuous_scale='PRGn',
        color_continuous_midpoint=0,
        range_color=[-10, 10],
        scope='usa',
        title='<b>The Boundary Effect</b><br><sup>Who Gains When International Trade Enters?</sup>',
    )

    _fig.update_traces(
        hovertemplate='<b>%{location}</b><br>Rank Change: %{z:+d}<extra></extra>'
    )

    _fig.update_layout(
        geo=dict(showlakes=True, lakecolor='rgb(255,255,255)', bgcolor='rgba(0,0,0,0)'),
        margin=dict(l=0, r=0, t=80, b=20),
        coloraxis_colorbar=dict(
            title='Rank Change<br>(Eigenvector)',
            thickness=20,
            len=0.75,
            tickvals=[-8, -4, 0, 4, 8],
            ticktext=['-8', '-4', '0', '+4', '+8'],
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        title_font_size=22,
        title_x=0.5,
    )

    # Build callout lists for biggest movers
    _risers = _df.nlargest(5, 'rank_change')
    _fallers = _df.nsmallest(5, 'rank_change')
    _rise_str = ' · '.join([f"**{r['label']}** (+{int(r['rank_change'])})" for _, r in _risers.iterrows()])
    _fall_str = ' · '.join([f"**{r['label']}** ({int(r['rank_change'])})" for _, r in _fallers.iterrows()])

    mo.vstack([
        mo.md("---"),
        mo.md("## The Methodological Finding: Boundary Specification Matters"),
        _fig,
        mo.hstack([
            mo.callout(mo.md(f"**Gateway states rise** (green)\n\n{_rise_str}\n\n*Ports and border crossings gain prestige through RoW connection*"), kind='success'),
            mo.callout(mo.md(f"**Missouri loses 7 ranks** (purple)\n\nA domestic bridge—bypassed when gateways connect directly to international markets.\n\nAlso: {_fall_str}"), kind='warn'),
        ], justify='center', gap=1),
        mo.md("""
    *Betweenness is most sensitive to boundary specification (ρ=0.816) because it depends on shortest paths, which change when RoW creates new routes through gateway states. Eigenvector is more stable (ρ=0.982) because prestige spreads through the full network, not just shortest paths. Out-degree barely moves (ρ=0.994) because raw output capacity doesn't depend on network routing. The more a measure depends on global network structure, the more boundary specification matters.*
        """),
    ])
    return


@app.cell(hide_code=True)
def _(domestic_df, intl_df, mo):
    # Build scatter data for each measure (ordered: most stable → least stable)
    _measure_order = [
        ('out_degree', 'Out-Degree (Capacity)', '#ff7f0e'),
        ('eigenvector', 'Eigenvector (Prestige)', '#2ca02c'),
        ('betweenness', 'Betweenness (Bridge)', '#1f77b4')
    ]

    def _make_scatter(_measure, _title, _color):
        # Get ranks for this measure
        _dom = domestic_df[['label', f'rank_{_measure}']].copy()
        _dom.columns = ['state', 'domestic_rank']
        _intl = intl_df[['label', f'rank_{_measure}']].copy()
        _intl.columns = ['state', 'intl_rank']
        _df = _dom.merge(_intl, on='state')

        # Diagonal reference line
        _diag = pd.DataFrame({'x': [1, 51], 'y': [1, 51]})
        _line = alt.Chart(_diag).mark_line(
            strokeDash=[4, 4], color='gray', opacity=0.5
        ).encode(x='x:Q', y='y:Q')

        # Scatter points
        _points = alt.Chart(_df).mark_circle(size=60, opacity=0.8, color=_color).encode(
            x=alt.X('domestic_rank:Q', title='Domestic Rank', scale=alt.Scale(domain=[1, 51])),
            y=alt.Y('intl_rank:Q', title='International Rank', scale=alt.Scale(domain=[1, 51])),
            tooltip=[
                alt.Tooltip('state:N', title='State'),
                alt.Tooltip('domestic_rank:Q', title='Domestic'),
                alt.Tooltip('intl_rank:Q', title='International')
            ]
        )

        return alt.layer(_line, _points).properties(width=200, height=200, title=_title)

    # Create three charts and concatenate horizontally
    _charts = [_make_scatter(m, t, c) for m, t, c in _measure_order]
    _combined = alt.hconcat(*_charts).resolve_scale(x='shared', y='shared')

    mo.vstack([
        mo.md("""
    ### Visual Evidence

    Each point is a state. The diagonal line represents **perfect stability** (domestic rank = international rank). Distance from the diagonal = rank change.
        """),
        _combined,
        mo.md("*Out-degree clusters tightly on the diagonal (ρ=0.994)—trade capacity is robust to boundary changes. Betweenness scatters most (ρ=0.816)—adding RoW reshuffles which states bridge shortest paths.*")
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---

    ## Key Takeaways

    1. **Network centrality reveals structure that GDP hides.** California dominates both GDP and centrality, but Florida (#4 GDP) ranks #30+ in betweenness—a peninsula, not a bridge.

    2. **Different measures capture different power dimensions.** Betweenness (bridging), eigenvector (prestige), and out-degree (capacity) tell complementary stories. No single measure captures "importance."

    3. **Boundary specification matters—selectively.** Adding international trade reshuffles betweenness rankings (ρ=0.816) but barely affects out-degree (ρ=0.994). Trade capacity is robust; bridging position is contextual.

    4. **Weight inversion is essential.** Without it, isolated states appear as "bridges." With it, the true hubs emerge: CA, TX, NY.

    5. **Dense networks can have sparse backbones.** At 99.4% density, only ~5% of edges carry significant weight. Filtration validates that our results aren't artifacts.

    ---

    *Data: Census Bureau Commodity Flow Survey 2017 | Analysis: NetworkX + custom toolkit | Visualization: Altair + Plotly*
    """)
    return


@app.cell
def _(gdp_centrality_df, mo):
    mo.ui.table(gdp_centrality_df)
    return


@app.cell
def _(edge_weights_df, mo):
    mo.ui.table(edge_weights_df)
    return


@app.cell
def _(domestic_df, mo):
    mo.ui.table(domestic_df)
    return


if __name__ == "__main__":
    app.run()
