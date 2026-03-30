"""
Enhanced Trade Matrix Visualizations
===================================
Generate multiple trade matrix views for comprehensive analysis:
- 50×50 complete matrix (all states)
- 25×25 regional splits (geographic analysis)
- Existing 20×20 top states (executive summary)

Focus: Clear regional patterns and complete network coverage.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')


def set_matrix_style():
    """Set clean style for trade matrix visualizations."""
    plt.style.use('default')
    plt.rcParams.update({
        'font.size': 10,
        'font.family': 'Arial',
        'axes.labelsize': 12,
        'axes.titlesize': 14,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 10,
        'figure.titlesize': 16,
        'figure.facecolor': 'white',
        'axes.facecolor': 'white'
    })


def get_regional_grouping() -> Dict[str, List[str]]:
    """
    Define regional groupings for 25×25 matrix splits.

    Returns two balanced regional groups plus DC special handling.
    """

    # US regions for balanced geographic analysis
    regions = {
        'eastern': [
            'ME', 'NH', 'VT', 'MA', 'RI', 'CT', 'NY', 'NJ', 'PA',
            'DE', 'MD', 'VA', 'WV', 'NC', 'SC', 'GA', 'FL',
            'KY', 'TN', 'AL', 'MS', 'OH', 'IN', 'MI', 'WI'
        ],
        'western': [
            'MN', 'IA', 'MO', 'ND', 'SD', 'NE', 'KS', 'OK', 'TX',
            'AR', 'LA', 'MT', 'WY', 'CO', 'NM', 'ID', 'UT', 'AZ',
            'NV', 'WA', 'OR', 'CA', 'AK', 'HI', 'IL'  # IL goes west to balance
        ]
    }

    return regions


def create_complete_trade_matrix(
    G: nx.DiGraph,
    save_path: Optional[Path] = None,
    log_scale: bool = False
) -> plt.Figure:
    """
    Create 50×50 (or 51×51) complete trade matrix showing all states.

    Args:
        G: NetworkX graph with trade flows
        save_path: Optional path to save figure
        log_scale: Whether to use log scale for values

    Returns:
        matplotlib Figure object
    """
    set_matrix_style()

    # Extract adjacency matrix
    node_labels = {}
    for node in G.nodes():
        if 'label' in G.nodes[node]:
            node_labels[node] = G.nodes[node]['label']
        else:
            node_labels[node] = str(node)

    adj_matrix = nx.to_pandas_adjacency(G, weight='weight')

    # Replace node IDs with labels
    adj_matrix.index = adj_matrix.index.map(lambda x: node_labels.get(x, str(x)))
    adj_matrix.columns = adj_matrix.columns.map(lambda x: node_labels.get(x, str(x)))

    # Sort states alphabetically for consistent layout
    sorted_states = sorted(adj_matrix.index.tolist())
    adj_matrix = adj_matrix.loc[sorted_states, sorted_states]

    # Convert to billions for readability
    display_matrix = adj_matrix / 1e9

    # Apply log scale if requested
    if log_scale:
        display_matrix = np.log10(display_matrix + 1)
        title_suffix = " (Log Scale)"
        cbar_label = "Trade Flow (Log₁₀ Billions USD)"
    else:
        title_suffix = ""
        cbar_label = "Trade Flow (Billions USD)"

    # Create figure - larger for complete matrix
    n_states = len(display_matrix)
    fig_size = min(16, max(12, n_states * 0.3))  # Scale with number of states
    fig, ax = plt.subplots(figsize=(fig_size, fig_size))

    # Create heatmap without annotations (too crowded for 50×50)
    sns.heatmap(
        display_matrix,
        annot=False,  # No text annotations for readability
        cmap='YlOrRd',
        square=True,
        linewidths=0.1,
        cbar_kws={'label': cbar_label, 'shrink': 0.8},
        ax=ax
    )

    # Customize
    ax.set_title(f'Complete Interstate Trade Matrix ({n_states}×{n_states}){title_suffix}',
                fontweight='bold', pad=20)
    ax.set_xlabel('Destination State', fontweight='bold')
    ax.set_ylabel('Origin State', fontweight='bold')

    # Rotate labels for readability
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.savefig(save_path.with_suffix('.pdf'), bbox_inches='tight')

    return fig


def create_regional_trade_matrices(
    G: nx.DiGraph,
    output_dir: Path,
    log_scale: bool = False
) -> List[plt.Figure]:
    """
    Create 25×25 regional trade matrices (Eastern vs Western US).

    Args:
        G: NetworkX graph with trade flows
        output_dir: Directory to save figures
        log_scale: Whether to use log scale for values

    Returns:
        List of matplotlib Figure objects
    """
    set_matrix_style()

    # Get regional groupings
    regions = get_regional_grouping()

    # Extract adjacency matrix
    node_labels = {}
    for node in G.nodes():
        if 'label' in G.nodes[node]:
            node_labels[node] = G.nodes[node]['label']
        else:
            node_labels[node] = str(node)

    adj_matrix = nx.to_pandas_adjacency(G, weight='weight')
    adj_matrix.index = adj_matrix.index.map(lambda x: node_labels.get(x, str(x)))
    adj_matrix.columns = adj_matrix.columns.map(lambda x: node_labels.get(x, str(x)))

    figures = []

    for region_name, state_list in regions.items():
        # Filter states that actually exist in our data
        available_states = [s for s in state_list if s in adj_matrix.index]

        # Add DC to eastern region if it exists
        if region_name == 'eastern' and 'DC' in adj_matrix.index:
            available_states.append('DC')

        if len(available_states) < 10:  # Skip if too few states
            continue

        # Create regional matrix
        regional_matrix = adj_matrix.loc[available_states, available_states]

        # Sort alphabetically within region
        sorted_states = sorted(available_states)
        regional_matrix = regional_matrix.loc[sorted_states, sorted_states]

        # Convert to billions
        display_matrix = regional_matrix / 1e9

        # Apply log scale if requested
        if log_scale:
            display_matrix = np.log10(display_matrix + 1)
            title_suffix = " (Log Scale)"
            cbar_label = "Trade Flow (Log₁₀ Billions USD)"
            fmt = '.2f'
        else:
            title_suffix = ""
            cbar_label = "Trade Flow (Billions USD)"
            fmt = '.1f'

        # Create figure
        n_states = len(display_matrix)
        fig_size = min(14, max(10, n_states * 0.4))
        fig, ax = plt.subplots(figsize=(fig_size, fig_size))

        # Create heatmap with annotations for regional matrices
        sns.heatmap(
            display_matrix,
            annot=True,
            fmt=fmt,
            cmap='YlOrRd',
            square=True,
            linewidths=0.5,
            cbar_kws={'label': cbar_label, 'shrink': 0.8},
            ax=ax
        )

        # Customize
        region_title = region_name.replace('_', ' ').title()
        ax.set_title(f'{region_title} US Regional Trade Matrix ({n_states}×{n_states}){title_suffix}',
                    fontweight='bold', pad=20)
        ax.set_xlabel('Destination State', fontweight='bold')
        ax.set_ylabel('Origin State', fontweight='bold')

        # Rotate labels
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)

        plt.tight_layout()

        # Save figure
        save_path = output_dir / f'trade_matrix_{region_name}_regional.png'
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.savefig(save_path.with_suffix('.pdf'), bbox_inches='tight')

        figures.append(fig)

    return figures


def create_enhanced_trade_matrix_suite(
    G: nx.DiGraph,
    output_dir: Path,
    formats: List[str] = ['png', 'pdf']
) -> Dict[str, str]:
    """
    Generate complete enhanced trade matrix suite.

    Args:
        G: NetworkX graph with trade flows
        output_dir: Directory to save all figures
        formats: List of formats to save (png, pdf)

    Returns:
        Dictionary of generated file paths
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    generated_files = {}

    print("   Generating enhanced trade matrix suite...")

    # 1. Complete matrix (50×50 or 51×51)
    print("      Creating complete trade matrix...")
    try:
        complete_fig = create_complete_trade_matrix(
            G,
            save_path=output_dir / 'trade_matrix_complete.png'
        )
        generated_files['complete_matrix'] = 'trade_matrix_complete.png'
        plt.close(complete_fig)
    except Exception as e:
        print(f"      ⚠️ Warning: Could not create complete matrix: {e}")

    # 2. Regional matrices (25×25 each)
    print("      Creating regional trade matrices...")
    try:
        regional_figs = create_regional_trade_matrices(G, output_dir)
        generated_files['regional_matrices'] = [
            'trade_matrix_eastern_regional.png',
            'trade_matrix_western_regional.png'
        ]
        for fig in regional_figs:
            plt.close(fig)
    except Exception as e:
        print(f"      ⚠️ Warning: Could not create regional matrices: {e}")

    # 3. Log scale versions for high dynamic range data
    print("      Creating log-scale variants...")
    try:
        # Complete log scale
        complete_log_fig = create_complete_trade_matrix(
            G,
            save_path=output_dir / 'trade_matrix_complete_log.png',
            log_scale=True
        )
        generated_files['complete_matrix_log'] = 'trade_matrix_complete_log.png'
        plt.close(complete_log_fig)

        # Regional log scale
        regional_log_figs = create_regional_trade_matrices(G, output_dir, log_scale=True)
        # Files already saved with _log suffix in the function
        for fig in regional_log_figs:
            plt.close(fig)

    except Exception as e:
        print(f"      ⚠️ Warning: Could not create log-scale matrices: {e}")

    # Count total files generated
    total_files = sum(1 if isinstance(v, str) else len(v) for v in generated_files.values())
    print(f"   ✓ Generated {total_files} enhanced trade matrix files")

    return generated_files


