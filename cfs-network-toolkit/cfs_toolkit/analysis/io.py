"""
I/O utilities for loading graphs and configuration data.
"""

import logging
from pathlib import Path
import pickle

import numpy as np
import pandas as pd
import networkx as nx

log = logging.getLogger(__name__)


def load_network_graph(result_dir):
    """
    Load NetworkX graph from pipeline result directory.

    Args:
        result_dir (Path): Path to result directory containing .gpickle file

    Returns:
        nx.DiGraph: Loaded trade network
    """
    result_path = Path(result_dir)

    # Find .gpickle file
    gpickle_files = list(result_path.glob('*.gpickle'))
    if not gpickle_files:
        raise FileNotFoundError(f"No .gpickle file found in {result_dir}")

    gpickle_path = gpickle_files[0]
    log.info(f"Loading graph from {gpickle_path.name}")

    with open(gpickle_path, 'rb') as f:
        G = pickle.load(f)

    log.info(f"  Loaded: {len(G.nodes())} nodes, {len(G.edges())} edges")
    log.info(f"  Type: {G.graph.get('network_type', 'unknown')}")
    log.info(f"  Density: {nx.density(G):.6f}")

    return G


def extract_edge_weights(G):
    """
    Extract all edge weights from graph.

    Args:
        G (nx.DiGraph): Trade network

    Returns:
        np.array: Array of edge weights
    """
    weights = np.array([data['weight'] for _, _, data in G.edges(data=True)])
    log.info(f"  Extracted {len(weights):,} edge weights")
    return weights


def load_thresholds_from_csv(thresholds_csv, network_type='51x51', levels=None):
    """
    Load threshold values from recommended_thresholds.csv.

    Args:
        thresholds_csv (Path): Path to CSV with threshold recommendations
        network_type (str): '51x51' or '52x52'
        levels (list, optional): Subset of levels to use (e.g., ['moderate', 'aggressive'])

    Returns:
        list: Threshold values
    """
    df = pd.read_csv(thresholds_csv, index_col=0)

    if network_type not in df.index:
        raise ValueError(f"Network type '{network_type}' not found in {thresholds_csv}")

    if levels is None:
        levels = df.columns.tolist()  # Use all available levels

    thresholds = [df.loc[network_type, level] for level in levels]
    log.info(f"Loaded {len(thresholds)} thresholds for {network_type}: {levels}")

    return thresholds
