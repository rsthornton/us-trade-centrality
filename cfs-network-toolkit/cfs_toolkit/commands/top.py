"""
cfs top - Show top N states by centrality measure.

Usage:
    cfs top                    Top 10 by eigenvector (default)
    cfs top 20                 Top 20 by eigenvector
    cfs top 10 betweenness     Top 10 by betweenness
    cfs top --run results/X    From specific run
"""

from pathlib import Path

from cfs_toolkit.commands._utils import STATE_NAMES, find_latest_run, load_centralities


def top_command(args):
    """Show top N states by centrality measure."""
    # Determine run directory
    if args.run:
        run_dir = Path(args.run)
    else:
        run_dir = find_latest_run(args.results_dir)

    if not run_dir or not run_dir.exists():
        print("No run directory found. Run the pipeline first:")
        print("  python main.py")
        return 1

    # Load centralities
    df = load_centralities(run_dir)
    if df is None:
        print(f"No centralities file found in: {run_dir}")
        return 1

    # Validate measure
    measure = args.measure
    if measure not in df.columns:
        available = [c for c in df.columns if c not in ['state_id', 'label']]
        print(f"Unknown measure: {measure}")
        print(f"Available: {', '.join(available)}")
        return 1

    # Get top N
    n = args.n
    top_df = df.nlargest(n, measure)[['label', measure]]

    # Determine network type from run name
    run_name = run_dir.name
    network_type = "52x52 international" if "52x52" in run_name or "intl" in run_name else "51x51 domestic"

    # Print formatted output
    print(f"\nTOP {n} BY {measure.upper()} ({network_type})")
    print("─" * 38)

    for i, (_, row) in enumerate(top_df.iterrows(), 1):
        label = row['label']
        value = row[measure]
        full_name = STATE_NAMES.get(label, label)
        print(f"#{i:>2}  {label:<4} {value:.3f}   {full_name}")

    print()
    return 0


def add_top_parser(subparsers):
    """Add top subcommand to parser."""
    parser = subparsers.add_parser(
        'top',
        help='Show top N states by centrality',
        description='Display top-ranked states by a centrality measure.'
    )
    parser.add_argument(
        'n',
        type=int,
        nargs='?',
        default=10,
        help='Number of states to show (default: 10)'
    )
    parser.add_argument(
        'measure',
        nargs='?',
        default='eigenvector',
        help='Centrality measure: eigenvector, betweenness, out_degree (default: eigenvector)'
    )
    parser.add_argument(
        '--run',
        help='Run directory (default: latest run)'
    )
    parser.add_argument(
        '--results-dir',
        default='results',
        help='Results directory (default: results)'
    )
    parser.set_defaults(func=top_command)
