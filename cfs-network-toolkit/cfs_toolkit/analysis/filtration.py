"""
Graph filtration analysis for centrality robustness testing.
"""

import logging
import numpy as np
import networkx as nx
import pandas as pd

log = logging.getLogger(__name__)


def calculate_rank_changes(full_df, threshold_df, centrality_measure):
    """
    Calculate rank changes between full network and filtered network.

    Args:
        full_df (pd.DataFrame): Centralities from full network
        threshold_df (pd.DataFrame): Centralities from filtered network
        centrality_measure (str): Which centrality to compare ('betweenness', 'eigenvector', 'out_degree')

    Returns:
        pd.DataFrame: Columns [state_id, label, full_rank, threshold_rank, rank_change, sensitivity]
    """
    # Rank states in both networks
    full_df = full_df.copy()
    threshold_df = threshold_df.copy()

    full_df['rank'] = full_df[centrality_measure].rank(ascending=False, method='min')
    threshold_df['rank'] = threshold_df[centrality_measure].rank(ascending=False, method='min')

    # Merge on state_id
    comparison = full_df[['state_id', 'label', 'rank']].merge(
        threshold_df[['state_id', 'rank']],
        on='state_id',
        suffixes=('_full', '_threshold')
    )

    # Calculate change
    comparison['rank_change'] = comparison['rank_threshold'] - comparison['rank_full']
    comparison['sensitivity'] = comparison['rank_change'].abs()

    return comparison.sort_values('sensitivity', ascending=False)


def count_components_at_filtration(G, percentile, weight_attr='weight'):
    """
    Count strongly connected components at a given filtration percentile.

    Args:
        G (nx.DiGraph): Original graph
        percentile (float): Percentile threshold (0-100). Edges below this
                           percentile of weights are removed.
        weight_attr (str): Edge attribute name for weights

    Returns:
        dict: {
            'percentile': filtration level,
            'threshold': dollar threshold,
            'edges_remaining': count of edges after filtration,
            'edges_removed': count of edges removed,
            'removal_pct': percentage of edges removed,
            'n_strongly_connected': number of SCCs,
            'n_weakly_connected': number of WCCs,
            'is_connected': True if single SCC
        }

    Example:
        >>> result = count_components_at_filtration(G, 30)
        >>> print(f"At 30%: {result['n_strongly_connected']} components")
    """
    weights = [d[weight_attr] for u, v, d in G.edges(data=True)]
    threshold = np.percentile(weights, percentile)

    # Filter graph
    G_filtered = G.copy()
    edges_to_remove = [
        (u, v) for u, v, d in G_filtered.edges(data=True)
        if d.get(weight_attr, 0) < threshold
    ]
    G_filtered.remove_edges_from(edges_to_remove)

    n_scc = nx.number_strongly_connected_components(G_filtered)
    n_wcc = nx.number_weakly_connected_components(G_filtered)

    return {
        'percentile': percentile,
        'threshold': threshold,
        'edges_remaining': G_filtered.number_of_edges(),
        'edges_removed': len(edges_to_remove),
        'removal_pct': len(edges_to_remove) / G.number_of_edges() * 100,
        'n_strongly_connected': n_scc,
        'n_weakly_connected': n_wcc,
        'is_connected': n_scc == 1
    }


