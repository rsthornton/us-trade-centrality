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
| Embeddedness | in-flow eigenvector centrality rank (1 = highest); see `analysis/eigenvector_direction/` |
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
- Thresholds are not tuned. See Robustness below for how much the roles move
  when each one shifts.

## Robustness

`sensitivity.py` moves each threshold one step down and one step up, all else
fixed (`output/sensitivity.json`). No single step changes more than 10 of the
153 state-years (6.5%). The Sustainer cutoff is the most sensitive: at 6
places only Kentucky and Mississippi stay Sustainers in all three years, at 7
only Kentucky. The statement that does not depend on any cutoff: Kentucky,
Mississippi, Indiana, Louisiana, Tennessee and Michigan sit at least 5 places
above their GDP rank in every survey year (minimum gaps 11, 6, 5, 5, 5, 5).
Claims about individual states should cite the gaps, not the role label.

## Clustering check

`cluster_check.py` asks whether rule-free grouping recovers the roles
(`output/cluster_check.json`). Agreement is the adjusted Rand index (ARI;
0 = chance, 1 = identical).

| | 2012 | 2017 | 2022 |
|---|---|---|---|
| k-means, k = 6, on the standardized measures | 0.23 | 0.16 | 0.27 |
| Ward, k = 6, same measures | 0.16 | 0.19 | 0.16 |
| Structural equivalence (partner-share profiles), k = 6 | −0.03 | 0.01 | 0.02 |

- Clusters recover the roles only weakly, and the profile space has no strong
  natural grouping (best silhouette 0.28 to 0.37, at a different k each year).
  The k = 6 clusters are themselves unstable across years (ARI 0.20 to 0.41).
  The main axis they find is scale, which the rules split into Engines,
  Sustainers and the rest.
- The one grouping clusters find every year is a pure Market core: DC and
  Hawaii in every year, joined by Alaska in 2017 and 2022.
- Partner similarity groups states by region (South, New England,
  Mid-Atlantic, Northwest, Midwest, Mountain West), not by role.
- A near-router group (CO, CT, VA with MA, MD, MN, WA) appears in 2012 and
  2017 and dissolves in 2022, so no split of the Generalists is warranted.

Reading: the roles are definitions, an interpretive classification of
distinct ways to matter, not types discovered in the data. They should be
presented that way.

## Figures

`make_figures.py` draws four figures from `output/state_roles.json` into
`figures/` (PNG at 200 dpi and SVG):

- `gap-undervalued`: places above GDP rank for the eight undervalued states,
  2012, 2017, 2022, with the Sustainer cutoff marked
- `periodic-table-2017`: one tile per state, grouped by 2017 role
- `tile-map-decade`: decade role on a tile map, with the role in each year
- `role-stability`: role per state and year

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
python analysis/state_roles/sensitivity.py
python analysis/state_roles/cluster_check.py   # needs scikit-learn
python analysis/state_roles/make_figures.py
pytest tests/test_state_roles.py
```

## Files

- `roles.yaml`: thresholds and role priority
- `run_state_roles.py`: classification script
- `output/state_roles.json`: per-state, per-year roles, measures and decade summary
- `output/state_roles.csv`: the same data, one row per state and year
- `sensitivity.py`, `output/sensitivity.json`: threshold sensitivity
- `cluster_check.py`, `output/cluster_check.json`: clustering check
- `make_figures.py`, `figures/`: figures and the first design draft (see `figures/README.md`)
