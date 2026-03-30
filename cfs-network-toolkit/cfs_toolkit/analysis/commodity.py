"""
Commodity-Level Network Analysis
=================================

Analyzes trade networks broken down by SCTG commodity codes.

This module enables:
- Building commodity-specific networks from full CFS dataset
- Computing centralities for individual commodity sectors
- Identifying states that specialize in specific commodities
- Multi-commodity leadership analysis

SCTG Commodity Codes (examples):
- '01': Agricultural Products
- '02': Live Animals/Fish
- '03': Animal Feed
- '06': Cereal Grains
- '07': Other Agricultural Products
- '08': Alcoholic Beverages
- '09': Tobacco Products
- '10': Building Stone
- '11': Natural Sands
- '12': Gravel and Crushed Stone

Full list: https://www.census.gov/programs-surveys/cfs/technical-documentation/code-lists.html
"""

import pandas as pd
import networkx as nx
from typing import Dict, List, Tuple, Optional
import warnings


# ============================================================================
# COMMODITY NETWORK CONSTRUCTION
# ============================================================================

def build_commodity_network(df: pd.DataFrame,
                            sctg_code: str,
                            interstate_only: bool = True) -> nx.DiGraph:
    """
    Build network for a specific commodity sector.

    Args:
        df: Full CFS dataset (preprocessed)
        sctg_code: SCTG commodity code (e.g., '01' for agriculture)
        interstate_only: Filter out intrastate flows (default True)

    Returns:
        NetworkX DiGraph for that commodity only

    Example:
        >>> df = load_cfs_data('data/cfs_2017_puf.csv')
        >>> G_ag = build_commodity_network(df, '01')
        >>> print(f"Agriculture network: {G_ag.number_of_nodes()} nodes, {G_ag.number_of_edges()} edges")
    """
    # Filter to commodity
    commodity_df = df[df['SCTG'] == sctg_code].copy()

    if len(commodity_df) == 0:
        warnings.warn(f"No data found for commodity code {sctg_code}")
        return nx.DiGraph()

    # Use existing preprocessing and network building from Layer 1 (Core)
    from cfs_toolkit.core.preprocessor import preprocess_cfs_data, aggregate_cfs_to_edges
    from cfs_toolkit.core.network_builder import build_trade_network

    # Preprocess: create weighted_value, filter interstate
    preprocessed = preprocess_cfs_data(commodity_df, interstate_only=interstate_only)

    if len(preprocessed) == 0:
        warnings.warn(f"No interstate flows found for commodity code {sctg_code}")
        return nx.DiGraph()

    # Aggregate to edges
    edges = aggregate_cfs_to_edges(preprocessed)

    # Build network
    G = build_trade_network(edges)

    # Add commodity metadata to graph
    G.graph['commodity_code'] = sctg_code
    G.graph['commodity_name'] = SCTG_NAMES.get(sctg_code, 'Unknown')

    return G


def build_all_commodity_networks(df: pd.DataFrame,
                                 commodities: Optional[List[str]] = None) -> Dict[str, nx.DiGraph]:
    """
    Build networks for multiple commodity sectors.

    Args:
        df: Full CFS dataset
        commodities: List of SCTG codes. If None, builds all available commodities.

    Returns:
        Dictionary mapping commodity codes to NetworkX graphs

    Example:
        >>> networks = build_all_commodity_networks(df, ['01', '06', '07'])
        >>> for code, G in networks.items():
        ...     print(f"{code}: {G.number_of_edges()} edges")
    """
    if commodities is None:
        # Auto-detect commodities in dataset
        commodities = df['SCTG'].unique().tolist()

    networks = {}
    for sctg in commodities:
        G = build_commodity_network(df, sctg)
        if G.number_of_nodes() > 0:  # Only include non-empty networks
            networks[sctg] = G

    return networks


# ============================================================================
# COMMODITY CENTRALITY ANALYSIS
# ============================================================================

