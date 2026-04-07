"""
Centrality vs. Control Variable Scatter Plots

Generalized scatter functions for comparing centrality measures against
control variables (GDP, Population, etc.) with Spearman rank correlation.
Also supports control-vs-control comparisons and LaTeX rho table generation.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from scipy.stats import spearmanr
from adjustText import adjust_text
from matplotlib.patches import Patch


def load_population_data(pop_csv_path):
    """
    Load population data from cleaned CSV file.

    Parameters
    ----------
    pop_csv_path : str or Path
        Path to state_population_2017.csv

    Returns
    -------
    dict
        Dictionary mapping state_abbrev to pop_2017_acs
    """
    df = pd.read_csv(pop_csv_path)
    df['state_abbrev'] = df['state_abbrev'].str.strip()
    return dict(zip(df['state_abbrev'], df['pop_2017_acs']))


def generate_control_scatter(
    centralities_df, control_data, centrality_measure, control_name,
    control_unit, output_path, label_threshold=8, rank_method='first'
):
    """
    Create publication-quality scatter plot comparing a control variable rank
    to a centrality measure rank, with Spearman rho annotation.

    Parameters
    ----------
    centralities_df : pd.DataFrame
        Centrality data with columns: state_id, label, <centrality_measure>,
        rank_<centrality_measure>
    control_data : dict
        State abbreviation to control variable value mapping
    centrality_measure : str
        One of 'betweenness', 'eigenvector', 'out_degree'
    control_name : str
        Display name for the control variable (e.g., 'GDP', 'Population')
    control_unit : str
        Unit string for axis label (e.g., '2017 Q4', '2017 ACS')
    output_path : str or Path
        Path for output PNG file (will also create PDF version)
    label_threshold : int, default=8
        Label states with |rank_diff| >= this value in bold
    rank_method : str, default='first'
        Ranking method for scatter positions. 'first' gives visual separation
        for tied values (e.g., 31 states with zero betweenness).

    Returns
    -------
    tuple[float, float]
        (spearman_rho, p_value) computed with method='min' ranking
    """
    # Build working dataframe
    df = centralities_df.copy()
    df['state_abbrev'] = df['label'].str.strip()
    df['control_value'] = df['state_abbrev'].map(control_data)

    # Drop any states without control data
    df = df.dropna(subset=['control_value'])

    # Compute control rank (1 = highest value)
    df['control_rank'] = df['control_value'].rank(ascending=False, method='min').astype(int)

    # Compute centrality rank for scatter positions using specified method
    # This gives visual separation for tied values
    df['centrality_rank_scatter'] = df[centrality_measure].rank(
        ascending=False, method=rank_method
    ).astype(int)

    # Compute rank difference (positive = overperformer)
    df['rank_diff'] = df['control_rank'] - df['centrality_rank_scatter']

    # Spearman correlation using method='min' to match canonical cited values
    df['control_rank_min'] = df['control_value'].rank(ascending=False, method='min')
    df['centrality_rank_min'] = df[centrality_measure].rank(ascending=False, method='min')
    rho, p_value = spearmanr(df['control_rank_min'], df['centrality_rank_min'])

    # Clean centrality name for display
    measure_display = centrality_measure.replace('_', '-').title()
    if centrality_measure == 'out_degree':
        measure_display = 'Out-Degree'

    # Set publication style
    sns.set_style("whitegrid")
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.size'] = 14

    fig, ax = plt.subplots(figsize=(10, 8))

    # Color mapping (red = overperformer, blue = underperformer, gray = neutral)
    colors = df['rank_diff'].apply(
        lambda x: '#d62728' if x > 0 else '#1f77b4' if x < 0 else '#7f7f7f'
    )

    # Scatter plot
    ax.scatter(
        df['control_rank'],
        df['centrality_rank_scatter'],
        c=colors,
        s=80,
        alpha=0.7,
        edgecolors='black',
        linewidth=0.5
    )

    # Diagonal reference line (perfect correspondence)
    ax.plot([0, 54], [0, 54], 'k--', alpha=0.3, linewidth=1,
            label=f'{control_name} = Centrality')

    # Label all states using adjustText
    texts = []
    for _, row in df.iterrows():
        x, y = row['control_rank'], row['centrality_rank_scatter']
        fontweight = 'bold' if abs(row['rank_diff']) >= label_threshold else 'normal'
        fontsize = 13 if abs(row['rank_diff']) >= label_threshold else 10
        t = ax.text(x, y, row['state_abbrev'],
                    fontsize=fontsize, fontweight=fontweight, ha='center', va='center')
        texts.append(t)

    adjust_text(texts, ax=ax,
                arrowprops=dict(arrowstyle='-', color='gray', alpha=0.4, lw=0.5),
                expand=(1.5, 1.5),
                force_text=(0.8, 0.8),
                force_points=(0.5, 0.5))

    # Axes and labels
    ax.set_xlabel(f'{control_name} Rank ({control_unit})  \u2190 Larger', fontsize=17)
    ax.set_ylabel(f'{measure_display} Centrality Rank (51\u00d751)  \u2190 More Central',
                  fontsize=17)
    ax.set_title(
        f'{control_name} vs. {measure_display} Centrality',
        fontsize=19,
        fontweight='bold',
        pad=15
    )

    # Invert axes (rank 1 = best)
    ax.invert_xaxis()
    ax.invert_yaxis()

    # Axis limits
    ax.set_xlim(54, -2)
    ax.set_ylim(54, -2)

    # Grid
    ax.grid(True, alpha=0.3)

    # Spearman annotation box (lower-right, committee.py style)
    stats_text = f"\u03c1 = {rho:.3f}"
    ax.text(0.97, 0.03, stats_text,
            transform=ax.transAxes, va='bottom', ha='right',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white',
                      alpha=0.9, edgecolor='gray', linewidth=1.5),
            fontsize=14, fontweight='bold', family='monospace')

    # Legend
    legend_elements = [
        Patch(facecolor='#d62728', label=f'Overperformer (Centrality > {control_name})'),
        Patch(facecolor='#1f77b4', label=f'Underperformer (Centrality < {control_name})'),
        plt.Line2D([0], [0], color='k', linestyle='--', label='Perfect Correspondence')
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=14,
              framealpha=0.9, edgecolor='gray')

    plt.tight_layout()

    # Save as both PNG and PDF
    output_path = Path(output_path)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.savefig(output_path.with_suffix('.pdf'), bbox_inches='tight')
    plt.close()

    print(f"\u2713 Scatter plot saved: {output_path}")
    print(f"\u2713 PDF version saved: {output_path.with_suffix('.pdf')}")

    return rho, p_value


def generate_control_vs_control_scatter(
    x_data, y_data, x_name, y_name, x_unit, y_unit,
    output_path, label_threshold=8
):
    """
    Create publication-quality scatter plot comparing two control variables
    (e.g., GDP vs Population) with Spearman rho annotation.

    Parameters
    ----------
    x_data : dict
        State abbreviation to x-variable value mapping
    y_data : dict
        State abbreviation to y-variable value mapping
    x_name : str
        Display name for x variable (e.g., 'GDP')
    y_name : str
        Display name for y variable (e.g., 'Population')
    x_unit : str
        Unit string for x-axis label (e.g., '2017 Q4')
    y_unit : str
        Unit string for y-axis label (e.g., '2017 ACS')
    output_path : str or Path
        Path for output PNG file (will also create PDF version)
    label_threshold : int, default=8
        Label states with |rank_diff| >= this value in bold

    Returns
    -------
    tuple[float, float]
        (spearman_rho, p_value)
    """
    # Build working dataframe from intersection of both dicts
    common = set(x_data.keys()) & set(y_data.keys())
    df = pd.DataFrame({
        'state_abbrev': list(common),
        'x_value': [x_data[s] for s in common],
        'y_value': [y_data[s] for s in common],
    })

    # Rank both (1 = highest)
    df['x_rank'] = df['x_value'].rank(ascending=False, method='first').astype(int)
    df['y_rank'] = df['y_value'].rank(ascending=False, method='first').astype(int)
    df['rank_diff'] = df['x_rank'] - df['y_rank']

    # Spearman on min-ranked values (for canonical rho)
    df['x_rank_min'] = df['x_value'].rank(ascending=False, method='min')
    df['y_rank_min'] = df['y_value'].rank(ascending=False, method='min')
    rho, p_value = spearmanr(df['x_rank_min'], df['y_rank_min'])

    # Publication style matching generate_control_scatter
    sns.set_style("whitegrid")
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.size'] = 14

    fig, ax = plt.subplots(figsize=(10, 8))

    colors = df['rank_diff'].apply(
        lambda x: '#d62728' if x > 0 else '#1f77b4' if x < 0 else '#7f7f7f'
    )

    ax.scatter(
        df['x_rank'], df['y_rank'],
        c=colors, s=80, alpha=0.7,
        edgecolors='black', linewidth=0.5
    )

    ax.plot([0, 54], [0, 54], 'k--', alpha=0.3, linewidth=1,
            label=f'{x_name} Rank = {y_name} Rank')

    texts = []
    for _, row in df.iterrows():
        x, y = row['x_rank'], row['y_rank']
        fontweight = 'bold' if abs(row['rank_diff']) >= label_threshold else 'normal'
        fontsize = 13 if abs(row['rank_diff']) >= label_threshold else 10
        t = ax.text(x, y, row['state_abbrev'],
                    fontsize=fontsize, fontweight=fontweight, ha='center', va='center')
        texts.append(t)

    adjust_text(texts, ax=ax,
                arrowprops=dict(arrowstyle='-', color='gray', alpha=0.4, lw=0.5),
                expand=(1.5, 1.5),
                force_text=(0.8, 0.8),
                force_points=(0.5, 0.5))

    ax.set_xlabel(f'{x_name} Rank ({x_unit})  \u2190 Larger', fontsize=17)
    ax.set_ylabel(f'{y_name} Rank ({y_unit})  \u2190 Larger', fontsize=17)
    ax.set_title(f'{x_name} vs. {y_name}', fontsize=19, fontweight='bold', pad=15)

    ax.invert_xaxis()
    ax.invert_yaxis()
    ax.set_xlim(54, -2)
    ax.set_ylim(54, -2)
    ax.grid(True, alpha=0.3)

    stats_text = f"\u03c1 = {rho:.3f}"
    ax.text(0.97, 0.03, stats_text,
            transform=ax.transAxes, va='bottom', ha='right',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white',
                      alpha=0.9, edgecolor='gray', linewidth=1.5),
            fontsize=14, fontweight='bold', family='monospace')

    legend_elements = [
        Patch(facecolor='#d62728', label=f'{x_name} rank > {y_name} rank'),
        Patch(facecolor='#1f77b4', label=f'{y_name} rank > {x_name} rank'),
        plt.Line2D([0], [0], color='k', linestyle='--', label='Perfect Correspondence')
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=14,
              framealpha=0.9, edgecolor='gray')

    plt.tight_layout()

    output_path = Path(output_path)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.savefig(output_path.with_suffix('.pdf'), bbox_inches='tight')
    plt.close()

    print(f"\u2713 Control scatter saved: {output_path}")
    print(f"\u2713 PDF version saved: {output_path.with_suffix('.pdf')}")

    return rho, p_value


def generate_rho_table_latex(rho_results):
    """
    Generate a 2×3 LaTeX table of Spearman rho values.

    Parameters
    ----------
    rho_results : list of tuples
        Each tuple: (control_name, centrality_name, rho, p_value)
        Expected: 6 tuples covering GDP and Population × 3 centrality measures.

    Returns
    -------
    str
        Complete LaTeX table environment ready for \\input{}.
    """
    # Pivot into a lookup
    lookup = {}
    for control, measure, rho, pval in rho_results:
        lookup[(control, measure)] = rho

    measures = ['eigenvector', 'betweenness', 'out_degree']
    measure_labels = ['Eigenvector', 'Betweenness', 'Out-Degree']
    controls = ['GDP', 'Population']

    lines = []
    lines.append(r'\begin{table}[ht]')
    lines.append(r'\centering')
    lines.append(r'\caption{Spearman rank correlations ($\rho$) between control variables '
                 r'and centrality measures (51$\times$51 domestic network). '
                 r'All correlations significant at $p < 0.001$.}')
    lines.append(r'\label{tab:rho_correlations}')
    lines.append(r'\begin{tabular}{l c c c}')
    lines.append(r'\hline')
    lines.append(r' & \textbf{Eigenvector} & \textbf{Betweenness} & \textbf{Out-Degree} \\')
    lines.append(r'\hline')

    for control in controls:
        cells = []
        for measure in measures:
            rho = lookup.get((control, measure), 0)
            cells.append(f'${rho:.3f}$')
        lines.append(f'\\textbf{{{control}}} & {" & ".join(cells)} \\\\')

    lines.append(r'\hline')
    lines.append(r'\end{tabular}')
    lines.append(r'\end{table}')

    return '\n'.join(lines)
