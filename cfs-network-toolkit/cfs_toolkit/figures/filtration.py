"""
Filtration analysis visualizations.
"""

import logging
import matplotlib.pyplot as plt
import numpy as np

log = logging.getLogger(__name__)


def generate_connectivity_threshold_figure(G, output_path, max_pct=50):
    """
    Generate figure showing why 34% filtration threshold was chosen.

    Shows number of strongly connected components at each filtration level,
    with clear marking of where connectivity breaks.

    Args:
        G (nx.DiGraph): Network graph
        output_path (Path): Output file path
        max_pct (int): Maximum percentile to scan (default 50)
    """
    import networkx as nx
    from cfs_toolkit.analysis.filtration import count_components_at_filtration

    # Scan connectivity across percentiles
    percentiles = list(range(0, max_pct + 1))
    n_components = []
    edges_remaining = []

    for pct in percentiles:
        result = count_components_at_filtration(G, pct)
        n_components.append(result['n_strongly_connected'])
        edges_remaining.append(result['edges_remaining'])

    # Find breaking point
    breaking_idx = next((i for i, n in enumerate(n_components) if n > 1), len(percentiles))
    max_safe_pct = percentiles[breaking_idx - 1] if breaking_idx > 0 else 0

    # Create figure with two y-axes
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Plot component count
    color_components = '#E63946'  # Red for fragmentation
    ax1.set_xlabel('Edge Weight Filtration Threshold (%)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Strongly Connected Components', fontsize=12, fontweight='bold', color=color_components)

    # Color bars by connectivity status
    colors = ['#2A9D8F' if n == 1 else color_components for n in n_components]
    bars = ax1.bar(percentiles, n_components, color=colors, alpha=0.7, edgecolor='black', linewidth=0.5)
    ax1.tick_params(axis='y', labelcolor=color_components)
    ax1.set_ylim(0, max(n_components) * 1.2)

    # Add vertical line at breaking point
    ax1.axvline(x=max_safe_pct + 0.5, color='#264653', linestyle='--', linewidth=2.5)

    # Add legend for colors
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#2A9D8F', edgecolor='black', alpha=0.7, label='Connected (1 SCC)'),
        Patch(facecolor=color_components, edgecolor='black', alpha=0.7, label='Fragmented (>1 SCC)'),
    ]
    ax1.legend(handles=legend_elements, loc='upper left', fontsize=10)

    # Title
    ax1.set_title(
        'Network Connectivity vs Edge Weight Filtration\n'
        f'Maximum safe threshold: {max_safe_pct}% (network stays strongly connected)',
        fontsize=14, fontweight='bold', pad=15
    )

    ax1.grid(axis='y', alpha=0.3, linestyle='--')
    ax1.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')

    # Also save PDF
    pdf_path = output_path.with_suffix('.pdf')
    plt.savefig(pdf_path, bbox_inches='tight', facecolor='white')

    log.info(f"Connectivity threshold figure saved to {output_path}")
    plt.close()

    return max_safe_pct


def generate_rank_stability_figure(results_df, centrality_measure, output_path):
    """
    Generate figure showing rank stability across thresholds.

    Args:
        results_df (pd.DataFrame): Combined results from compute_centralities_at_multiple_thresholds
        centrality_measure (str): Which centrality to visualize
        output_path (Path): Output file path
    """
    # Get unique threshold labels
    threshold_labels = results_df['threshold_label'].unique()

    # Focus on top 10 states in full network
    full_network_df = results_df[results_df['threshold_label'] == 'full_network'].copy()
    full_network_df['rank'] = full_network_df[centrality_measure].rank(ascending=False, method='min')
    top_10_states = full_network_df.nsmallest(10, 'rank')['state_id'].tolist()

    # Track ranks across thresholds for top 10
    rank_matrix = []
    for state_id in top_10_states:
        state_ranks = []
        state_label = full_network_df[full_network_df['state_id'] == state_id]['label'].iloc[0]

        for threshold_label in threshold_labels:
            threshold_df = results_df[results_df['threshold_label'] == threshold_label].copy()
            threshold_df['rank'] = threshold_df[centrality_measure].rank(ascending=False, method='min')
            state_rank = threshold_df[threshold_df['state_id'] == state_id]['rank'].iloc[0]
            state_ranks.append(state_rank)

        rank_matrix.append({'state': state_label, 'ranks': state_ranks})

    # Plot
    fig, ax = plt.subplots(figsize=(12, 8))

    for i, row in enumerate(rank_matrix):
        ax.plot(range(len(threshold_labels)), row['ranks'], marker='o', label=row['state'], linewidth=2)

    ax.set_xlabel('Filtration Level', fontsize=12)
    ax.set_ylabel(f'Rank ({centrality_measure.capitalize()})', fontsize=12)
    ax.set_title(f'Rank Stability Across Graph Filtration - {centrality_measure.capitalize()} Centrality',
                 fontsize=14, fontweight='bold')
    ax.set_xticks(range(len(threshold_labels)))
    ax.set_xticklabels([label.replace('_', ' ').title() for label in threshold_labels], rotation=45, ha='right')
    ax.invert_yaxis()  # Lower rank number = better
    ax.legend(loc='best', fontsize=9)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    log.info(f"Rank stability figure saved to {output_path}")
    plt.close()
