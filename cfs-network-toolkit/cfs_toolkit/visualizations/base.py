"""
Base Visualization Module
========================
Core visualization functions without import-time style configuration.
Uses lazy imports and callable styling from styles.py.
"""

from pathlib import Path
from typing import Optional, Dict, Tuple, List, Union, Any
import warnings

# Lazy imports for optional plotting dependencies
def _import_plotting_libs():
    """Lazy import plotting libraries to avoid hard dependencies."""
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        import plotly.graph_objects as go
        import plotly.express as px
        import networkx as nx
        import pandas as pd
        import numpy as np
        return plt, sns, go, px, nx, pd, np
    except ImportError as e:
        raise ImportError(f"Plotting libraries not available: {e}. Install with 'pip install project[viz]'")

def create_centrality_comparison(
    centralities_df,
    top_n: int = 10,
    save_path: Optional[Path] = None
):
    """
    Create three-panel centrality comparison bar charts.

    Args:
        centralities_df: Pipeline output with columns [label, betweenness, eigenvector, out_degree, rank_*]
        top_n: Number of top states to display
        save_path: Optional path to save figure

    Returns:
        matplotlib Figure object

    Raises:
        ValueError: If required columns are missing
    """
    plt, sns, go, px, nx, pd, np = _import_plotting_libs()
    from cfs_toolkit.visualizations.styles import set_publication_style, get_color_palette

    # Apply styling
    set_publication_style()
    COLORS = get_color_palette()

    # Validate input
    required_cols = ['label', 'betweenness', 'eigenvector', 'out_degree']
    missing_cols = [col for col in required_cols if col not in centralities_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Prepare data
    measures = [
        ('Betweenness\n(Regional Bridging)', 'betweenness', 'rank_betweenness'),
        ('Eigenvector\n(Influence Networks)', 'eigenvector', 'rank_eigenvector'),
        ('Out-Degree\n(Distribution Power)', 'out_degree', 'rank_out_degree')
    ]

    # Create figure
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle('Three-Level Network Centrality Analysis', fontsize=14, fontweight='bold')

    for i, (title, score_col, rank_col) in enumerate(measures):
        ax = axes[i]

        # Get top N states
        if rank_col in centralities_df.columns:
            top_states = centralities_df.nsmallest(top_n, rank_col)
        else:
            # Fallback: sort by score directly
            top_states = centralities_df.nlargest(top_n, score_col)

        # Color coding: top 3 highlighted
        colors = [COLORS['secondary'] if j < 3 else COLORS['primary']
                 for j in range(len(top_states))]

        # Create bars
        bars = ax.bar(range(len(top_states)), top_states[score_col], color=colors, alpha=0.8)

        # Formatting
        ax.set_xticks(range(len(top_states)))
        ax.set_xticklabels(top_states['label'], rotation=45, ha='right')
        ax.set_title(title, fontweight='bold')
        ax.set_ylabel('Centrality Score')
        ax.grid(axis='y', alpha=0.3)

        # Add value labels on bars
        for j, bar in enumerate(bars):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                   f'{height:.3f}', ha='center', va='bottom', fontsize=8)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, bbox_inches='tight', facecolor='white')
        print(f"Centrality comparison saved to {save_path}")

    return fig

