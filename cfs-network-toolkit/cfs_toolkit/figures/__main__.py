"""
CLI interface for publication figure generation.

Usage:
    python -m cfs_toolkit.figures --all
    python -m cfs_toolkit.figures --filtration
    python -m cfs_toolkit.figures --distribution
    python -m cfs_toolkit.figures --diagrams
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
import numpy as np

from cfs_toolkit.figures import (
    generate_rank_stability_figure,
    generate_distribution_figure,
    create_network_construction_figure,
    create_centrality_framework_diagram,
)
from cfs_toolkit.analysis import load_network_graph, extract_edge_weights


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate publication-quality figures from thesis results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all figures
  python -m cfs_toolkit.figures --all

  # Generate specific figure types
  python -m cfs_toolkit.figures --diagrams
  python -m cfs_toolkit.figures --distribution
  python -m cfs_toolkit.figures --filtration

  # Specify custom output directory
  python -m cfs_toolkit.figures --all --output figures/
        """
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Generate all publication figures'
    )

    parser.add_argument(
        '--diagrams',
        action='store_true',
        help='Generate methodology diagrams (network construction, centrality framework)'
    )

    parser.add_argument(
        '--distribution',
        action='store_true',
        help='Generate edge weight distribution figures'
    )

    parser.add_argument(
        '--filtration',
        action='store_true',
        help='Generate filtration rank stability figures (requires filtration results)'
    )

    parser.add_argument(
        '--domestic-run',
        type=Path,
        default=Path('results/51x51_domestic_20251111_115541'),
        help='Path to 51x51 domestic results directory (default: canonical Nov 11 run)'
    )

    parser.add_argument(
        '--intl-run',
        type=Path,
        default=Path('results/52x52_intl_20251111_115620'),
        help='Path to 52x52 international results directory (default: canonical Nov 11 run)'
    )

    parser.add_argument(
        '--output',
        type=Path,
        default=Path('results/publication_figures'),
        help='Output directory for generated figures (default: results/publication_figures)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    return parser.parse_args()


def generate_diagrams(output_dir, verbose=False):
    """Generate methodology diagrams."""
    print("\n" + "=" * 80)
    print("GENERATING METHODOLOGY DIAGRAMS")
    print("=" * 80)
    print()

    # Network construction schematic
    print("Step 1: Generating network construction schematic...")
    output_path = output_dir / "fig_network_construction_schematic.pdf"
    create_network_construction_figure(output_path)
    print(f"✓ Saved: {output_path}")

    # Centrality framework diagram
    print("\nStep 2: Generating centrality framework diagram...")
    output_path = output_dir / "fig_centrality_framework.pdf"
    create_centrality_framework_diagram(output_path)
    print(f"✓ Saved: {output_path}")


def generate_distributions(domestic_run, intl_run, output_dir, verbose=False):
    """Generate edge weight distribution figures."""
    print("\n" + "=" * 80)
    print("GENERATING EDGE WEIGHT DISTRIBUTIONS")
    print("=" * 80)
    print()

    # Load networks
    print("Step 1: Loading network graphs...")
    G_51 = load_network_graph(domestic_run)
    G_52 = load_network_graph(intl_run)
    print(f"✓ Loaded 51×51: {G_51.number_of_nodes()} nodes, {G_51.number_of_edges()} edges")
    print(f"✓ Loaded 52×52: {G_52.number_of_nodes()} nodes, {G_52.number_of_edges()} edges")

    # Extract edge weights
    print("\nStep 2: Extracting edge weights...")
    weights_51 = extract_edge_weights(G_51)
    weights_52 = extract_edge_weights(G_52)

    # Calculate statistics
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

    print(f"✓ 51×51 stats: mean=${stats_51['mean']:,.0f}, median=${stats_51['median']:,.0f}")
    print(f"✓ 52×52 stats: mean=${stats_52['mean']:,.0f}, median=${stats_52['median']:,.0f}")

    # Generate figure
    print("\nStep 3: Generating distribution figure...")
    output_path = output_dir / "fig_edge_weight_distribution.png"
    generate_distribution_figure(weights_51, weights_52, stats_51, stats_52, output_path)
    print(f"✓ Saved: {output_path}")


def generate_filtration_figures(domestic_run, output_dir, verbose=False):
    """Generate filtration rank stability figures."""
    print("\n" + "=" * 80)
    print("GENERATING FILTRATION RANK STABILITY FIGURES")
    print("=" * 80)
    print()

    # Check for filtration results
    filtration_file = domestic_run / "filtration_results.csv"
    if not filtration_file.exists():
        print(f"⚠️  Filtration results not found: {filtration_file}")
        print("   Run filtration analysis first (not yet implemented in pipeline)")
        print("   Skipping filtration figures...")
        return

    # Load filtration results
    print("Step 1: Loading filtration results...")
    results_df = pd.read_csv(filtration_file)
    print(f"✓ Loaded filtration results: {len(results_df)} rows")

    # Generate figure for each centrality measure
    measures = ['betweenness', 'eigenvector', 'out_degree']
    for i, measure in enumerate(measures, 1):
        print(f"\nStep {i+1}: Generating {measure} rank stability figure...")
        output_path = output_dir / f"fig_filtration_rank_stability_{measure}.png"
        generate_rank_stability_figure(results_df, measure, output_path)
        print(f"✓ Saved: {output_path}")


def main():
    """Execute figure generation CLI."""
    args = parse_arguments()

    # Validate inputs
    if not args.domestic_run.exists():
        print(f"ERROR: Domestic results not found: {args.domestic_run}")
        print("Please ensure canonical results exist or specify --domestic-run")
        sys.exit(1)

    if not args.intl_run.exists():
        print(f"ERROR: International results not found: {args.intl_run}")
        print("Please ensure canonical results exist or specify --intl-run")
        sys.exit(1)

    # Create output directory
    args.output.mkdir(exist_ok=True, parents=True)

    print("=" * 80)
    print("PUBLICATION FIGURE GENERATION")
    print("=" * 80)
    print(f"Domestic results: {args.domestic_run}")
    print(f"International results: {args.intl_run}")
    print(f"Output directory: {args.output}")
    print("=" * 80)

    # Determine which figures to generate
    generate_all = args.all or not any([args.diagrams, args.distribution, args.filtration])

    figures_generated = 0

    # Generate diagrams
    if generate_all or args.diagrams:
        generate_diagrams(args.output, args.verbose)
        figures_generated += 2

    # Generate distribution figures
    if generate_all or args.distribution:
        generate_distributions(args.domestic_run, args.intl_run, args.output, args.verbose)
        figures_generated += 1

    # Generate filtration figures
    if generate_all or args.filtration:
        generate_filtration_figures(args.domestic_run, args.output, args.verbose)
        # Filtration generates 3 figures (one per measure), but may skip if data missing
        # Don't count here to avoid misleading count

    # Summary
    print("\n" + "=" * 80)
    print("FIGURE GENERATION COMPLETE")
    print("=" * 80)
    print(f"Output directory: {args.output}/")
    print(f"Figures generated: Check output directory for all files")
    print("=" * 80)


if __name__ == '__main__':
    main()
