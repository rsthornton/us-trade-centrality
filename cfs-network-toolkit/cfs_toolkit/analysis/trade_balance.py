"""
Trade Balance Analysis

Computes per-state trade flow metrics (inflows, outflows, ratios, RoW shares)
from network graph objects. Produces LaTeX tables for thesis appendices.
"""

import pickle
import pandas as pd
import numpy as np
from pathlib import Path

from .gdp_comparison import load_gdp_data
from .control_scatter import load_population_data


def compute_trade_balance_table(
    domestic_gpickle_path, intl_gpickle_path,
    gdp_csv_path, pop_csv_path
):
    """Compute per-state trade balance from domestic + international graphs."""
    with open(domestic_gpickle_path, 'rb') as f:
        G_dom = pickle.load(f)
    with open(intl_gpickle_path, 'rb') as f:
        G_intl = pickle.load(f)

    # Detect RoW node dynamically
    row_node = None
    for n in G_intl.nodes():
        label = G_intl.nodes[n].get('label', '')
        if label == 'RoW' or str(n) == '52':
            row_node = n
            break

    # Compute domestic inflows/outflows from 51×51
    records = []
    for node in G_dom.nodes():
        label = G_dom.nodes[node].get('label', str(node))
        total_out = sum(G_dom[node][s]['weight'] for s in G_dom.successors(node))
        total_in = sum(G_dom[p][node]['weight'] for p in G_dom.predecessors(node))
        ratio = total_in / total_out if total_out > 0 else 0

        # RoW-specific flows from 52×52
        row_out = 0  # state exports to RoW
        row_in = 0   # state imports from RoW
        if row_node is not None and node in G_intl.nodes():
            if G_intl.has_edge(node, row_node):
                row_out = G_intl[node][row_node]['weight']
            if G_intl.has_edge(row_node, node):
                row_in = G_intl[row_node][node]['weight']

        records.append({
            'state_abbrev': label,
            'net_in_dollars': total_in,
            'net_out_dollars': total_out,
            'ratio': ratio,
            'row_in': row_in,
            'row_out': row_out,
        })

    df = pd.DataFrame(records)

    # Compute RoW shares (each state's fraction of total RoW flows)
    total_row_in = df['row_in'].sum()
    total_row_out = df['row_out'].sum()
    df['row_in_share'] = df['row_in'] / total_row_in if total_row_in > 0 else 0
    df['row_out_share'] = df['row_out'] / total_row_out if total_row_out > 0 else 0

    # Domestic-to-international flow ratios per state
    df['dom_in_over_row_in'] = df.apply(
        lambda r: r['net_in_dollars'] / r['row_in'] if r['row_in'] > 0 else np.inf, axis=1
    )
    df['dom_out_over_row_out'] = df.apply(
        lambda r: r['net_out_dollars'] / r['row_out'] if r['row_out'] > 0 else np.inf, axis=1
    )

    # Merge GDP and population
    gdp_data = load_gdp_data(gdp_csv_path)
    gdp_data = {k.strip(): v for k, v in gdp_data.items()}
    pop_data = load_population_data(pop_csv_path)

    df['gdp_billions'] = df['state_abbrev'].map(
        lambda s: gdp_data.get(s, 0) / 1000  # millions → billions
    )
    df['pop_millions'] = df['state_abbrev'].map(
        lambda s: pop_data.get(s, 0) / 1_000_000  # raw → millions
    )

    # Sort by total outflow descending
    df = df.sort_values('net_out_dollars', ascending=False).reset_index(drop=True)

    # Select final columns
    df = df[[
        'state_abbrev', 'net_in_dollars', 'net_out_dollars', 'ratio',
        'row_in_share', 'row_out_share',
        'dom_in_over_row_in', 'dom_out_over_row_out',
        'gdp_billions', 'pop_millions'
    ]]

    return df


def generate_trade_balance_latex(df):
    """Format trade balance DataFrame as LaTeX longtable for appendix."""
    lines = []
    lines.append(r'\begin{footnotesize}')
    lines.append(r'\begin{singlespace}')
    lines.append(r'\begin{longtable}{l r r r r r r r r r}')

    caption = (
        r'\caption{Trade Flow Metrics by State (51$\times$51 Domestic Network, 2017 CFS). '
        r'Net In and Net Out are total inbound and outbound commodity flows in billions USD. '
        r'Ratio = Net In / Net Out (values $>$1 indicate net importer). '
        r'RoW In Share and RoW Out Share are each state\textquotesingle s fraction of total '
        r'cross-border flows with the Rest of World node (52$\times$52 network). '
        r'Dom In/RoW In and Dom Out/RoW Out are ratios of domestic to international '
        r'flows per state (higher = more domestically oriented). '
        r'GDP in billions (2017 Q4 BEA). Pop in millions (2017 ACS). '
        r'States sorted by total outbound trade.}'
    )
    lines.append(caption)
    lines.append(r'\label{tab:trade_balance} \\')

    header = (
        r'\hline'
        '\n'
        r'\textbf{State} & \textbf{Net In (\$B)} & \textbf{Net Out (\$B)} & '
        r'\textbf{Ratio} & \textbf{RoW In} & \textbf{RoW Out} & '
        r'\textbf{Dom In/RoW In} & \textbf{Dom Out/RoW Out} & '
        r'\textbf{GDP (\$B)} & \textbf{Pop (M)} \\'
        '\n'
        r'\hline'
    )

    lines.append(header)
    lines.append(r'\endfirsthead')
    lines.append(r'\hline')
    lines.append(
        r'\textbf{State} & \textbf{Net In (\$B)} & \textbf{Net Out (\$B)} & '
        r'\textbf{Ratio} & \textbf{RoW In} & \textbf{RoW Out} & '
        r'\textbf{Dom In/RoW In} & \textbf{Dom Out/RoW Out} & '
        r'\textbf{GDP (\$B)} & \textbf{Pop (M)} \\'
    )
    lines.append(r'\hline')
    lines.append(r'\endhead')
    lines.append(r'\hline')
    lines.append(r'\endfoot')

    for _, row in df.iterrows():
        net_in_b = row['net_in_dollars'] / 1e9
        net_out_b = row['net_out_dollars'] / 1e9
        ratio = row['ratio']
        row_in_pct = row['row_in_share'] * 100
        row_out_pct = row['row_out_share'] * 100
        di_ri = row['dom_in_over_row_in']
        do_ro = row['dom_out_over_row_out']
        di_ri_s = f"{di_ri:.1f}" if np.isfinite(di_ri) else "---"
        do_ro_s = f"{do_ro:.1f}" if np.isfinite(do_ro) else "---"
        gdp = row['gdp_billions']
        pop = row['pop_millions']

        line = (
            f"{row['state_abbrev']} & "
            f"{net_in_b:.1f} & {net_out_b:.1f} & "
            f"{ratio:.3f} & "
            f"{row_in_pct:.1f}\\% & {row_out_pct:.1f}\\% & "
            f"{di_ri_s} & {do_ro_s} & "
            f"{gdp:.1f} & {pop:.2f} \\\\"
        )
        lines.append(line)

    lines.append(r'\end{longtable}')
    lines.append(r'\end{singlespace}')
    lines.append(r'\end{footnotesize}')

    return '\n'.join(lines)
