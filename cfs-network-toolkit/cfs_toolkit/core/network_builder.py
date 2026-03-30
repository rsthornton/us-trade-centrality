"""
Build NetworkX directed graphs from preprocessed edge lists.

Constructs weighted DiGraphs for both 51x51 domestic and 52x52
international network configurations.
"""

import networkx as nx
import pandas as pd
import numpy as np
import logging

log = logging.getLogger(__name__)

# State code to abbreviation mapping for node labels
STATE_CODES = {
    1: 'AL', 2: 'AK', 4: 'AZ', 5: 'AR', 6: 'CA', 8: 'CO', 9: 'CT', 10: 'DE', 
    11: 'DC', 12: 'FL', 13: 'GA', 15: 'HI', 16: 'ID', 17: 'IL', 18: 'IN', 
    19: 'IA', 20: 'KS', 21: 'KY', 22: 'LA', 23: 'ME', 24: 'MD', 25: 'MA', 
    26: 'MI', 27: 'MN', 28: 'MS', 29: 'MO', 30: 'MT', 31: 'NE', 32: 'NV', 
    33: 'NH', 34: 'NJ', 35: 'NM', 36: 'NY', 37: 'NC', 38: 'ND', 39: 'OH', 
    40: 'OK', 41: 'OR', 42: 'PA', 44: 'RI', 45: 'SC', 46: 'SD', 47: 'TN', 
    48: 'TX', 49: 'UT', 50: 'VT', 51: 'VA', 53: 'WA', 54: 'WV', 55: 'WI', 
    56: 'WY', 52: 'RoW'  # Rest of World for international flows
}


def build_trade_network(edges_df, node_labels=True, validate_edges=True):
    """
    Build NetworkX DiGraph from preprocessed edge list.
    
    Args:
        edges_df (pd.DataFrame): Edge list with columns ['ORIG_STATE', 'DEST_STATE', 'SHIPMT_VALUE']
        node_labels (bool): Add state abbreviation labels to nodes
        validate_edges (bool): Perform edge validation before construction
        
    Returns:
        nx.DiGraph: Directed trade network with weighted edges
        
    Graph Properties:
        - Directed: Trade flows have direction (origin → destination)
        - Weighted: Edge weights represent trade value in USD
        - Nodes: State codes (1-56) or state codes + 52 (Rest of World)
        - Node labels: State abbreviations (optional)
    """
    
    if validate_edges:
        _validate_edge_schema(edges_df)
    
    log.info(f"Building NetworkX graph from {len(edges_df):,} edges")
    
    # Create directed graph
    G = nx.DiGraph()
    
    # Add all unique nodes (ensures isolated nodes are included)
    all_nodes = set(edges_df['ORIG_STATE'].unique()) | set(edges_df['DEST_STATE'].unique())
    G.add_nodes_from(all_nodes)
    
    # Add edges with weights (faster than iterrows)
    G.add_weighted_edges_from(
        ((r.ORIG_STATE, r.DEST_STATE, r.SHIPMT_VALUE) 
         for r in edges_df.itertuples(index=False)),
        weight='weight'
    )
    
    # Add node labels if requested
    if node_labels:
        node_labels_dict = {}
        for node in G.nodes():
            if node in STATE_CODES:
                node_labels_dict[node] = STATE_CODES[node]
            else:
                node_labels_dict[node] = f"State_{node}"  # Fallback for unknown codes
        
        nx.set_node_attributes(G, node_labels_dict, 'label')
    
    # Add graph metadata
    total_trade_value = edges_df['SHIPMT_VALUE'].sum()
    has_international = (edges_df['ORIG_STATE'] == 52).any() or (edges_df['DEST_STATE'] == 52).any()
    network_size = f"{len(G.nodes())}×{len(G.nodes())}"
    
    G.graph['total_trade_value'] = total_trade_value
    G.graph['network_type'] = 'international' if has_international else 'domestic'
    G.graph['network_size'] = network_size
    G.graph['edge_count'] = len(G.edges())
    G.graph['node_count'] = len(G.nodes())
    
    log.info(f"Graph construction complete:")
    log.info(f"   Nodes: {len(G.nodes())} ({network_size} network)")
    log.info(f"   Edges: {len(G.edges()):,}")
    log.info(f"   Type: {G.graph['network_type']}")
    log.info(f"   Total trade value: ${total_trade_value:,.0f}")
    log.info(f"   Density: {nx.density(G):.4f}")
    
    return G


