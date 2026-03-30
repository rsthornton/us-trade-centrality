# CFS Network Toolkit

Python package for U.S. interstate commodity flow network analysis. Built for the thesis *Testing Network Centrality for Economic Power Measurement: Structure and Boundaries in U.S. Interstate Trade*.

All analysis code is consolidated into this single pip-installable package — core pipeline, analysis modules, figure generation, and visualization. Install with `pip install -e cfs-network-toolkit/` from the repository root.

## Reproducing Paper Analyses

### Publication Figures

```bash
# Generate all 35+ figures
cfs viz-all

# List available categories
cfs viz-all --list
# Output: base, committee, matrices, figures, geographic, gdp

# Generate specific category
cfs viz-all --category gdp
```

**Programmatic:**
```python
from cfs_toolkit.visualizations import (
    create_boundary_sensitivity_summary,
    create_3d_centrality_plot,
    create_centrality_comparison
)
from cfs_toolkit.analysis import load_network_graph
import pandas as pd

# Load canonical results (Nov 29, 2025 - with weight inversion fix)
G_51 = load_network_graph('results/51x51_domestic')
G_52 = load_network_graph('results/52x52_international')
cent_51 = pd.read_csv('results/51x51_domestic/centralities_51x51_domestic.csv')
cent_52 = pd.read_csv('results/52x52_international/centralities_52x52_intl.csv')

create_boundary_sensitivity_summary(cent_51, cent_52, 'figures/boundary_sensitivity.png')
create_3d_centrality_plot(G_51, cent_51, 'figures/3d_centrality_51x51.html')
```

### Edge Weight Distribution

```python
from cfs_toolkit.analysis import load_network_graph, extract_edge_weights, calculate_distribution_stats
from cfs_toolkit.figures import generate_distribution_figure

G_51 = load_network_graph('results/51x51_domestic')
G_52 = load_network_graph('results/52x52_international')

weights_51 = extract_edge_weights(G_51)
weights_52 = extract_edge_weights(G_52)
stats_51 = calculate_distribution_stats(weights_51, '51x51')
stats_52 = calculate_distribution_stats(weights_52, '52x52')

generate_distribution_figure(weights_51, weights_52, stats_51, stats_52,
                            'figures/edge_weight_distribution.png')
```

### Filtration Analysis (Section 4.4)

```python
from cfs_toolkit.core import compute_centralities_at_multiple_thresholds
from cfs_toolkit.analysis import load_network_graph
from cfs_toolkit.figures import generate_rank_stability_figure

G = load_network_graph('results/51x51_domestic')

thresholds = [0, 1e9, 5e9, 1e10, 2e10]
results = compute_centralities_at_multiple_thresholds(G, thresholds)

for measure in ['betweenness', 'eigenvector', 'out_degree']:
    generate_rank_stability_figure(results, measure,
                                   f'figures/rank_stability_{measure}.png')
```

### GDP Comparison (Section 4.5)

```python
from cfs_toolkit.analysis import (
    load_gdp_data,
    compute_gdp_vs_centrality_comparison,
    identify_outliers
)
from cfs_toolkit.analysis.gdp_comparison import (
    generate_gdp_centrality_scatter,
    generate_normalized_centrality_bar
)
import pandas as pd

centralities = pd.read_csv('results/51x51_domestic/centralities_51x51_domestic.csv')
gdp_dict = load_gdp_data('data/state_gdp_2017.csv')

comparison = compute_gdp_vs_centrality_comparison(centralities, gdp_dict)
outliers = identify_outliers(comparison, threshold=5)

generate_gdp_centrality_scatter(comparison, 'figures/gdp_scatter.png')
generate_normalized_centrality_bar(comparison, 'figures/gdp_normalized.png')
```

### Methodology Diagrams (Section 3)

```python
from cfs_toolkit.figures import create_network_construction_figure

create_network_construction_figure('figures/network_construction_schematic.pdf')
```

## Computational Reproducibility

This package guarantees 100% computational reproducibility:

```bash
# Run pipeline and verify against canonical run
python main.py
cfs verify
```

All centrality measures match canonical results at machine precision (difference = 0.0).

## Data Requirements

- `data/cfs_2017_puf.csv` — CFS 2017 Public Use File (~477MB)
- `data/FAF5.7.1_State.csv` — FAF5 state-level flows (~504MB)
- `data/state_gdp_2017.csv` — State GDP data

## Package Structure

```
cfs_toolkit/
├── cli.py + commands/    # 10 CLI commands
├── core/                 # Data loading, network building, centralities
├── analysis/             # Comparative stats, GDP, filtration
├── figures/              # Connectivity threshold, rank stability
└── visualizations/       # Plots, reports, choropleths
```
