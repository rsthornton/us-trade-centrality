"""
cfs verify - Verify reproducibility against canonical runs.

Usage:
    cfs verify                       Compare latest run vs canonical Nov 29
    cfs verify --run X               Compare specific run
"""

import numpy as np
from pathlib import Path

from cfs_toolkit.commands._utils import (
    CANONICAL_DOMESTIC, CANONICAL_INTL,
    find_latest_runs_excluding_canonical as find_latest_runs,
    load_centralities,
)


def verify_command(args):
    """Verify reproducibility against canonical runs."""
    # Determine what to verify
    if args.run:
        test_run = Path(args.run)
        # Detect type from name
        if '52x52' in test_run.name or 'intl' in test_run.name:
            canonical = CANONICAL_INTL
            network_type = "52x52"
        else:
            canonical = CANONICAL_DOMESTIC
            network_type = "51x51"
        test_runs = [(test_run, canonical, network_type)]
    else:
        domestic, intl = find_latest_runs(args.results_dir)
        test_runs = []
        if domestic:
            test_runs.append((domestic, CANONICAL_DOMESTIC, "51x51"))
        if intl:
            test_runs.append((intl, CANONICAL_INTL, "52x52"))

    if not test_runs:
        print("No runs to verify. Run the pipeline first:")
        print("  python main.py")
        return 1

    print()
    print("=" * 60)
    print("  REPRODUCIBILITY VERIFICATION")
    print("=" * 60)

    all_passed = True
    measures = ['betweenness', 'eigenvector', 'out_degree']

    for test_run, canonical, network_type in test_runs:
        print(f"\n  {network_type} Network")
        print("  " + "─" * 50)
        print(f"  Test:      {test_run.name}")
        print(f"  Canonical: {canonical.name}")

        if not canonical.exists():
            print(f"  ⚠️  Canonical run not found!")
            all_passed = False
            continue

        if not test_run.exists():
            print(f"  ⚠️  Test run not found!")
            all_passed = False
            continue

        # Load centralities
        df_test = load_centralities(test_run)
        df_canonical = load_centralities(canonical)

        if df_test is None or df_canonical is None:
            print(f"  ⚠️  Could not load centrality data!")
            all_passed = False
            continue

        # Merge on state
        merged = df_test.merge(
            df_canonical,
            on='label',
            suffixes=('_test', '_canonical')
        )

        print()
        print(f"  {'Measure':12s} {'Max Diff':>12s} {'Status':>10s}")
        print("  " + "─" * 38)

        for measure in measures:
            col_test = f"{measure}_test"
            col_canonical = f"{measure}_canonical"

            if col_test not in merged.columns or col_canonical not in merged.columns:
                print(f"  {measure:12s} {'N/A':>12s} {'MISSING':>10s}")
                all_passed = False
                continue

            diff = (merged[col_test] - merged[col_canonical]).abs()
            max_diff = diff.max()

            # Machine precision tolerance
            if max_diff < 1e-10:
                status = "✓ EXACT"
            elif max_diff < 1e-6:
                status = "~ CLOSE"
            else:
                status = "✗ DIFF"
                all_passed = False

            print(f"  {measure:12s} {max_diff:>12.2e} {status:>10s}")

    print()
    print("=" * 60)
    if all_passed:
        print("  RESULT: ✓ PASSED - All measures match canonical runs")
    else:
        print("  RESULT: ✗ FAILED - Some measures differ from canonical")
    print("=" * 60)
    print()

    return 0 if all_passed else 1


def add_verify_parser(subparsers):
    """Add verify subcommand to parser."""
    parser = subparsers.add_parser(
        'verify',
        help='Verify reproducibility',
        description='Verify that current results match canonical Nov 29 runs.'
    )
    parser.add_argument(
        '--run',
        help='Specific run to verify (default: latest non-canonical)'
    )
    parser.add_argument(
        '--results-dir',
        default='results',
        help='Results directory (default: results)'
    )
    parser.set_defaults(func=verify_command)
