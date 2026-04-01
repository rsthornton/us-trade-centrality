"""
cfs network - Network structure analysis.

Usage:
    cfs network                      Full structure report
    cfs network --components         Component analysis
    cfs network --summary            Quick summary stats
"""

from pathlib import Path

from cfs_toolkit.commands._utils import CANONICAL_DOMESTIC, find_latest_domestic


def network_command(args):
    """Analyze network structure."""
    from cfs_toolkit.analysis import load_network_graph, extract_edge_weights
    import networkx as nx

    # Determine run directory
    if args.run:
        run_dir = Path(args.run)
    elif CANONICAL_DOMESTIC.exists():
        run_dir = CANONICAL_DOMESTIC
    else:
        run_dir = find_latest_domestic(args.results_dir)

    if not run_dir or not run_dir.exists():
        print("No run found. Run the pipeline first:")
        print("  python main.py")
        return 1

    # Load network
    G = load_network_graph(run_dir)

    print()
    print("=" * 60)
    print("  NETWORK STRUCTURE ANALYSIS")
    print("=" * 60)
    print(f"  Run: {run_dir.name}")
    print("=" * 60)

    # Basic stats
    print("\n  TOPOLOGY")
    print("  " + "─" * 40)
    print(f"  Nodes:       {G.number_of_nodes()}")
    print(f"  Edges:       {G.number_of_edges()}")
    print(f"  Density:     {nx.density(G):.4f}")

    # Potential edges
    n = G.number_of_nodes()
    max_edges = n * (n - 1)  # directed
    missing = max_edges - G.number_of_edges()
    print(f"  Max edges:   {max_edges}")
    print(f"  Missing:     {missing}")

    # Connectivity
    print("\n  CONNECTIVITY")
    print("  " + "─" * 40)

    n_scc = nx.number_strongly_connected_components(G)
    n_wcc = nx.number_weakly_connected_components(G)
    print(f"  Strongly CC: {n_scc}")
    print(f"  Weakly CC:   {n_wcc}")

    if n_scc == 1:
        print(f"  Status:      ✓ Fully connected (single SCC)")
    else:
        print(f"  Status:      ⚠️ {n_scc} components")

    # Path lengths (only if single component)
    if n_scc == 1:
        try:
            diameter = nx.diameter(G)
            avg_path = nx.average_shortest_path_length(G)
            print(f"\n  PATH LENGTHS")
            print("  " + "─" * 40)
            print(f"  Diameter:    {diameter}")
            print(f"  Avg path:    {avg_path:.3f}")
        except Exception:
            pass

    # Edge weight stats
    print("\n  EDGE WEIGHTS")
    print("  " + "─" * 40)

    weights = extract_edge_weights(G)
    print(f"  Min:         ${weights.min()/1e6:.0f}M")
    print(f"  Max:         ${weights.max()/1e9:.1f}B")
    print(f"  Mean:        ${weights.mean()/1e9:.2f}B")
    print(f"  Median:      ${np.median(weights)/1e6:.0f}M")
    print(f"  Total:       ${weights.sum()/1e12:.2f}T")

    # Percentiles
    print("\n  WEIGHT PERCENTILES")
    print("  " + "─" * 40)
    for p in [25, 50, 75, 90, 95, 99]:
        val = np.percentile(weights, p)
        print(f"  {p:>3d}th:       ${val/1e6:.0f}M")

    # Component analysis if requested
    if args.components and n_scc > 1:
        print("\n  COMPONENT SIZES")
        print("  " + "─" * 40)

        sccs = sorted(nx.strongly_connected_components(G), key=len, reverse=True)
        for i, scc in enumerate(sccs[:5]):
            labels = [G.nodes[n].get('label', n) for n in scc]
            print(f"  Component {i+1}: {len(scc)} nodes")
            print(f"    {', '.join(sorted(labels)[:10])}")

    # Reciprocity
    print("\n  RECIPROCITY")
    print("  " + "─" * 40)
    recip = nx.reciprocity(G)
    print(f"  Overall:     {recip:.3f} ({recip*100:.1f}%)")

    print()
    print("=" * 60)

    return 0


def add_network_parser(subparsers):
    """Add network subcommand to parser."""
    parser = subparsers.add_parser(
        'network',
        help='Network structure analysis',
        description='Analyze network structure and connectivity.'
    )
    parser.add_argument(
        '--components',
        action='store_true',
        help='Show component breakdown (if multiple SCCs)'
    )
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Quick summary only'
    )
    parser.add_argument(
        '--run',
        help='Run directory (default: canonical Nov 29)'
    )
    parser.add_argument(
        '--results-dir',
        default='results',
        help='Results directory for auto-detection (default: results)'
    )
    parser.set_defaults(func=network_command)
