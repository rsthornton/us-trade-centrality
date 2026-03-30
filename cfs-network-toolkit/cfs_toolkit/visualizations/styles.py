"""
Visualization Styles Module
===========================
Centralized styling configuration for all visualizations.
Avoids import-time plt.rcParams configuration for reliable style isolation.
"""

import matplotlib.pyplot as plt
import seaborn as sns

# Color palette
COLORS = {
    'primary': '#2166ac',
    'secondary': '#d73027',
    'tertiary': '#5aae61',
    'highlight': '#762a83',
    'neutral': 'steelblue'
}

def set_publication_style():
    """Configure matplotlib for publication-quality figures."""
    plt.rcParams['figure.dpi'] = 300
    plt.rcParams['savefig.dpi'] = 300
    plt.rcParams['font.size'] = 13
    plt.rcParams['axes.titlesize'] = 16
    plt.rcParams['axes.labelsize'] = 14
    plt.rcParams['xtick.labelsize'] = 12
    plt.rcParams['ytick.labelsize'] = 12
    plt.rcParams['legend.fontsize'] = 12

def set_committee_style():
    """Configure styling for committee-ready visualizations."""
    set_publication_style()
    plt.rcParams['figure.figsize'] = (10, 6)
    plt.rcParams['axes.spines.top'] = False
    plt.rcParams['axes.spines.right'] = False

def set_matrix_style():
    """Configure styling for trade matrix visualizations."""
    set_publication_style()
    plt.rcParams['figure.figsize'] = (12, 10)

def get_color_palette():
    """Return the standard color palette."""
    return COLORS

def apply_seaborn_style():
    """Apply seaborn styling with custom parameters."""
    sns.set_style("whitegrid")
    sns.set_palette([COLORS['primary'], COLORS['secondary'], COLORS['tertiary']])