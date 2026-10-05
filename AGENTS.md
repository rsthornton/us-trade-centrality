# AGENTS.md

Instructions for any coding agent working in this repository. The research framing
is [`README.md`](README.md); the layer map is [`ARCHITECTURE.md`](ARCHITECTURE.md);
the dashboard's design system is [`web/DESIGN.md`](web/DESIGN.md).

## What this is

Network centrality on the 2017 Commodity Flow Survey: a Python pipeline
(`main.py` + `cfs-network-toolkit/`), committed canonical results (`results/`),
Marimo notebooks, the thesis LaTeX (`paper/`), and the Interstate Power Observatory
web app (`web/`, live at ustradeflow.systems).

## First commands

```bash
python -m venv .venv && source .venv/bin/activate   # project venv; never install globally
pip install -r requirements.txt && pip install -e cfs-network-toolkit/
python main.py                     # 51×51 domestic (default); --international for 52×52
python tests/validate_pipeline.py  # end-to-end validation

cd web && npm ci && npm run dev    # the Observatory
```

CI (`.github/workflows/ci.yml`) runs, and a change should pass before it is pushed:
`npm run typecheck`, `npm run lint`, `npm run test`, `npm run build` in `web/`;
`ruff check cfs-network-toolkit scripts tests main.py`; `pytest tests/test_export_schema.py`.

## Do not touch

- **`evolution/` is frozen.** It holds a ResearchHub pre-registration whose
  `thresholds.yaml` hash is published. Do not modify, move, or re-run anything under
  it outside a deliberate post-registration step. CI skips it.
- **Raw data is never committed.** The raw files (`data/cfs_2017_puf.csv`,
  `data/FAF5*.csv`) are gitignored; the CFS 2017 Public Use File cannot be
  redistributed. `data/README.md` says how to obtain them. The derived tables in
  `data/` are tracked.
- `results/` holds the canonical pipeline outputs; change them only by re-running
  the pipeline.
- `web/public/data/*.json` is the web app's data contract, written by
  `scripts/export_viz_data.py`; regenerate it with that script.

## Commits

- Conventional commits; AI-written commits carry the writing tool's co-author
  trailer.
- **Exception: thesis ETD revisions** (formal academic submission, `paper/`):
  lowercase, minimal, no conventional prefix, no AI attribution.
