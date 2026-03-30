"""
Phase 3: Generate node distribution table.

Joins centralities with GDP and population data for all 51 domestic nodes.
Outputs LaTeX longtable snippet to paper/figures/.
"""

import sys
from pathlib import Path

# Add toolkit to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'cfs-network-toolkit'))

import pandas as pd
from cfs_toolkit.analysis.gdp_comparison import load_gdp_data
from cfs_toolkit.analysis.control_scatter import load_population_data

# Paths
PROJECT = Path(__file__).parent.parent
RESULTS = PROJECT / 'results' / '51x51_domestic'
FIGURES = PROJECT / 'paper' / 'figures'
DATA = PROJECT / 'data'


def main():
    print("=" * 60)
    print("  PHASE 3: Node Distribution Table")
    print("=" * 60)

    # Load data
    centralities_df = pd.read_csv(RESULTS / 'centralities_51x51_domestic.csv')
    gdp_data = load_gdp_data(DATA / 'state_gdp_2017.csv')
    pop_data = load_population_data(DATA / 'state_population_2017.csv')

    # Strip whitespace
    gdp_data = {k.strip(): v for k, v in gdp_data.items()}
    centralities_df['label'] = centralities_df['label'].str.strip()

    # Build table
    df = centralities_df.copy()
    df['state'] = df['label']
    df['pop'] = df['state'].map(pop_data)
    df['gdp'] = df['state'].map(gdp_data)

    # Convert units
    df['pop_m'] = df['pop'] / 1e6       # millions
    df['gdp_b'] = df['gdp'] / 1e3       # billions (already in millions)

    # Compute ranks with method='min'
    df['rank_betweenness'] = df['betweenness'].rank(ascending=False, method='min').astype(int)
    df['rank_eigenvector'] = df['eigenvector'].rank(ascending=False, method='min').astype(int)
    df['rank_out_degree'] = df['out_degree'].rank(ascending=False, method='min').astype(int)

    # Sort by eigenvector rank
    df = df.sort_values('rank_eigenvector')

    # Verify
    print(f"\n  Rows: {len(df)}")
    print(f"  NaN pop: {df['pop'].isna().sum()}")
    print(f"  NaN gdp: {df['gdp'].isna().sum()}")
    print(f"  NaN betweenness: {df['betweenness'].isna().sum()}")

    # Generate LaTeX longtable
    lines = []
    lines.append(r'\begin{longtable}{l r r r r r r r r}')
    lines.append(r'\caption{Node Distribution: All 51 Domestic States Sorted by Eigenvector Centrality Rank. '
                 r'Pop.\ in millions (2017 ACS), GDP in billions (2017 Q4). '
                 r'Centrality values are normalized scores; Rk = rank (1 = highest).} \\')
    lines.append(r'\label{tab:node_distribution}')
    lines.append(r'\hline')
    lines.append(r'\textbf{State} & \textbf{Pop (M)} & \textbf{GDP (\$B)} & '
                 r'\textbf{Betw.} & \textbf{Rk} & '
                 r'\textbf{Eig.} & \textbf{Rk} & '
                 r'\textbf{Out-D.} & \textbf{Rk} \\')
    lines.append(r'\hline')
    lines.append(r'\endfirsthead')
    lines.append(r'\hline')
    lines.append(r'\textbf{State} & \textbf{Pop (M)} & \textbf{GDP (\$B)} & '
                 r'\textbf{Betw.} & \textbf{Rk} & '
                 r'\textbf{Eig.} & \textbf{Rk} & '
                 r'\textbf{Out-D.} & \textbf{Rk} \\')
    lines.append(r'\hline')
    lines.append(r'\endhead')
    lines.append(r'\hline')
    lines.append(r'\endfoot')

    for _, row in df.iterrows():
        betw_str = f'{row["betweenness"]:.4f}' if row['betweenness'] > 0 else '0'
        lines.append(
            f'{row["state"]} & {row["pop_m"]:.2f} & {row["gdp_b"]:.1f} & '
            f'{betw_str} & {row["rank_betweenness"]} & '
            f'{row["eigenvector"]:.4f} & {row["rank_eigenvector"]} & '
            f'{row["out_degree"]:.4f} & {row["rank_out_degree"]} \\\\'
        )

    lines.append(r'\end{longtable}')

    latex = '\n'.join(lines)
    output_path = FIGURES / 'table_node_distribution_latex.txt'
    output_path.write_text(latex)
    print(f"\n  \u2713 LaTeX table saved: {output_path}")

    # Print top 10 for verification
    print("\n  Top 10 by Eigenvector Rank:")
    for _, row in df.head(10).iterrows():
        print(f"    {row['state']:>2}: Eig #{row['rank_eigenvector']}, "
              f"GDP ${row['gdp_b']:.0f}B, Pop {row['pop_m']:.1f}M")

    print(f"\n  Total rows: {len(df)}")
    print("=" * 60)

if __name__ == '__main__':
    main()
