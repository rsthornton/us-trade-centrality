"""
cfs figures - Generate publication figures.

Usage:
    cfs figures                      Generate all figures from latest runs
    cfs figures --gdp                Just GDP figures
    cfs figures --diagrams           Methodology diagrams
    cfs figures --distribution       Edge weight distributions
"""

import sys
from pathlib import Path

from cfs_toolkit.commands._utils import (
    CANONICAL_DOMESTIC, CANONICAL_INTL, find_latest_runs,
)


def figures_command(args):
    """Generate publication figures."""
    # Import figures module functions
    from cfs_toolkit.figures import (
        generate_distribution_figure,
        create_network_construction_figure,
        create_centrality_framework_diagram,
    )
    from cfs_toolkit.analysis import load_network_graph, extract_edge_weights
    from cfs_toolkit.analysis.gdp_comparison import (
        load_gdp_data,
        compute_gdp_vs_centrality_comparison,
        generate_gdp_centrality_scatter,
        generate_normalized_centrality_bar,
    )
    import pandas as pd
    import numpy as np

    # Determine run directories
    if args.domestic_run:
        domestic_run = Path(args.domestic_run)
    elif CANONICAL_DOMESTIC.exists():
        domestic_run = CANONICAL_DOMESTIC
    else:
        domestic_run, _ = find_latest_runs(args.results_dir)

    if args.intl_run:
        intl_run = Path(args.intl_run)
    elif CANONICAL_INTL.exists():
        intl_run = CANONICAL_INTL
    else:
        _, intl_run = find_latest_runs(args.results_dir)

    if not domestic_run or not domestic_run.exists():
        print("No domestic run found. Run the pipeline first:")
        print("  python main.py")
        return 1

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 50)
    print("  PUBLICATION FIGURE GENERATION")
    print("=" * 50)
    print(f"  Domestic: {domestic_run.name}")
    if intl_run and intl_run.exists():
        print(f"  International: {intl_run.name}")
    print(f"  Output: {output_dir}")
    print("=" * 50)

    # Determine what to generate
    generate_paper = getattr(args, 'paper', False)
    generate_all = args.all or generate_paper or not any([args.gdp, args.diagrams, args.distribution, generate_paper])

    # GDP Figures
    if generate_all or args.gdp:
        print("\n[GDP FIGURES]")
        gdp_path = Path('data/state_gdp_2017.csv')
        centralities_file = list(domestic_run.glob('centralities_*.csv'))

        if gdp_path.exists() and centralities_file:
            gdp_dict = load_gdp_data(gdp_path)
            cent_df = pd.read_csv(centralities_file[0])

            # Need rank_eigenvector column
            cent_df['rank_eigenvector'] = cent_df['eigenvector'].rank(ascending=False, method='min').astype(int)

            comparison_df = compute_gdp_vs_centrality_comparison(cent_df, gdp_dict)

            scatter_path = output_dir / 'gdp_vs_eigenvector_scatter.png'
            generate_gdp_centrality_scatter(comparison_df, scatter_path)

            bar_path = output_dir / 'gdp_normalized_centrality_bar.png'
            generate_normalized_centrality_bar(comparison_df, bar_path)
        else:
            print(f"  Missing: {'GDP data' if not gdp_path.exists() else 'centralities'}")

    # Methodology Diagrams
    if generate_all or args.diagrams:
        print("\n[METHODOLOGY DIAGRAMS]")

        network_path = output_dir / 'network_construction_schematic.pdf'
        create_network_construction_figure(network_path)
        print(f"  ✓ {network_path.name}")

        framework_path = output_dir / 'centrality_framework.pdf'
        create_centrality_framework_diagram(framework_path)
        print(f"  ✓ {framework_path.name}")

    # Distribution Figures
    if generate_all or args.distribution:
        print("\n[EDGE WEIGHT DISTRIBUTION]")

        if intl_run and intl_run.exists():
            G_51 = load_network_graph(domestic_run)
            G_52 = load_network_graph(intl_run)

            weights_51 = extract_edge_weights(G_51)
            weights_52 = extract_edge_weights(G_52)

            stats_51 = {
                'edge_count': len(weights_51),
                'mean': np.mean(weights_51),
                'median': np.median(weights_51),
                'p25': np.percentile(weights_51, 25),
                'p50': np.percentile(weights_51, 50),
                'p75': np.percentile(weights_51, 75),
                'p90': np.percentile(weights_51, 90),
            }
            stats_52 = {
                'edge_count': len(weights_52),
                'mean': np.mean(weights_52),
                'median': np.median(weights_52),
                'p25': np.percentile(weights_52, 25),
                'p50': np.percentile(weights_52, 50),
                'p75': np.percentile(weights_52, 75),
                'p90': np.percentile(weights_52, 90),
            }

            dist_path = output_dir / 'edge_weight_distribution.png'
            generate_distribution_figure(weights_51, weights_52, stats_51, stats_52, dist_path)
            print(f"  ✓ {dist_path.name}")
        else:
            print("  Skipped: No international run available")

    # Choropleth Figures (paper-only or --paper)
    if generate_paper:
        print("\n[CHOROPLETH FIGURES]")
        from cfs_toolkit.figures.choropleths import (
            generate_physical_economy_divergence,
            generate_boundary_effect_choropleth,
        )

        gdp_path = Path('data/state_gdp_2017.csv')
        centralities_file = list(domestic_run.glob('centralities_*.csv'))
        intl_centralities_file = list(intl_run.glob('centralities_*.csv')) if intl_run and intl_run.exists() else []

        if gdp_path.exists() and centralities_file:
            phys_path = output_dir / 'marimo-physical-economy-divergence.png'
            generate_physical_economy_divergence(centralities_file[0], gdp_path, phys_path)
        else:
            print(f"  Missing: {'GDP data' if not gdp_path.exists() else 'centralities'}")

        if centralities_file and intl_centralities_file:
            boundary_path = output_dir / 'marimo-boundary-effect.png'
            generate_boundary_effect_choropleth(centralities_file[0], intl_centralities_file[0], boundary_path)
        else:
            print("  Skipped boundary effect: No international centralities available")

    # Copy to paper/figures/ if --paper
    if generate_paper:
        print("\n[COPY TO PAPER]")
        paper_figures_dir = Path('paper/figures')
        paper_figures_dir.mkdir(exist_ok=True, parents=True)
        import shutil

        paper_figure_names = [
            'network_construction_schematic.png',
            'centrality_framework.png',
            'gdp_vs_eigenvector_scatter.png',
            'gdp_normalized_centrality_bar.png',
            'marimo-physical-economy-divergence.png',
            'marimo-boundary-effect.png',
            'edge_weight_distribution.png',
        ]

        for fname in paper_figure_names:
            src = output_dir / fname
            if src.exists():
                dst = paper_figures_dir / fname
                # Map generated names to paper names
                if fname == 'centrality_framework.png':
                    dst = paper_figures_dir / 'centrality_framework_v2.png'
                elif fname == 'network_construction_schematic.png':
                    # Spring figure is generated separately via data-driven code
                    continue
                # Skip if src and dst resolve to the same file
                if src.resolve() != dst.resolve():
                    shutil.copy2(src, dst)
                print(f"  ✓ {dst.name}")
            else:
                print(f"  ⚠ Not found: {fname}")

    print()
    print("=" * 50)
    print(f"  Complete. Output: {output_dir}/")
    print("=" * 50)

    return 0


