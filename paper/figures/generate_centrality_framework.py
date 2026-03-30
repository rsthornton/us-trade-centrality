"""
Generate three-panel centrality framework figure for thesis.
Replaces incorrect D.C. example with Texas for betweenness.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import numpy as np

# Set up figure
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle('Three-Level Centrality Framework (Adapted from Jang & Yang 2023)',
             fontsize=14, fontweight='bold', y=0.98)

# Colors
HIGH = '#D64541'      # Red - high centrality / important nodes
EIGENVECTOR = '#27AE60'  # Green - high eigenvector (connected to important)
MEDIUM = '#F39C12'    # Orange - medium centrality
LOW = '#BDC3C7'       # Gray - low/baseline
EDGE_COLOR = '#2C3E50'  # Dark blue-gray for edges

# =============================================================================
# Panel 1: Betweenness Centrality (MACRO)
# =============================================================================
ax1 = axes[0]
ax1.set_title('MACRO: Betweenness Centrality', fontsize=12, fontweight='bold', pad=10)

G1 = nx.Graph()
# Left cluster - compact, far left
G1.add_nodes_from(['L1', 'L2', 'L3'])
G1.add_edges_from([('L1', 'L2'), ('L2', 'L3'), ('L1', 'L3')])
# Right cluster - compact, far right
G1.add_nodes_from(['R1', 'R2', 'R3'])
G1.add_edges_from([('R1', 'R2'), ('R2', 'R3'), ('R1', 'R3')])
# Bridge node - CLEARLY in center with long edges to each cluster
G1.add_node('B')
G1.add_edges_from([('L1', 'B'), ('B', 'R1')])

# Symmetric layout: clusters far apart, bridge dead center
pos1 = {
    'L1': (-1.5, 0), 'L2': (-1.9, 0.5), 'L3': (-1.9, -0.5),  # Left cluster
    'B': (0, 0),  # BRIDGE - dead center
    'R1': (1.5, 0), 'R2': (1.9, 0.5), 'R3': (1.9, -0.5)  # Right cluster
}

node_colors1 = [LOW, LOW, LOW, LOW, LOW, LOW, HIGH]  # B is index 6 (last added)
node_sizes1 = [400, 400, 400, 400, 400, 400, 700]

nx.draw_networkx_nodes(G1, pos1, ax=ax1, node_color=node_colors1,
                       node_size=node_sizes1, edgecolors='white', linewidths=2)
nx.draw_networkx_edges(G1, pos1, ax=ax1, edge_color=EDGE_COLOR, width=2, alpha=0.7)

ax1.text(0, -1.1, '"Which states bridge\nregional clusters?"',
         ha='center', va='top', fontsize=9, style='italic',
         bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFF9E6', edgecolor='#E6D9A6'))
ax1.text(0, -1.7, 'High betweenness node connects\notherwise disconnected regions',
         ha='center', va='top', fontsize=8, color='#555')
ax1.text(0, -2.2, 'Example: Texas, Pennsylvania, Washington',
         ha='center', va='top', fontsize=9, fontweight='bold',
         bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFF9E6', edgecolor='#C9A227'))

ax1.set_xlim(-2.2, 2.2)
ax1.set_ylim(-2.6, 1.2)
ax1.axis('off')

# =============================================================================
# Panel 2: Eigenvector Centrality (MESO)
# =============================================================================
ax2 = axes[1]
ax2.set_title('MESO: Eigenvector Centrality', fontsize=12, fontweight='bold', pad=10)

G2 = nx.Graph()
# Jang & Yang style: Central node A connected to hub nodes, each hub has spokes
# Central HIGH node (red) - important because connected to important nodes
G2.add_node('A')
# Hub nodes (orange) - important nodes that A connects to, each with their own connections
G2.add_nodes_from(['H1', 'H2', 'H3', 'H4'])
G2.add_edges_from([('A', 'H1'), ('A', 'H2'), ('A', 'H3'), ('A', 'H4')])
# Spokes from each hub (gray) - shows the hubs are themselves well-connected
G2.add_nodes_from(['S1', 'S2', 'S3', 'S4', 'S5', 'S6'])
G2.add_edges_from([('H1', 'S1'), ('H1', 'S2'),  # H1's spokes
                   ('H2', 'S3'),  # H2's spoke
                   ('H3', 'S4'), ('H3', 'S5'),  # H3's spokes
                   ('H4', 'S6')])  # H4's spoke

# Layout inspired by Jang & Yang Figure 3
pos2 = {
    'A': (0, 0),  # Central node
    'H1': (-0.8, 0.6), 'H2': (0.7, 0.7), 'H3': (0.6, -0.5), 'H4': (-0.6, -0.6),  # Hubs around A
    'S1': (-1.4, 0.9), 'S2': (-1.3, 0.2),  # H1's spokes
    'S3': (1.3, 0.5),  # H2's spoke
    'S4': (1.2, -0.3), 'S5': (0.8, -1.1),  # H3's spokes
    'S6': (-1.2, -0.9)  # H4's spoke
}

# A = EIGENVECTOR (green - high eigenvector); H1-H4 = HIGH (red - important nodes); S1-S6 = LOW (gray)
node_colors2 = [EIGENVECTOR, HIGH, HIGH, HIGH, HIGH, LOW, LOW, LOW, LOW, LOW, LOW]
node_sizes2 = [700, 500, 500, 500, 500, 300, 300, 300, 300, 300, 300]

nx.draw_networkx_nodes(G2, pos2, ax=ax2, node_color=node_colors2,
                       node_size=node_sizes2, edgecolors='white', linewidths=2)
nx.draw_networkx_edges(G2, pos2, ax=ax2, edge_color=EDGE_COLOR, width=2, alpha=0.7)

ax2.text(0, -1.7, '"Which states trade\nwith powerhouses?"',
         ha='center', va='top', fontsize=9, style='italic',
         bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFF9E6', edgecolor='#E6D9A6'))
ax2.text(0, -2.25, 'High eigenvector node connected\nto other important nodes',
         ha='center', va='top', fontsize=8, color='#555')
ax2.text(0, -2.75, 'Example: Texas, Ohio, Florida',
         ha='center', va='top', fontsize=9, fontweight='bold',
         bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFF9E6', edgecolor='#C9A227'))

ax2.set_xlim(-2, 2)
ax2.set_ylim(-3.2, 1.8)
ax2.axis('off')

# =============================================================================
# Panel 3: Weighted Out-Degree (MICRO)
# =============================================================================
ax3 = axes[2]
ax3.set_title('MICRO: Weighted Out-Degree', fontsize=12, fontweight='bold', pad=10)

G3 = nx.DiGraph()
# Central high out-degree node
G3.add_node('C')
# Peripheral nodes receiving from center
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

ax3.text(0, -1.8, '"Which states have\nhighest production capacity?"',
         ha='center', va='top', fontsize=9, style='italic',
         bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFF9E6', edgecolor='#E6D9A6'))
ax3.text(0, -2.35, 'High out-degree node distributes\nlarge volumes to many destinations',
         ha='center', va='top', fontsize=8, color='#555')
ax3.text(0, -2.85, 'Example: California, Illinois, Indiana',
         ha='center', va='top', fontsize=9, fontweight='bold',
         bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFF9E6', edgecolor='#C9A227'))

ax3.set_xlim(-2, 2)
ax3.set_ylim(-3.2, 1.8)
ax3.axis('off')

# =============================================================================
# Legend
# =============================================================================
legend_elements = [
    mpatches.Patch(facecolor=HIGH, edgecolor='white', label='High centrality'),
    mpatches.Patch(facecolor=EIGENVECTOR, edgecolor='white', label='High eigenvector'),
    mpatches.Patch(facecolor=LOW, edgecolor='white', label='Low/baseline'),
]
fig.legend(handles=legend_elements, loc='lower center', ncol=3,
           fontsize=10, frameon=True, fancybox=True,
           bbox_to_anchor=(0.5, 0.02))

plt.tight_layout(rect=[0, 0.08, 1, 0.95])
plt.savefig('paper/figures/centrality_framework_v2.png',
            dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
plt.savefig('paper/figures/centrality_framework_v2.pdf',
            bbox_inches='tight', facecolor='white', edgecolor='none')
print("Saved: centrality_framework_v2.png and centrality_framework_v2.pdf")
plt.show()