def analyze_commodity_centralities(df: pd.DataFrame,
                                   commodities: List[str]) -> pd.DataFrame:
    """
    Compute centralities for multiple commodities.

    Args:
        df: Full CFS dataset
        commodities: List of SCTG codes to analyze

    Returns:
        DataFrame with columns:
            - state_id, label
            - commodity_code, commodity_name
            - betweenness, eigenvector, out_degree
            - rank_betweenness, rank_eigenvector, rank_out_degree

    Example:
        >>> results = analyze_commodity_centralities(df, ['01', '06'])
        >>> top_ag = results[results['commodity_code'] == '01'].nlargest(5, 'eigenvector')
        >>> print(top_ag[['label', 'eigenvector', 'rank_eigenvector']])
    """
    from cfs_toolkit.core import compute_all_centralities

    results = []

    for sctg in commodities:
        print(f"Analyzing commodity {sctg}: {SCTG_NAMES.get(sctg, 'Unknown')}...")

        # Build commodity-specific network
        G = build_commodity_network(df, sctg)

        if G.number_of_nodes() == 0:
            warnings.warn(f"Skipping empty network for commodity {sctg}")
            continue

        # Compute centralities (reuse Layer 1 function - guaranteed correct!)
        centralities = compute_all_centralities(G)

        # Add commodity metadata
        centralities['commodity_code'] = sctg
        centralities['commodity_name'] = SCTG_NAMES.get(sctg, 'Unknown')

        results.append(centralities)

    if len(results) == 0:
        return pd.DataFrame()

    return pd.concat(results, ignore_index=True)


# ============================================================================
# COMMODITY SPECIALIZATION ANALYSIS
# ============================================================================

def identify_commodity_specialists(commodity_centralities: pd.DataFrame,
                                   measure: str = 'eigenvector',
                                   threshold: float = 0.8) -> pd.DataFrame:
    """
    Identify states that dominate specific commodities.

    A "specialist" is a state with high centrality (>threshold) in a commodity sector.

    Args:
        commodity_centralities: Output from analyze_commodity_centralities()
        measure: Centrality measure to use ('eigenvector', 'betweenness', 'out_degree')
        threshold: Centrality score threshold for "specialist" (0-1 scale)

    Returns:
        DataFrame of state-commodity specialist pairings with:
            - state_id, label
            - commodity_code, commodity_name
            - centrality score
            - num_commodities (how many commodities this state specializes in)

    Example:
        >>> specialists = identify_commodity_specialists(results, threshold=0.8)
        >>> multi_specialists = specialists[specialists['num_commodities'] > 3]
        >>> print(f"States specializing in 3+ commodities: {len(multi_specialists)}")
    """
    # Filter to high-centrality states
    specialists = commodity_centralities[
        commodity_centralities[measure] >= threshold
    ].copy()

    # Count commodities per state
    state_counts = specialists.groupby('state_id')['commodity_code'].count()

    # Merge back
    specialists = specialists.merge(
        state_counts.rename('num_commodities'),
        left_on='state_id',
        right_index=True
    )

    # Sort by number of commodities (multi-specialists first)
    specialists = specialists.sort_values(
        ['num_commodities', measure],
        ascending=[False, False]
    )

    return specialists


def compute_commodity_leadership_matrix(commodity_centralities: pd.DataFrame,
                                        measure: str = 'eigenvector',
                                        top_n: int = 10) -> pd.DataFrame:
    """
    Create matrix showing which states lead in which commodities.

    Args:
        commodity_centralities: Output from analyze_commodity_centralities()
        measure: Centrality measure to use
        top_n: Number of top states to include per commodity

    Returns:
        Wide-format DataFrame with states as rows, commodities as columns,
        containing ranks (1 = highest centrality in that commodity)

    Example:
        >>> matrix = compute_commodity_leadership_matrix(results, top_n=10)
        >>> print(matrix.head())  # Shows top 10 states across all commodities
    """
    # TODO: Implement pivot table of ranks
    # For each commodity, show state ranks
    # This creates a "leadership matrix" visualization
    pass


def analyze_commodity_diversification(commodity_centralities: pd.DataFrame,
                                     measure: str = 'eigenvector',
                                     threshold: float = 0.5) -> pd.DataFrame:
    """
    Analyze state diversification across commodity sectors.

    Identifies whether states are:
    - Specialists (high centrality in 1-2 commodities)
    - Diversified (moderate centrality across many commodities)
    - Generalists (low centrality across all commodities)

    Args:
        commodity_centralities: Output from analyze_commodity_centralities()
        measure: Centrality measure to use
        threshold: Minimum centrality to count as "participation"

    Returns:
        DataFrame with state-level diversification metrics:
            - state_id, label
            - num_commodities_active (centrality > threshold)
            - avg_centrality (across active commodities)
            - max_centrality (best commodity)
            - diversification_score (coefficient of variation)

    Example:
        >>> div = analyze_commodity_diversification(results, threshold=0.5)
        >>> specialists = div[div['num_commodities_active'] <= 2]
        >>> generalists = div[div['num_commodities_active'] >= 10]
    """
    # TODO: Implement diversification metrics
    # Group by state, compute:
    # - Count of commodities above threshold
    # - Average centrality
    # - Coefficient of variation (diversity measure)
    pass


