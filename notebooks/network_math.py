# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "pandas==2.3.1",
#     "numpy==2.3.2",
#     "altair==5.5.0",
#     "plotly==5.24.1",
# ]
# [tool.marimo.display]
# theme = "system"
# ///

import marimo

__generated_with = "0.23.8"
app = marimo.App(width="full", auto_download=["html"])

with app.setup(hide_code=True):
    import pandas as pd
    import numpy as np
    import altair as alt
    import plotly.express as px
    import marimo as mo
    from pathlib import Path

    REPO_ROOT = Path(__file__).parent.parent
    VIZ_DATA = REPO_ROOT / "viz" / "data"

    _c51 = pd.read_csv(VIZ_DATA / "centralities_51x51.csv").rename(columns={"label": "state"})
    _gdp = pd.read_csv(VIZ_DATA / "state_gdp_2017.csv")
    _gdp["gdp_billions"] = _gdp["gdp_2017_q4_millions"] / 1000
    _gdp["gdp_rank"] = _gdp["gdp_billions"].rank(ascending=False, method="min").astype(int)
    _coords = pd.read_csv(VIZ_DATA / "state_coords.csv")

    df = _c51.merge(
        _gdp[["state_abbrev", "gdp_billions", "gdp_rank"]],
        left_on="state", right_on="state_abbrev", how="left",
    ).drop(columns=["state_abbrev"])
    df = df.merge(
        _coords[["state_abbr", "state_name"]],
        left_on="state", right_on="state_abbr", how="left",
    ).drop(columns=["state_abbr"])
    df["divergence"] = df["gdp_rank"] - df["rank_eigenvector"]
    df["abs_divergence"] = df["divergence"].abs()

    STATE_LIST = sorted(
        [(row["state_name"], row["state"]) for _, row in df.iterrows()],
        key=lambda x: x[0],
    )


@app.cell(hide_code=True)
def _():
    mo.md("""
    # What GDP Misses About Your State's Economy

    If someone asked you to rank the 50 states by economic importance,
    you'd probably reach for GDP. California, Texas, New York — the usual suspects.

    But what if that ranking is **systematically wrong about 40% of states?**

    GDP answers one question: *how much does this state produce?*

    There's a different question: *how does this state sit within the web of
    trade relationships across the country?*

    **Those are fundamentally different questions, and they need different math.**
    This notebook shows you why — with concrete examples you can explore yourself.
    """)
    return


@app.cell(hide_code=True)
def _():
    _fig = px.choropleth(
        df,
        locations="state",
        locationmode="USA-states",
        color="gdp_billions",
        color_continuous_scale="Blues",
        scope="usa",
        hover_name="state_name",
        hover_data={"gdp_billions": ":.0f", "gdp_rank": True, "state": False},
        labels={"gdp_billions": "GDP ($B)", "gdp_rank": "GDP Rank"},
    )
    _fig.update_layout(
        title=None,
        geo=dict(bgcolor="rgba(0,0,0,0)", lakecolor="rgba(0,0,0,0)"),
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        coloraxis_colorbar=dict(title="GDP ($B)"),
        height=380,
    )
    mo.vstack([
        mo.md("## The Familiar Map"),
        mo.ui.plotly(_fig),
        mo.callout(
            mo.md(
                "**Top 5 by GDP:** California (\$2,802B), Texas (\$1,747B), "
                "New York (\$1,564B), Florida (\$984B), Illinois (\$836B)"
            ),
            kind="info",
        ),
        mo.md("*This map measures how much each state produces. It says nothing about how states connect.*"),
    ])
    return


@app.cell(hide_code=True)
def _():
    mo.md("""
    ## Same Totals, Different Structures

    Before we look at real data, consider a thought experiment. Here are two
    tiny trade networks. **Every node has the same total trade volume** — \$100
    billion in and \$100 billion out. By GDP logic, they're all equally important.

    But look at the *structure:*
    """)
    return


