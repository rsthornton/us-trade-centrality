"""
Figure generation modules for publication-quality visualizations.
"""

from .filtration import (
    generate_rank_stability_figure,
    generate_connectivity_threshold_figure,
)
from .distributions import (
    generate_distribution_figure,
)
from .diagrams import (
    create_network_construction_figure,
    create_network_spring_figure,
    create_centrality_framework_diagram,
    create_edge_weight_rank_figure,
    create_matrix_comparison_figure,
)
from .choropleths import (
    generate_physical_economy_divergence,
    generate_boundary_effect_choropleth,
)

__all__ = [
    'generate_rank_stability_figure',
    'generate_connectivity_threshold_figure',
    'generate_distribution_figure',
    'create_network_construction_figure',
    'create_network_spring_figure',
    'create_centrality_framework_diagram',
    'create_edge_weight_rank_figure',
    'create_matrix_comparison_figure',
    'generate_physical_economy_divergence',
    'generate_boundary_effect_choropleth',
]
