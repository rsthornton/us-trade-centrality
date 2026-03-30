"""
Choropleth figure generation for thesis paper.

Extracts Plotly choropleth logic from the Marimo companion notebook
into standalone functions that export static PNGs via kaleido.
"""

import pandas as pd
import plotly.express as px
import plotly.io as pio
from pathlib import Path


def generate_physical_economy_divergence(domestic_centralities_path, gdp_path, output_path):
    """
    GDP rank vs eigenvector rank divergence choropleth.

    Uses PRGn colorscale, range [-12, 12].
    Green = overperformer (more central than GDP predicts).
    Purple = underperformer (less central than GDP predicts).

    Args:
        domestic_centralities_path: Path to domestic centralities CSV
        gdp_path: Path to state_gdp_2017.csv
        output_path: Path for output PNG
    """
    output_path = Path(output_path)

    # Load data
    cent_df = pd.read_csv(domestic_centralities_path)
    gdp_df = pd.read_csv(gdp_path)

    # Compute eigenvector rank
    cent_df['eig_rank'] = cent_df['eigenvector'].rank(ascending=False, method='min').astype(int)

    # Merge with GDP
    gdp_dict = dict(zip(gdp_df['state_abbrev'], gdp_df['gdp_2017_q4_millions']))
    cent_df['gdp_value'] = cent_df['label'].map(gdp_dict)
    cent_df['gdp_rank'] = cent_df['gdp_value'].rank(ascending=False, method='min').astype(int)

    # Compute divergence
    cent_df['divergence'] = cent_df['gdp_rank'] - cent_df['eig_rank']

    # Create choropleth
    fig = px.choropleth(
        cent_df,
        locations='label',
        locationmode='USA-states',
        color='divergence',
        color_continuous_scale='PRGn',
        color_continuous_midpoint=0,
        range_color=[-12, 12],
        scope='usa',
        title='<b>The Physical Economy</b><br><sup>Who Punches Above Their Weight?</sup>',
    )

    fig.update_traces(
        hovertemplate='<b>%{location}</b><br>Divergence: %{z:+d}<extra></extra>'
    )

    fig.update_layout(
        geo=dict(showlakes=True, lakecolor='rgb(255,255,255)', bgcolor='rgba(0,0,0,0)'),
        margin=dict(l=0, r=0, t=80, b=20),
        coloraxis_colorbar=dict(
            title=dict(text='GDP Rank −<br>Centrality Rank', font=dict(size=16)),
            thickness=20,
            len=0.75,
            tickvals=[-10, -5, 0, 5, 10],
            ticktext=['-10', '-5', '0', '+5', '+10'],
            tickfont=dict(size=14),
        ),
        paper_bgcolor='white',
        title_font_size=26,
        title_x=0.5,
    )

    # Export
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pio.write_image(fig, str(output_path), width=1000, height=600, scale=2)
    print(f"✓ Physical economy divergence choropleth saved: {output_path}")


def generate_boundary_effect_choropleth(domestic_centralities_path, intl_centralities_path, output_path):
    """
    Domestic vs international eigenvector rank change choropleth.

    Uses PRGn colorscale, range [-10, 10].
    Green = gained ranks when international trade added (gateway states).
    Purple = lost ranks (interior bridges bypassed).

    Args:
        domestic_centralities_path: Path to domestic centralities CSV
        intl_centralities_path: Path to international centralities CSV
        output_path: Path for output PNG
    """
    output_path = Path(output_path)

    # Load data
    dom_df = pd.read_csv(domestic_centralities_path)
    intl_df = pd.read_csv(intl_centralities_path)

    # Compute eigenvector ranks
    dom_df['domestic_rank'] = dom_df['eigenvector'].rank(ascending=False, method='min').astype(int)
    intl_df['intl_rank'] = intl_df['eigenvector'].rank(ascending=False, method='min').astype(int)

    # Filter international to US states only (exclude RoW)
    intl_df = intl_df[intl_df['label'] != 'RoW'].copy()

    # Merge
    merged = dom_df[['label', 'domestic_rank']].merge(
        intl_df[['label', 'intl_rank']], on='label'
    )

    # Rank change: positive = improved (domestic was higher number, now lower)
    merged['rank_change'] = merged['domestic_rank'] - merged['intl_rank']

    # Create choropleth
    fig = px.choropleth(
        merged,
        locations='label',
        locationmode='USA-states',
        color='rank_change',
        color_continuous_scale='PRGn',
        color_continuous_midpoint=0,
        range_color=[-10, 10],
        scope='usa',
        title='<b>The Boundary Effect</b><br><sup>Who Gains When International Trade Enters?</sup>',
    )

    fig.update_traces(
        hovertemplate='<b>%{location}</b><br>Rank Change: %{z:+d}<extra></extra>'
    )

    fig.update_layout(
        geo=dict(showlakes=True, lakecolor='rgb(255,255,255)', bgcolor='rgba(0,0,0,0)'),
        margin=dict(l=0, r=0, t=80, b=20),
        coloraxis_colorbar=dict(
            title=dict(text='Rank Change<br>(Eigenvector)', font=dict(size=16)),
            thickness=20,
            len=0.75,
            tickvals=[-8, -4, 0, 4, 8],
            ticktext=['-8', '-4', '0', '+4', '+8'],
            tickfont=dict(size=14),
        ),
        paper_bgcolor='white',
        title_font_size=26,
        title_x=0.5,
    )

    # Export
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pio.write_image(fig, str(output_path), width=1000, height=600, scale=2)
    print(f"✓ Boundary effect choropleth saved: {output_path}")
