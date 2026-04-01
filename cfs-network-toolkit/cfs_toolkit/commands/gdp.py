"""
cfs gdp - GDP vs centrality analysis.

Usage:
    cfs gdp                          Full GDP comparison
    cfs gdp --scatter                Just scatter plot
    cfs gdp --normalized             Just normalized bar chart
    cfs gdp --table                  Print comparison table
"""

from pathlib import Path

from cfs_toolkit.commands._utils import CANONICAL_DOMESTIC, find_latest_domestic, load_centralities


def gdp_command(args):
    """Run GDP vs centrality analysis."""
    from cfs_toolkit.analysis.gdp_comparison import (
        load_gdp_data,
        compute_gdp_vs_centrality_comparison,
        identify_outliers,
        generate_gdp_centrality_scatter,
        generate_normalized_centrality_bar,
    )

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

    # Load data
    gdp_path = Path('data/state_gdp_2017.csv')
    if not gdp_path.exists():
        print(f"GDP data not found: {gdp_path}")
        return 1

    cent_df = load_centralities(run_dir)
    if cent_df is None:
        print(f"No centralities found in: {run_dir}")
        return 1

    # Add rank column
    cent_df['rank_eigenvector'] = cent_df['eigenvector'].rank(ascending=False, method='min').astype(int)

    gdp_dict = load_gdp_data(gdp_path)
    comparison_df = compute_gdp_vs_centrality_comparison(cent_df, gdp_dict)

    print()
    print("=" * 60)
    print("  GDP VS CENTRALITY ANALYSIS")
    print("=" * 60)
    print(f"  Run: {run_dir.name}")
    print("=" * 60)

    # Summary stats
    over, under = identify_outliers(comparison_df, threshold=5)

    print(f"\n  States with ≥5 rank divergence: {len(over) + len(under)}")
    print(f"  Overperformers (centrality > GDP): {len(over)}")
    print(f"  Underperformers (centrality < GDP): {len(under)}")

    # Print table if requested or default
    if args.table or not (args.scatter or args.normalized):
        print("\n  TOP STRUCTURAL OVERPERFORMERS")
        print("  " + "─" * 50)
        print(f"  {'State':5s} {'Δ Rank':>8s} {'GDP#':>6s} {'Eig#':>6s}  Interpretation")
        print("  " + "─" * 50)

        for state, diff, gdp_rank, eig_rank, narrative in over[:5]:
            print(f"  {state:5s} {'+' + str(diff):>8s} {gdp_rank:>6d} {eig_rank:>6d}  {narrative[:40]}")

        print("\n  TOP STRUCTURAL UNDERPERFORMERS")
        print("  " + "─" * 50)
        print(f"  {'State':5s} {'Δ Rank':>8s} {'GDP#':>6s} {'Eig#':>6s}  Interpretation")
        print("  " + "─" * 50)

        for state, diff, gdp_rank, eig_rank, narrative in under[:5]:
            print(f"  {state:5s} {diff:>8d} {gdp_rank:>6d} {eig_rank:>6d}  {narrative[:40]}")

    # Generate figures
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True, parents=True)

    generate_figs = args.scatter or args.normalized or not args.table

    if generate_figs and (args.scatter or not args.normalized):
        print("\n  Generating scatter plot...")
        scatter_path = output_dir / 'gdp_vs_eigenvector_scatter.png'
        generate_gdp_centrality_scatter(comparison_df, scatter_path)

    if generate_figs and (args.normalized or not args.scatter):
        print("\n  Generating normalized bar chart...")
        bar_path = output_dir / 'gdp_normalized_centrality_bar.png'
        generate_normalized_centrality_bar(comparison_df, bar_path)

    print()
    print("=" * 60)
    if generate_figs:
        print(f"  Figures saved to: {output_dir}/")
    print("=" * 60)

    return 0


def add_gdp_parser(subparsers):
    """Add gdp subcommand to parser."""
    parser = subparsers.add_parser(
        'gdp',
        help='GDP vs centrality analysis',
        description='Analyze GDP divergence from network centrality.'
    )
    parser.add_argument(
        '--scatter',
        action='store_true',
        help='Generate scatter plot only'
    )
    parser.add_argument(
        '--normalized',
        action='store_true',
        help='Generate normalized bar chart only'
    )
    parser.add_argument(
        '--table',
        action='store_true',
        help='Print outliers table only (no figures)'
    )
    parser.add_argument(
        '--run',
        help='Run directory (default: canonical Nov 29)'
    )
    parser.add_argument(
        '--output',
        default='results/publication_figures',
        help='Output directory (default: results/publication_figures)'
    )
    parser.add_argument(
        '--results-dir',
        default='results',
        help='Results directory for auto-detection (default: results)'
    )
    parser.set_defaults(func=gdp_command)
