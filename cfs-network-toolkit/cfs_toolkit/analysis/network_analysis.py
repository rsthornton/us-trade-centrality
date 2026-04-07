"""
Network structure analysis: components, strong connectivity, and centrality bounds.

Provides component size distribution, SCC hierarchy analysis, and
centrality normalization checks for network validation.
"""

import networkx as nx
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import warnings

# TODO: temporal analysis when 2022 CFS is released


def analyze_component_sizes(G: nx.Graph) -> Dict[str, Any]:
    """
    Analyze connected component size distribution for network validation.

    Checks whether the network forms a single connected component (expected
    for a complete interstate trade network).

    Args:
        G: NetworkX graph (will be converted to undirected for component analysis)
        
    Returns:
        Dictionary containing:
        - component_count: Number of connected components
        - size_distribution: List of component sizes (sorted desc)
        - largest_component_size: Size of largest component
        - network_size: Total nodes in network
        - is_fully_connected: Boolean indicating single component
        - connectivity_ratio: Largest component size / total nodes
        - isolated_nodes: List of isolated nodes (if any)
    """
    
    # Convert to undirected for connectivity analysis
    if G.is_directed():
        G_undirected = G.to_undirected()
    else:
        G_undirected = G.copy()
    
    # Find all connected components
    components = list(nx.connected_components(G_undirected))
    component_sizes = sorted([len(c) for c in components], reverse=True)
    
    # Identify isolated nodes (components of size 1)
    isolated_nodes = [list(c)[0] for c in components if len(c) == 1]
    
    # Calculate connectivity metrics
    network_size = G.number_of_nodes()
    largest_size = max(component_sizes) if component_sizes else 0
    connectivity_ratio = largest_size / network_size if network_size > 0 else 0
    
    analysis = {
        'component_count': len(components),
        'size_distribution': component_sizes,
        'largest_component_size': largest_size,
        'network_size': network_size,
        'is_fully_connected': len(components) == 1,
        'connectivity_ratio': connectivity_ratio,
        'isolated_nodes': isolated_nodes,
        'analysis_type': 'component_sizes',
        'graph_type': 'directed' if G.is_directed() else 'undirected'
    }
    
    return analysis


def analyze_strongly_connected_components(G: nx.DiGraph) -> Dict[str, Any]:
    """
    Analyze strongly connected components and hierarchical structure.

    Identifies trade cycle structures and dependency hierarchies via
    SCC decomposition and DAG condensation.

    Args:
        G: NetworkX directed graph
        
    Returns:
        Dictionary containing:
        - scc_count: Number of strongly connected components
        - scc_sizes: List of SCC sizes (sorted desc)
        - largest_scc_size: Size of largest SCC
        - condensation_nodes: Number of nodes in condensed graph
        - condensation_edges: Number of edges in condensed graph
        - hierarchy_levels: Length of longest path in condensation (hierarchy depth)
        - trivial_sccs: Number of single-node SCCs
        - non_trivial_sccs: Number of multi-node SCCs (actual cycles)
        - scc_details: List of SCC information for largest components
    """
    
    if not G.is_directed():
        raise ValueError("Strongly connected component analysis requires directed graph")
    
    # Find strongly connected components
    sccs = list(nx.strongly_connected_components(G))
    scc_sizes = sorted([len(scc) for scc in sccs], reverse=True)
    
    # Create condensation (DAG of SCCs)
    try:
        condensation = nx.condensation(G)
        condensation_nodes = condensation.number_of_nodes()
        condensation_edges = condensation.number_of_edges()
        
        # Calculate hierarchy depth (longest path in DAG)
        if condensation_nodes > 0:
            hierarchy_levels = nx.dag_longest_path_length(condensation)
        else:
            hierarchy_levels = 0
            
    except Exception as e:
        warnings.warn(f"Condensation analysis failed: {e}")
        condensation_nodes = len(sccs)
        condensation_edges = 0
        hierarchy_levels = 0
    
    # Analyze SCC types
    trivial_sccs = sum(1 for size in scc_sizes if size == 1)
    non_trivial_sccs = sum(1 for size in scc_sizes if size > 1)
    
    # Detailed information for largest SCCs
    scc_details = []
    for i, scc in enumerate(sorted(sccs, key=len, reverse=True)[:5]):  # Top 5 largest
        nodes = list(scc)
        # Try to get node labels if available
        try:
            labels = [G.nodes[node].get('label', str(node)) for node in nodes]
        except Exception:
            labels = [str(node) for node in nodes]
            
        scc_details.append({
            'rank': i + 1,
            'size': len(scc),
            'nodes': nodes,
            'labels': labels
        })
    
    analysis = {
        'scc_count': len(sccs),
        'scc_sizes': scc_sizes,
        'largest_scc_size': max(scc_sizes) if scc_sizes else 0,
        'condensation_nodes': condensation_nodes,
        'condensation_edges': condensation_edges,
        'hierarchy_levels': hierarchy_levels,
        'trivial_sccs': trivial_sccs,
        'non_trivial_sccs': non_trivial_sccs,
        'scc_details': scc_details,
        'analysis_type': 'strongly_connected_components',
        'network_size': G.number_of_nodes()
    }
    
    return analysis