def create_3d_centrality_plot(centralities_df, save_path: Optional[Path] = None):
    """Create 3D interactive centrality scatter plot using Plotly."""
    plt, sns, go, px, nx, pd, np = _import_plotting_libs()

    # Create 3D scatter plot
    fig = go.Figure(data=go.Scatter3d(
        x=centralities_df['betweenness'],
        y=centralities_df['eigenvector'],
        z=centralities_df['out_degree'],
        mode='markers+text',
        text=centralities_df['label'],
        textposition='top center',
        marker=dict(
            size=8,
            color=centralities_df['betweenness'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Betweenness Centrality")
        ),
        hovertemplate='<b>%{text}</b><br>' +
                     'Betweenness: %{x:.3f}<br>' +
                     'Eigenvector: %{y:.3f}<br>' +
                     'Out-degree: %{z:.3f}<extra></extra>'
    ))

    fig.update_layout(
        title='3D Network Centrality Space',
        scene=dict(
            xaxis_title='Betweenness (Regional Bridging)',
            yaxis_title='Eigenvector (Influence)',
            zaxis_title='Out-Degree (Distribution Power)'
        ),
        showlegend=False
    )

    if save_path:
        fig.write_html(str(save_path))
        print(f"3D centrality plot saved to {save_path}")

    return fig


def create_static_3d_plots(
    centralities_df,
    save_dir: Optional[Path] = None,
    network_label: str = "51×51"
):
    """
    Create static 3D scatter plots suitable for PDF inclusion.
    Generates multiple viewing angles of the 3D centrality space.

    Args:
        centralities_df: Pipeline output with columns [label, betweenness, eigenvector, out_degree]
        save_dir: Directory to save figures
        network_label: Label for this network

    Returns:
        List of matplotlib Figure objects
    """
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    import pandas as pd
    import numpy as np

    from cfs_toolkit.visualizations.styles import set_publication_style, get_color_palette

    set_publication_style()
    COLORS = get_color_palette()

    # Normalize measures to [0, 1] for color mapping
    df = centralities_df.copy()

    # Create color based on betweenness (like interactive version)
    if df['betweenness'].max() > 0:
        color_vals = df['betweenness'] / df['betweenness'].max()
    else:
        color_vals = np.zeros(len(df))

    figures = []

    # Define viewing angles (elevation, azimuth)
    views = [
        (30, 45, "perspective"),     # Default perspective
        (0, 0, "front"),             # Front view (eigenvector vs betweenness)
        (0, 90, "side"),             # Side view (out-degree vs betweenness)
    ]

    for elev, azim, view_name in views:
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')

        # Scatter plot with color gradient
        scatter = ax.scatter(
            df['betweenness'],
            df['eigenvector'],
            df['out_degree'],
            c=color_vals,
            cmap='viridis',
            s=100,
            alpha=0.7,
            edgecolors='black',
            linewidth=0.5
        )

        # Annotate top states (top 3 in each measure)
        top_states = set()
        for measure in ['betweenness', 'eigenvector', 'out_degree']:
            top_3 = df.nlargest(3, measure)['label'].tolist()
            top_states.update(top_3)

        for _, row in df[df['label'].isin(top_states)].iterrows():
            ax.text(
                row['betweenness'],
                row['eigenvector'],
                row['out_degree'],
                row['label'],
                fontsize=8,
                alpha=0.8
            )

        # Axis labels
        ax.set_xlabel('Betweenness\n(Macro)', fontweight='bold', fontsize=11)
        ax.set_ylabel('Eigenvector\n(Meso)', fontweight='bold', fontsize=11)
        ax.set_zlabel('Out-Degree\n(Micro)', fontweight='bold', fontsize=11)

        # Set viewing angle
        ax.view_init(elev=elev, azim=azim)

        # Title
        ax.set_title(
            f'3D Centrality Space ({network_label})\n{view_name.title()} View',
            fontweight='bold',
            fontsize=14,
            pad=20
        )

        # Colorbar
        cbar = plt.colorbar(scatter, ax=ax, pad=0.1, shrink=0.8)
        cbar.set_label('Betweenness Centrality', fontweight='bold')

        # Grid
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_dir:
            filename = f'3d_centrality_{view_name}.png'
            fig.savefig(save_dir / filename, dpi=300, bbox_inches='tight', facecolor='white')
            print(f"Saved {filename}")

        figures.append(fig)

    return figures

def create_pairwise_scatter_plots(
    centralities_df,
    save_dir: Optional[Path] = None,
    network_label: str = "51×51"
):
    """
    Create pairwise scatter plots for all centrality measure combinations.
    Addresses Advisor's concern about vector space visualization.

    Args:
        centralities_df: Pipeline output with columns [label, betweenness, eigenvector, out_degree]
        save_dir: Directory to save figures (creates 3 PNG files)
        network_label: Label for this network (e.g., "51×51 Domestic" or "52×52 International")

    Returns:
        List of matplotlib Figure objects
    """
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np

    from cfs_toolkit.visualizations.styles import set_publication_style, get_color_palette

    set_publication_style()
    COLORS = get_color_palette()

    # Define measure pairs
    pairs = [
        ('betweenness', 'eigenvector', 'Betweenness', 'Eigenvector'),
        ('betweenness', 'out_degree', 'Betweenness', 'Out-Degree'),
        ('eigenvector', 'out_degree', 'Eigenvector', 'Out-Degree')
    ]

    figures = []

    for x_col, y_col, x_label, y_label in pairs:
        fig, ax = plt.subplots(figsize=(8, 8))

        # Scatter plot
        ax.scatter(
            centralities_df[x_col],
            centralities_df[y_col],
            alpha=0.6,
            s=80,
            color=COLORS['primary'],
            edgecolors=COLORS['secondary'],
            linewidths=1.5
        )

        # Annotate top 5 states by each measure
        top_x = centralities_df.nlargest(5, x_col)
        top_y = centralities_df.nlargest(5, y_col)
        annotated = set()

        for _, row in pd.concat([top_x, top_y]).iterrows():
            if row['label'] not in annotated:
                ax.annotate(
                    row['label'],
                    (row[x_col], row[y_col]),
                    xytext=(5, 5),
                    textcoords='offset points',
                    fontsize=9,
                    alpha=0.8
                )
                annotated.add(row['label'])

        # Formatting
        ax.set_xlabel(f'{x_label} Centrality', fontweight='bold', fontsize=12)
        ax.set_ylabel(f'{y_label} Centrality', fontweight='bold', fontsize=12)
        ax.set_title(f'{x_label} vs {y_label} ({network_label})',
                    fontweight='bold', fontsize=14)
        ax.grid(True, alpha=0.3)

        # Add diagonal reference line if both measures are on similar scales
        if x_col != 'out_degree' and y_col != 'out_degree':
            lims = [
                np.min([ax.get_xlim(), ax.get_ylim()]),
                np.max([ax.get_xlim(), ax.get_ylim()])
            ]
            ax.plot(lims, lims, 'k--', alpha=0.3, zorder=0, label='y=x reference')
            ax.legend(loc='lower right', fontsize=9)

        plt.tight_layout()

        if save_dir:
            filename = f'pairwise_{x_col}_vs_{y_col}.png'
            fig.savefig(save_dir / filename, dpi=300, bbox_inches='tight', facecolor='white')
            print(f"Saved {filename}")

        figures.append(fig)

    return figures


def create_boundary_sensitivity_summary(
    df_51: Any,
    df_52: Any,
    save_path: Optional[Path] = None
):
    """
    Create publication-quality summary of boundary sensitivity analysis.
    Shows percentage of states that changed rank for each centrality measure.

    Args:
        df_51: 51×51 network centralities DataFrame
        df_52: 52×52 network centralities DataFrame (filtered to 51 states)
        save_path: Path to save figure

    Returns:
        matplotlib Figure object
    """
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np

    from cfs_toolkit.visualizations.styles import set_publication_style, get_color_palette

    set_publication_style()
    COLORS = get_color_palette()

    # Merge dataframes on label
    merged = df_51.merge(df_52, on='label', suffixes=('_51', '_52'))

    # Calculate rank changes for each measure
    measures = ['betweenness', 'eigenvector', 'out_degree']
    measure_labels = ['Betweenness\n(Macro)', 'Eigenvector\n(Meso)', 'Out-Degree\n(Micro)']
    pct_changed = []

    for measure in measures:
        rank_col_51 = f'rank_{measure}_51'
        rank_col_52 = f'rank_{measure}_52'

        if rank_col_51 in merged.columns and rank_col_52 in merged.columns:
            changed = (merged[rank_col_51] != merged[rank_col_52]).sum()
            pct = (changed / len(merged)) * 100
        else:
            # Fallback: compute ranks from scores
            merged[f'temp_rank_51'] = merged[f'{measure}_51'].rank(ascending=False, method='min')
            merged[f'temp_rank_52'] = merged[f'{measure}_52'].rank(ascending=False, method='min')
            changed = (merged['temp_rank_51'] != merged['temp_rank_52']).sum()
            pct = (changed / len(merged)) * 100

        pct_changed.append(pct)

    # Create bar chart
    fig, ax = plt.subplots(figsize=(10, 6))

    colors = [COLORS['tertiary'], COLORS['secondary'], COLORS['highlight']]
    bars = ax.bar(measure_labels, pct_changed, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)

    # Add value labels on bars
    for bar, pct in zip(bars, pct_changed):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width()/2.,
            height + 1,
            f'{pct:.0f}%',
            ha='center',
            va='bottom',
            fontsize=17,
            fontweight='bold'
        )

    # Formatting
    ax.set_ylabel('States Changed Rank (%)', fontweight='bold', fontsize=17)
    ax.set_title('Boundary Sensitivity Varies by Centrality Measure',
                fontweight='bold', fontsize=19, pad=20)
    ax.set_ylim(0, max(pct_changed) * 1.15)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

    # Add interpretation note
    ax.text(
        0.5, -0.15,
        'Lower percentages indicate more stable rankings when international flows are included',
        ha='center',
        transform=ax.transAxes,
        fontsize=14,
        style='italic',
        color='gray'
    )

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"Boundary sensitivity summary saved to {save_path}")

    return fig


# Add more base visualization functions here as needed...