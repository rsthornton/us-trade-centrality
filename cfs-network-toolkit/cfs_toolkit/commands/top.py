"""
cfs top - Show top N states by centrality measure.

Usage:
    cfs top                    Top 10 by eigenvector (default)
    cfs top 20                 Top 20 by eigenvector
    cfs top 10 betweenness     Top 10 by betweenness
    cfs top --run results/X    From specific run
"""

import pandas as pd
from pathlib import Path


# State abbreviation to full name mapping
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
    """Find the most recent run directory."""
    results_path = Path(results_dir)
    if not results_path.exists():
        return None

    runs = [d for d in results_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
    if not runs:
        return None

    return max(runs, key=lambda x: x.stat().st_mtime)


def load_centralities(run_dir):
    """Load centralities CSV from a run directory."""
    run_path = Path(run_dir)

    # Find the centralities file (pattern: centralities_*.csv)
    csv_files = list(run_path.glob('centralities_*.csv'))
    if not csv_files:
        return None

    return pd.read_csv(csv_files[0])


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
