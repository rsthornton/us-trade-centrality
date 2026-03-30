"""
CFS Network Toolkit CLI - Interstate Commerce Network Analysis.

Usage:
    cfs <command> [args]

Commands:
    top     Show top N states by centrality measure
    show    Deep dive on a specific state
    ls      List available runs

Examples:
    cfs top                    Top 10 by eigenvector
    cfs top 20 betweenness     Top 20 by betweenness
    cfs show CA                California profile
    cfs ls                     List all runs
"""

import argparse
import sys

from .commands.ls import add_ls_parser
from .commands.top import add_top_parser
from .commands.show import add_show_parser
from .commands.figures import add_figures_parser
from .commands.compare import add_compare_parser
from .commands.gdp import add_gdp_parser
from .commands.verify import add_verify_parser
from .commands.filtration import add_filtration_parser
from .commands.network import add_network_parser
from .commands.vizall import add_vizall_parser


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='cfs',
        description='CFS Network Toolkit - Explore interstate commerce network analysis results.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  cfs top                    Show top 10 states by eigenvector centrality
  cfs top 20 betweenness     Show top 20 states by betweenness centrality
  cfs show CA                Deep dive on California
  cfs show TX                Deep dive on Texas
  cfs ls                     List all available runs

Run the pipeline first:
  python main.py             Generate network analysis results
        """
    )

    parser.add_argument(
        '--version',
        action='version',
        version='cfs 0.1.0'
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(
        title='commands',
        dest='command',
        metavar='<command>'
    )

    # Add individual command parsers
    add_ls_parser(subparsers)
    add_top_parser(subparsers)
    add_show_parser(subparsers)
    add_figures_parser(subparsers)
    add_compare_parser(subparsers)
    add_gdp_parser(subparsers)
    add_verify_parser(subparsers)
    add_filtration_parser(subparsers)
    add_network_parser(subparsers)
    add_vizall_parser(subparsers)

    # Parse arguments
    args = parser.parse_args()

    # If no command given, show help
    if args.command is None:
        parser.print_help()
        return 0

    # Execute the command
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
