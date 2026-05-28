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
cd /path/to/us-trade-centrality
source venv/bin/activate
marimo edit notebooks/companion.py
```

## replication.py — Methodology Replication Notebook

Static replication notebook (5 sections, 18 cells) that delegates all computation to `cfs_toolkit`. Covers data exploration, centrality computation, filtration validation, GDP divergence, and boundary sensitivity. Each cell documents the equivalent `main.py` command for from-scratch replication.

## network_math.py — Network Math for Policymakers

Accessible notebook teaching why network centrality differs from GDP. Designed for non-technical audiences (policymakers, funders, journalists). Built from first principles informed by real communication failures (the "Luke conversation" — where a smart engineer couldn't get past the scalar assumption).

Pedagogical sequence:
1. **GDP baseline** — familiar map, establish common ground
2. **Same Totals, Different Structures** — toy hub-vs-ring network that breaks the scalar assumption
3. **The Surprise** — PRGn divergence map showing 40% of states diverge (results before method)
4. **State Stories** — Kentucky (+14), Florida (zero betweenness) with toy-network callbacks
5. **Look Up Your State** — interactive dropdown with profile card + scatter plot
6. **Why the Math Differs** — "GDP is addition, centrality is multiplication" (concepts after intuition)
7. **Why This Matters** — policy implications, three takeaways

Key design principle: show the output before the method. Let the reader generate hypotheses before formalizing.

```bash
marimo edit notebooks/network_math.py --port 2730
```

## Data Dependencies

Uses canonical Nov 29, 2025 results (with weight inversion fix):
```
results/51x51_domestic/
results/52x52_international/
data/state_gdp_2017.csv
data/state_population_2017.csv
```
