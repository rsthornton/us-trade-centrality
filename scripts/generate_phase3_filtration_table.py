"""
Phase 3: Generate post-filtration network properties table.

Computes network properties for full graph and 33% filtered graph,
outputs LaTeX table snippet to paper/figures/.
"""

import sys
from pathlib import Path

# Add toolkit to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'cfs-network-toolkit'))

import networkx as nx
from cfs_toolkit.analysis import load_network_graph, filter_graph_by_percentile

# Paths
PROJECT = Path(__file__).parent.parent
RESULTS = PROJECT / 'results' / '51x51_domestic'
FIGURES = PROJECT / 'paper' / 'figures'


def compute_properties(G, label):
    """Compute network properties for a graph."""
    props = {}
    props['label'] = label
    props['nodes'] = G.number_of_nodes()
    props['edges'] = G.number_of_edges()
    n = G.number_of_nodes()
    max_edges = n * (n - 1)
    props['density'] = G.number_of_edges() / max_edges if max_edges > 0 else 0
    props['reciprocity'] = nx.reciprocity(G)

    n_scc = nx.number_strongly_connected_components(G)
    props['n_scc'] = n_scc

    if n_scc == 1:
        props['diameter'] = nx.diameter(G)
        props['avg_path_length'] = nx.average_shortest_path_length(G)
    else:
        # Use largest SCC for diameter
        largest_scc = max(nx.strongly_connected_components(G), key=len)
        G_scc = G.subgraph(largest_scc)
        props['diameter'] = nx.diameter(G_scc)
        props['avg_path_length'] = nx.average_shortest_path_length(G_scc)
        props['note'] = f'{n_scc} SCCs (largest used)'

    return props


def generate_latex_table(full_props, filt_props, threshold_val):
    """Generate LaTeX table snippet."""
    lines = []
    lines.append(r'\begin{table}[ht]')
    lines.append(r'  \centering')
    lines.append(r'  \caption{Network Properties Before and After 33\% Graph Filtration (51$\times$51 Domestic Network). '
                 f'Filtration removes edges below the 33rd percentile (\\${threshold_val/1e6:.0f}M threshold), '
                 r'the maximum level before network fragmentation.}')
    lines.append(r'  \label{tab:filtration_properties}')
    lines.append(r'  \begin{tabular}{lcc}')
    lines.append(r'  \hline')
    lines.append(r'  \textbf{Property} & \textbf{Full Network} & \textbf{Filtered (33\%)} \\')
    lines.append(r'  \hline')
    lines.append(f'  Nodes & {full_props["nodes"]} & {filt_props["nodes"]} \\\\')
    lines.append(f'  Edges & {full_props["edges"]:,} & {filt_props["edges"]:,} \\\\')
    lines.append(f'  Density & {full_props["density"]:.3f} & {filt_props["density"]:.3f} \\\\')
    lines.append(f'  Diameter & {full_props["diameter"]} & {filt_props["diameter"]} \\\\')
    lines.append(f'  Avg.\\ Path Length & {full_props["avg_path_length"]:.3f} & {filt_props["avg_path_length"]:.3f} \\\\')
    lines.append(f'  Reciprocity & {full_props["reciprocity"]:.3f} & {filt_props["reciprocity"]:.3f} \\\\')
    lines.append(r'  \hline')
    lines.append(r'  \end{tabular}')
    lines.append(r'\end{table}')
    return '\n'.join(lines)


def main():
    print("=" * 60)
    print("  PHASE 3: Post-Filtration Network Properties")
    print("=" * 60)

    # Load network
    G = load_network_graph(RESULTS)
    print(f"\n  Full network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # Compute full properties
    full_props = compute_properties(G, 'Full')
    print(f"  Full diameter: {full_props['diameter']}")
    print(f"  Full avg path: {full_props['avg_path_length']:.3f}")
    print(f"  Full density: {full_props['density']:.3f}")
    print(f"  Full reciprocity: {full_props['reciprocity']:.3f}")

    # Apply 33% filtration
    G_filt, threshold = filter_graph_by_percentile(G, 33)
    print(f"\n  Filtered network (33%): {G_filt.number_of_nodes()} nodes, {G_filt.number_of_edges()} edges")
    print(f"  Threshold: ${threshold/1e6:.0f}M")

    # Check connectivity
    n_scc = nx.number_strongly_connected_components(G_filt)
    print(f"  Strongly connected components: {n_scc}")

    # Compute filtered properties
    filt_props = compute_properties(G_filt, 'Filtered (33%)')
    print(f"  Filtered diameter: {filt_props['diameter']}")
    print(f"  Filtered avg path: {filt_props['avg_path_length']:.3f}")
    print(f"  Filtered density: {filt_props['density']:.3f}")
    print(f"  Filtered reciprocity: {filt_props['reciprocity']:.3f}")

    # Generate LaTeX
    latex = generate_latex_table(full_props, filt_props, threshold)
    output_path = FIGURES / 'table_filtration_properties_latex.txt'
    output_path.write_text(latex)
    print(f"\n  \u2713 LaTeX table saved: {output_path}")

    # Verify key result: diameter should increase under filtration
    if filt_props['diameter'] > full_props['diameter']:
        print(f"  \u2713 Diameter increased: {full_props['diameter']} \u2192 {filt_props['diameter']}")
    else:
        print(f"  \u26a0 Diameter did NOT increase: {full_props['diameter']} \u2192 {filt_props['diameter']}")

    print("\n" + "=" * 60)

if __name__ == '__main__':
    main()
