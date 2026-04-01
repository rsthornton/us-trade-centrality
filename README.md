# Measuring Structural Power in U.S. Interstate Commerce

A network centrality analysis of the U.S. interstate commodity trade system using 2017 Census Bureau data. This repository contains the complete analysis pipeline, results, interactive notebooks, and publication figures for the associated master's thesis.

## Quick Start

```bash
# 1. Set up environment
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install -e cfs-network-toolkit/

# 2. Obtain data (see data/README.md for download instructions)
python scripts/setup_data.py   # verify data files are in place

# 3. Run the pipeline
python main.py                 # 51×51 domestic network (default)
python main.py --international # 52×52 with Rest of World node
```

## What This Does

The pipeline builds weighted directed networks from CFS shipment microdata (5.9M records) and computes three centrality measures at macro, meso, and micro scales:

- **Betweenness** (macro) — which states bridge trade routes between others?
- **Eigenvector** (meso) — which states trade with important partners?
- **Weighted out-degree** (micro) — which states ship the most value?

It then validates results through graph filtration (edge removal stress testing) and boundary sensitivity analysis (comparing domestic-only vs. internationally-integrated networks).

## Repository Structure

```
us-trade-centrality/
├── main.py                    # Pipeline entry point
├── configs/                   # YAML pipeline configurations
│   ├── domestic.yaml          #   51×51 (default)
│   ├── international.yaml     #   52×52 with RoW
│   └── filtered_33pct.yaml    #   33% edge filtration
├── cfs-network-toolkit/       # Pip-installable analysis library
│   └── cfs_toolkit/
│       ├── core/              #   Pipeline: load → preprocess → build → centralities
│       ├── analysis/          #   Filtration, boundary sensitivity, GDP comparison
│       ├── figures/           #   Static figure generation
│       ├── visualizations/    #   Publication-ready charts
│       └── commands/          #   CLI interface (cfs <command>)
├── data/                      # Data directory (see data/README.md)
├── results/                   # Canonical pipeline outputs
│   ├── 51x51_domestic/        #   Domestic network results
│   ├── 52x52_international/   #   International network results
│   └── commodity_analysis/    #   Per-SCTG commodity analysis
├── notebooks/                 # Marimo interactive notebooks
│   ├── companion.py           #   5-act interactive exploration
│   ├── replication.py         #   Static replication notebook
│   └── __marimo__/            #   Pre-rendered HTML exports
├── paper/                     # Thesis LaTeX and figures
│   ├── figures/               #   All publication figures (PNG + PDF)
│   └── references.bib
├── scripts/                   # Standalone utilities
│   ├── setup_data.py          #   Data verification
│   ├── generate_phase3_*.py   #   Table/figure generation scripts
│   └── fetch_population.py
├── tests/
│   └── validate_pipeline.py   # End-to-end pipeline validation
└── viz/                       # Interactive Dash visualization app
    ├── app.py                 #   Entry point
    └── data/                  #   Pre-computed data for the app
```

## Data

The pipeline requires the **CFS 2017 Public Use File** (~477 MB, 5,978,523 records) from the U.S. Census Bureau. This file cannot be redistributed. See [`data/README.md`](data/README.md) for download instructions and placement.

The **FAF 5.7.1** dataset (~504 MB) is needed only for the 52×52 international network.

## Reproducing Results

**Canonical results** are included in `results/` — you can explore them immediately without running the pipeline.

**To regenerate from scratch:**

```bash
# Core pipeline (produces centralities + network graph)
python main.py                          # 51×51 domestic
python main.py --international          # 52×52 with RoW

# Publication figures
python -m cfs_toolkit.figures results/51x51_domestic/

# Validation
python tests/validate_pipeline.py
```

**Interactive exploration:**

```bash
marimo edit notebooks/companion.py      # Interactive 5-act notebook
marimo edit notebooks/replication.py    # Static replication
```

## Key Findings

- Three centrality measures reveal distinct structural roles invisible to GDP rankings
- Betweenness centrality diverges ~40% when international trade is included; eigenvector and out-degree remain stable
- All measures prove robust under systematic graph filtration

## Citation

Thesis citation and DOI will be added upon publication.

## License

License information will be added prior to public release.