@app.cell(hide_code=True)
def _():
    # Two toy networks — same totals, different structures
    # Hub-and-spoke
    _hub_nodes = pd.DataFrame({
        "node": ["A", "B", "C", "D", "E"],
        "x": [300, 150, 450, 150, 450],
        "y": [200, 50, 50, 350, 350],
        "total_trade": [100, 100, 100, 100, 100],
        "color": ["#dd3344", "#4488ff", "#4488ff", "#4488ff", "#4488ff"],
    })

    _hub = alt.Chart(_hub_nodes).mark_circle(size=1200, stroke="white", strokeWidth=2).encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[0, 600]), axis=alt.Axis(labels=False, ticks=False, domain=False, title=None, grid=False)),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[0, 400]), axis=alt.Axis(labels=False, ticks=False, domain=False, title=None, grid=False)),
        color=alt.Color("color:N", scale=None),
        tooltip=["node:N", "total_trade:Q"],
    )
    _hub_labels = alt.Chart(_hub_nodes).mark_text(fontSize=16, fontWeight="bold", color="white").encode(
        x="x:Q", y="y:Q", text="node:N",
    )

    _hub_edge_data = pd.DataFrame([
        {"x": 300, "y": 200, "x2": 150, "y2": 50},
        {"x": 300, "y": 200, "x2": 450, "y2": 50},
        {"x": 300, "y": 200, "x2": 150, "y2": 350},
        {"x": 300, "y": 200, "x2": 450, "y2": 350},
    ])
    _hub_edges = alt.Chart(_hub_edge_data).mark_rule(color="#aaa", strokeWidth=2).encode(
        x="x:Q", y="y:Q", x2="x2:Q", y2="y2:Q",
    )

    _hub_chart = (_hub_edges + _hub + _hub_labels).properties(
        width=280, height=220, title=alt.Title("Hub-and-Spoke", subtitle="A is central — remove it and the network collapses")
    )

    # Ring
    _ring_nodes = pd.DataFrame({
        "node": ["A", "B", "C", "D", "E"],
        "x": [300, 105, 180, 420, 495],
        "y": [50, 200, 370, 370, 200],
        "total_trade": [100, 100, 100, 100, 100],
    })

    _ring = alt.Chart(_ring_nodes).mark_circle(size=1200, color="#4488ff", stroke="white", strokeWidth=2).encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[0, 600]), axis=alt.Axis(labels=False, ticks=False, domain=False, title=None, grid=False)),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[0, 400]), axis=alt.Axis(labels=False, ticks=False, domain=False, title=None, grid=False)),
        tooltip=["node:N", "total_trade:Q"],
    )
    _ring_labels = alt.Chart(_ring_nodes).mark_text(fontSize=16, fontWeight="bold", color="white").encode(
        x="x:Q", y="y:Q", text="node:N",
    )

    _ring_edge_data = pd.DataFrame([
        {"x": 300, "y": 50, "x2": 105, "y2": 200},
        {"x": 105, "y": 200, "x2": 180, "y2": 370},
        {"x": 180, "y": 370, "x2": 420, "y2": 370},
        {"x": 420, "y": 370, "x2": 495, "y2": 200},
        {"x": 495, "y": 200, "x2": 300, "y2": 50},
    ])
    _ring_edges = alt.Chart(_ring_edge_data).mark_rule(color="#aaa", strokeWidth=2).encode(
        x="x:Q", y="y:Q", x2="x2:Q", y2="y2:Q",
    )

    _ring_chart = (_ring_edges + _ring + _ring_labels).properties(
        width=280, height=220, title=alt.Title("Ring", subtitle="No node is special — remove any one, the rest still connect")
    )

    mo.vstack([
        mo.hstack([_hub_chart, _ring_chart]),
        mo.callout(
            mo.md(
                "**Every node trades \$100B total.** But in the hub network, Node A is clearly "
                "the most important — remove it and the network falls apart. In the ring, no "
                "node is special.\n\n"
                "**This is what GDP misses.** GDP would rank all five nodes equally in both "
                "networks. Network centrality sees the difference: A's *position* makes it "
                "powerful, not its *size*."
            ),
            kind="warn",
        ),
    ])
    return


