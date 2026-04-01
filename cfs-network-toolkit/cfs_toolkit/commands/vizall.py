"""
cfs viz-all - Generate all available visualizations.

Batch-generates all implemented visualizations from the toolkit
to surface what's available and evaluate thesis usefulness.

Usage:
    cfs viz-all                      Generate all from canonical runs
    cfs viz-all --output figures/    Custom output directory
    cfs viz-all --list               List available visualizations (no generation)
    cfs viz-all --category base      Generate only specific category
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

from cfs_toolkit.commands._utils import CANONICAL_DOMESTIC, CANONICAL_INTL


def list_available_visualizations():
    """List all available visualization functions with status."""
    print()
    print("=" * 70)
    print("  AVAILABLE VISUALIZATIONS")
    print("=" * 70)

    categories = {
        'base': [
            ('create_centrality_comparison', 'Three-panel bar charts', 'PNG'),
            ('create_3d_centrality_plot', 'Interactive 3D scatter', 'HTML'),
            ('create_static_3d_plots', 'Static 3D (3 angles)', 'PNG'),
            ('create_pairwise_scatter_plots', 'Pairwise centrality scatter', 'PNG'),
            ('create_boundary_sensitivity_summary', 'Rank change % bar chart', 'PNG'),
        ],
        'committee': [
            ('create_correlation_paradox_chart', 'Correlation vs changes', 'PNG/PDF'),
            ('create_ranking_change_chart', 'Horizontal rank change bars', 'PNG/PDF'),
            ('create_before_after_scatter', '51 vs 52 value scatter', 'PNG/PDF'),
            ('create_rank_scatter', '51 vs 52 rank scatter', 'PNG/PDF'),
        ],
        'matrices': [
            ('create_complete_trade_matrix', 'Full NxN trade heatmap', 'PNG/PDF'),
            ('create_regional_trade_matrices', 'Eastern/Western splits', 'PNG/PDF'),
            ('create_interactive_matrix_comparison', '4-panel interactive', 'HTML'),
            ('create_network_flow_sankey', 'Sankey flow diagram', 'HTML'),
        ],
        'state_reports': [
            ('create_state_report_card', 'Individual state HTML', 'HTML'),
            ('create_all_state_report_cards', 'All 51 states + index', 'HTML'),
        ],
        'figures': [
            ('create_network_construction_figure', 'Methodology schematic', 'PDF/PNG'),
            ('create_network_spring_figure', 'Data-driven spring layout', 'PDF/PNG'),
            ('generate_distribution_figure', 'Edge weight histograms', 'PNG'),
            ('generate_rank_stability_figure', 'Filtration rank stability', 'PNG'),
        ],
        'overlays': [
            ('create_gdp_vs_centrality_table', 'GDP vs centrality ranks', 'PNG'),
        ],
        'commodity (STUBS)': [
            ('create_commodity_leadership_matrix', 'NOT IMPLEMENTED', '-'),
            ('create_specialist_bar_chart', 'NOT IMPLEMENTED', '-'),
            ('create_diversification_profile', 'NOT IMPLEMENTED', '-'),
        ],
    }

    for category, funcs in categories.items():
        print(f"\n  {category.upper()}")
        print("  " + "-" * 50)
        for name, description, output_type in funcs:
            status = "STUB" if "NOT IMPLEMENTED" in description else "OK"
            print(f"  [{status:4s}] {name}")
            print(f"         {description} -> {output_type}")

    print()
    print("=" * 70)
    print(f"  Total: {sum(len(f) for f in categories.values())} functions")
    print(f"  Implemented: {sum(len([x for x in f if 'NOT IMPLEMENTED' not in x[1]]) for f in categories.values())}")
    print(f"  Stubs: {sum(len([x for x in f if 'NOT IMPLEMENTED' in x[1]]) for f in categories.values())}")
    print("=" * 70)
    print()


def generate_base_visualizations(centralities_51, centralities_52, output_dir):
    """Generate base centrality visualizations."""
    from cfs_toolkit.visualizations import (
        create_centrality_comparison,
        create_3d_centrality_plot,
        create_static_3d_plots,
        create_pairwise_scatter_plots,
        create_boundary_sensitivity_summary,
    )

    generated = []
    base_dir = output_dir / 'base'
    base_dir.mkdir(exist_ok=True)

    print("\n  BASE VISUALIZATIONS")
    print("  " + "-" * 40)

    # 1. Centrality comparison (3-panel bar charts)
    try:
        print("  Generating centrality_comparison...")
        fig = create_centrality_comparison(
            centralities_51,
            top_n=10,
            save_path=base_dir / 'centrality_comparison.png'
        )
        import matplotlib.pyplot as plt
        plt.close(fig)
        generated.append('centrality_comparison.png')
    except Exception as e:
        print(f"    ERROR: {e}")

    # 2. 3D interactive plot
    try:
        print("  Generating 3d_centrality_interactive...")
        fig = create_3d_centrality_plot(
            centralities_51,
            save_path=base_dir / '3d_centrality_interactive.html'
        )
        generated.append('3d_centrality_interactive.html')
    except Exception as e:
        print(f"    ERROR: {e}")

    # 3. Static 3D plots (3 angles)
    try:
        print("  Generating static_3d_plots (3 angles)...")
        figs = create_static_3d_plots(
            centralities_51,
            save_dir=base_dir,
            network_label="51×51"
        )
        import matplotlib.pyplot as plt
        for fig in figs:
            plt.close(fig)
        generated.extend(['3d_centrality_perspective.png', '3d_centrality_front.png', '3d_centrality_side.png'])
    except Exception as e:
        print(f"    ERROR: {e}")

    # 4. Pairwise scatter plots (3 pairs)
    try:
        print("  Generating pairwise_scatter_plots (3 pairs)...")
        figs = create_pairwise_scatter_plots(
            centralities_51,
            save_dir=base_dir,
            network_label="51×51"
        )
        import matplotlib.pyplot as plt
        for fig in figs:
            plt.close(fig)
        generated.extend([
            'pairwise_betweenness_vs_eigenvector.png',
            'pairwise_betweenness_vs_out_degree.png',
            'pairwise_eigenvector_vs_out_degree.png'
        ])
    except Exception as e:
        print(f"    ERROR: {e}")

    # 5. Boundary sensitivity summary
    try:
        print("  Generating boundary_sensitivity_summary...")
        fig = create_boundary_sensitivity_summary(
            centralities_51,
            centralities_52,
            save_path=base_dir / 'boundary_sensitivity_summary.png'
        )
        import matplotlib.pyplot as plt
        plt.close(fig)
        generated.append('boundary_sensitivity_summary.png')
    except Exception as e:
        print(f"    ERROR: {e}")

    print(f"  Generated {len(generated)} base visualizations")
    return generated


def generate_committee_visualizations(centralities_51, centralities_52, output_dir):
    """Generate committee-friendly comparison visualizations."""
    from cfs_toolkit.visualizations.committee import (
        create_correlation_paradox_chart,
        create_ranking_change_chart,
        create_before_after_scatter,
        create_rank_scatter,
    )
    from cfs_toolkit.analysis.comparison_utils import (
        compute_rank_correlations,
        compute_rank_changes,
        summarize_effect_sizes,
    )

    generated = []
    comm_dir = output_dir / 'committee'
    comm_dir.mkdir(exist_ok=True)

    print("\n  COMMITTEE VISUALIZATIONS")
    print("  " + "-" * 40)

    measures = ['betweenness', 'eigenvector', 'out_degree']

    # Compute comparative stats
    try:
        correlations = compute_rank_correlations(centralities_51, centralities_52, measures)
        rank_changes = compute_rank_changes(centralities_51, centralities_52, measures)
        effect_sizes = summarize_effect_sizes(rank_changes)

        comparative_stats = {
            'correlations': correlations,
            'rank_changes': rank_changes,
            'effect_sizes': effect_sizes,
        }
    except Exception as e:
        print(f"    ERROR computing stats: {e}")
        return generated

    # 1. Correlation paradox chart
    try:
        print("  Generating correlation_paradox_chart...")
        create_correlation_paradox_chart(comparative_stats, measures, comm_dir)
        generated.extend(['correlation_paradox_chart.png', 'correlation_paradox_chart.pdf'])
    except Exception as e:
        print(f"    ERROR: {e}")

    # 2. Ranking change charts (one per measure)
    for measure in measures:
        try:
            print(f"  Generating ranking_changes_{measure}...")
            create_ranking_change_chart(rank_changes, measure, comm_dir)
            generated.extend([f'ranking_changes_{measure}.png', f'ranking_changes_{measure}.pdf'])
        except Exception as e:
            print(f"    ERROR: {e}")

    # 3. Before/after scatter plots (one per measure)
    for measure in measures:
        try:
            print(f"  Generating before_after_scatter_{measure}...")
            create_before_after_scatter(centralities_51, centralities_52, measure, comm_dir)
            generated.extend([f'before_after_scatter_{measure}.png', f'before_after_scatter_{measure}.pdf'])
        except Exception as e:
            print(f"    ERROR: {e}")

    # 4. Rank scatter plots (one per measure)
    for measure in measures:
        try:
            print(f"  Generating rank_scatter_{measure}...")
            create_rank_scatter(centralities_51, centralities_52, measure, comm_dir)
            generated.extend([f'rank_scatter_{measure}.png', f'rank_scatter_{measure}.pdf'])
        except Exception as e:
            print(f"    ERROR: {e}")

    print(f"  Generated {len(generated)} committee visualizations")
    return generated


def generate_matrix_visualizations(G_51, G_52, output_dir):
    """Generate trade matrix visualizations."""
    from cfs_toolkit.visualizations.matrices import (
        create_complete_trade_matrix,
        create_regional_trade_matrices,
        create_enhanced_trade_matrix_suite,
    )

    generated = []
    matrix_dir = output_dir / 'matrices'
    matrix_dir.mkdir(exist_ok=True)

    print("\n  MATRIX VISUALIZATIONS")
    print("  " + "-" * 40)

    # 1. Complete trade matrix
    try:
        print("  Generating complete_trade_matrix...")
        fig = create_complete_trade_matrix(G_51, save_path=matrix_dir / 'trade_matrix_complete.png')
        import matplotlib.pyplot as plt
        plt.close(fig)
        generated.extend(['trade_matrix_complete.png', 'trade_matrix_complete.pdf'])
    except Exception as e:
        print(f"    ERROR: {e}")

    # 2. Regional trade matrices
    try:
        print("  Generating regional_trade_matrices...")
        figs = create_regional_trade_matrices(G_51, matrix_dir)
        import matplotlib.pyplot as plt
        for fig in figs:
            plt.close(fig)
        generated.extend([
            'trade_matrix_eastern_regional.png',
            'trade_matrix_western_regional.png'
        ])
    except Exception as e:
        print(f"    ERROR: {e}")

    print(f"  Generated {len(generated)} matrix visualizations")
    return generated


def generate_figure_visualizations(output_dir, G_51=None, G_52=None):
    """Generate publication figures."""
    from cfs_toolkit.figures import (
        create_network_construction_figure,
        create_network_spring_figure,
    )

    generated = []
    figures_dir = output_dir / 'figures'
    figures_dir.mkdir(exist_ok=True)

    print("\n  PUBLICATION FIGURES")
    print("  " + "-" * 40)

    # 1. Network construction schematic (conceptual diagram)
    try:
        print("  Generating network_construction_figure (schematic)...")
        create_network_construction_figure(output_path=figures_dir / 'fig_network_construction_schematic.pdf')
        generated.extend(['fig_network_construction_schematic.pdf', 'fig_network_construction_schematic.png'])
    except Exception as e:
        print(f"    ERROR: {e}")

    # 2. Network spring layout (data-driven topology)
    if G_51 is not None and G_52 is not None:
        try:
            print("  Generating network_construction_spring (data-driven)...")
            import matplotlib.pyplot as plt
            fig = create_network_spring_figure(
                G_51, G_52,
                output_path=figures_dir / 'network_construction_spring.png',
                top_n=10
            )
            plt.close(fig)
            generated.extend(['network_construction_spring.png', 'network_construction_spring.pdf'])
        except Exception as e:
            print(f"    ERROR: {e}")

    # 2. Connectivity threshold figure (explains why 34% filtration)
    if G_51 is not None:
        try:
            print("  Generating connectivity_threshold_figure...")
            from cfs_toolkit.figures import generate_connectivity_threshold_figure

            max_safe = generate_connectivity_threshold_figure(
                G_51,
                figures_dir / 'connectivity_threshold.png',
                max_pct=50
            )
            print(f"    Max safe filtration: {max_safe}%")
            generated.extend(['connectivity_threshold.png', 'connectivity_threshold.pdf'])
        except Exception as e:
            print(f"    ERROR: {e}")

    print(f"  Generated {len(generated)} publication figures")
    return generated


def generate_gdp_visualizations(centralities_df, output_dir):
    """Generate GDP comparison visualizations."""
    from cfs_toolkit.analysis.gdp_comparison import (
        load_gdp_data,
        compute_gdp_vs_centrality_comparison,
        generate_gdp_centrality_scatter,
        generate_normalized_centrality_bar,
    )

    generated = []
    gdp_dir = output_dir / 'gdp'
    gdp_dir.mkdir(exist_ok=True)

    print("\n  GDP COMPARISON VISUALIZATIONS")
    print("  " + "-" * 40)

    # Load GDP data
    gdp_path = Path('data/state_gdp_2017.csv')
    if not gdp_path.exists():
        print(f"    WARNING: GDP data not found at {gdp_path}")
        return generated

    try:
        gdp_dict = load_gdp_data(gdp_path)
        comparison_df = compute_gdp_vs_centrality_comparison(centralities_df, gdp_dict)

        # 1. GDP vs Eigenvector scatter
        print("  Generating gdp_vs_eigenvector_scatter...")
        generate_gdp_centrality_scatter(comparison_df, gdp_dir / 'gdp_vs_eigenvector_scatter.png')
        generated.extend(['gdp_vs_eigenvector_scatter.png', 'gdp_vs_eigenvector_scatter.pdf'])

        # 2. Normalized centrality bar chart
        print("  Generating gdp_normalized_centrality_bar...")
        generate_normalized_centrality_bar(comparison_df, gdp_dir / 'gdp_normalized_centrality_bar.png')
        generated.extend(['gdp_normalized_centrality_bar.png', 'gdp_normalized_centrality_bar.pdf'])

    except Exception as e:
        print(f"    ERROR: {e}")

    print(f"  Generated {len(generated)} GDP visualizations")
    return generated


def vizall_command(args):
    """Run viz-all command."""

    # List mode
    if args.list:
        list_available_visualizations()
        return 0

    # Check for canonical runs
    if not CANONICAL_DOMESTIC.exists():
        print("No canonical domestic run found. Run the pipeline first:")
        print("  python main.py")
        return 1

    if not CANONICAL_INTL.exists():
        print("No canonical international run found. Run the pipeline with --international first:")
        print("  python main.py --international")
        return 1

    # Setup output directory
    output_dir = Path(args.output) if args.output else Path('results/viz_all_output')
    output_dir.mkdir(parents=True, exist_ok=True)

    print()
    print("=" * 60)
    print("  GENERATING ALL VISUALIZATIONS")
    print("=" * 60)
    print(f"  Domestic run: {CANONICAL_DOMESTIC.name}")
    print(f"  International run: {CANONICAL_INTL.name}")
    print(f"  Output: {output_dir}")
    print("=" * 60)

    # Load data
    print("\n  Loading data...")
    from cfs_toolkit.analysis import load_network_graph

    try:
        centralities_51 = pd.read_csv(CANONICAL_DOMESTIC / 'centralities_51x51_domestic.csv')
        centralities_52 = pd.read_csv(CANONICAL_INTL / 'centralities_52x52_intl.csv')
        # Filter 52 to exclude RoW for comparison
        centralities_52_filtered = centralities_52[centralities_52['label'] != 'RoW'].copy()
        print(f"    51×51: {len(centralities_51)} states")
        print(f"    52×52: {len(centralities_52)} nodes ({len(centralities_52_filtered)} states)")
    except Exception as e:
        print(f"  ERROR loading centralities: {e}")
        return 1

    try:
        G_51 = load_network_graph(CANONICAL_DOMESTIC)
        G_52 = load_network_graph(CANONICAL_INTL)
        print(f"    G_51: {G_51.number_of_nodes()} nodes, {G_51.number_of_edges()} edges")
        print(f"    G_52: {G_52.number_of_nodes()} nodes, {G_52.number_of_edges()} edges")
    except Exception as e:
        print(f"  ERROR loading graphs: {e}")
        G_51, G_52 = None, None

    all_generated = []

    # Generate by category
    category = args.category if hasattr(args, 'category') and args.category else 'all'

    if category in ['all', 'base']:
        generated = generate_base_visualizations(centralities_51, centralities_52_filtered, output_dir)
        all_generated.extend(generated)

    if category in ['all', 'committee']:
        generated = generate_committee_visualizations(centralities_51, centralities_52_filtered, output_dir)
        all_generated.extend(generated)

    if category in ['all', 'matrices'] and G_51 is not None:
        generated = generate_matrix_visualizations(G_51, G_52, output_dir)
        all_generated.extend(generated)

    if category in ['all', 'figures']:
        generated = generate_figure_visualizations(output_dir, G_51, G_52)
        all_generated.extend(generated)

    if category in ['all', 'gdp']:
        generated = generate_gdp_visualizations(centralities_51, output_dir)
        all_generated.extend(generated)

    # Summary
    print()
    print("=" * 60)
    print(f"  COMPLETE: Generated {len(all_generated)} visualization files")
    print("=" * 60)
    print(f"\n  Output directory: {output_dir}")
    print("\n  Subdirectories:")
    for subdir in sorted(output_dir.iterdir()):
        if subdir.is_dir():
            count = len(list(subdir.glob('*')))
            print(f"    {subdir.name}/: {count} files")
    print()

    return 0


def add_vizall_parser(subparsers):
    """Add viz-all subcommand to parser."""
    parser = subparsers.add_parser(
        'viz-all',
        help='Generate all available visualizations',
        description='Batch-generate all implemented visualizations from canonical runs.'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List available visualizations without generating'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output directory (default: results/viz_all_output)'
    )
    parser.add_argument(
        '--category',
        choices=['all', 'base', 'committee', 'matrices', 'figures', 'gdp'],
        default='all',
        help='Generate only specific category (default: all)'
    )
    parser.set_defaults(func=vizall_command)
