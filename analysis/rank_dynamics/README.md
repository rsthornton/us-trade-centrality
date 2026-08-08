# Rank dynamics — temporal null model

**Post-hoc exploratory analysis. Not pre-registered.** The pre-registered
hypotheses and verdicts live in `evolution/`; nothing here touches them.

Extends the committee-response permutation test (May 2026, which compared the
51-node and 52-node boundary rankings against a full-shuffle null) to the
temporal arcs of the evolution study, using the displacement framework of
Morales et al. 2018 (doi:10.3389/fphy.2018.00045) and Iñiguez, Pineda,
Gershenson & Barabási 2022 (doi:10.1038/s41467-022-29256-x).

Two questions, per centrality measure, per arc:

1. **Displacement calibration (m\*)** — how many random single-element
   displacements of the 2017 ranking produce the same Spearman ρ as the
   observed transition? Converts "ρ = 0.985" into an interpretable unit
   of change.
2. **Mobility profile** — |rank change| by starting rank, against the
   zero-flux prediction (closed ranking, no entry/exit: extremes stable,
   middle churns).

## Results (2026-08-08, seed 42, 500 reps)

| Arc | Measure | ρ observed | m* (IQR) | mean shift top10 / mid |
|---|---|---|---|---|
| 2017→2012 | eigenvector | 0.988 | 1 (1–2) | 0.7 / 2.1 |
| 2017→2012 | out_degree | 0.985 | 1 (1–3) | 0.6 / 2.5 |
| 2017→2012 | betweenness | 0.783 | 12 (10–15) | 0.7 / 10.8 |
| 2017→2022 | eigenvector | 0.985 | 1 (1–3) | 1.1 / 2.5 |
| 2017→2022 | out_degree | 0.984 | 1 (1–3) | 1.0 / 2.8 |
| 2017→2022 | betweenness | 0.742 | 15 (12–19) | 1.7 / 8.1 |

Readings:

- Five years of hub-ranking evolution, through COVID, is equivalent to
  roughly **one random displacement** in a 51-element ranking. The
  pre-COVID control interval gives the same answer.
- Betweenness churns at **12–15 displacement-equivalents**, an order of
  magnitude more, and more in the COVID arc (15) than the control (12).
  The pre-registered hub-stable / brokerage-reshuffled split reproduces
  on a calibrated scale.
- Mobility concentrates mid-rank while the top 10 is nearly frozen, in
  line with the zero-flux regime of Iñiguez et al. The extreme-bottom
  bucket is undefined for betweenness: ~31 states have exactly zero
  betweenness and share one tied rank (see the committee-response
  notebook), itself a degeneracy worth reporting.

Observed ρ values reproduce `evolution/results/evolution_20260808_093628/report.md`
exactly, via an independent path from the cached centrality tables.

## Run

```
./venv/bin/python analysis/rank_dynamics/run_rank_dynamics.py
```

Reads `evolution/cache/cfs_{2012,2017,2022}_full.pkl` read-only; writes
`output/rank_dynamics.json`.
