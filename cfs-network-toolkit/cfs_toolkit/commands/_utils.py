"""Shared utilities for CFS CLI commands."""

import pandas as pd
from pathlib import Path

CANONICAL_DOMESTIC = Path('results/51x51_domestic')
CANONICAL_INTL = Path('results/52x52_international')

STATE_NAMES = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
    'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
    'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
    'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
    'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
    'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
    'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
    'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
    'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
    'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
    'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia',
    'RoW': 'Rest of World'
}


def find_latest_run(results_dir):
    """Find the most recently modified run directory."""
    results_path = Path(results_dir)
    if not results_path.exists():
        return None

    runs = [d for d in results_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
    if not runs:
        return None

    return max(runs, key=lambda x: x.stat().st_mtime)


def find_latest_runs(results_dir):
    """Find latest domestic and international run directories."""
    results_path = Path(results_dir)

    domestic_runs = sorted(
        [d for d in results_path.glob('51x51_domestic_*') if d.is_dir()],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    intl_runs = sorted(
        [d for d in results_path.glob('52x52_intl_*') if d.is_dir()],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    domestic = domestic_runs[0] if domestic_runs else None
    intl = intl_runs[0] if intl_runs else None

    return domestic, intl


def find_latest_runs_excluding_canonical(results_dir):
    """Find latest runs, skipping canonical directories (for verify)."""
    results_path = Path(results_dir)

    domestic_runs = sorted(
        [d for d in results_path.glob('51x51_domestic_*') if d.is_dir()],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    intl_runs = sorted(
        [d for d in results_path.glob('52x52_intl_*') if d.is_dir()],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    domestic = None
    for run in domestic_runs:
        if run != CANONICAL_DOMESTIC:
            domestic = run
            break

    intl = None
    for run in intl_runs:
        if run != CANONICAL_INTL:
            intl = run
            break

    return domestic, intl


def find_latest_domestic(results_dir):
    """Find latest domestic run directory."""
    results_path = Path(results_dir)

    domestic_runs = sorted(
        [d for d in results_path.glob('51x51_domestic_*') if d.is_dir()],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    return domestic_runs[0] if domestic_runs else None


def load_centralities(run_dir):
    """Load centralities CSV from a run directory."""
    csv_files = list(Path(run_dir).glob('centralities_*.csv'))
    if not csv_files:
        return None
    return pd.read_csv(csv_files[0])