def add_figures_parser(subparsers):
    """Add figures subcommand to parser."""
    parser = subparsers.add_parser(
        'figures',
        help='Generate publication figures',
        description='Generate publication-quality figures from thesis results.'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Generate all figures (default if no specific type selected)'
    )
    parser.add_argument(
        '--paper',
        action='store_true',
        help='Generate all 9 paper figures and copy to paper/figures/'
    )
    parser.add_argument(
        '--gdp',
        action='store_true',
        help='Generate GDP comparison figures (scatter + normalized bar)'
    )
    parser.add_argument(
        '--diagrams',
        action='store_true',
        help='Generate methodology diagrams'
    )
    parser.add_argument(
        '--distribution',
        action='store_true',
        help='Generate edge weight distribution figure'
    )
    parser.add_argument(
        '--domestic-run',
        help='Path to domestic run (default: canonical Nov 29)'
    )
    parser.add_argument(
        '--intl-run',
        help='Path to international run (default: canonical Nov 29)'
    )
    parser.add_argument(
        '--output',
        default='results/publication_figures',
        help='Output directory (default: results/publication_figures)'
    )
    parser.add_argument(
        '--results-dir',
        default='results',
        help='Results directory for auto-detection (default: results)'
    )
    parser.set_defaults(func=figures_command)
