#!/usr/bin/env python3
"""
Data setup verification for us-trade-centrality.

Checks that required data files are present and valid before running the pipeline.
Run this after downloading the CFS and FAF5 datasets (see data/README.md).
"""

import sys
from pathlib import Path

# Expected data files relative to repo root
REQUIRED = {
    "data/cfs_2017_puf.csv": {
        "description": "CFS 2017 Public Use File (primary dataset)",
        "required": True,
        "expected_columns": ["ORIG_STATE", "DEST_STATE", "SHIPMT_VALUE", "WGT_FACTOR", "SCTG"],
        "expected_min_rows": 5_900_000,  # PUF has 5,978,523 records
    },
}

OPTIONAL = {
    "data/FAF5.7.1_State.csv": {
        "description": "FAF 5.7.1 State-Level Data (for 52×52 international network)",
        "required": False,
    },
}

INCLUDED = {
    "data/state_gdp_2017.csv": "State GDP 2017",
    "data/state_population_2017.csv": "State population 2017",
}


def check_file(repo_root, rel_path, info, verbose=True):
    """Check if a data file exists and optionally validate structure."""
    path = repo_root / rel_path
    if not path.exists():
        return False, f"MISSING: {rel_path}"

    size_mb = path.stat().st_size / (1024 * 1024)

    # Basic row count check for CSV
    if "expected_min_rows" in info:
        try:
            with open(path) as f:
                row_count = sum(1 for _ in f) - 1  # subtract header
            if row_count < info["expected_min_rows"]:
                return False, f"LOW ROW COUNT: {rel_path} has {row_count:,} rows (expected ≥{info['expected_min_rows']:,})"
            if verbose:
                return True, f"OK: {rel_path} ({size_mb:.0f} MB, {row_count:,} records)"
        except Exception as e:
            return True, f"OK: {rel_path} ({size_mb:.0f} MB, could not count rows: {e})"

    return True, f"OK: {rel_path} ({size_mb:.0f} MB)"


def main():
    # Find repo root (parent of scripts/)
    repo_root = Path(__file__).resolve().parent.parent

    print(f"Checking data setup for: {repo_root}\n")

    all_ok = True
    missing_required = False

    # Check included files
    print("Included files (redistributable):")
    for rel_path, desc in INCLUDED.items():
        path = repo_root / rel_path
        if path.exists():
            print(f"  ✓ {rel_path} — {desc}")
        else:
            print(f"  ✗ {rel_path} — {desc} (MISSING)")
            all_ok = False

    # Check required files
    print("\nRequired files (must download):")
    for rel_path, info in REQUIRED.items():
        ok, msg = check_file(repo_root, rel_path, info)
        print(f"  {'✓' if ok else '✗'} {msg}")
        if not ok:
            print(f"    → {info['description']}")
            print(f"    → See data/README.md for download instructions")
            all_ok = False
            missing_required = True

    # Check optional files
    print("\nOptional files:")
    for rel_path, info in OPTIONAL.items():
        path = repo_root / rel_path
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            print(f"  ✓ {rel_path} ({size_mb:.0f} MB)")
        else:
            print(f"  ○ {rel_path} — not present (only needed for 52×52 international runs)")

    # Check toolkit installation
    print("\nToolkit:")
    try:
        import cfs_toolkit
        print(f"  ✓ cfs-network-toolkit installed")
    except ImportError:
        print(f"  ✗ cfs-network-toolkit not installed")
        print(f"    → Run: pip install -e cfs-network-toolkit/")
        all_ok = False

    # Summary
    print()
    if missing_required:
        print("✗ Required data files missing. See data/README.md for download instructions.")
        sys.exit(1)
    elif all_ok:
        print("✓ All data files present. Ready to run: python main.py")
        sys.exit(0)
    else:
        print("⚠ Some optional components missing (see above). Core pipeline can still run.")
        sys.exit(0)


if __name__ == "__main__":
    main()
