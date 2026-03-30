"""
Centrality calculations with optional edge-weight filtration.
"""

import networkx as nx
import pandas as pd
import logging

log = logging.getLogger(__name__)


def compute_all_centralities(G, invert_betweenness_weights=True):
    """
    Compute three-level centrality measures (minimal implementation).

    Args:
        G (nx.DiGraph): Network graph with 'weight' edge attribute (trade values)
        invert_betweenness_weights (bool): If True, invert weights for betweenness
            so that high trade value = short distance (preferred path).
            Default True because NetworkX treats weight as distance.

    Returns:
        pd.DataFrame: Columns [state_id, label, betweenness, eigenvector, out_degree]

    Note on betweenness weight handling:
        NetworkX betweenness_centrality treats edge weight as DISTANCE (higher = further).
        For trade networks, we want high trade value = PROXIMITY (preferred path).
        Setting invert_betweenness_weights=True applies: distance = max_weight / weight
    """

    log.info("Computing centralities...")

    # Betweenness centrality (normalized [0,1])
    # IMPORTANT: Invert weights so high trade value = short distance
    if invert_betweenness_weights:
        log.info("  Inverting weights for betweenness (high trade = short distance)")
        G_betw = G.copy()
        max_weight = max(d['weight'] for _, _, d in G.edges(data=True))
        for u, v, d in G_betw.edges(data=True):
            d['distance'] = max_weight / d['weight']
        betweenness = nx.betweenness_centrality(G_betw, normalized=True, weight='distance')
    else:
        log.warning("  Using raw weights for betweenness (may produce inverted results)")
        betweenness = nx.betweenness_centrality(G, normalized=True, weight='weight')
    
    # Eigenvector centrality with PageRank fallback
    try:
        eigenvector = nx.eigenvector_centrality_numpy(G, weight='weight')
    except:
        log.warning("Eigenvector centrality failed, using PageRank")
        eigenvector = nx.pagerank(G, weight='weight')
    
    # Weighted out-degree (normalized [0,1])
    out_degree_raw = dict(G.out_degree(weight='weight'))
    max_degree = max(out_degree_raw.values()) if out_degree_raw else 1
    out_degree = {node: val/max_degree for node, val in out_degree_raw.items()}
    
    # Combine into DataFrame
    nodes = list(G.nodes())
    df = pd.DataFrame({
        'state_id': nodes,
        'label': [G.nodes[node].get('label', str(node)) for node in nodes],
        'betweenness': [betweenness.get(node, 0) for node in nodes],
        'eigenvector': [eigenvector.get(node, 0) for node in nodes], 
        'out_degree': [out_degree.get(node, 0) for node in nodes]
    })
    
    log.info(f"Centralities computed for {len(df)} nodes")
    return df


def filter_graph_by_threshold(G, threshold, weight_attr='weight'):
    """
    Create filtered graph by removing edges below threshold.

    Args:
        G (nx.DiGraph): Original graph
        threshold (float): Minimum edge weight to keep
        weight_attr (str): Edge attribute name for weights

    Returns:
        nx.DiGraph: Filtered graph with only edges >= threshold

    Notes:
        - Preserves all nodes (even if isolated after filtering)
        - Preserves node attributes
        - Creates deep copy to avoid modifying original
    """
    log.info(f"Filtering graph with threshold: ${threshold:,.0f}")

    # Create deep copy to avoid modifying original
    G_filtered = G.copy()

    # Remove edges below threshold
    edges_to_remove = [
        (u, v) for u, v, data in G_filtered.edges(data=True)
        if data.get(weight_attr, 0) < threshold
    ]

    G_filtered.remove_edges_from(edges_to_remove)

    # Log filtration results
    original_edges = len(G.edges())
    filtered_edges = len(G_filtered.edges())
    removed_edges = original_edges - filtered_edges
    removal_pct = (removed_edges / original_edges) * 100 if original_edges > 0 else 0

    log.info(f"  Original edges: {original_edges:,}")
    log.info(f"  Filtered edges: {filtered_edges:,}")
    log.info(f"  Removed edges: {removed_edges:,} ({removal_pct:.1f}%)")
    log.info(f"  New density: {nx.density(G_filtered):.6f}")

    # Check for isolated nodes
    isolated_nodes = list(nx.isolates(G_filtered))
    if isolated_nodes:
        log.warning(f"  Filtration created {len(isolated_nodes)} isolated nodes")

    return G_filtered


def compute_all_centralities_with_filtration(G, threshold=None, weight_attr='weight'):
    """
    Compute centralities with optional graph filtration.

    Args:
        G (nx.DiGraph): Original graph
        threshold (float, optional): Edge weight threshold for filtration.
                                      If None, uses full graph.
        weight_attr (str): Edge attribute name for weights

    Returns:
        pd.DataFrame: Centrality results with additional metadata

    Notes:
        - If threshold is None, delegates to compute_all_centralities()
        - Adds 'threshold' column to output for tracking
        - Handles isolated nodes by assigning zero centrality
    """
    if threshold is None:
        log.info("Computing centralities on full graph (no filtration)")
        df = compute_all_centralities(G)
        df['threshold'] = None
        return df

    # Apply filtration
    G_filtered = filter_graph_by_threshold(G, threshold, weight_attr)

    # Compute centralities on filtered graph
    log.info(f"Computing centralities on filtered graph...")
    df = compute_all_centralities(G_filtered)
    df['threshold'] = threshold

    # Handle isolated nodes (assign zero centrality if not already handled)
    isolated_nodes = list(nx.isolates(G_filtered))
    if isolated_nodes:
        log.info(f"  Assigning zero centrality to {len(isolated_nodes)} isolated nodes")
        for node in isolated_nodes:
            mask = df['state_id'] == node
            if mask.any():
                df.loc[mask, ['betweenness', 'eigenvector', 'out_degree']] = 0.0

    return df


def compute_centralities_at_multiple_thresholds(G, thresholds, weight_attr='weight'):
    """
    Compute centralities across multiple filtration thresholds.

    Args:
        G (nx.DiGraph): Original graph
        thresholds (list): List of threshold values to test
        weight_attr (str): Edge attribute name for weights

    Returns:
        pd.DataFrame: Combined results with threshold column for each run

    Example:
        thresholds = [170_000_000, 773_000_000, 2_811_000_000]  # 25th, 50th, 75th percentile
        results_df = compute_centralities_at_multiple_thresholds(G, thresholds)
    """
    log.info(f"Computing centralities at {len(thresholds)} threshold levels")

    all_results = []

    # Add full graph (no filtration) as baseline
    log.info("\n=== Baseline: Full Graph (No Filtration) ===")
    baseline_df = compute_all_centralities_with_filtration(G, threshold=None, weight_attr=weight_attr)
    baseline_df['threshold_label'] = 'full_network'
    all_results.append(baseline_df)

    # Compute for each threshold
    for i, threshold in enumerate(thresholds, 1):
        log.info(f"\n=== Threshold {i}/{len(thresholds)}: ${threshold:,.0f} ===")
        threshold_df = compute_all_centralities_with_filtration(G, threshold=threshold, weight_attr=weight_attr)
        threshold_df['threshold_label'] = f'threshold_{i}'
        all_results.append(threshold_df)

    # Combine all results
    combined_df = pd.concat(all_results, ignore_index=True)

    log.info(f"\n=== Filtration Analysis Complete ===")
    log.info(f"Total runs: {len(thresholds) + 1} (1 baseline + {len(thresholds)} thresholds)")
    log.info(f"Total records: {len(combined_df)}")

    return combined_df