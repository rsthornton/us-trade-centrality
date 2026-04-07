"""
Session C: Generate all Appendix C and D outputs for Cliff's April 6 revisions.

Outputs
-------
paper/figures/gdp_vs_population_scatter.png  (+ .pdf)
paper/figures/table_rho_correlations.tex
paper/figures/table_trade_balance.tex

Usage:
    python scripts/generate_session_c.py
"""
import sys
from pathlib import Path

# Add toolkit to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'cfs-network-toolkit'))

import pandas as pd
from cfs_toolkit.analysis.gdp_comparison import load_gdp_data
from cfs_toolkit.analysis.control_scatter import (
    load_population_data,
    generate_control_scatter,
    generate_control_vs_control_scatter,
    generate_rho_table_latex,
)
from cfs_toolkit.analysis.trade_balance import (
    compute_trade_balance_table,
    generate_trade_balance_latex,
)

# Paths
PROJECT = Path(__file__).parent.parent
RESULTS = PROJECT / 'results' / '51x51_domestic'
FIGURES = PROJECT / 'paper' / 'figures'
DATA = PROJECT / 'data'


def main():
    print("Generating Appendix C + D outputs...")

    # Load shared data
    centralities_df = pd.read_csv(RESULTS / 'centralities_51x51_domestic.csv')
    gdp_data = load_gdp_data(DATA / 'state_gdp_2017.csv')
    gdp_data = {k.strip(): v for k, v in gdp_data.items()}
    pop_data = load_population_data(DATA / 'state_population_2017.csv')

    # === APPENDIX C ===

    # 1. GDP vs Population scatter (new figure)
    print("\n--- GDP vs Population Scatter ---")
    rho_gdp_pop, p_gdp_pop = generate_control_vs_control_scatter(
        x_data=gdp_data,
        y_data=pop_data,
        x_name='GDP', y_name='Population',
        x_unit='2017 Q4', y_unit='2017 ACS',
        output_path=FIGURES / 'gdp_vs_population_scatter.png',
    )
    print(f"  GDP vs Population: ρ = {rho_gdp_pop:.3f}, p = {p_gdp_pop:.2e}")

    # 2. Re-run all 6 centrality×control scatters to collect fresh rho values
    print("\n--- Collecting ρ values for all 6 combinations ---")
    configs = [
        ('eigenvector', gdp_data, 'GDP', '2017 Q4', 'gdp_vs_eigenvector_scatter.png'),
        ('betweenness', gdp_data, 'GDP', '2017 Q4', 'gdp_vs_betweenness_scatter.png'),
        ('out_degree', gdp_data, 'GDP', '2017 Q4', 'gdp_vs_out_degree_scatter.png'),
        ('eigenvector', pop_data, 'Population', '2017 ACS', 'pop_vs_eigenvector_scatter.png'),
        ('betweenness', pop_data, 'Population', '2017 ACS', 'pop_vs_betweenness_scatter.png'),
        ('out_degree', pop_data, 'Population', '2017 ACS', 'pop_vs_out_degree_scatter.png'),
    ]

    rho_results = []
    for measure, control, name, unit, filename in configs:
        rho, pval = generate_control_scatter(
            centralities_df, control, measure, name, unit,
            FIGURES / filename,
            label_threshold=8,
            rank_method='first'
        )
        rho_results.append((name, measure, rho, pval))
        print(f"  {name} × {measure}: ρ = {rho:.3f}")

    # 3. Generate ρ table LaTeX
    print("\n--- Generating ρ table ---")
    latex_rho = generate_rho_table_latex(rho_results)
    rho_path = FIGURES / 'table_rho_correlations.tex'
    rho_path.write_text(latex_rho)
    print(f"  ✓ Saved to {rho_path}")

    # === APPENDIX D ===

    # 4. Compute trade balance table
    print("\n--- Computing trade balance table ---")
    df_balance = compute_trade_balance_table(
        domestic_gpickle_path=RESULTS / 'network_51x51_domestic.gpickle',
        intl_gpickle_path=PROJECT / 'results' / '52x52_international' / 'network_52x52_intl.gpickle',
        gdp_csv_path=DATA / 'state_gdp_2017.csv',
        pop_csv_path=DATA / 'state_population_2017.csv',
    )
    print(f"  {len(df_balance)} states computed")
    print(f"  Top exporter: {df_balance.iloc[0]['state_abbrev']} "
          f"(${df_balance.iloc[0]['net_out_dollars']/1e9:.1f}B out)")

    # 5. Generate trade balance LaTeX
    latex_balance = generate_trade_balance_latex(df_balance)
    balance_path = FIGURES / 'table_trade_balance.tex'
    balance_path.write_text(latex_balance)
    print(f"  ✓ Saved to {balance_path}")

    print(f"\nDone. Generated {len(rho_results)} scatter plots + rho table + trade balance table.")


if __name__ == '__main__':
    main()
