"""
cfs ls - List available runs.

Usage:
    cfs ls              List all runs
    cfs ls --details    Include node/edge counts
"""

from pathlib import Path


def ls_command(args):
    """List available pipeline runs."""
    results_dir = Path(args.results_dir)

    if not results_dir.exists():
        print(f"No results directory found at: {results_dir}")
        return 1

    runs = sorted(
        [d for d in results_dir.iterdir() if d.is_dir() and not d.name.startswith('.')],
        key=lambda x: x.stat().st_mtime,
        reverse=True  # Most recent first
    )

    if not runs:
        print("No runs found in results/")
        return 0

    # Find the latest run (by modification time)
    latest = runs[0]

    print("\nAVAILABLE RUNS")
    print("──────────────")

    for run in runs:
        marker = "* " if run == latest else "  "
        label = "(latest)" if run == latest else ""
        print(f"{marker}{run.name}   {label}")

    print(f"\nUse: cfs top --run <name>")
    return 0


def add_ls_parser(subparsers):
    """Add ls subcommand to parser."""
    parser = subparsers.add_parser(
        'ls',
        help='List available runs',
        description='List all pipeline runs in the results directory.'
    )
    parser.add_argument(
        '--results-dir',
        default='results',
        help='Results directory (default: results)'
    )
    parser.add_argument(
        '--details',
        action='store_true',
        help='Show node/edge counts for each run'
    )
    parser.set_defaults(func=ls_command)
