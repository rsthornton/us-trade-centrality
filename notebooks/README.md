# Thesis Companion Notebooks

Interactive exploration of U.S. interstate commerce network analysis results.

## companion.py — Interactive Thesis Companion

Marimo notebook for exploring analysis results interactively. Structured in 5 acts:

1. **Orientation** — Network overview, edge weight distribution, top corridors
2. **Three Lenses** — Betweenness/Eigenvector/Out-degree explained with interactive state selector
3. **Boundary Sensitivity** — 51x51 vs 52x52 comparison (the main finding)
4. **GDP Divergence** — Who punches above their weight?
5. **Validation** — Filtration stability (rho ~ 1.000)

Features interactive state selector with profile cards, Altair visualizations (choropleth maps, scatter plots), master state dataframe (GDP + centralities + flows), and filtration slider.

```bash
cd /path/to/cfs-network-analysis
source venv/bin/activate
marimo edit notebooks/companion.py
```

## replication.py — Methodology Replication Notebook

Static replication notebook (5 sections, 18 cells) that delegates all computation to `cfs_toolkit`. Covers data exploration, centrality computation, filtration validation, GDP divergence, and boundary sensitivity. Each cell documents the equivalent `main.py` command for from-scratch replication.

## Data Dependencies

Uses canonical Nov 29, 2025 results (with weight inversion fix):
```
results/51x51_domestic/
results/52x52_international/
data/state_gdp_2017.csv
data/state_population_2017.csv
```
