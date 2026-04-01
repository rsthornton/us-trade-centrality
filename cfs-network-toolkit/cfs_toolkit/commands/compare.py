"""
cfs compare - Compare 51x51 vs 52x52 network results.

Usage:
    cfs compare                      Compare latest domestic vs international
    cfs compare run1 run2            Compare specific runs
    cfs compare --format table       Output as markdown table
"""

from pathlib import Path

from cfs_toolkit.commands._utils import (
    CANONICAL_DOMESTIC, CANONICAL_INTL, find_latest_runs, load_centralities,
)


def compare_command(args):
    """Compare two network analysis runs."""
    from cfs_toolkit.analysis.comparison_utils import (
        align_measures,
        compute_rank_correlations,
        compute_rank_changes,
        compute_topk_overlap,
        summarize_effect_sizes,
    )

    # Determine run directories
    if args.run1 and args.run2:
        run1 = Path(args.run1)
        run2 = Path(args.run2)
    elif CANONICAL_DOMESTIC.exists() and CANONICAL_INTL.exists():
        run1 = CANONICAL_DOMESTIC
        run2 = CANONICAL_INTL
    else:
        run1, run2 = find_latest_runs(args.results_dir)

    if not run1 or not run1.exists():
        print("No first run found. Run the pipeline first:")
        print("  python main.py")
        return 1

    if not run2 or not run2.exists():
        print("No second run found. Run:")
        print("  python main.py --international")
        return 1

    # Load centralities
    df1 = load_centralities(run1)
    df2 = load_centralities(run2)

    if df1 is None or df2 is None:
        print("Could not load centrality data from runs")
        return 1

    # Exclude RoW from comparison
    df2 = df2[df2['label'] != 'RoW'].copy()

    measures = ['betweenness', 'eigenvector', 'out_degree']

    print()
    print("=" * 60)
    print("  NETWORK COMPARISON: 51×51 vs 52×52")
    print("=" * 60)
    print(f"  Run 1: {run1.name}")
    print(f"  Run 2: {run2.name}")
    print("=" * 60)

    # Rank correlations
    print("\n  RANK CORRELATIONS")
    print("  " + "─" * 40)
    correlations = compute_rank_correlations(df1, df2, measures)

    for measure in measures:
        rho = correlations[measure]['spearman']
        tau = correlations[measure]['kendall']
        print(f"  {measure:12s}  ρ = {rho:.4f}  τ = {tau:.4f}")

    # Rank changes
    print("\n  RANK CHANGE SUMMARY")
    print("  " + "─" * 40)
    rank_changes = compute_rank_changes(df1, df2, measures)
    effect_sizes = summarize_effect_sizes(rank_changes)

    for measure in measures:
        stats = effect_sizes[measure]
        pct_changed = stats['states_changed'] / stats['total_states'] * 100
        print(f"  {measure:12s}  {stats['states_changed']}/{stats['total_states']} changed ({pct_changed:.0f}%)")
        print(f"               mean: {stats['mean_abs_change']:.1f}, max: {stats['max_abs_change']}")

    # Top-k overlap
    print("\n  TOP-K OVERLAP (Jaccard)")
    print("  " + "─" * 40)
    overlaps = compute_topk_overlap(df1, df2, measures, ks=[5, 10])

    header = f"  {'Measure':12s}  {'Top-5':>8s}  {'Top-10':>8s}"
    print(header)
    for measure in measures:
        j5 = overlaps[measure][5]['jaccard']
        j10 = overlaps[measure][10]['jaccard']
        print(f"  {measure:12s}  {j5:>8.2%}  {j10:>8.2%}")

    # Top movers
    print("\n  TOP RANK CHANGES")
    print("  " + "─" * 40)

    for measure in measures:
        measure_changes = rank_changes[rank_changes['measure'] == measure].copy()
        measure_changes = measure_changes.sort_values('abs_delta_rank', ascending=False)
        top_movers = measure_changes.head(3)

        print(f"  {measure}:")
        for _, row in top_movers.iterrows():
            direction = "↑" if row['delta_rank'] < 0 else "↓"
            print(f"    {row['label']:3s} {direction}{abs(int(row['delta_rank'])):<2d} (#{int(row['rank_51'])} → #{int(row['rank_52'])})")

    print()
    print("=" * 60)

    return 0


def add_compare_parser(subparsers):
    """Add compare subcommand to parser."""
    parser = subparsers.add_parser(
        'compare',
        help='Compare 51x51 vs 52x52 results',
        description='Compare centrality rankings between two network analysis runs.'
    )
    parser.add_argument(
        'run1',
        nargs='?',
        help='First run directory (default: latest domestic)'
    )
    parser.add_argument(
        'run2',
        nargs='?',
        help='Second run directory (default: latest international)'
    )
    parser.add_argument(
        '--format',
        choices=['text', 'table', 'json'],
        default='text',
        help='Output format (default: text)'
    )
    parser.add_argument(
        '--results-dir',
        default='results',
        help='Results directory for auto-detection (default: results)'
    )
    parser.set_defaults(func=compare_command)
