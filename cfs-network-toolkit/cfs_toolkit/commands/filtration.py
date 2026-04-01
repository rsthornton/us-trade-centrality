"""
cfs filtration - Edge weight filtration analysis.

Usage:
    cfs filtration --search          Find connectivity breaking point
    cfs filtration --percentile 33   Run at specific threshold
    cfs filtration --sweep 10 50 5   Sweep from 10% to 50% by 5%
"""

from pathlib import Path

from cfs_toolkit.commands._utils import CANONICAL_DOMESTIC, find_latest_domestic


def filtration_command(args):
    """Run filtration analysis."""
    from cfs_toolkit.analysis import load_network_graph
    from cfs_toolkit.analysis.filtration import (
        filter_graph_by_percentile,
        find_connectivity_breaking_point,
    )
    from cfs_toolkit.core.centralities import compute_all_centralities
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
    print()
    print("=" * 60)
    print("  FILTRATION ANALYSIS")
    print("=" * 60)
    print(f"  Run: {run_dir.name}")
    print("=" * 60)

    G = load_network_graph(run_dir)
    print(f"\n  Network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # Binary search for breaking point
    if args.search:
        print("\n  CONNECTIVITY BREAKING POINT SEARCH")
        print("  " + "─" * 45)

        result = find_connectivity_breaking_point(G)
        print(f"\n  RESULT:")
        print(f"  Breaking point: {result['breaking_pct']}%")
        print(f"  Breaking threshold: ${result['breaking_threshold']/1e6:.0f}M")
        print(f"  Max safe percentile: {result['max_connected_pct']}%")
        print(f"  Max safe threshold: ${result['max_connected_threshold']/1e6:.0f}M")

    # Run at specific percentile
    if args.percentile:
        print(f"\n  FILTRATION AT {args.percentile}%")
        print("  " + "─" * 45)

        G_filtered, stats = filter_graph_by_percentile(G, args.percentile)

        print(f"  Edges before: {stats['edges_before']}")
        print(f"  Edges after:  {stats['edges_after']}")
        print(f"  Removed:      {stats['edges_removed']} ({stats['pct_removed']:.1f}%)")
        print(f"  Threshold:    ${stats['threshold']/1e6:.0f}M")

        n_scc = nx.number_strongly_connected_components(G_filtered)
        if n_scc == 1:
            print(f"  Connectivity: ✓ Single SCC maintained")
        else:
            print(f"  Connectivity: ⚠️ {n_scc} SCCs (network fragmented)")

        # Compute centralities on filtered graph
        cent_df = compute_all_centralities(G_filtered)

        print("\n  Top 5 by betweenness (filtered):")
        top5 = cent_df.nlargest(5, 'betweenness')[['label', 'betweenness', 'eigenvector']]
        for _, row in top5.iterrows():
            print(f"    {row['label']}: bet={row['betweenness']:.3f}, eig={row['eigenvector']:.3f}")

    # Sweep across percentiles
    if args.sweep:
        start, end, step = args.sweep
        print(f"\n  FILTRATION SWEEP ({start}% to {end}% by {step}%)")
        print("  " + "─" * 45)

        print(f"\n  {'%ile':>5s} {'Threshold':>12s} {'Edges':>8s} {'SCCs':>6s}")
        print("  " + "─" * 35)

        for pct in range(int(start), int(end) + 1, int(step)):
            G_filtered, stats = filter_graph_by_percentile(G, pct)
            n_scc = nx.number_strongly_connected_components(G_filtered)
            threshold_m = stats['threshold'] / 1e6

            scc_marker = "✓" if n_scc == 1 else f"⚠️ {n_scc}"
            print(f"  {pct:>5.0f} ${threshold_m:>10.0f}M {stats['edges_after']:>8d} {scc_marker:>6s}")

    print()
    print("=" * 60)

    return 0


def add_filtration_parser(subparsers):
    """Add filtration subcommand to parser."""
    parser = subparsers.add_parser(
        'filtration',
        help='Edge weight filtration analysis',
        description='Analyze network robustness under edge weight filtration.'
    )
    parser.add_argument(
        '--search',
        action='store_true',
        help='Find connectivity breaking point via binary search'
    )
    parser.add_argument(
        '--percentile',
        type=float,
        metavar='N',
        help='Filter at Nth percentile threshold'
    )
    parser.add_argument(
        '--sweep',
        nargs=3,
        type=float,
        metavar=('START', 'END', 'STEP'),
        help='Sweep from START to END by STEP percentile'
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
    parser.set_defaults(func=filtration_command)
