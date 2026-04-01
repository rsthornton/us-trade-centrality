"""
cfs show - Deep dive on a specific state.

Usage:
    cfs show CA                Show California profile
    cfs show TX                Show Texas profile
    cfs show --run results/X   From specific run
"""

from pathlib import Path

from cfs_toolkit.analysis import load_network_graph
from cfs_toolkit.commands._utils import STATE_NAMES, find_latest_run, load_centralities


def format_dollars(value):
    """Format dollar values in human-readable form."""
    if value >= 1e12:
        return f"${value/1e12:.1f}T"
    elif value >= 1e9:
        return f"${value/1e9:.1f}B"
    elif value >= 1e6:
        return f"${value/1e6:.0f}M"
    else:
        return f"${value:,.0f}"


def get_rank(df, state, measure):
    """Get rank of state for a measure (1-indexed)."""
    df_sorted = df.sort_values(measure, ascending=False).reset_index(drop=True)
    matches = df_sorted[df_sorted['label'] == state].index
    if len(matches) == 0:
        return None
    return matches[0] + 1


def make_bar(value, max_val, width=30):
    """Create a simple ASCII bar chart element."""
    if max_val == 0:
        return ""
    filled = int((value / max_val) * width)
    return "█" * filled


def show_command(args):
    """Show detailed profile for a specific state."""
    state = args.state.upper()

    # Validate state
    if state not in STATE_NAMES:
        print(f"Unknown state: {state}")
        print("Use two-letter state abbreviation (e.g., CA, TX, NY)")
        return 1

    # Determine run directory
    if args.run:
        run_dir = Path(args.run)
    else:
        run_dir = find_latest_run(args.results_dir)

    if not run_dir or not run_dir.exists():
        print("No run directory found. Run the pipeline first:")
        print("  python main.py")
        return 1

    # Load data
    df = load_centralities(run_dir)
    try:
        G = load_network_graph(run_dir)
    except FileNotFoundError:
        G = None

    if df is None:
        print(f"No centralities file found in: {run_dir}")
        return 1

    # Get state data
    state_row = df[df['label'] == state]
    if state_row.empty:
        print(f"State {state} not found in results")
        return 1

    state_data = state_row.iloc[0]
    full_name = STATE_NAMES[state]

    # Calculate ranks
    bet_rank = get_rank(df, state, 'betweenness')
    eig_rank = get_rank(df, state, 'eigenvector')
    deg_rank = get_rank(df, state, 'out_degree')
    n_states = len(df)

    # Print header
    print()
    print(f"{full_name.upper()} ({state})")
    print("═" * 40)

    # Centrality rankings with bars
    print()
    print("  CENTRALITY RANKINGS")
    print("  ───────────────────")

    bet_val = state_data['betweenness']
    eig_val = state_data['eigenvector']
    deg_val = state_data['out_degree']

    max_val = max(df['betweenness'].max(), df['eigenvector'].max(), df['out_degree'].max())

    print(f"  Betweenness:   #{bet_rank:<2} ({bet_val:.3f})  {make_bar(bet_val, max_val, 20)}")
    print(f"  Eigenvector:   #{eig_rank:<2} ({eig_val:.3f})  {make_bar(eig_val, max_val, 20)}")
    print(f"  Out-Degree:    #{deg_rank:<2} ({deg_val:.3f})  {make_bar(deg_val, max_val, 20)}")

    # Interpretation
    print()
    print("  INTERPRETATION")
    print("  ──────────────")

    # Generate interpretation based on rankings
    interp_parts = []
    if bet_rank <= 3:
        interp_parts.append(f"#{bet_rank} bridge state (betweenness)")
    if eig_rank <= 3:
        interp_parts.append(f"#{eig_rank} in network influence (eigenvector)")
    if deg_rank <= 3:
        interp_parts.append(f"#{deg_rank} in distribution capacity (out-degree)")

    if interp_parts:
        print(f"  {state} is {', '.join(interp_parts)}.")
    else:
        avg_rank = (bet_rank + eig_rank + deg_rank) / 3
        print(f"  {state} ranks ~#{int(avg_rank)} on average across measures.")

    # Trading partners (if network loaded)
    # Find state node ID from label attribute
    state_node = None
    if G is not None:
        for node, data in G.nodes(data=True):
            if data.get('label') == state:
                state_node = node
                break

    if G is not None and state_node is not None:
        print()
        print("  TOP OUTFLOWS (to)")
        print("  ─────────────────")

        # Get outflows
        outflows = []
        for neighbor in G.successors(state_node):
            weight = G[state_node][neighbor].get('weight', 0)
            neighbor_label = G.nodes[neighbor].get('label', str(neighbor))
            outflows.append((neighbor_label, weight))

        outflows.sort(key=lambda x: x[1], reverse=True)
        top_out = outflows[:5]

        if top_out:
            out_str = "  " + "    ".join([f"→ {s} {format_dollars(w)}" for s, w in top_out])
            # Wrap if too long
            print(out_str[:78])
            if len(out_str) > 78:
                print("  " + out_str[78:156])

        print()
        print("  TOP INFLOWS (from)")
        print("  ──────────────────")

        # Get inflows
        inflows = []
        for predecessor in G.predecessors(state_node):
            weight = G[predecessor][state_node].get('weight', 0)
            predecessor_label = G.nodes[predecessor].get('label', str(predecessor))
            inflows.append((predecessor_label, weight))

        inflows.sort(key=lambda x: x[1], reverse=True)
        top_in = inflows[:5]

        if top_in:
            in_str = "  " + "    ".join([f"← {s} {format_dollars(w)}" for s, w in top_in])
            print(in_str[:78])
            if len(in_str) > 78:
                print("  " + in_str[78:156])

    print()
    return 0


def add_show_parser(subparsers):
    """Add show subcommand to parser."""
    parser = subparsers.add_parser(
        'show',
        help='Deep dive on a specific state',
        description='Display detailed centrality profile and trading partners for a state.'
    )
    parser.add_argument(
        'state',
        help='State abbreviation (e.g., CA, TX, NY)'
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
    parser.set_defaults(func=show_command)