# ============================================================================
# COMPARATIVE COMMODITY ANALYSIS
# ============================================================================

def compare_commodity_structures(networks: Dict[str, nx.DiGraph]) -> pd.DataFrame:
    """
    Compare network structure across commodity sectors.

    Args:
        networks: Dictionary of commodity code -> NetworkX graph

    Returns:
        DataFrame with commodity-level network statistics:
            - commodity_code, commodity_name
            - num_nodes, num_edges
            - density, avg_clustering
            - avg_in_degree, avg_out_degree
            - network_diameter (if connected)

    Example:
        >>> networks = build_all_commodity_networks(df, ['01', '06', '07'])
        >>> comparison = compare_commodity_structures(networks)
        >>> print(comparison.sort_values('density', ascending=False))
    """
    # TODO: Implement network structure comparison
    # For each commodity:
    # - Basic stats (nodes, edges, density)
    # - Clustering coefficient
    # - Degree distribution
    # - Connectivity metrics
    pass


# ============================================================================
# COMMODITY CODE MAPPINGS
# ============================================================================

# SCTG commodity names (subset - expand as needed)
SCTG_NAMES = {
    '01': 'Agricultural Products',
    '02': 'Live Animals/Fish',
    '03': 'Animal Feed',
    '04': 'Meat/Seafood',
    '05': 'Milled Grain Products',
    '06': 'Cereal Grains',
    '07': 'Other Agricultural Products',
    '08': 'Alcoholic Beverages',
    '09': 'Tobacco Products',
    '10': 'Building Stone',
    '11': 'Natural Sands',
    '12': 'Gravel and Crushed Stone',
    '13': 'Nonmetallic Minerals',
    '14': 'Metallic Ores',
    '15': 'Coal',
    '16': 'Crude Petroleum',
    '17': 'Gasoline and Aviation Fuel',
    '18': 'Fuel Oils',
    '19': 'Coal and Petroleum Products',
    '20': 'Basic Chemicals',
    '21': 'Pharmaceutical Products',
    '22': 'Fertilizers',
    '23': 'Chemical Products',
    '24': 'Plastics/Rubber',
    '25': 'Logs and Other Wood',
    '26': 'Wood Products',
    '27': 'Newsprint/Paper',
    '28': 'Paper Articles',
    '29': 'Printed Products',
    '30': 'Textiles/Leather',
    '31': 'Nonmetallic Mineral Products',
    '32': 'Base Metal',
    '33': 'Articles of Base Metal',
    '34': 'Machinery',
    '35': 'Electronic Equipment',
    '36': 'Motorized Vehicles',
    '37': 'Transportation Equipment',
    '38': 'Precision Instruments',
    '39': 'Furniture',
    '40': 'Misc. Manufactured Products',
    '41': 'Waste/Scrap',
    '43': 'Mixed Freight',
}


# Commodity groupings for higher-level analysis
COMMODITY_GROUPS = {
    'Agriculture': ['01', '02', '03', '04', '05', '06', '07'],
    'Energy': ['15', '16', '17', '18', '19'],
    'Manufacturing': ['34', '35', '36', '37', '38'],
    'Raw_Materials': ['10', '11', '12', '13', '14', '25'],
    'Chemicals': ['20', '21', '22', '23', '24'],
    'Consumer_Goods': ['39', '40'],
}


def get_commodity_group(sctg_code: str) -> Optional[str]:
    """Get commodity group for a given SCTG code."""
    for group, codes in COMMODITY_GROUPS.items():
        if sctg_code in codes:
            return group
    return None


# ============================================================================
# CLI INTERFACE
# ============================================================================

