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
