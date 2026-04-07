"""
Regenerate thesis figures: network spring layout, matrix comparison, edge weight distribution.

Usage:
    python scripts/regenerate_figures.py
"""
import pickle
from pathlib import Path
import sys

# Add toolkit to path
sys.path.insert(0, str(Path(__file__).parent.parent / "cfs-network-toolkit"))

from cfs_toolkit.figures.diagrams import (
    create_network_spring_figure,
    create_matrix_comparison_figure,
    create_edge_weight_rank_figure,
)

RESULTS = Path(__file__).parent.parent / "results"
FIGURES = Path(__file__).parent.parent / "paper" / "figures"

# Load graphs
with open(RESULTS / "51x51_domestic/network_51x51_domestic.gpickle", "rb") as f:
    G_51 = pickle.load(f)
with open(RESULTS / "52x52_international/network_52x52_intl.gpickle", "rb") as f:
    G_52 = pickle.load(f)

print(f"Loaded G_51: {G_51.number_of_nodes()} nodes, {G_51.number_of_edges()} edges")
print(f"Loaded G_52: {G_52.number_of_nodes()} nodes, {G_52.number_of_edges()} edges")

# Regenerate Fig 3.1
print("\n--- Fig 3.1: Network Spring Layout ---")
create_network_spring_figure(G_51, G_52, output_path=FIGURES / "network_construction_spring.png")

# Regenerate Fig 3.2
print("\n--- Fig 3.2: Matrix Comparison ---")
centralities_csv = RESULTS / "51x51_domestic/centralities_51x51_domestic.csv"
if centralities_csv.exists():
    print(f"Using canonical centralities: {centralities_csv}")
    create_matrix_comparison_figure(G_51, G_52,
                                    centralities_csv=centralities_csv,
                                    output_path=FIGURES / "matrix_comparison.png")
else:
    print("Warning: centralities CSV not found, computing from graph")
    create_matrix_comparison_figure(G_51, G_52,
                                    output_path=FIGURES / "matrix_comparison.png")

# Regenerate edge weight rank distribution (new figure for §3.4)
print("\n--- Fig 3.X: Edge Weight Rank Distribution ---")
create_edge_weight_rank_figure(G_51, output_path=FIGURES / "edge_weight_rank_distribution.png")

print("\nDone. Upload all PNGs to Overleaf.")
