# Three-Survey Evolution Study

Extends the thesis pipeline (2017 CFS) across all three surveys: 2012, 2017, 2022.
2017 is the anchor. The retrodiction arc (2017 -> 2012) tests pre-period stability
and is expected to hold. The prediction arc (2017 -> 2022) is the live forecast.
Retrodiction holding while the prediction breaks quantifies COVID-era structural
disruption.

Pre-registered thresholds live in `thresholds.yaml`. The ResearchHub proposal
(vault: `coordination/clients/researchhub-cfs-proposal-v1.md`) quotes those numbers
verbatim; change them in both places or neither.

## Setup (once)

```sh
cd ..                                # repo root
python3 -m venv venv
./venv/bin/pip install -r requirements.txt scikit-learn -e ./cfs-network-toolkit
```

Data (all already on disk as of 2026-06-10):

| Year | File | Status |
|---|---|---|
| 2012 | `archive/reference/cfs_2012_pumf_csv.txt` (359 MB, 4.5M rows) | downloaded via `data/fetch_cfs_2012.sh` |
| 2017 | `archive/research/cfs-network-analysis/data/cfs_2017_puf.csv` (477 MB) | thesis original |
| 2022 | `archive/reference/cfs_2022_pums.csv` (2.6 GB, 37.5M rows) | PUMS (sample, weighted) |

State GDP controls: `data/state_gdp_2012.csv` and `data/state_gdp_2022.csv`, built
from BEA SQGDP1 (current-dollar, Q4) by `data/build_state_gdp.py`; schema matches
the thesis `data/state_gdp_2017.csv`.

## Run

```sh
source ../venv/bin/activate
python run_evolution.py --sample 200000   # smoke run, ~1 min
python run_evolution.py                   # full run (the Saturday button)
```

Outputs land in `results/evolution_<timestamp>/`:

- `report.md` - gates, verdict table (Hn-R / Hn-P -> HOLD / BREAK), year stats
- `results.json` - full machine-readable results, thresholds sha256, config trail
- `thresholds.yaml` - copy of the exact thresholds evaluated

Year bundles cache to `cache/` keyed by sample size; `--refresh-cache` rebuilds.

## Before the full run

- Fill `gates.published_totals` in `thresholds.yaml` from the Census CFS
  publications (national weighted totals per year) so the national-total gate
  evaluates PASS/FAIL instead of REVIEW.
- SCTG 16 (crude petroleum) is excluded from every year automatically: it is out
  of scope in 2022. Grouped codes covering 16 (e.g. 15-19) are also dropped for
  parity; the report logs how many records that removes.

## Module map

- `src/loaders.py` - year-aware load/preprocess/build on top of `cfs_toolkit`
- `src/gates.py` - go/no-go gates (national totals, grouped-code share, truncation)
- `src/hypotheses.py` - H1-H5 tests; reuses `cfs_toolkit.analysis.comparison_utils`
- `run_evolution.py` - orchestration + auditable artifacts