@app.cell(hide_code=True)
def _():
    mo.md("""
    ## Now Apply This to Real States

    The Census Bureau tracks what every state ships to every other state —
    billions of dollars of physical goods across 2,534 trade routes between
    51 states. When we compute each state's *position* in that network
    (using the same logic as the hub example), and compare it to GDP, the
    results are surprising.

    **Green = states whose network position exceeds their GDP rank** (structurally undervalued)

    **Purple = states whose GDP overstates their trade network importance** (structurally overvalued)
    """)
    return


@app.cell(hide_code=True)
def _():
    _fig = px.choropleth(
        df,
        locations="state",
        locationmode="USA-states",
        color="divergence",
        color_continuous_scale="PRGn",
        color_continuous_midpoint=0,
        range_color=[-15, 15],
        scope="usa",
        hover_name="state_name",
        hover_data={"gdp_rank": True, "rank_eigenvector": True, "divergence": True, "state": False},
        labels={"divergence": "Divergence", "gdp_rank": "GDP Rank", "rank_eigenvector": "Network Rank"},
    )
    _fig.update_layout(
        title=None,
        geo=dict(bgcolor="rgba(0,0,0,0)", lakecolor="rgba(0,0,0,0)"),
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        coloraxis_colorbar=dict(title="Divergence<br>(+ = undervalued<br>by GDP)"),
        height=400,
    )
    mo.ui.plotly(_fig)
    return


@app.cell(hide_code=True)
def _():
    mo.hstack(
        [
            mo.callout(
                mo.md(
                    "**Structurally undervalued** (network > GDP)\n\n"
                    "- **Kentucky** (+14): GDP #28, Network #14\n"
                    "- **Mississippi** (+10): GDP #37, Network #27\n"
                    "- **Montana** (+8): GDP #49, Network #41\n"
                    "- **Louisiana** (+7): GDP #24, Network #17\n"
                    "- **South Carolina** (+7): GDP #26, Network #19\n\n"
                    "*Manufacturing, energy, and agricultural states. They make, "
                    "extract, and ship physical goods — connecting them to the "
                    "biggest hubs in the network.*"
                ),
                kind="success",
            ),
            mo.callout(
                mo.md(
                    "**Structurally overvalued** (GDP > network)\n\n"
                    "- **DC** (-15): GDP #34, Network #49\n"
                    "- **Massachusetts** (-11): GDP #11, Network #22\n"
                    "- **Minnesota** (-9): GDP #17, Network #26\n"
                    "- **Colorado** (-9): GDP #19, Network #28\n"
                    "- **Washington** (-8): GDP #13, Network #21\n\n"
                    "*Service and knowledge economies. High GDP from finance, "
                    "tech, healthcare — but less central in the physical "
                    "trade network.*"
                ),
                kind="danger",
            ),
        ],
        widths="equal",
    )
    return


@app.cell(hide_code=True)
def _():
    mo.md("""
    ### The Kentucky Story

    Kentucky's GDP ranks **#28** — a modest, mid-tier economy at \$206 billion.
    But its network centrality ranks **#14**, placing it in the top quarter.

    Why? Kentucky is a manufacturing and logistics nexus: automobiles
    (Toyota's largest North American plant), bourbon, tobacco, and coal. It
    sits at the crossroads of I-65, I-64, I-71, and I-75. It trades heavily
    with Ohio (#4 in the network), Indiana (#10), Tennessee (#12), and
    Illinois (#6).

    **Its trading partners are themselves major hubs.** Think back to the toy
    example: Kentucky is like a spoke connected directly to Node A. That
    connection to the hub raises its importance — even though its own
    economy is mid-tier.

    This recursive relationship — importance flowing through connections — is
    exactly what network centrality measures and GDP cannot.
    """)
    return


