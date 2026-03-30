"""
Main Pipeline Orchestrator
==========================
Minimal core pipeline for interstate commerce network analysis.

Usage:
    python main.py                           # Default (domestic, unfiltered)
    python main.py --international           # 52x52 with RoW
    python main.py --filtration 33           # Filter at 33% percentile
    python main.py --full                    # Full artifacts (summaries, reports)
    python main.py --config configs/X.yaml   # Custom configuration

Core Outputs (default):
    results/run_YYYYMMDD_HHMMSS/
    ├── network_*.gpickle      # The graph
    ├── centralities_*.csv     # The scores
    └── run_config.yaml        # What was run

On-Demand Generation:
    python -m cfs_toolkit.figures results/run_X/      # Figures
    python -m cfs_toolkit.compare results/A results/B  # Comparisons
"""

import argparse
import yaml
import sys
from pathlib import Path


def load_config(config_path):
    """Load configuration from YAML file."""
    config_file = Path(config_path)
    if not config_file.exists():
        print(f"Error: Config file {config_path} not found")
        sys.exit(1)

    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    return config


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Run interstate commerce network analysis pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                         # Quick domestic run
  python main.py --international         # Include international flows
  python main.py --filtration 33         # Filter weak edges (33rd percentile)
  python main.py --sample 5000           # Test with sample data
  python main.py --full                  # Generate all artifacts
        """
    )

    parser.add_argument(
        '--config',
        default='configs/domestic.yaml',
        help='Path to configuration file (default: configs/domestic.yaml)'
    )

    parser.add_argument(
        '--sample',
        type=int,
        help='Sample size for testing (overrides config file)'
    )

    parser.add_argument(
        '--international',
        action='store_true',
        help='Include international flows (52x52 matrix)'
    )

    parser.add_argument(
        '--filtration',
        type=float,
        metavar='N',
        help='Filter edges below Nth percentile (e.g., 33 for maximum single-SCC)'
    )

    parser.add_argument(
        '--full',
        action='store_true',
        help='Generate full artifacts (summaries, top flows, comparisons)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    return parser.parse_args()


def main():
    """
    Run interstate commerce network analysis.

    Default: minimal core outputs (network, centralities, config).
    Use --full for comprehensive artifacts.
    """

    # Parse arguments and load config
    args = parse_arguments()
    config = load_config(args.config)
    verbose = args.verbose or config['output'].get('verbose', False)

    # Apply CLI overrides
    if args.sample:
        config['data']['sample_size'] = args.sample
    if args.international:
        config['network']['include_international'] = True
    if args.filtration is not None:
        config['network']['filtration'] = {
            'enabled': True,
            'percentile': args.filtration,
            'verify_connectivity': True
        }

    network_type = "52x52" if config['network']['include_international'] else "51x51"
    print(f"\n{'='*50}")
    print(f"Pipeline: {network_type} network analysis")
    print(f"{'='*50}")

    # Step 1: Load Data
    print("\n[1/5] Loading data...")
    from cfs_toolkit.core.data_loader import load_data

    df_raw = load_data(config)
    print(f"      Loaded {len(df_raw):,} records")

    # Step 2: Preprocess
    print("\n[2/5] Preprocessing...")
    from cfs_toolkit.core.preprocessor import (
        preprocess_cfs_data, aggregate_cfs_to_edges,
        preprocess_faf_edges, combine_domestic_international_edges
    )

    if config['data']['source'] == 'cfs':
        df_clean = preprocess_cfs_data(
            df_raw,
            interstate_only=config['network']['interstate_only']
        )
        edges = aggregate_cfs_to_edges(df_clean)
    else:
        edges = preprocess_faf_edges(df_raw)

    print(f"      {len(edges):,} edges")

    # Handle international (52x52)
    if config['network']['include_international']:
        from cfs_toolkit.core.faf_loader import load_faf5_international_edges

        faf_edges = load_faf5_international_edges(
            config['data']['faf_path'],
            year=config['data'].get('year', 2017)
        )
        edges = combine_domestic_international_edges(edges, faf_edges)
        print(f"      + international → {len(edges):,} total edges")

    # Step 3: Build Network
    print("\n[3/5] Building network...")
    from cfs_toolkit.core.network_builder import build_trade_network
    from cfs_toolkit.core.validators import validate_network_structure

    G = build_trade_network(edges, node_labels=True, validate_edges=True)
    validation = validate_network_structure(G)

    if not validation['is_valid']:
        raise ValueError(f"Network validation failed: {validation['issues']}")

    print(f"      {G.number_of_nodes()} nodes, {G.number_of_edges():,} edges")

    # Step 4: Optional Filtration
    filtration_config = config['network'].get('filtration', {})
    if filtration_config.get('enabled', False):
        print("\n[3.5] Applying filtration...")
        import numpy as np
        import networkx as nx
        from cfs_toolkit.core.centralities import filter_graph_by_threshold

        percentile = filtration_config.get('percentile', 33)
        weights = [d['weight'] for _, _, d in G.edges(data=True)]
        threshold = np.percentile(weights, percentile)

        edges_before = G.number_of_edges()
        G = filter_graph_by_threshold(G, threshold)
        edges_after = G.number_of_edges()

        print(f"      {percentile}th percentile: ${threshold/1e6:.0f}M threshold")
        print(f"      {edges_before - edges_after:,} edges removed → {edges_after:,} remaining")

        if filtration_config.get('verify_connectivity', True):
            n_scc = nx.number_strongly_connected_components(G)
            if n_scc > 1:
                raise ValueError(f"Filtration broke connectivity: {n_scc} SCCs. Lower percentile.")
            print(f"      ✓ Single SCC maintained")

    # Step 5: Compute Centralities
    print("\n[4/5] Computing centralities...")
    from cfs_toolkit.core.centralities import compute_all_centralities

    centralities_df = compute_all_centralities(G)
    print(f"      {len(centralities_df)} nodes scored")

    if verbose:
        top = centralities_df.nlargest(5, 'betweenness')[['label', 'betweenness', 'eigenvector']]
        print("\n      Top 5 by betweenness:")
        for _, row in top.iterrows():
            print(f"        {row['label']}: bet={row['betweenness']:.3f}, eig={row['eigenvector']:.3f}")

    # Step 6: Save Artifacts
    print("\n[5/5] Saving artifacts...")

    if args.full:
        # Full artifacts mode
        from cfs_toolkit.core.artifacts import save_pipeline_artifacts

        artifacts_info = save_pipeline_artifacts(
            config=config,
            G=G,
            centralities_df=centralities_df,
            edges=edges,
            comparative_results=None  # Comparisons now handled separately
        )
        print(f"      Full artifacts: {artifacts_info['artifact_count']} files")
    else:
        # Minimal core outputs (default)
        from cfs_toolkit.core.artifacts import save_core_artifacts

        artifacts_info = save_core_artifacts(
            config=config,
            G=G,
            centralities_df=centralities_df
        )
        print(f"      Core artifacts: {artifacts_info['artifact_count']} files")

    # Enhanced Summary Output
    network_label = "INTERNATIONAL" if config['network']['include_international'] else "DOMESTIC"
    print(f"\n{'='*50}")
    print(f"  {network_type} {network_label} | {G.number_of_nodes()} nodes, {G.number_of_edges():,} edges")
    print(f"{'='*50}")

    # Top 5 by betweenness and eigenvector (side by side)
    top_bet = centralities_df.nlargest(5, 'betweenness')[['label', 'betweenness']].values
    top_eig = centralities_df.nlargest(5, 'eigenvector')[['label', 'eigenvector']].values

    print()
    print("  TOP 5 BETWEENNESS          TOP 5 EIGENVECTOR")
    print("  ─────────────────          ─────────────────")
    for i in range(5):
        bet_label, bet_val = top_bet[i]
        eig_label, eig_val = top_eig[i]
        print(f"  #{i+1:<2} {bet_label:<3} {bet_val:.3f}              #{i+1:<2} {eig_label:<3} {eig_val:.3f}")

    print()
    print(f"  Output: {artifacts_info['run_dir']}")
    print()
    print("  EXPLORE:")
    print("    cfs top 10 eigenvector    Show top 10 by eigenvector")
    print("    cfs show CA               Deep dive on California")
    print("    cfs ls                    List all runs")
    print(f"{'='*50}")

    return config, G, centralities_df


if __name__ == "__main__":
    main()
