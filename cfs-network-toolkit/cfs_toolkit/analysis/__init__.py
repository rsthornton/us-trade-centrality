"""
Analysis modules for boundary sensitivity and filtration analysis.
"""

from .io import (
    load_network_graph,
    load_thresholds_from_csv,
    extract_edge_weights,
)
from .filtration import (
    calculate_rank_changes,
    count_components_at_filtration,
    find_connectivity_breaking_point,
    filter_graph_by_percentile,
    scan_filtration_range,
)
from .distributions import (
    calculate_distribution_stats,
    recommend_thresholds,
)
from .comparison_utils import (
    load_comparison_data_from_results,
    prepare_comparison_data_for_pipeline,
    align_measures,
    rank_columns,
    compute_rank_correlations,
    compute_rank_changes,
    compute_topk_overlap,
    summarize_effect_sizes,
)
from .gdp_comparison import (
    load_gdp_data,
    compute_gdp_vs_centrality_comparison,
    identify_outliers,
    generate_gdp_centrality_scatter,
    generate_normalized_centrality_bar,
)
from .control_scatter import (
    load_population_data,
    generate_control_scatter,
)
from .network_analysis import (
    analyze_component_sizes,
    analyze_strongly_connected_components,
    analyze_centrality_bounds,
    comprehensive_network_structure_analysis,
    generate_structure_insights,
)
from .commodity import (
    build_commodity_network,
    build_all_commodity_networks,
    analyze_commodity_centralities,
    identify_commodity_specialists,
    compute_commodity_leadership_matrix,
    analyze_commodity_diversification,
    compare_commodity_structures,
    SCTG_NAMES,
    COMMODITY_GROUPS,
    get_commodity_group,
)

__all__ = [
    # I/O functions
    'load_network_graph',
    'load_thresholds_from_csv',
    'extract_edge_weights',
    # Filtration analysis
    'calculate_rank_changes',
    'count_components_at_filtration',
    'find_connectivity_breaking_point',
    'filter_graph_by_percentile',
    'scan_filtration_range',
    # Distribution analysis
    'calculate_distribution_stats',
    'recommend_thresholds',
    # Comparison utilities
    'load_comparison_data_from_results',
    'prepare_comparison_data_for_pipeline',
    'align_measures',
    'rank_columns',
    'compute_rank_correlations',
    'compute_rank_changes',
    'compute_topk_overlap',
    'summarize_effect_sizes',
    # GDP comparison
    'load_gdp_data',
    'compute_gdp_vs_centrality_comparison',
    'identify_outliers',
    'generate_gdp_centrality_scatter',
    'generate_normalized_centrality_bar',
    # Control scatter
    'load_population_data',
    'generate_control_scatter',
    # Network structure analysis
    'analyze_component_sizes',
    'analyze_strongly_connected_components',
    'analyze_centrality_bounds',
    'comprehensive_network_structure_analysis',
    'generate_structure_insights',
    # Commodity analysis
    'build_commodity_network',
    'build_all_commodity_networks',
    'analyze_commodity_centralities',
    'identify_commodity_specialists',
    'compute_commodity_leadership_matrix',
    'analyze_commodity_diversification',
    'compare_commodity_structures',
    'SCTG_NAMES',
    'COMMODITY_GROUPS',
    'get_commodity_group',
]
