# State roles: how each state powers the interstate network

**Post-hoc exploratory analysis. Not pre-registered.** The pre-registered
hypotheses and verdicts live in `evolution/`; nothing here touches them. The
thresholds below are first-pass choices for discussion, not fitted values.

## Question

GDP ranks states by size. The thesis showed that network position ranks them
differently. This analysis asks the next question: which states power
interstate economic activity, and in what different ways? Each state gets a
primary role, defined by a rule and by a counterfactual: what would stop if
that state's flows stopped.

## Data

All three survey years come from the evolution cache
(`evolution/cache/cfs_{2012,2017,2022}_full.pkl`, read only), so they share
one pipeline: CFS 2012 PUMF, 2017 PUF and 2022 PUMS, weighted shipment value,
51 nodes (50 states plus DC), with SCTG 16 (crude petroleum) excluded in every
year for parity with 2022. Because of that exclusion, 2017 ranks here can
differ slightly from the thesis run and the dashboard. GDP ranks use the BEA
Q4 files listed in `run_state_roles.py`.

| Measure | Definition |
|---|---|
| Embeddedness | eigenvector centrality rank (1 = highest) |
| Supply reach | weighted out-degree rank |
| Brokerage | betweenness rank, among states with nonzero betweenness |
| Places above GDP | GDP rank minus eigenvector rank |
| Pull | value received divided by value shipped, interstate |
| Signature | commodity (single SCTG code) with the highest location quotient among those where the state ships at least 3% of national interstate value (1% fallback) |
| Location quotient | state's share of a commodity's shipments divided by its share of all shipments |

## Roles

A state takes the first role it qualifies for, in the order below. States that
meet no rule are Generalists. Thresholds live in `roles.yaml`.

| Role | Rule | Without them |
|---|---|---|
| Engine | eigenvector rank ≤ 7 and out-degree rank ≤ 7 | every other state loses its largest suppliers and buyers at once |
| Sustainer | eigenvector rank at least 5 places above GDP rank | production in the engines loses inputs that output figures do not credit |
| Router | betweenness rank ≤ 12 in that year | flows between other states lose their shortest paths |
| Specialist | signature location quotient ≥ 15 and at least 5% of the nation's shipments of it | one sector loses a supply that is hard to replace |
| Market | pull ≥ 1.3 | other states lose buyers for their output |
| Generalist | none of the above | activity thins broadly rather than failing at one point |

Each year is classified on its own data. The decade summary takes the role a
state held most often across the three years (ties go to 2017), records
whether the role was the same in all three, and flags states that met the
router rule in at least two years (`router_decade`), because betweenness churns
far more than the other measures (see `analysis/rank_dynamics/`).

## Results

| Role | 2012 | 2017 | 2022 |
|---|---|---|---|
| Engine | 6 | 6 | 5 |
| Sustainer | 10 | 11 | 10 |
| Router | 5 | 6 | 7 |
| Specialist | 5 | 5 | 6 |
| Market | 8 | 8 | 9 |
| Generalist | 17 | 15 | 14 |

30 of 51 states hold the same role in all three years:

- Engines: CA, IL, OH, PA, TX
- Sustainers: IN, KY, LA, MI, MS, TN, WV
- Routers: GA, MA, MN
- Specialist: WY
- Markets: AK, DC, FL, HI, ME, NH
- Generalists: CT, DE, IA, KS, MO, NE, OR, RI

Readings:

- Seven of the eight states the thesis identified as structurally undervalued
  (IN, KY, LA, MI, MS, TN, MT) are Sustainers in 2012 and 2017; all but Montana
  remain so in 2022. Montana's gap narrows to 3 places in 2022, below the
  threshold, and its grain specialization makes it a Specialist that year.
  South Carolina is a Sustainer only in 2017. Dated findings: `LOG.md`.
- Massachusetts and Minnesota rank low on embeddedness but route in every
  year: their role is brokerage, not supply. Washington and Maryland route in
  two of three years.
- Colorado meets the router rule only in 2017 (betweenness ranks 15, 11, 26
  across the three years), so its 2017 role is not a stable property.
- New York drops out of the engines in 2022 and routes instead; Alabama,
  Arkansas and Wisconsin become Sustainers in 2022.

Difference from the first canvas draft (October 2026), which used thesis 2017
data and a decade-level router rule: Colorado and North Carolina route in 2017
under the year rule, and Maryland's 2017 role is Market (it routes in 2012 and
2022).

## Caveats

- Commodity trade only. Services, crude oil and electricity are outside the
  data, so states that power the economy mainly through services appear as
  routers or generalists.
- The 2022 file is a sample (PUMS) while 2012 and 2017 are full files; see the
  evolution study's comparability notes.
- The signature depends on the method: the largest national share would pick
  different commodities for several states.
- Roles describe position in commodity flows. They are not claims about
  political power or coercion: states cannot interrupt interstate trade, the
  condition Hirschman (1945, p. 16) names for trade-based coercion.
- Thresholds are not tuned; a sensitivity analysis is the next step.

## Lineage

- Hirschman, *National Power and the Structure of Foreign Trade* (1945):
  dependence and the difficulty of replacing a partner (pp. 17, 30).
- Hirschman, *The Strategy of Economic Development* (1958): backward and
  forward linkages.
- Rasmussen, *Studies in Inter-Sectoral Relations* (1956): the "power of
  dispersion" and "sensitivity of dispersion" indices.
- Jang and Yang (2023): macro, meso and micro centrality as distinct kinds of
  network power, the framework the thesis adapts.
- Patty and Penn (2017): centrality measures differ because power is a
  multifaceted concept.

## Reproduce

Requires the local evolution cache (not committed).

```
python analysis/state_roles/run_state_roles.py
pytest tests/test_state_roles.py
```

## Files

- `roles.yaml`: thresholds and role priority
- `run_state_roles.py`: classification script
- `output/state_roles.json`: per-state, per-year roles, measures and decade summary
- `output/state_roles.csv`: the same data, one row per state and year
- `figures/`: design drafts (see `figures/README.md`)