@app.cell(hide_code=True)
def _():
    mo.callout(
        mo.md(
            '''
            ### The Peninsula Puzzle: Florida

            Florida is the **4th largest economy** in the nation at nearly \$1 trillion.
            Its network prestige is #5 — roughly proportional.

            But here's the puzzle: Florida sits on **zero** of the shortest trade paths
            between other states. Of 51 states, 31 share this property — but Florida
            is the largest economy among them.

            Why? Geography. A peninsula has no through-traffic. Trade flows *into*
            Florida (consumer goods for 22 million residents), but the major corridors
            between other states bypass it entirely.

            In our toy example, Florida is a spoke connected to the hub — well-connected
            but not a *bridge*. If supply chains need to reroute, Florida has no
            alternative paths. It's a well-connected dead end.
            '''
        ),
        kind="info",
    )
    return


@app.cell(hide_code=True)
def _():
    _options = {name: abbr for name, abbr in STATE_LIST}
    state_picker = mo.ui.dropdown(options=_options, value="Indiana", label="Select a state")
    mo.vstack([
        mo.md("## Look Up Your State"),
        mo.md("Every state has a unique structural fingerprint in the trade network."),
        state_picker,
    ])
    return (state_picker,)


@app.cell(hide_code=True)
def _(state_picker):
    _abbr = state_picker.value or "IN"
    _row = df[df["state"] == _abbr].iloc[0]
    _div = int(_row["divergence"])

    _kind = "info" if abs(_div) < 3 else ("success" if _div > 0 else "danger")
    _status = (
        "**Proportional** — GDP and network position roughly aligned"
        if abs(_div) < 3
        else f"**Punches above weight** (+{_div}) — network position exceeds GDP"
        if _div > 0
        else f"**Punches below weight** ({_div}) — GDP overstates network role"
    )

    mo.vstack([
        mo.md(
            f"### {_row['state_name']} ({_abbr})\n\n"
            f"| Measure | Value | Rank |\n"
            f"|---------|-------|------|\n"
            f"| **GDP (2017)** | ${_row['gdp_billions']:.0f}B | #{int(_row['gdp_rank'])} |\n"
            f"| **Eigenvector** (trade prestige) | {_row['eigenvector']:.4f} | #{int(_row['rank_eigenvector'])} |\n"
            f"| **Betweenness** (bridge position) | {_row['betweenness']:.4f} | #{int(_row['rank_betweenness'])} |\n"
            f"| **Out-Degree** (export reach) | {_row['out_degree']:.4f} | #{int(_row['rank_out_degree'])} |"
        ),
        mo.callout(mo.md(_status), kind=_kind),
    ])
    return


@app.cell(hide_code=True)
def _(state_picker):
    _abbr = state_picker.value or "IN"
    _plot_df = df.copy()
    _plot_df["is_selected"] = _plot_df["state"] == _abbr

    _scatter = alt.Chart(_plot_df).mark_circle().encode(
        x=alt.X("gdp_rank:Q", title="GDP Rank (1 = largest economy)", scale=alt.Scale(domain=[1, 51])),
        y=alt.Y("rank_eigenvector:Q", title="Network Rank (1 = most central)", scale=alt.Scale(domain=[1, 51])),
        color=alt.condition(
            alt.datum.is_selected,
            alt.value("#dd3344"),
            alt.Color("divergence:Q", scale=alt.Scale(scheme="purplegreen", domainMid=0), legend=None),
        ),
        size=alt.condition(alt.datum.is_selected, alt.value(200), alt.value(60)),
        tooltip=["state_name:N", "gdp_rank:Q", "rank_eigenvector:Q", "divergence:Q"],
    ).properties(width=500, height=400)

    _diag = alt.Chart(pd.DataFrame({"x": [1, 51], "y": [1, 51]})).mark_line(
        strokeDash=[4, 4], color="gray", opacity=0.5,
    ).encode(x="x:Q", y="y:Q")

    mo.vstack([
        mo.md("*Above the diagonal = structurally undervalued by GDP. Below = overvalued.*"),
        mo.ui.altair_chart(_scatter + _diag),
    ])
    return


