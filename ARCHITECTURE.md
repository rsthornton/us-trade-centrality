# Architecture

Orientation for contributors and future sessions. See `README.md` for the research framing and
`web/DESIGN.md` for the dashboard's design system.

## Layers

| Layer | Where | What |
|---|---|---|
| Pipeline | `main.py` + `cfs-network-toolkit/cfs_toolkit/core/` | load → preprocess → build graph → centralities → save. Driven by `configs/*.yaml`. |
| Analysis | `cfs_toolkit/analysis/` | filtration, boundary sensitivity, GDP comparison, commodity decomposition. |
| Canonical results | `results/` | committed pipeline outputs (no raw data needed to explore). |
| Notebooks | `notebooks/` | Marimo exploration / replication / defense. |
| Export bridge | `scripts/export_viz_data.py` | reads `viz/data/*.csv` + the pickled graph → writes `web/public/data/*.json` (the web app's data contract). |
| Web app | `web/` | The Interstate Power Observatory (React 19 + TypeScript + Vite + Tailwind 4; zero-dependency SVG map). |
| Evolution study | `evolution/` | three-survey (2012/2017/2022) pre-registration. **Frozen — see below.** |
| Paper | `paper/` | thesis LaTeX + figures. |

## The frozen guardrail

`evolution/` holds a ResearchHub pre-registration. `evolution/thresholds.yaml` is hashed and the
hash is published; **public registration must precede any full-data run.** Do not modify, move, or
re-run anything under `evolution/` outside a deliberate, post-registration step. CI is scoped to
skip it (`paths-ignore` + no job touches it).

## Data flow

Raw CFS 2017 PUF (gated, ~477 MB, not committed) → pipeline → `results/` + `viz/data/` CSVs →
`scripts/export_viz_data.py` → `web/public/data/*.json` → the React app via `web/src/data/loader.ts`.
The JSON shapes are the contract; `web/src/types.ts` mirrors them, and `tests/test_export_schema.py`
guards them with no gated data. To change a field, change the export script, the type, and the
consuming component together.

## Working on the web app

Use the `trade-observatory` skill, or: read `web/DESIGN.md`, then `cd web && npm install && npm run dev`
(read the port Vite prints). Quality gates: `npm run typecheck && npm run lint && npm run test && npm run build`.
The component gallery is at `#/components` in dev.

## Quality gates

- **Web:** typecheck (tsc strict), eslint, vitest, vite build. CI job `web`.
- **Python:** `ruff check` (advisory for now — the analysis code predates ruff) + `pytest tests/test_export_schema.py`
  (zero gated data). CI job `python`. Config in the root `pyproject.toml`.
- Install the toolkit editable: `pip install -e cfs-network-toolkit/` (metadata in `setup.py`,
  build backend in its `pyproject.toml`).

## Conventions

Conventional commits with the Claude co-author trailer. Web work happens on a feature branch;
Vercel auto-deploys `main` (project `tradeflows`). Prose follows `strategy/writing-style-guide.md`
(no em dashes in user-facing copy).
