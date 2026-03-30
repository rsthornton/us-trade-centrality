"""
Conceptual/methodology diagram generation.

Unlike data-driven figures, these are educational diagrams explaining
methodological concepts.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import numpy as np
from pathlib import Path


def create_network_construction_figure(output_path=None):
    """
    Figure 3.1: Network Construction Methodology

    Shows side-by-side comparison of 51×51 domestic vs 52×52 international networks.
    Uses simplified representation (8 representative states) for clarity.
    """

    if output_path is None:
        output_path = Path("results/publication_figures") / "fig_network_construction_schematic.pdf"
    else:
        output_path = Path(output_path)

    # Create figure with two panels
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # ===== Panel 1: 51×51 Domestic Network =====

    # Create simplified network (8 representative states)
    G_domestic = nx.DiGraph()

    # Representative states: major economies + geographic diversity
    states_domestic = {
        6: 'CA',   # California (West Coast)
        48: 'TX',  # Texas (South)
        17: 'IL',  # Illinois (Midwest)
        36: 'NY',  # New York (Northeast)
        12: 'FL',  # Florida (Southeast)
        53: 'WA',  # Washington (Northwest)
        39: 'OH',  # Ohio (Midwest)
        42: 'PA',  # Pennsylvania (Mid-Atlantic)
    }

    G_domestic.add_nodes_from(states_domestic.keys())

    # Add representative edges (simplified for clarity)
    domestic_edges = [
        (6, 48),   # CA → TX
        (6, 53),   # CA → WA
        (48, 12),  # TX → FL
        (17, 39),  # IL → OH
        (17, 42),  # IL → PA
        (36, 42),  # NY → PA
        (39, 36),  # OH → NY
        (42, 36),  # PA → NY
        (53, 6),   # WA → CA
        (48, 17),  # TX → IL
    ]
    G_domestic.add_edges_from(domestic_edges)

    # Rough geographic positioning (mimics US map)
    pos_domestic = {
        6: (0.1, 0.6),   # CA (West)
        53: (0.15, 0.85), # WA (Northwest)
        48: (0.4, 0.2),   # TX (South)
        17: (0.5, 0.6),   # IL (Midwest)
        39: (0.65, 0.6),  # OH (Midwest-East)
        42: (0.8, 0.65),  # PA (Mid-Atlantic)
        36: (0.85, 0.75), # NY (Northeast)
        12: (0.75, 0.15), # FL (Southeast)
    }

    # Draw domestic network
    nx.draw_networkx_nodes(G_domestic, pos_domestic,
                           node_color='lightgray',
                           node_size=1200,
                           ax=ax1)

    nx.draw_networkx_labels(G_domestic, pos_domestic,
                           labels=states_domestic,
                           font_size=13,
                           font_weight='bold',
                           ax=ax1)

    nx.draw_networkx_edges(G_domestic, pos_domestic,
                          edge_color='gray',
                          arrows=True,
                          arrowsize=15,
                          arrowstyle='->',
                          width=1.5,
                          alpha=0.6,
                          ax=ax1,
                          connectionstyle='arc3,rad=0.1')

    ax1.set_title('51×51 Domestic Network\n(Baseline)',
                  fontsize=15, fontweight='bold', pad=10)
    ax1.text(0.5, -0.05, '51 nodes, ~2,534 edges\n$7.6T trade value',
            ha='center', va='top', transform=ax1.transAxes,
            fontsize=12, style='italic')
    ax1.axis('off')
    ax1.set_xlim(-0.05, 1.05)
    ax1.set_ylim(-0.1, 1.0)

    # ===== Panel 2: 52×52 International Network =====

    # Create international network (same states + RoW)
    G_intl = G_domestic.copy()
    G_intl.add_node(52)  # Rest of World

    states_intl = {**states_domestic, 52: 'RoW'}

    # Add international edges (gateway states ↔ RoW)
    intl_edges = [
        (6, 52),   # CA → RoW (exports)
        (52, 6),   # RoW → CA (imports)
        (48, 52),  # TX → RoW
        (52, 48),  # RoW → TX
        (36, 52),  # NY → RoW
        (52, 36),  # RoW → NY
        (12, 52),  # FL → RoW
        (52, 12),  # RoW → FL
    ]
    G_intl.add_edges_from(intl_edges)

    # Position RoW node at top center
    pos_intl = {**pos_domestic, 52: (0.5, 0.95)}

    # Identify gateway states (have international connections)
    gateway_states = {6, 48, 36, 12}

    # Color nodes: gateway states highlighted
    node_colors = ['lightblue' if node in gateway_states else 'lightgray'
                   for node in G_intl.nodes()]

    # Draw international network
    nx.draw_networkx_nodes(G_intl, pos_intl,
                          nodelist=list(G_intl.nodes()),
                          node_color=node_colors,
                          node_size=1200,
                          ax=ax2)

    # Special styling for RoW node
    nx.draw_networkx_nodes(G_intl, pos_intl,
                          nodelist=[52],
                          node_color='wheat',
                          node_size=1400,
                          node_shape='s',  # Square for RoW
                          ax=ax2)

    nx.draw_networkx_labels(G_intl, pos_intl,
                           labels=states_intl,
                           font_size=13,
                           font_weight='bold',
                           ax=ax2)

    # Draw edges with different colors
    # Domestic edges (gray)
    nx.draw_networkx_edges(G_intl, pos_intl,
                          edgelist=domestic_edges,
                          edge_color='gray',
                          arrows=True,
                          arrowsize=15,
                          arrowstyle='->',
                          width=1.5,
                          alpha=0.4,
                          ax=ax2,
                          connectionstyle='arc3,rad=0.1')

    # International edges (blue)
    nx.draw_networkx_edges(G_intl, pos_intl,
                          edgelist=intl_edges,
                          edge_color='steelblue',
                          arrows=True,
                          arrowsize=15,
                          arrowstyle='->',
                          width=2.5,
                          alpha=0.8,
                          ax=ax2,
                          connectionstyle='arc3,rad=0.1')

    ax2.set_title('52×52 International Network\n(Boundary Extended)',
                  fontsize=15, fontweight='bold', pad=10)
    ax2.text(0.5, -0.05, '52 nodes, ~2,636 edges\n$11.4T trade value',
            ha='center', va='top', transform=ax2.transAxes,
            fontsize=12, style='italic')
    ax2.axis('off')
    ax2.set_xlim(-0.05, 1.05)
    ax2.set_ylim(-0.1, 1.05)

    # Add legend
    legend_elements = [
        mpatches.Patch(color='lightgray', label='Domestic state'),
        mpatches.Patch(color='lightblue', label='Gateway state'),
        mpatches.Patch(color='wheat', label='Rest of World'),
        mpatches.Rectangle((0,0),1,1, fc='gray', alpha=0.6, label='Domestic flow'),
        mpatches.Rectangle((0,0),1,1, fc='steelblue', alpha=0.8, label='International flow'),
    ]
    fig.legend(handles=legend_elements,
              loc='lower center',
              ncol=5,
              frameon=False,
              fontsize=12,
              bbox_to_anchor=(0.5, -0.02))

    # Overall title
    fig.suptitle('Network Construction Methodology',
                fontsize=17, fontweight='bold', y=0.98)

    plt.tight_layout(rect=[0, 0.03, 1, 0.96])

    # Save figure
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, format='pdf', bbox_inches='tight', dpi=300)
    plt.savefig(output_path.with_suffix('.png'), format='png', bbox_inches='tight', dpi=300)

    print(f"✓ Network construction figure saved to:")
    print(f"  - {output_path}")
    print(f"  - {output_path.with_suffix('.png')}")

    plt.close()


def create_network_spring_figure(G_51, G_52, output_path=None, top_n=10):
    """
    Data-driven network visualization using spring layout.

    Shows actual network topology based on edge weights, with top N states
    by out-degree for visual clarity. Side-by-side comparison of 51×51
    domestic vs 52×52 international networks.

    Args:
        G_51: NetworkX DiGraph for 51×51 domestic network
        G_52: NetworkX DiGraph for 52×52 international network
        output_path: Output file path (default: results/viz_all_output/figures/)
        top_n: Number of top states to show (default: 10)

    Returns:
        matplotlib Figure object
    """
    import numpy as np

    if output_path is None:
        output_path = Path("results/viz_all_output/figures") / "network_construction_spring.png"
    else:
        output_path = Path(output_path)

    # FIPS code to state abbreviation mapping
    FIPS_TO_STATE = {
        1: 'AL', 2: 'AK', 4: 'AZ', 5: 'AR', 6: 'CA', 8: 'CO', 9: 'CT', 10: 'DE',
        11: 'DC', 12: 'FL', 13: 'GA', 15: 'HI', 16: 'ID', 17: 'IL', 18: 'IN',
        19: 'IA', 20: 'KS', 21: 'KY', 22: 'LA', 23: 'ME', 24: 'MD', 25: 'MA',
        26: 'MI', 27: 'MN', 28: 'MS', 29: 'MO', 30: 'MT', 31: 'NE', 32: 'NV',
        33: 'NH', 34: 'NJ', 35: 'NM', 36: 'NY', 37: 'NC', 38: 'ND', 39: 'OH',
        40: 'OK', 41: 'OR', 42: 'PA', 44: 'RI', 45: 'SC', 46: 'SD', 47: 'TN',
        48: 'TX', 49: 'UT', 50: 'VT', 51: 'VA', 53: 'WA', 54: 'WV', 55: 'WI',
        56: 'WY', 99: 'RoW'  # RoW uses 99 in the international network
    }

    # Compute weighted out-degree for each node in G_51
    out_degrees = {}
    for node in G_51.nodes():
        out_deg = sum(G_51[node][nbr].get('weight', 1) for nbr in G_51.successors(node))
        out_degrees[node] = out_deg

    # Get top N nodes by out-degree
    top_nodes = sorted(out_degrees.keys(), key=lambda x: out_degrees[x], reverse=True)[:top_n]

    # Create subgraphs with only top nodes
    G_51_sub = G_51.subgraph(top_nodes).copy()

    # For G_52, include top nodes plus RoW if present
    row_node = None
    for node in G_52.nodes():
        label = G_52.nodes[node].get('label', '')
        if label == 'RoW' or FIPS_TO_STATE.get(node, '') == 'RoW' or node == 99:
            row_node = node
            break

    intl_nodes = list(top_nodes)
    if row_node is not None and row_node in G_52.nodes():
        intl_nodes.append(row_node)
    G_52_sub = G_52.subgraph([n for n in intl_nodes if n in G_52.nodes()]).copy()

    # Create figure with two panels
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 9))

    # ===== Panel 1: 51×51 Domestic Network =====

    # Spring layout based on edge weights (invert so high weight = close)
    # Use weight as attraction strength
    edge_weights_51 = nx.get_edge_attributes(G_51_sub, 'weight')
    if edge_weights_51:
        max_weight = max(edge_weights_51.values())
        # Normalize weights to [0.1, 1] range for layout
        normalized_weights = {e: 0.1 + 0.9 * (w / max_weight) for e, w in edge_weights_51.items()}
        nx.set_edge_attributes(G_51_sub, normalized_weights, 'weight_norm')
        pos_51 = nx.spring_layout(G_51_sub, weight='weight_norm', k=2, iterations=100, seed=42)
    else:
        pos_51 = nx.spring_layout(G_51_sub, k=2, iterations=100, seed=42)

    # Node sizes based on out-degree
    node_sizes_51 = [300 + 2000 * (out_degrees.get(n, 0) / max(out_degrees.values()))
                     for n in G_51_sub.nodes()]

    # Node labels (check graph attribute first, then FIPS lookup, then str fallback)
    labels_51 = {n: G_51_sub.nodes[n].get('label', '') or FIPS_TO_STATE.get(n, str(n))
                 for n in G_51_sub.nodes()}

    # Edge widths based on weight
    if edge_weights_51:
        edge_widths_51 = [0.5 + 4 * (edge_weights_51.get((u, v), 0) / max_weight)
                         for u, v in G_51_sub.edges()]
    else:
        edge_widths_51 = [1.5] * G_51_sub.number_of_edges()

    # Draw domestic network
    nx.draw_networkx_nodes(G_51_sub, pos_51,
                           node_color='#4ECDC4',  # Teal
                           node_size=node_sizes_51,
                           alpha=0.9,
                           ax=ax1)

    nx.draw_networkx_labels(G_51_sub, pos_51,
                            labels=labels_51,
                            font_size=15,
                            font_weight='bold',
                            ax=ax1)

    nx.draw_networkx_edges(G_51_sub, pos_51,
                           edge_color='#556270',
                           arrows=True,
                           arrowsize=12,
                           arrowstyle='-|>',
                           width=edge_widths_51,
                           alpha=0.5,
                           ax=ax1,
                           connectionstyle='arc3,rad=0.1')

    ax1.set_title(f'51×51 Domestic Network\n(Top {top_n} states by out-degree)',
                  fontsize=18, fontweight='bold', pad=15)
    ax1.text(0.5, -0.08, f'{G_51.number_of_nodes()} nodes, {G_51.number_of_edges():,} edges\n'
             f'Showing top {top_n} by trade volume',
             ha='center', va='top', transform=ax1.transAxes,
             fontsize=14, style='italic', color='#555')
    ax1.axis('off')

    # ===== Panel 2: 52×52 International Network =====

    # Use same positions as base, add RoW at top
    pos_52 = {n: pos_51[n] for n in G_52_sub.nodes() if n in pos_51}
    if row_node is not None and row_node in G_52_sub.nodes():
        # Place RoW at top center
        pos_52[row_node] = (0, 1.2)

    # Edge weights for G_52
    edge_weights_52 = nx.get_edge_attributes(G_52_sub, 'weight')
    max_weight_52 = max(edge_weights_52.values()) if edge_weights_52 else 1

    # Identify edges to/from RoW
    intl_edges = [(u, v) for u, v in G_52_sub.edges()
                  if u == row_node or v == row_node]
    domestic_edges = [(u, v) for u, v in G_52_sub.edges()
                      if u != row_node and v != row_node]

    # Node colors: RoW is different
    node_colors_52 = ['#FF6B6B' if n == row_node else '#4ECDC4'
                      for n in G_52_sub.nodes()]

    # Node sizes
    node_sizes_52 = []
    for n in G_52_sub.nodes():
        if n == row_node:
            node_sizes_52.append(2500)  # RoW is large
        else:
            node_sizes_52.append(300 + 2000 * (out_degrees.get(n, 0) / max(out_degrees.values())))

    # Node labels (check graph attribute first, then FIPS lookup, then str fallback)
    labels_52 = {n: G_52_sub.nodes[n].get('label', '') or FIPS_TO_STATE.get(n, str(n))
                 for n in G_52_sub.nodes()}

    # Draw international network
    nx.draw_networkx_nodes(G_52_sub, pos_52,
                           node_color=node_colors_52,
                           node_size=node_sizes_52,
                           alpha=0.9,
                           ax=ax2)

    nx.draw_networkx_labels(G_52_sub, pos_52,
                            labels=labels_52,
                            font_size=15,
                            font_weight='bold',
                            ax=ax2)

    # Draw domestic edges (gray)
    if domestic_edges:
        dom_widths = [0.5 + 4 * (edge_weights_52.get((u, v), 0) / max_weight_52)
                      for u, v in domestic_edges]
        nx.draw_networkx_edges(G_52_sub, pos_52,
                               edgelist=domestic_edges,
                               edge_color='#556270',
                               arrows=True,
                               arrowsize=12,
                               arrowstyle='-|>',
                               width=dom_widths,
                               alpha=0.4,
                               ax=ax2,
                               connectionstyle='arc3,rad=0.1')

    # Draw international edges (blue, prominent)
    if intl_edges:
        intl_widths = [1 + 3 * (edge_weights_52.get((u, v), 0) / max_weight_52)
                       for u, v in intl_edges]
        nx.draw_networkx_edges(G_52_sub, pos_52,
                               edgelist=intl_edges,
                               edge_color='#FF6B6B',
                               arrows=True,
                               arrowsize=15,
                               arrowstyle='-|>',
                               width=intl_widths,
                               alpha=0.7,
                               ax=ax2,
                               connectionstyle='arc3,rad=0.15')

    ax2.set_title(f'52×52 International Network\n(+ Rest of World node)',
                  fontsize=18, fontweight='bold', pad=15)
    ax2.text(0.5, -0.08, f'{G_52.number_of_nodes()} nodes, {G_52.number_of_edges():,} edges\n'
             f'Gateway states connect to international trade',
             ha='center', va='top', transform=ax2.transAxes,
             fontsize=14, style='italic', color='#555')
    ax2.axis('off')

    # Add legend
    legend_elements = [
        mpatches.Patch(color='#4ECDC4', alpha=0.9, label='U.S. State'),
        mpatches.Patch(color='#FF6B6B', alpha=0.9, label='Rest of World'),
        plt.Line2D([0], [0], color='#556270', linewidth=2, alpha=0.5, label='Domestic flow'),
        plt.Line2D([0], [0], color='#FF6B6B', linewidth=2.5, alpha=0.7, label='International flow'),
    ]
    fig.legend(handles=legend_elements,
               loc='lower center',
               ncol=4,
               frameon=False,
               fontsize=14,
               bbox_to_anchor=(0.5, -0.02))

    # Overall title
    fig.suptitle('Network Topology: Spring Layout Based on Trade Weights',
                 fontsize=20, fontweight='bold', y=0.98)

    plt.tight_layout(rect=[0, 0.05, 1, 0.95])

    # Save figure
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, format='png', bbox_inches='tight', dpi=300, facecolor='white')

    # Also save PDF
    pdf_path = output_path.with_suffix('.pdf')
    plt.savefig(pdf_path, format='pdf', bbox_inches='tight', facecolor='white')

    print(f"✓ Network spring layout figure saved to:")
    print(f"  - {output_path}")
    print(f"  - {pdf_path}")

    return fig


def create_centrality_framework_diagram(output_path=None):
    """
    Figure 3.2 - Three-Level Centrality Framework

    Visual diagram explaining macro/meso/micro framework.
    Three panels showing betweenness (bridging), eigenvector (influence),
    and weighted out-degree (distribution capacity).

    Adapted from Jang & Yang (2023).
    """

    if output_path is None:
        output_path = Path("results/publication_figures") / "fig_centrality_framework.pdf"
    else:
        output_path = Path(output_path)

    # Set up figure
    fig, axes = plt.subplots(1, 3, figsize=(16, 7))
    fig.suptitle('Three-Level Centrality Framework (Adapted from Jang & Yang 2023)',
                 fontsize=20, fontweight='bold', y=0.98)

    # Colors
    HIGH = '#D64541'      # Red - high centrality / important nodes
    EIGENVECTOR = '#27AE60'  # Green - high eigenvector (connected to important)
    LOW = '#BDC3C7'       # Gray - low/baseline
    EDGE_COLOR = '#2C3E50'  # Dark blue-gray for edges

    # === Panel 1: Betweenness Centrality (MACRO) ===
    ax1 = axes[0]
    ax1.set_title('MACRO: Betweenness Centrality', fontsize=17, fontweight='bold', pad=10)

    G1 = nx.Graph()
    G1.add_nodes_from(['L1', 'L2', 'L3'])
    G1.add_edges_from([('L1', 'L2'), ('L2', 'L3'), ('L1', 'L3')])
    G1.add_nodes_from(['R1', 'R2', 'R3'])
    G1.add_edges_from([('R1', 'R2'), ('R2', 'R3'), ('R1', 'R3')])
    G1.add_node('B')
    G1.add_edges_from([('L1', 'B'), ('B', 'R1')])

    pos1 = {
        'L1': (-1.5, 0), 'L2': (-1.9, 0.5), 'L3': (-1.9, -0.5),
        'B': (0, 0),
        'R1': (1.5, 0), 'R2': (1.9, 0.5), 'R3': (1.9, -0.5)
    }

    node_colors1 = [LOW, LOW, LOW, LOW, LOW, LOW, HIGH]
    node_sizes1 = [400, 400, 400, 400, 400, 400, 700]

    nx.draw_networkx_nodes(G1, pos1, ax=ax1, node_color=node_colors1,
                           node_size=node_sizes1, edgecolors='white', linewidths=2)
    nx.draw_networkx_edges(G1, pos1, ax=ax1, edge_color=EDGE_COLOR, width=2, alpha=0.7)

    ax1.text(0, -1.0, 'Bridges regional clusters',
             ha='center', va='top', fontsize=15, style='italic',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='#FFF9E6', edgecolor='#C9A227'))
    ax1.text(0, -1.6, 'e.g. TX, PA, WA',
             ha='center', va='top', fontsize=14, fontweight='bold', color='#333')

    ax1.set_xlim(-2.2, 2.2)
    ax1.set_ylim(-2.0, 1.2)
    ax1.axis('off')

    # === Panel 2: Eigenvector Centrality (MESO) ===
    ax2 = axes[1]
    ax2.set_title('MESO: Eigenvector Centrality', fontsize=17, fontweight='bold', pad=10)

    G2 = nx.Graph()
    G2.add_node('A')
    G2.add_nodes_from(['H1', 'H2', 'H3', 'H4'])
    G2.add_edges_from([('A', 'H1'), ('A', 'H2'), ('A', 'H3'), ('A', 'H4')])
    G2.add_nodes_from(['S1', 'S2', 'S3', 'S4', 'S5', 'S6'])
    G2.add_edges_from([('H1', 'S1'), ('H1', 'S2'),
                       ('H2', 'S3'),
                       ('H3', 'S4'), ('H3', 'S5'),
                       ('H4', 'S6')])

    pos2 = {
        'A': (0, 0),
        'H1': (-0.8, 0.6), 'H2': (0.7, 0.7), 'H3': (0.6, -0.5), 'H4': (-0.6, -0.6),
        'S1': (-1.4, 0.9), 'S2': (-1.3, 0.2),
        'S3': (1.3, 0.5),
        'S4': (1.2, -0.3), 'S5': (0.8, -1.1),
        'S6': (-1.2, -0.9)
    }

    node_colors2 = [EIGENVECTOR, HIGH, HIGH, HIGH, HIGH, LOW, LOW, LOW, LOW, LOW, LOW]
    node_sizes2 = [700, 500, 500, 500, 500, 300, 300, 300, 300, 300, 300]

    nx.draw_networkx_nodes(G2, pos2, ax=ax2, node_color=node_colors2,
                           node_size=node_sizes2, edgecolors='white', linewidths=2)
    nx.draw_networkx_edges(G2, pos2, ax=ax2, edge_color=EDGE_COLOR, width=2, alpha=0.7)

    ax2.text(0, -1.5, 'Connected to important nodes',
             ha='center', va='top', fontsize=15, style='italic',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='#FFF9E6', edgecolor='#C9A227'))
    ax2.text(0, -2.1, 'e.g. TX, OH, FL',
             ha='center', va='top', fontsize=14, fontweight='bold', color='#333')

    ax2.set_xlim(-2, 2)
    ax2.set_ylim(-2.5, 1.8)
    ax2.axis('off')

    # === Panel 3: Weighted Out-Degree (MICRO) ===
    ax3 = axes[2]
    ax3.set_title('MICRO: Weighted Out-Degree', fontsize=17, fontweight='bold', pad=10)

    G3 = nx.DiGraph()
    G3.add_node('C')
    G3.add_nodes_from(['T1', 'T2', 'T3', 'T4', 'T5', 'T6'])
    G3.add_edges_from([('C', 'T1'), ('C', 'T2'), ('C', 'T3'),
                       ('C', 'T4'), ('C', 'T5'), ('C', 'T6')])

    pos3 = {
        'C': (0, 0),
        'T1': (0, 1.2), 'T2': (1, 0.6), 'T3': (1, -0.6),
        'T4': (0, -1.2), 'T5': (-1, -0.6), 'T6': (-1, 0.6)
    }

    node_colors3 = [HIGH] + [LOW] * 6
    node_sizes3 = [700] + [350] * 6

    nx.draw_networkx_nodes(G3, pos3, ax=ax3, node_color=node_colors3,
                           node_size=node_sizes3, edgecolors='white', linewidths=2)
    nx.draw_networkx_edges(G3, pos3, ax=ax3, edge_color=EDGE_COLOR, width=2,
                           alpha=0.7, arrows=True, arrowsize=15,
                           connectionstyle='arc3,rad=0.1')

    ax3.text(0, -1.6, 'Total outbound trade volume',
             ha='center', va='top', fontsize=15, style='italic',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='#FFF9E6', edgecolor='#C9A227'))
    ax3.text(0, -2.2, 'e.g. CA, IL, IN',
             ha='center', va='top', fontsize=14, fontweight='bold', color='#333')

    ax3.set_xlim(-2, 2)
    ax3.set_ylim(-2.6, 1.8)
    ax3.axis('off')

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor=HIGH, edgecolor='white', label='High centrality'),
        mpatches.Patch(facecolor=EIGENVECTOR, edgecolor='white', label='High eigenvector'),
        mpatches.Patch(facecolor=LOW, edgecolor='white', label='Low/baseline'),
    ]
    fig.legend(handles=legend_elements, loc='lower center', ncol=3,
               fontsize=15, frameon=True, fancybox=True,
               bbox_to_anchor=(0.5, 0.02))

    plt.tight_layout(rect=[0, 0.08, 1, 0.95])

    # Save figure
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight', dpi=300, facecolor='white', edgecolor='none')
    plt.savefig(output_path.with_suffix('.png'), bbox_inches='tight', dpi=300, facecolor='white', edgecolor='none')

    print(f"✓ Centrality framework diagram saved to:")
    print(f"  - {output_path}")
    print(f"  - {output_path.with_suffix('.png')}")

    plt.close()
