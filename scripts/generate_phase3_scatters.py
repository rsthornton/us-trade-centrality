"""
Phase 3: Generate 6 centrality-vs-control scatter plots.

Produces 12 files (6 PNG + 6 PDF) in paper/figures/.
"""

import sys
from pathlib import Path

# Add toolkit to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'cfs-network-toolkit'))

import pandas as pd
from cfs_toolkit.analysis.gdp_comparison import load_gdp_data
from cfs_toolkit.analysis.control_scatter import load_population_data, generate_control_scatter

# Paths
PROJECT = Path(__file__).parent.parent
RESULTS = PROJECT / 'results' / '51x51_domestic'
FIGURES = PROJECT / 'paper' / 'figures'
DATA = PROJECT / 'data'

def main():
    # Load data
    centralities_df = pd.read_csv(RESULTS / 'centralities_51x51_domestic.csv')
    gdp_data = load_gdp_data(DATA / 'state_gdp_2017.csv')
    pop_data = load_population_data(DATA / 'state_population_2017.csv')

    # Strip whitespace from state abbreviations in GDP data
    gdp_data = {k.strip(): v for k, v in gdp_data.items()}

    # Define the 6 scatter plot configurations
    configs = [
        # (centrality_measure, control_data, control_name, control_unit, filename)
        ('eigenvector', gdp_data, 'GDP', '2017 Q4', 'gdp_vs_eigenvector_scatter.png'),
        ('betweenness', gdp_data, 'GDP', '2017 Q4', 'gdp_vs_betweenness_scatter.png'),
        ('out_degree', gdp_data, 'GDP', '2017 Q4', 'gdp_vs_out_degree_scatter.png'),
        ('eigenvector', pop_data, 'Population', '2017 ACS', 'pop_vs_eigenvector_scatter.png'),
        ('betweenness', pop_data, 'Population', '2017 ACS', 'pop_vs_betweenness_scatter.png'),
        ('out_degree', pop_data, 'Population', '2017 ACS', 'pop_vs_out_degree_scatter.png'),
    ]

    print("=" * 60)
    print("  PHASE 3: Centrality vs Control Scatter Plots")
    print("=" * 60)

    results = []
    for measure, control, name, unit, filename in configs:
        print(f"\n--- {name} vs {measure} ---")
        rho, pval = generate_control_scatter(
            centralities_df, control, measure, name, unit,
            FIGURES / filename,
            label_threshold=8,
            rank_method='first'
        )
        results.append((name, measure, rho, pval))

    # Summary
    print("\n" + "=" * 60)
    print("  SPEARMAN RANK CORRELATIONS")
    print("=" * 60)
    print(f"  {'Control':<12} {'Centrality':<14} {'rho':>8} {'p-value':>12}")
    print("  " + "-" * 50)
    for name, measure, rho, pval in results:
        print(f"  {name:<12} {measure:<14} {rho:>8.3f} {pval:>12.2e}")

    print(f"\n  Total files: {len(configs) * 2} (PNG + PDF)")
    print("=" * 60)

if __name__ == '__main__':
    main()