def analyze_centrality_bounds(centralities_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze centrality measure bounds and normalization implications.

    Determines theoretical and observed bounds for each centrality measure
    to inform normalization strategy when combining scores.

    Args:
        centralities_df: DataFrame with centrality measures (must have columns:
                        'betweenness', 'eigenvector', 'out_degree')
                        
    Returns:
        Dictionary containing bounds analysis for each centrality measure:
        - theoretical_bounds: Known mathematical bounds
        - observed_range: [min, max] in actual data
        - is_bounded: Boolean indicating if measure has upper bound
        - normalization_method: Recommended approach
        - distribution_stats: Basic statistics
        - combined_score_feasibility: Analysis for creating combined scores
    """
    
    required_columns = ['betweenness', 'eigenvector', 'out_degree']
    missing_columns = [col for col in required_columns if col not in centralities_df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    n = len(centralities_df)
    
    # Analyze each centrality measure
    measures_analysis = {}
    
    # Out-degree analysis
    out_degree_data = centralities_df['out_degree']
    measures_analysis['out_degree'] = {
        'theoretical_bounds': [0, n - 1],
        'theoretical_max_explanation': 'Bounded by (n-1) possible connections to other nodes',
        'observed_range': [float(out_degree_data.min()), float(out_degree_data.max())],
        'is_bounded': True,
        'bound_utilization': float(out_degree_data.max()) / (n - 1) if n > 1 else 0,
        'normalization_method': 'divide_by_max_possible',
        'normalization_formula': 'out_degree / (n-1)',
        'distribution_stats': {
            'mean': float(out_degree_data.mean()),
            'std': float(out_degree_data.std()),
            'skewness': float(out_degree_data.skew()),
            'zeros_count': int((out_degree_data == 0).sum())
        }
    }
    
    # Betweenness centrality analysis
    betweenness_data = centralities_df['betweenness']
    measures_analysis['betweenness'] = {
        'theoretical_bounds': [0, 'unbounded'],
        'theoretical_max_explanation': 'Unbounded - can exceed 1.0 for highly central nodes',
        'observed_range': [float(betweenness_data.min()), float(betweenness_data.max())],
        'is_bounded': False,
        'exceeds_one': bool((betweenness_data > 1.0).any()),
        'normalization_method': 'z_score_or_min_max',
        'normalization_formula': '(x - mean) / std or (x - min) / (max - min)',
        'distribution_stats': {
            'mean': float(betweenness_data.mean()),
            'std': float(betweenness_data.std()),
            'skewness': float(betweenness_data.skew()),
            'zeros_count': int((betweenness_data == 0).sum())
        }
    }
    
    # Eigenvector centrality analysis
    eigenvector_data = centralities_df['eigenvector']
    measures_analysis['eigenvector'] = {
        'theoretical_bounds': [0, 1],
        'theoretical_max_explanation': 'Mathematically bounded [0,1] but practical range varies',
        'observed_range': [float(eigenvector_data.min()), float(eigenvector_data.max())],
        'is_bounded': True,
        'bound_utilization': float(eigenvector_data.max()),  # Since max theoretical is 1.0
        'normalization_method': 'already_normalized',
        'normalization_formula': 'No normalization needed - already [0,1]',
        'distribution_stats': {
            'mean': float(eigenvector_data.mean()),
            'std': float(eigenvector_data.std()),
            'skewness': float(eigenvector_data.skew()),
            'zeros_count': int((eigenvector_data == 0).sum())
        }
    }
    
    # Combined score feasibility analysis
    combined_score_analysis = {
        'normalization_required': True,
        'recommended_approach': 'z_score_standardization',
        'rationale': 'Different bounds require standardization before combination',
        'alternative_methods': [
            'min_max_scaling',
            'rank_based_scoring', 
            'percentile_transformation'
        ],
        'considerations': [
            'Out-degree bounded by network size',
            'Betweenness unbounded - can have extreme values',
            'Eigenvector naturally bounded but range varies by network',
            'Distribution shapes differ significantly between measures'
        ]
    }
    
    analysis = {
        'network_size': n,
        'measures_analysis': measures_analysis,
        'combined_score_feasibility': combined_score_analysis,
        'analysis_type': 'centrality_bounds',
        'summary': {
            'bounded_measures': ['out_degree', 'eigenvector'],
            'unbounded_measures': ['betweenness'],
            'normalization_complexity': 'high'
        }
    }
    
    return analysis


def comprehensive_network_structure_analysis(
    G: nx.Graph, 
    centralities_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Run all three network structure analyses in sequence.
    
    Runs connectivity, path length, and degree distribution analyses.
    
    Args:
        G: NetworkX graph from pipeline
        centralities_df: Centrality results from pipeline
        
    Returns:
        Dictionary containing all three analyses plus summary insights
    """
    
    results = {
        'analysis_timestamp': pd.Timestamp.now().isoformat(),
        'network_info': {
            'nodes': G.number_of_nodes(),
            'edges': G.number_of_edges(),
            'is_directed': G.is_directed(),
            'graph_type': type(G).__name__
        }
    }
    
    try:
        # Analysis 1: Component sizes
        print("Analyzing component sizes...")
        results['component_analysis'] = analyze_component_sizes(G)
        
        # Analysis 2: Strongly connected components (only for directed graphs)
        if G.is_directed():
            print("Analyzing strongly connected components...")
            results['scc_analysis'] = analyze_strongly_connected_components(G)
        else:
            results['scc_analysis'] = {
                'error': 'Skipped - requires directed graph',
                'analysis_type': 'strongly_connected_components'
            }
        
        # Analysis 3: Centrality bounds
        print("Analyzing centrality bounds...")
        results['centrality_bounds'] = analyze_centrality_bounds(centralities_df)
        
        # Summary insights
        results['summary_insights'] = generate_structure_insights(results)
        
    except Exception as e:
        results['error'] = str(e)
        warnings.warn(f"Network structure analysis failed: {e}")
    
    return results


def generate_structure_insights(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate high-level insights from structure analysis results."""
    
    insights = {
        'network_connectivity': 'unknown',
        'hierarchical_complexity': 'unknown',
        'centrality_methodology': 'unknown',
        'validation_status': 'unknown'
    }
    
    try:
        # Connectivity insights
        if 'component_analysis' in analysis_results:
            comp_analysis = analysis_results['component_analysis']
            if comp_analysis['is_fully_connected']:
                insights['network_connectivity'] = 'fully_connected'
            else:
                insights['network_connectivity'] = f"fragmented_{comp_analysis['component_count']}_components"
        
        # Hierarchy insights
        if 'scc_analysis' in analysis_results and 'error' not in analysis_results['scc_analysis']:
            scc_analysis = analysis_results['scc_analysis']
            levels = scc_analysis.get('hierarchy_levels', 0)
            non_trivial = scc_analysis.get('non_trivial_sccs', 0)
            
            if levels > 5 and non_trivial > 3:
                insights['hierarchical_complexity'] = 'highly_hierarchical'
            elif levels > 2 or non_trivial > 1:
                insights['hierarchical_complexity'] = 'moderately_hierarchical'
            else:
                insights['hierarchical_complexity'] = 'weakly_hierarchical'
        
        # Centrality methodology insights
        if 'centrality_bounds' in analysis_results:
            bounds_analysis = analysis_results['centrality_bounds']
            complexity = bounds_analysis['summary']['normalization_complexity']
            insights['centrality_methodology'] = f"normalization_{complexity}_complexity"
        
        # Overall validation
        connectivity_ok = insights['network_connectivity'] == 'fully_connected'
        has_hierarchy = 'hierarchical' in insights['hierarchical_complexity']
        has_methodology = 'centrality_methodology' in insights and insights['centrality_methodology'] != 'unknown'
        
        if connectivity_ok and has_hierarchy and has_methodology:
            insights['validation_status'] = 'comprehensive_analysis_complete'
        elif connectivity_ok:
            insights['validation_status'] = 'basic_validation_passed'
        else:
            insights['validation_status'] = 'validation_issues_detected'
            
    except Exception as e:
        insights['insight_generation_error'] = str(e)
    
    return insights