"""
Interactive HTML Comparison of Full 51×51 vs 52×52 Matrices
============================================================
Creative visualizations for comparing large adjacency matrices.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from pathlib import Path
from typing import Dict, Optional
import networkx as nx


def create_interactive_matrix_comparison(
    matrix_51: pd.DataFrame,
    matrix_52: pd.DataFrame,
    state_labels: Dict[int, str],
    save_path: Optional[Path] = None
) -> go.Figure:
    """
    Create interactive comparison of 51×51 vs 52×52 matrices using multiple strategies.
    
    Strategies:
    1. Heatmap with zoom/pan for full detail
    2. Difference heatmap showing what changed
    3. Top flows comparison
    4. Aggregated regional view
    """
    
    # Create subplot figure with 2x2 layout
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            '51×51 Domestic Network (Interactive - Zoom to Explore)',
            '52×52 International Network (Node 52 = Rest of World)',
            'Change in Flow Intensity (52×52 - 51×51)',
            'Top 20 State Pairs: Flow Comparison'
        ),
        specs=[
            [{"type": "heatmap"}, {"type": "heatmap"}],
            [{"type": "heatmap"}, {"type": "bar"}]
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )
    
    # Prepare state labels for axes
    states_51 = [state_labels.get(i, str(i)) for i in matrix_51.index]
    states_52 = [state_labels.get(i, str(i)) if i != 52 else 'RoW' for i in matrix_52.index]
    
    # 1. 51×51 Heatmap (log scale for better visibility)
    matrix_51_log = np.log10(matrix_51.values + 1)  # Add 1 to avoid log(0)
    fig.add_trace(
        go.Heatmap(
            z=matrix_51_log,
            x=states_51,
            y=states_51,
            colorscale='Blues',
            text=matrix_51.values,
            texttemplate='%{text:.0f}M',
            textfont={"size": 6},
            hovertemplate='%{y} → %{x}<br>Flow: $%{text:.0f}M<extra></extra>',
            showscale=False,
            colorbar=dict(title='Log₁₀(Flow)', x=0.45, y=0.75)
        ),
        row=1, col=1
    )
    
    # 2. 52×52 Heatmap (log scale)
    matrix_52_log = np.log10(matrix_52.values + 1)
    fig.add_trace(
        go.Heatmap(
            z=matrix_52_log,
            x=states_52,
            y=states_52,
            colorscale='Viridis',
            text=matrix_52.values,
            texttemplate='%{text:.0f}M',
            textfont={"size": 6},
            hovertemplate='%{y} → %{x}<br>Flow: $%{text:.0f}M<extra></extra>',
            showscale=False,
            colorbar=dict(title='Log₁₀(Flow)', x=0.98, y=0.75)
        ),
        row=1, col=2
    )
    
    # 3. Difference Heatmap (what changed)
    # Align matrices for comparison (51×51 subset of 52×52)
    common_states = [s for s in matrix_51.index if s in matrix_52.index]
    diff_matrix = matrix_52.loc[common_states, common_states] - matrix_51.loc[common_states, common_states]
    diff_labels = [state_labels.get(i, str(i)) for i in common_states]
    
    fig.add_trace(
        go.Heatmap(
            z=diff_matrix.values,
            x=diff_labels,
            y=diff_labels,
            colorscale='RdBu',
            zmid=0,
            text=diff_matrix.values,
            texttemplate='%{text:+.0f}M',
            textfont={"size": 6},
            hovertemplate='%{y} → %{x}<br>Change: $%{text:+.0f}M<extra></extra>',
            showscale=True,
            colorbar=dict(title='Change ($M)', x=0.45, y=0.25)
        ),
        row=2, col=1
    )
    
    # 4. Top Flows Comparison
    # Extract top flows from each matrix
    def get_top_flows(matrix, n=20):
        flows = []
        for i in matrix.index:
            for j in matrix.columns:
                if i != j and matrix.loc[i, j] > 0:
                    flows.append({
                        'origin': state_labels.get(i, str(i)) if i != 52 else 'RoW',
                        'dest': state_labels.get(j, str(j)) if j != 52 else 'RoW',
                        'flow': matrix.loc[i, j],
                        'pair': f"{state_labels.get(i, str(i))}→{state_labels.get(j, str(j))}"
                    })
        return pd.DataFrame(flows).nlargest(n, 'flow')
    
    top_51 = get_top_flows(matrix_51, 20)
    top_52 = get_top_flows(matrix_52, 20)
    
    # Merge and compare
    comparison = pd.merge(
        top_51[['pair', 'flow']],
        top_52[['pair', 'flow']],
        on='pair',
        how='outer',
        suffixes=('_51', '_52')
    ).fillna(0)
    comparison = comparison.sort_values('flow_52', ascending=True)
    
    # Bar chart comparison
    fig.add_trace(
        go.Bar(
            x=comparison['flow_51'],
            y=comparison['pair'],
            orientation='h',
            name='51×51',
            marker=dict(color='#3498db'),
            hovertemplate='%{y}<br>51×51: $%{x:.0f}M<extra></extra>'
        ),
        row=2, col=2
    )
    
    fig.add_trace(
        go.Bar(
            x=comparison['flow_52'],
            y=comparison['pair'],
            orientation='h',
            name='52×52',
            marker=dict(color='#9b59b6', opacity=0.7),
            hovertemplate='%{y}<br>52×52: $%{x:.0f}M<extra></extra>'
        ),
        row=2, col=2
    )
    
    # Update layout
    fig.update_layout(
        title={
            'text': 'Interactive Matrix Comparison: 51×51 vs 52×52 Networks<br><sub>Zoom/Pan to explore details. Values in millions USD.</sub>',
            'x': 0.5,
            'font': {'size': 16}
        },
        height=1200,
        width=1400,
        showlegend=True,
        legend=dict(x=0.85, y=0.35),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    # Update axes
    fig.update_xaxes(tickangle=45, tickfont=dict(size=8), row=1, col=1)
    fig.update_xaxes(tickangle=45, tickfont=dict(size=8), row=1, col=2)
    fig.update_xaxes(tickangle=45, tickfont=dict(size=8), row=2, col=1)
    fig.update_xaxes(title='Flow Value ($M)', row=2, col=2)
    
    fig.update_yaxes(tickfont=dict(size=8), row=1, col=1)
    fig.update_yaxes(tickfont=dict(size=8), row=1, col=2)
    fig.update_yaxes(tickfont=dict(size=8), row=2, col=1)
    fig.update_yaxes(title='', tickfont=dict(size=9), row=2, col=2)
    
    if save_path:
        fig.write_html(save_path)
    
    return fig


def create_regional_aggregation_comparison(
    matrix_51: pd.DataFrame,
    matrix_52: pd.DataFrame,
    state_labels: Dict[int, str],
    save_path: Optional[Path] = None
) -> go.Figure:
    """
    Create regional aggregation view to simplify large matrices.
    
    Groups states by census regions for cleaner comparison.
    """
    
    # Define census regions
    regions = {
        'Northeast': ['CT', 'ME', 'MA', 'NH', 'NJ', 'NY', 'PA', 'RI', 'VT'],
        'Midwest': ['IL', 'IN', 'IA', 'KS', 'MI', 'MN', 'MO', 'NE', 'ND', 'OH', 'SD', 'WI'],
        'South': ['AL', 'AR', 'DE', 'DC', 'FL', 'GA', 'KY', 'LA', 'MD', 'MS', 'NC', 'OK', 'SC', 'TN', 'TX', 'VA', 'WV'],
        'West': ['AZ', 'CA', 'CO', 'HI', 'ID', 'MT', 'NV', 'NM', 'OR', 'UT', 'WA', 'WY', 'AK']
    }
    
    # Create state to region mapping
    state_to_region = {}
    for region, states in regions.items():
        for state in states:
            state_to_region[state] = region
    
    # Function to aggregate matrix by regions
    def aggregate_by_region(matrix, labels_dict):
        # Map indices to regions
        region_map = {}
        for idx in matrix.index:
            if idx == 52:
                region_map[idx] = 'International'
            else:
                state = labels_dict.get(idx, '')
                region_map[idx] = state_to_region.get(state, 'Unknown')
        
        # Create aggregated matrix
        unique_regions = list(set(region_map.values()))
        agg_matrix = pd.DataFrame(0, index=unique_regions, columns=unique_regions)
        
        for i in matrix.index:
            for j in matrix.columns:
                reg_i = region_map[i]
                reg_j = region_map[j]
                agg_matrix.loc[reg_i, reg_j] += matrix.loc[i, j]
        
        return agg_matrix
    
    # Aggregate both matrices
    agg_51 = aggregate_by_region(matrix_51, state_labels)
    agg_52 = aggregate_by_region(matrix_52, state_labels)
    
    # Create figure with subplots
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=(
            'Regional Flows: 51×51 Domestic',
            'Regional Flows: 52×52 International',
            'Change in Regional Flows'
        ),
        specs=[[{"type": "heatmap"}, {"type": "heatmap"}, {"type": "heatmap"}]],
        horizontal_spacing=0.12
    )
    
    # Plot regional heatmaps
    fig.add_trace(
        go.Heatmap(
            z=agg_51.values,
            x=list(agg_51.columns),
            y=list(agg_51.index),
            colorscale='Blues',
            text=agg_51.values / 1000,  # Convert to billions
            texttemplate='%{text:.1f}B',
            hovertemplate='%{y} → %{x}<br>Flow: $%{text:.1f}B<extra></extra>',
            showscale=True,
            colorbar=dict(title='Flow ($M)', x=0.3)
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Heatmap(
            z=agg_52.values,
            x=list(agg_52.columns),
            y=list(agg_52.index),
            colorscale='Viridis',
            text=agg_52.values / 1000,
            texttemplate='%{text:.1f}B',
            hovertemplate='%{y} → %{x}<br>Flow: $%{text:.1f}B<extra></extra>',
            showscale=True,
            colorbar=dict(title='Flow ($M)', x=0.65)
        ),
        row=1, col=2
    )
    
    # Calculate difference
    common_regions = [r for r in agg_51.index if r in agg_52.index]
    diff = agg_52.loc[common_regions, common_regions] - agg_51.loc[common_regions, common_regions]
    
    fig.add_trace(
        go.Heatmap(
            z=diff.values,
            x=list(diff.columns),
            y=list(diff.index),
            colorscale='RdBu',
            zmid=0,
            text=diff.values / 1000,
            texttemplate='%{text:+.1f}B',
            hovertemplate='%{y} → %{x}<br>Change: $%{text:+.1f}B<extra></extra>',
            showscale=True,
            colorbar=dict(title='Change ($M)', x=1.0)
        ),
        row=1, col=3
    )
    
    # Update layout
    fig.update_layout(
        title={
            'text': 'Regional Aggregation: Simplified Matrix Comparison<br><sub>States grouped by U.S. Census regions for clarity</sub>',
            'x': 0.5,
            'font': {'size': 16}
        },
        height=500,
        width=1400,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    if save_path:
        fig.write_html(save_path)
    
    return fig


def create_network_flow_sankey(
    matrix_51: pd.DataFrame,
    matrix_52: pd.DataFrame,
    state_labels: Dict[int, str],
    top_n: int = 30,
    save_path: Optional[Path] = None
) -> go.Figure:
    """
    Create Sankey diagram showing flow redistribution between networks.
    
    Shows how top flows change from 51×51 to 52×52.
    """
    
    # Get top flows from each network
    def extract_top_flows(matrix, n=30):
        flows = []
        for i in matrix.index:
            for j in matrix.columns:
                if i != j and matrix.loc[i, j] > 0:
                    flows.append({
                        'source': state_labels.get(i, str(i)) if i != 52 else 'RoW',
                        'target': state_labels.get(j, str(j)) if j != 52 else 'RoW',
                        'value': matrix.loc[i, j]
                    })
        return pd.DataFrame(flows).nlargest(n, 'value')
    
    flows_51 = extract_top_flows(matrix_51, top_n)
    flows_52 = extract_top_flows(matrix_52, top_n)
    
    # Create node list (unique states)
    nodes = list(set(
        list(flows_51['source']) + list(flows_51['target']) +
        list(flows_52['source']) + list(flows_52['target'])
    ))
    node_dict = {node: i for i, node in enumerate(nodes)}
    
    # Create Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=nodes,
            color=["#3498db" if node != 'RoW' else "#e74c3c" for node in nodes]
        ),
        link=dict(
            source=[node_dict[s] for s in flows_52['source']],
            target=[node_dict[t] for t in flows_52['target']],
            value=flows_52['value'].tolist(),
            color=["rgba(155, 89, 182, 0.4)" if 'RoW' in [s, t] else "rgba(52, 152, 219, 0.4)"
                   for s, t in zip(flows_52['source'], flows_52['target'])]
        )
    )])
    
    fig.update_layout(
        title={
            'text': f'Top {top_n} Trade Flows in 52×52 Network<br><sub>International flows (involving RoW) shown in purple</sub>',
            'x': 0.5,
            'font': {'size': 16}
        },
        height=800,
        width=1200
    )
    
    if save_path:
        fig.write_html(save_path)
    
    return fig