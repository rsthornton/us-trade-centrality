"""
Visualization modules for publication-ready figures and reports.
"""

from .base import (
    create_centrality_comparison,
    create_3d_centrality_plot,
    create_static_3d_plots,
    create_pairwise_scatter_plots,
    create_boundary_sensitivity_summary,
)
from .styles import (
    set_publication_style,
    get_color_palette,
)

__all__ = [
    # Base visualizations
    'create_centrality_comparison',
    'create_3d_centrality_plot',
    'create_static_3d_plots',
    'create_pairwise_scatter_plots',
    'create_boundary_sensitivity_summary',
    # Styling
    'set_publication_style',
    'get_color_palette',
]