@app.cell(hide_code=True)
def _():
    mo.vstack([
        mo.md(
            '''
            ## Why the Math Is Different

            ### GDP Is Addition. Centrality Is Multiplication.

            **GDP** sums up everything produced within a state. It's a tally. Each state's
            number is independent — California's GDP doesn't affect Kentucky's GDP.

            **Network centrality** works differently. Your score depends on the scores of
            the states you trade with. If Kentucky trades heavily with Ohio (a major hub),
            Kentucky's centrality goes up. If Ohio also trades with Texas (another giant),
            that *indirectly* raises Kentucky's centrality too.

            It's recursive: importance flows through the network.

            This is why GDP and centrality can diverge: **GDP captures what you produce on
            your own. Centrality captures who you're embedded with.**
            '''
        ),
        mo.accordion(
            {
                "A bit more formally...": mo.md(
                    "A state's eigenvector centrality is proportional to the weighted "
                    "sum of its neighbors' centralities. If you trade with important "
                    "states, you become important. If those states trade with other "
                    "important states, your importance compounds. GDP has no such "
                    "feedback loop — it's a simple aggregate, while centrality is a "
                    "fixed-point solution to a system of simultaneous equations."
                ),
            }
        ),
        mo.md(
            '''
            ### The Bridge vs the Hub

            There's a second kind of structural role that GDP misses entirely.
            **Betweenness** asks: does trade between *other* states have to flow
            through you?

            Only **20 of 51 states** have any betweenness at all. The entire
            network's shortest trade paths flow through just CA, TX, NY, PA, IL,
            and a handful of others.

            You can be a major hub (high prestige) without being a bridge (zero
            betweenness). Florida is the perfect example — prestige #5 but zero
            betweenness. Conversely, Massachusetts is GDP #11 and prestige #22
            (underperformer), but **betweenness #6** — it sits on critical trade
            routes even though its own trade volume is modest.
            '''
        ),
    ])
    return


@app.cell(hide_code=True)
def _():
    mo.vstack([
        mo.md("## Why This Matters"),
        mo.md(
            '''
            States with high network centrality but low GDP are *structurally
            undervalued*: policymakers planning infrastructure investment based on
            GDP alone are systematically under-investing in the states that hold
            the trade network together.
            '''
        ),
        mo.hstack(
            [
                mo.callout(
                    mo.md(
                        "**GDP measures size.**\n"
                        "**Centrality measures position.**\n\n"
                        "They diverge for 40% of states."
                    ),
                    kind="neutral",
                ),
                mo.callout(
                    mo.md(
                        "**Manufacturing, energy, and agricultural states** are "
                        "structurally undervalued by GDP. Service economies are "
                        "structurally overvalued."
                    ),
                    kind="neutral",
                ),
                mo.callout(
                    mo.md(
                        "**Infrastructure policy, supply chain planning, and "
                        "investment decisions** should account for network position, "
                        "not just economic output."
                    ),
                    kind="neutral",
                ),
            ],
            widths="equal",
        ),
        mo.md(
            "---\n\n"
            "**Data:** U.S. Census Bureau Commodity Flow Survey 2017 | "
            "**Analysis:** Thornton (2026), *Interstate Commerce Network Centrality*, "
            "Master's Thesis, Binghamton University | "
            "**Method:** Eigenvector, betweenness, and weighted out-degree centrality "
            "on a directed network of 51 nodes with 2,534 edges"
        ),
    ])
    return


if __name__ == "__main__":
    app.run()