def parse_arguments():
    """Parse command-line arguments for commodity analysis."""
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(
        description='Analyze state centrality in commodity-specific networks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze agricultural commodities
  python -m cfs_toolkit.analysis.commodity --group Agriculture

  # Analyze specific commodities with sample data (fast)
  python -m cfs_toolkit.analysis.commodity --commodities 01 06 --sample 5000

  # Full analysis of all commodities (slow - full dataset)
  python -m cfs_toolkit.analysis.commodity
        """
    )

    parser.add_argument(
        '--commodities',
        nargs='+',
        help='SCTG commodity codes to analyze (e.g., 01 06 07). If not specified, analyzes all.'
    )

    parser.add_argument(
        '--group',
        choices=list(COMMODITY_GROUPS.keys()),
        help='Analyze predefined commodity group (Agriculture, Energy, Manufacturing, etc.)'
    )

    parser.add_argument(
        '--sample',
        type=int,
        help='Sample size for testing (uses first N rows of CFS data)'
    )

    parser.add_argument(
        '--threshold',
        type=float,
        default=0.8,
        help='Centrality threshold for identifying specialists (default: 0.8)'
    )

    parser.add_argument(
        '--measure',
        choices=['eigenvector', 'betweenness', 'out_degree'],
        default='eigenvector',
        help='Centrality measure to use for specialist identification (default: eigenvector)'
    )

    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('results/commodity_analysis'),
        help='Output directory (default: results/commodity_analysis)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    return parser.parse_args()


def main():
    """Execute commodity-level network analysis CLI."""
    import sys
    from pathlib import Path
    from datetime import datetime

    args = parse_arguments()

    print("=" * 80)
    print("COMMODITY-LEVEL NETWORK ANALYSIS")
    print("=" * 80)
    print()

    # ========================================================================
    # STEP 1: Load CFS Data
    # ========================================================================
    print("Step 1: Loading CFS data...")
    data_path = Path('data/cfs_2017_puf.csv')

    if not data_path.exists():
        print(f"ERROR: Data file not found: {data_path}")
        print("Please ensure CFS 2017 data is in data/ directory")
        sys.exit(1)

    # Load data (with optional sampling)
    from cfs_toolkit.core.data_loader import load_cfs_data
    df = load_cfs_data(str(data_path), sample_size=args.sample)

    if args.sample:
        print(f"  Using sample: {args.sample:,} rows")
    else:
        print(f"  Loaded full dataset: {len(df):,} rows")

    # ========================================================================
    # STEP 2: Determine Commodities to Analyze
    # ========================================================================
    if args.group:
        commodities = COMMODITY_GROUPS[args.group]
        print(f"\nStep 2: Analyzing commodity group '{args.group}' ({len(commodities)} commodities)")
    elif args.commodities:
        commodities = args.commodities
        print(f"\nStep 2: Analyzing {len(commodities)} specified commodities")
    else:
        # Auto-detect all commodities in dataset
        commodities = sorted(df['SCTG'].unique().tolist())
        print(f"\nStep 2: Analyzing all commodities in dataset ({len(commodities)} total)")

    # Show commodity names
    if args.verbose:
        print("\nCommodities to analyze:")
        for sctg in commodities:
            name = SCTG_NAMES.get(sctg, 'Unknown')
            print(f"  {sctg}: {name}")

    # ========================================================================
    # STEP 3: Compute Commodity Centralities
    # ========================================================================
    print(f"\nStep 3: Computing centralities for {len(commodities)} commodity sectors...")
    print("(This may take several minutes for full dataset)")
    print()

    results = analyze_commodity_centralities(df, commodities)

    if len(results) == 0:
        print("ERROR: No centrality results generated. Check data and commodity codes.")
        sys.exit(1)

    print(f"✓ Computed centralities for {len(results):,} state-commodity pairs")
    print(f"  States analyzed: {results['state_id'].nunique()}")
    print(f"  Commodities with results: {results['commodity_code'].nunique()}")

    # ========================================================================
    # STEP 4: Identify Commodity Specialists
    # ========================================================================
    print(f"\nStep 4: Identifying commodity specialists ({args.measure} ≥ {args.threshold})...")

    specialists = identify_commodity_specialists(
        results,
        measure=args.measure,
        threshold=args.threshold
    )

    print(f"✓ Found {len(specialists)} specialist state-commodity pairs")

    if len(specialists) > 0:
        multi_specialists = specialists[specialists['num_commodities'] > 1]
        print(f"  States specializing in multiple commodities: {multi_specialists['state_id'].nunique()}")

    # ========================================================================
    # STEP 5: Create Output Directory
    # ========================================================================
    print(f"\nStep 5: Creating output directory...")
    args.output_dir.mkdir(exist_ok=True, parents=True)
    print(f"✓ Output directory: {args.output_dir}")

    # ========================================================================
    # STEP 6: Save Results
    # ========================================================================
    print(f"\nStep 6: Saving results...")

    # Save commodity centralities
    centralities_path = args.output_dir / 'commodity_centralities.csv'
    results.to_csv(centralities_path, index=False)
    print(f"✓ Saved: {centralities_path}")

    # Save specialists
    if len(specialists) > 0:
        specialists_path = args.output_dir / 'commodity_specialists.csv'
        specialists.to_csv(specialists_path, index=False)
        print(f"✓ Saved: {specialists_path}")

    # ========================================================================
    # STEP 7: Generate Summary Report
    # ========================================================================
    print(f"\nStep 7: Generating summary report...")

    summary_path = args.output_dir / 'commodity_summary.txt'
    with open(summary_path, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("COMMODITY-LEVEL NETWORK ANALYSIS - SUMMARY REPORT\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Dataset: {data_path}\n")
        if args.sample:
            f.write(f"Sample Size: {args.sample:,} rows\n")
        f.write(f"Commodities Analyzed: {len(commodities)}\n")
        f.write(f"Specialist Threshold: {args.measure} ≥ {args.threshold}\n")
        f.write("\n")

        f.write("-" * 80 + "\n")
        f.write("OVERVIEW STATISTICS\n")
        f.write("-" * 80 + "\n\n")

        f.write(f"Total state-commodity pairs: {len(results):,}\n")
        f.write(f"States analyzed: {results['state_id'].nunique()}\n")
        f.write(f"Commodities with results: {results['commodity_code'].nunique()}\n")
        f.write(f"Commodity specialists found: {len(specialists):,}\n\n")

        if len(specialists) > 0:
            f.write("-" * 80 + "\n")
            f.write("TOP 10 MULTI-COMMODITY SPECIALISTS\n")
            f.write("-" * 80 + "\n\n")

            top_specialists = specialists.nlargest(10, 'num_commodities')
            for _, row in top_specialists.iterrows():
                f.write(f"{row['label']:20s} - {row['num_commodities']} commodities "
                       f"({args.measure}={row[args.measure]:.3f})\n")

            f.write("\n")

            f.write("-" * 80 + "\n")
            f.write("TOP 5 SPECIALISTS BY COMMODITY\n")
            f.write("-" * 80 + "\n\n")

            for sctg in commodities[:10]:  # First 10 commodities
                commodity_name = SCTG_NAMES.get(sctg, 'Unknown')
                f.write(f"\n{sctg}: {commodity_name}\n")

                commodity_specialists = specialists[
                    specialists['commodity_code'] == sctg
                ].nlargest(5, args.measure)

                if len(commodity_specialists) > 0:
                    for i, (_, row) in enumerate(commodity_specialists.iterrows(), 1):
                        f.write(f"  {i}. {row['label']:15s} - {args.measure}={row[args.measure]:.3f}\n")
                else:
                    f.write("  (No specialists found)\n")

    print(f"✓ Saved: {summary_path}")

    # ========================================================================
    # STEP 8: Display Summary to Console
    # ========================================================================
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE - SUMMARY")
    print("=" * 80)
    print()

    print(f"Outputs saved to: {args.output_dir}/")
    print(f"  - commodity_centralities.csv ({len(results):,} rows)")
    if len(specialists) > 0:
        print(f"  - commodity_specialists.csv ({len(specialists):,} rows)")
    print(f"  - commodity_summary.txt")
    print()

    if len(specialists) > 0:
        print("Top 5 Multi-Commodity Specialists:")
        top_5 = specialists.nlargest(5, 'num_commodities')
        for i, (_, row) in enumerate(top_5.iterrows(), 1):
            print(f"  {i}. {row['label']:15s} - {row['num_commodities']} commodities")

    print()
    print("=" * 80)


if __name__ == '__main__':
    main()
