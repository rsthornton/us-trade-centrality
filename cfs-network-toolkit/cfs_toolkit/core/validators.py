"""
Validate network structure after graph construction.

Checks connectivity, component distribution, edge weights, and
node labeling. Returns a validation report dictionary.
"""

import numpy as np
import networkx as nx
import logging

log = logging.getLogger(__name__)


def validate_network_structure(G):
    """
    Comprehensive network validation for research quality assurance.

    Args:
        G (nx.DiGraph): Graph to validate

    Returns:
        dict: Validation report with detailed diagnostics
    """

    validation = {
        'is_valid': True,
        'issues': [],
        'warnings': [],
        'diagnostics': {}
    }

    # Basic structure checks
    validation['diagnostics']['node_count'] = len(G.nodes())
    validation['diagnostics']['edge_count'] = len(G.edges())
    validation['diagnostics']['density'] = nx.density(G)
    validation['diagnostics']['is_directed'] = G.is_directed()

    # Check for empty graph
    if len(G.nodes()) == 0:
        validation['is_valid'] = False
        validation['issues'].append("Graph is empty (no nodes)")
        return validation

    # Check for isolated nodes
    isolated = list(nx.isolates(G))
    if isolated:
        validation['warnings'].append(f"Found {len(isolated)} isolated nodes: {isolated}")
        validation['diagnostics']['isolated_nodes'] = isolated

    # Connectivity analysis
    if G.is_directed():
        # For directed graphs, check weak/strong connectivity
        validation['diagnostics']['weakly_connected_components'] = nx.number_weakly_connected_components(G)
        validation['diagnostics']['strongly_connected_components'] = nx.number_strongly_connected_components(G)

        if not nx.is_weakly_connected(G):
            validation['warnings'].append("Graph is not weakly connected")

        if nx.number_strongly_connected_components(G) > 1:
            validation['warnings'].append("Graph has multiple strongly connected components")

    # Weight validation
    edge_weights = [data['weight'] for _, _, data in G.edges(data=True) if 'weight' in data]
    if edge_weights:
        validation['diagnostics']['edge_weights'] = {
            'count': len(edge_weights),
            'min': min(edge_weights),
            'max': max(edge_weights),
            'mean': np.mean(edge_weights),
            'zero_weights': sum(1 for w in edge_weights if w == 0),
            'negative_weights': sum(1 for w in edge_weights if w < 0)
        }

        if validation['diagnostics']['edge_weights']['negative_weights'] > 0:
            validation['is_valid'] = False
            validation['issues'].append("Graph contains negative edge weights")

    # Node label validation
    unlabeled_nodes = [node for node in G.nodes() if 'label' not in G.nodes[node]]
    if unlabeled_nodes:
        validation['warnings'].append(f"Found {len(unlabeled_nodes)} unlabeled nodes")

    log.info("Network structure validation complete")
    if validation['issues']:
        log.error(f"Validation issues found: {validation['issues']}")
    if validation['warnings']:
        log.warning(f"Validation warnings: {validation['warnings']}")

    return validation