def find_connectivity_breaking_point(G, weight_attr='weight', start=1, end=99, verbose=True):
    """
    Systematic percentile sweep to find the exact filtration percentile
    where network loses strong connectivity.

    Args:
        G (nx.DiGraph): Original graph
        weight_attr (str): Edge attribute name for weights
        start (int): Starting percentile for search (default 1)
        end (int): Ending percentile for search (default 99)
        verbose (bool): Print progress during search

    Returns:
        dict: {
            'max_connected_pct': highest percentile with 1 component,
            'breaking_pct': first percentile with >1 component,
            'max_connected_threshold': dollar threshold at max connected,
            'breaking_threshold': dollar threshold where it breaks,
            'scan_results': list of results for each percentile tested
        }

    Example:
        >>> result = find_connectivity_breaking_point(G)
        >>> print(f"Network breaks at {result['breaking_pct']}%")
        >>> print(f"Safe to filter up to {result['max_connected_pct']}%")
    """
    if verbose:
        log.info("Searching for connectivity breaking point...")
        print(f"{'%':>4} | {'Threshold':>12} | {'Edges':>6} | {'SCCs':>4} | Status")
        print("-" * 50)

    scan_results = []
    max_connected_pct = None
    breaking_pct = None

    for pct in range(start, end + 1):
        result = count_components_at_filtration(G, pct, weight_attr)
        scan_results.append(result)

        status = "✓ connected" if result['is_connected'] else f"✗ {result['n_strongly_connected']} components"

        if verbose:
            print(f"{pct:>3}% | ${result['threshold']/1e6:>9.1f}M | {result['edges_remaining']:>6} | {result['n_strongly_connected']:>4} | {status}")

        if result['is_connected']:
            max_connected_pct = pct
        elif breaking_pct is None:
            breaking_pct = pct
            if verbose:
                print(f"\n>>> Network breaks at {pct}% filtration <<<\n")

    # Get thresholds
    weights = [d[weight_attr] for u, v, d in G.edges(data=True)]
    max_threshold = np.percentile(weights, max_connected_pct) if max_connected_pct else None
    breaking_threshold = np.percentile(weights, breaking_pct) if breaking_pct else None

    return {
        'max_connected_pct': max_connected_pct,
        'breaking_pct': breaking_pct,
        'max_connected_threshold': max_threshold,
        'breaking_threshold': breaking_threshold,
        'scan_results': scan_results
    }


def filter_graph_by_percentile(G, percentile, weight_attr='weight'):
    """
    Filter graph by removing edges below a percentile threshold.

    Convenience function combining percentile calculation with graph filtering.

    Args:
        G (nx.DiGraph): Original graph
        percentile (float): Percentile threshold (0-100). Edges below this
                           percentile of weights are removed.
        weight_attr (str): Edge attribute name for weights

    Returns:
        tuple: (G_filtered, threshold_value)
            - G_filtered: NetworkX graph with weak edges removed
            - threshold_value: Dollar threshold used for filtering

    Example:
        >>> G_filtered, threshold = filter_graph_by_percentile(G, 33)
        >>> print(f"Filtered at ${threshold/1e6:.1f}M")
        >>> centralities = compute_all_centralities(G_filtered)
    """
    weights = [d[weight_attr] for u, v, d in G.edges(data=True)]
    threshold = np.percentile(weights, percentile)

    G_filtered = G.copy()
    edges_to_remove = [
        (u, v) for u, v, d in G_filtered.edges(data=True)
        if d.get(weight_attr, 0) < threshold
    ]
    G_filtered.remove_edges_from(edges_to_remove)

    log.info(f"Filtered at {percentile}% (${threshold/1e6:.1f}M): "
             f"{len(edges_to_remove)} edges removed, {G_filtered.number_of_edges()} remaining")

    return G_filtered, threshold


def scan_filtration_range(G, start_pct=25, end_pct=40, weight_attr='weight'):
    """
    Scan a range of filtration percentiles and return component counts.

    Useful for quickly checking connectivity around a suspected breaking point.

    Args:
        G (nx.DiGraph): Original graph
        start_pct (int): Starting percentile (default 25)
        end_pct (int): Ending percentile (default 40)
        weight_attr (str): Edge attribute name for weights

    Returns:
        pd.DataFrame: Columns [percentile, threshold, edges, n_scc, is_connected]

    Example:
        >>> df = scan_filtration_range(G, 30, 40)
        >>> print(df[df['is_connected'] == False].iloc[0])  # First breaking point
    """
    results = []

    for pct in range(start_pct, end_pct + 1):
        result = count_components_at_filtration(G, pct, weight_attr)
        results.append({
            'percentile': pct,
            'threshold': result['threshold'],
            'edges': result['edges_remaining'],
            'n_scc': result['n_strongly_connected'],
            'is_connected': result['is_connected']
        })

    return pd.DataFrame(results)