def create_adjacency_matrix(edges_df, node_order=None, sparse=False):
    """
    Create adjacency matrix from edge list for matrix-based analysis.
    
    Args:
        edges_df (pd.DataFrame): Edge list with standard schema
        node_order (list, optional): Specific ordering for nodes
        sparse (bool): Return scipy sparse matrix instead of dense
        
    Returns:
        pd.DataFrame or scipy.sparse matrix: Adjacency matrix representation
    """
    
    G = build_trade_network(edges_df, node_labels=False, validate_edges=False)
    
    if node_order is None:
        node_order = sorted(G.nodes())
    
    if sparse:
        try:
            import scipy.sparse
            adj_matrix = nx.adjacency_matrix(G, nodelist=node_order, weight='weight')
            return adj_matrix
        except ImportError:
            raise ImportError("scipy is required for sparse matrix output. Install with: pip install scipy")
    else:
        adj_matrix = nx.adjacency_matrix(G, nodelist=node_order, weight='weight').todense()
        adj_df = pd.DataFrame(
            adj_matrix, 
            index=[STATE_CODES.get(node, f"State_{node}") for node in node_order],
            columns=[STATE_CODES.get(node, f"State_{node}") for node in node_order]
        )
        return adj_df


def add_node_attributes(G, attribute_data, attribute_name):
    """
    Add additional node attributes to graph (GDP, population, etc.).
    
    Args:
        G (nx.DiGraph): Graph to enhance
        attribute_data (dict): {node_id: attribute_value} mapping
        attribute_name (str): Name of the attribute
        
    Returns:
        nx.DiGraph: Graph with enhanced node attributes
    """
    
    # Validate that all graph nodes have attribute data
    missing_nodes = set(G.nodes()) - set(attribute_data.keys())
    if missing_nodes:
        log.warning(f"Missing {attribute_name} data for nodes: {missing_nodes}")
    
    nx.set_node_attributes(G, attribute_data, attribute_name)
    
    log.info(f"Added {attribute_name} attributes to {len(attribute_data)} nodes")
    
    return G


# Note: validate_network_structure has been moved to validators.py
# Import it when needed:
# from validators import validate_network_structure


def _validate_edge_schema(edges_df):
    """
    Internal validation for edge list schema.
    
    Args:
        edges_df (pd.DataFrame): Edge list to validate
        
    Raises:
        ValueError: If schema is invalid
    """
    
    required_cols = ['ORIG_STATE', 'DEST_STATE', 'SHIPMT_VALUE']
    missing_cols = set(required_cols) - set(edges_df.columns)
    if missing_cols:
        raise ValueError(f"Edge list missing required columns: {missing_cols}")
    
    if len(edges_df) == 0:
        raise ValueError("Edge list is empty")
    
    # Check for invalid node codes
    all_nodes = set(edges_df['ORIG_STATE'].unique()) | set(edges_df['DEST_STATE'].unique())
    valid_range = set(range(1, 57)) | {52}  # States 1-56 + Rest of World
    invalid_nodes = all_nodes - valid_range
    if invalid_nodes:
        raise ValueError(f"Edge list contains invalid node codes: {invalid_nodes}")
    
    # Check for negative weights
    negative_weights = (edges_df['SHIPMT_VALUE'] < 0).sum()
    if negative_weights > 0:
        raise ValueError(f"Edge list contains {negative_weights} negative weights")


def get_network_summary(G):
    """
    Generate human-readable network summary for logging/reporting.
    
    Args:
        G (nx.DiGraph): Graph to summarize
        
    Returns:
        str: Formatted summary string
    """
    
    summary_lines = [
        f"=== Network Summary ===",
        f"Type: {G.graph.get('network_type', 'unknown')}",
        f"Size: {G.graph.get('network_size', 'unknown')}",
        f"Nodes: {len(G.nodes())}",
        f"Edges: {len(G.edges()):,}",
        f"Density: {nx.density(G):.4f}",
        f"Trade Value: ${G.graph.get('total_trade_value', 0):,.0f}",
    ]
    
    # Add connectivity info for directed graphs
    if G.is_directed() and len(G.nodes()) > 0:
        summary_lines.extend([
            f"Weakly Connected Components: {nx.number_weakly_connected_components(G)}",
            f"Strongly Connected Components: {nx.number_strongly_connected_components(G)}"
        ])
    
    return "\n".join(summary_lines)