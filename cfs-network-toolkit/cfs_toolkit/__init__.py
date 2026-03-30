"""
CFS Network Toolkit - U.S. Interstate Commerce Network Analysis

A Python package for analyzing U.S. interstate commodity flows using network
centrality measures.
"""

__version__ = "0.1.0"

# Core imports for convenience
from .core.data_loader import load_cfs_data, load_data
from .core.faf_loader import load_faf5_international_edges
from .core.network_builder import build_trade_network
from .core.centralities import (
    compute_all_centralities,
    compute_all_centralities_with_filtration,
    compute_centralities_at_multiple_thresholds,
)
from .core.preprocessor import preprocess_cfs_data
from .core.validators import validate_network_structure
from .core.artifacts import save_pipeline_artifacts

__all__ = [
    "load_cfs_data",
    "load_data",
    "load_faf5_international_edges",
    "build_trade_network",
    "compute_all_centralities",
    "compute_all_centralities_with_filtration",
    "compute_centralities_at_multiple_thresholds",
    "preprocess_cfs_data",
    "validate_network_structure",
    "save_pipeline_artifacts",
]
