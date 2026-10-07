# Research log: state roles

Dated decisions and findings, newest last. Method and full results are in
`README.md`; numbers here come from `output/state_roles.json`.

## 2026-10-07: origin and first pass

**Context.** After the thesis (2017 network) and the pre-registered ResearchHub
study (2012, 2017, 2022), the working question moved from "is network position
different from GDP" to "which states power interstate activity, and in what
different ways." The first draft was a set of design boards (a periodic table of
state roles, a tile map, an element key); see `figures/`.

**Decisions.**
- Six roles, each defined by a rule and a counterfactual: Engine, Sustainer,
  Router, Specialist, Market, Generalist. Priority order in `roles.yaml`.
- "Sustainer" names states that sustain production in the engines; an earlier
  draft name was dropped.
- All three years run through the evolution cache, so they share one pipeline
  (SCTG 16 excluded everywhere). 2017 ranks can differ slightly from the thesis.
- The router rule is applied per year, with a separate decade flag (router in at
  least two of three years), because betweenness churns an order of magnitude
  more than the other measures (`analysis/rank_dynamics/`).

**Findings.**
- 30 of 51 states hold the same role in all three years.
- The thesis's structural undervaluation is durable for six of its eight states.
  Network rank minus GDP rank (places above GDP), 2012 / 2017 / 2022:
  KY +11 / +14 / +14; MS +8 / +10 / +6; IN +7 / +5 / +10; LA +12 / +5 / +9;
  TN +5 / +6 / +5; MI +5 / +6 / +6. The thesis showed the gap in 2017 only; the
  ResearchHub study showed rankings are stable but did not test the gap itself.
  This is a replication over time of the same measure, not an independent test.
- The gap predates the AI data-center investment wave (2024-2026): these states
  were already undervalued in 2012. The link to investment remains a
  correlation.
- Montana's gap narrows to +3 in 2022 (from +12 in 2012), below the Sustainer
  threshold; its grain specialization makes it a Specialist that year.
- South Carolina is undervalued only in 2017 (+1 / +9 / +3); its 2017 status is
  not a durable property.
- Massachusetts and Minnesota rank low on embeddedness but are top-12 routers in
  every year: their role is brokerage, not supply. Colorado routes only in 2017
  (betweenness ranks 15, 11, 26).

**Caveats noted.**
- Several Sustainer cases sit at the threshold (+5: TN 2012 and 2022, MI 2012,
  IN and LA 2017). A sensitivity analysis comes before any public claim about
  individual states.

**Next.** Threshold sensitivity; clustering check against the rule-based roles;
script-generated figures; a Roles view on the dashboard.

## 2026-10-07: threshold sensitivity (quick pass)

Each threshold moved one step either way, all else fixed; count of the 153
state-years (51 states × 3 years) whose role changes:

| Threshold | Lower | Higher |
|---|---|---|
| Engine ranks (7) | 4 (6: NY, PA drop to Router) | 1 (8) |
| Sustainer places (5) | 8 (4) | 10 (6) |
| Router rank (12) | 5 (10) | 6 (14) |
| Specialist LQ (15) | 1 (12) | 3 (18) |
| Specialist share (5%) | 0 (4%) | 1 (6%) |
| Market pull (1.3) | 4 (1.2) | 4 (1.4) |

No single step changes more than 10 of 153 (6.5%). The Sustainer cutoff is the
most sensitive. Engines are stable at the top (TX, CA, IL, OH) but NY and PA
depend on the cutoff.

Undervalued states, years as Sustainer by cutoff: at 4 or 5 places, KY, MS,
IN, LA, TN and MI qualify in all three years; at 6, only KY and MS do; at 7,
only KY. The threshold-free statement: all six stay at least 5 places above
their GDP rank in every survey year (minimum gaps KY 11, MS 6, IN 5, LA 5,
TN 5, MI 5). Claims about individual states should cite the gaps, not the
role label.

Persisted as `sensitivity.py` (`output/sensitivity.json`); it reproduces the
table above.

## 2026-10-07: clustering check

Question: do rule-free clusters recover the roles? `cluster_check.py`, seed
42. Profile clusters use the seven standardized measures the rules read
(eigenvector, out-degree and betweenness ranks, places above GDP, log pull,
log signature LQ, signature share). Structural equivalence uses Ward on
unit-length outbound plus inbound partner-share vectors (after Maoz et al.
2006).

| ARI vs rules | 2012 | 2017 | 2022 |
|---|---|---|---|
| k-means k = 6 | 0.228 | 0.161 | 0.273 |
| Ward k = 6 | 0.156 | 0.194 | 0.164 |
| Structural equivalence k = 6 | −0.033 | 0.005 | 0.016 |

- Best silhouette: 0.28 (k = 8, 2012), 0.34 (k = 6, 2017), 0.37 (k = 4,
  2022). Weak structure, no stable k.
- k = 6 clusters across years: ARI 0.41 (2012-17), 0.20 (2017-22), 0.34
  (2012-22). The clusters are less stable than the rule roles (30 of 51 states
  constant).
- The only pure-role cluster every year is Market: DC and HI, plus AK in
  2017 and 2022 (AK sits in a mixed cluster in 2012).
- Partner similarity groups states by region, not role.
- Near-router Generalists (CO, CT, VA with MA, MD, MN, WA) group in 2012 and
  2017 and dissolve in 2022. **No Generalist split warranted.**

Finding: the roles are definitions, not discovered clusters. The measure
space is a continuum organized mainly by scale; the rules cut it by
counterfactual (what stops if this state's flows stop). Present the taxonomy
as an interpretive classification.

## 2026-10-07: script-generated figures

`make_figures.py` replaces the canvas drafts with four reproducible figures
(PNG and SVG): undervalued-state gaps by year, 2017 periodic table, decade tile
map with per-year codes, role-by-year grid. Fonts fall back to Helvetica Neue
when IBM Plex is not installed. The draft-a canvas board stays as a design
reference.
