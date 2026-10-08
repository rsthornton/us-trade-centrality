# Higher-order dependence in interstate commodity flows

**Post-hoc exploratory analysis. Not pre-registered.** Nothing here touches
`evolution/`. The study asks whether the interstate commodity network carries
structure that pairwise measures (the centralities behind the state roles)
cannot see, following Varley, Pope, Faskowitz and Sporns (2023), "Multivariate
information theory uncovers synergistic subsystems of the human cerebral
cortex", *Communications Biology* 6:451.

## Data

The raw survey files named in `evolution/configs/` (CFS 2012 PUMF, 2017 PUF,
2022 PUMS), read only. Interstate shipments only. Dropped in every year so the
three years share one commodity list (40 two-digit SCTG codes): grouped codes
(0.1 to 0.3% of records), unknown (00), live animals (01, not coded separately
in 2022), crude petroleum (16, out of scope in 2022) and other (99).
Records: 2,279,065 (2012), 2,943,533 (2017), 22,150,779 (2022).

## Two framings

**A. Origin, destination and commodity as three variables** (`run_three_way.py`).
One shipment is one observation. The information measures:

| Measure | Meaning |
|---|---|
| Total correlation | all dependence among O, D and C; the loss of the independence model O:D:C |
| O-information | total correlation minus dual total correlation; negative means synergy-dominated |
| Three-way part | the loss of the model OD:OC:DC, fitted by iterative proportional fitting |
| After distance | the same, with a distance band x commodity term added to the model |

The OD:OC:DC fit is the maximum-likelihood Poisson log-linear model with those
margins: the same form as a gravity equation with exporter-by-product,
importer-by-product and pair fixed effects. The three-way part is what such a
model cannot explain. The distance term lets each commodity have its own
distance profile (seven bands by the pair's median great-circle distance), so
whatever survives it is not commodity-specific distance decay. The sampling
null draws tables of the same size from the fitted model and refits them.

**B. States as variables** (`run_states_as_variables.py`), the literal Varley
framing. One observation is a slice: commodity x destination census division x
quarter (about 1,440 slices; 2012 and 2017, since the 2022 file has no
quarter). Each state's value is its shipped value in the slice, rank-transformed
to normal scores, with the slice-wide mean regressed out (the analogue of
global signal regression). O-information is computed from the correlation
matrix for random subsets and for the most synergistic subsets found by
simulated annealing. Two controls run through the same optimizer: columns
shuffled before the regression, and no regression.

## Results: framing A

Counted by records; dollar-weighted figures in brackets.

| | 2012 | 2017 | 2022 |
|---|---|---|---|
| Total correlation (bits) | 0.767 [1.458] | 0.754 [1.307] | 0.753 [1.309] |
| O-information (bits) | -0.154 [-0.386] | -0.148 [-0.348] | -0.164 [-0.361] |
| Three-way part (bits) | 0.160 [0.411] | 0.155 [0.362] | 0.169 [0.373] |
| Sampling null | 0.026 | 0.020 | 0.003 |
| Three-way part after distance | 0.119 | 0.113 | 0.128 |
| Share of the excess explained by distance | 30% | 31% | 25% |

- In all three years the flows are synergy-dominated: knowing the commodity
  makes the origin-destination pattern more informative, not less.
- About a fifth of the total dependence is three-way, 6 to 66 times the
  sampling null. Commodity-specific distance accounts for a quarter to a third
  of it; the rest is pair-specific.

Per state, the measure is the origin's share of the three-way part (after
distance, net of the null) divided by its share of records.

- It falls with size: larger states fit the pairwise model more closely
  (Spearman with eigenvector rank 0.88, 0.90, 0.78).
- Net of size (the residual of log measure on log share), the ranking is
  stable from 2012 to 2017 (Spearman 0.88) and weaker against 2022 (0.57,
  0.55).
- Mean net-of-size residual by 2017 role: Specialist 0.34, Sustainer 0.12,
  Generalist 0.10, Router -0.13, Engine -0.25, Market -0.28. In all three
  years Specialists are highest and Engines among the two lowest.

## Results: framing B

| Subset size | 3 | 5 | 8 | 10 |
|---|---|---|---|---|
| Random subsets synergistic, 2017 | 41% | 14% | 1.2% | 0.1% |
| Most synergistic found, 2017 (bits) | -0.034 | -0.107 | -0.133 | -0.137 |
| Same, columns shuffled first | -0.001 | -0.003 | -0.009 | -0.014 |
| Same, no slice regression | -0.016 | +0.011 | +0.145 | +0.392 |

2012 is similar (most synergistic -0.033, -0.087, -0.144, -0.137).

- Synergistic subsets exist and are about 10 to 40 times stronger than the
  same search finds in shuffled data, so the regression does not create them.
- Without the regression, the shared commodity-size signal makes larger
  subsets redundant, as global signal does in the brain data.
- Participation in the annealed subsets relative to chance, 2017: Specialist
  1.37, Market 1.30, Generalist 1.15, Sustainer 0.74, Engine 0.71, Router 0.69.
  Engines and Routers are under-represented in both years and Markets
  over-represented in both. Specialists are over-represented in 2017 and near
  chance in 2012 (1.03); Sustainers differ by year.

## Reading

Both framings point the same way: the states most central in the pairwise
network take part least in higher-order structure; specialist states (and, in
framing B, market states) take part most. Varley et al. report the analogue in the brain: pairs with strong
functional connectivity rarely sit together in synergistic subsets. This is a
hypothesis about the network, not yet a finding about the economy.

## Caveats

- Survey design: the record counts ignore the sampling design; dollar-weighted
  figures have no sample size.
- The 2022 file is a sample (PUMS) of a different size and structure, which
  may explain part of the weaker 2012-to-2022 agreement.
- Small states have concentrated portfolios, and the size slope is removed
  only linearly in logs.
- Framing B depends on the slice definition and on the regression step; its
  Gaussian estimator is applied to rank-transformed, zero-heavy values.
- Commodity trade only, as for the state roles.

## Reproduce

```bash
cd analysis/higher_order
python run_three_way.py           # writes output/three_way_*
python run_states_as_variables.py # writes output/states_as_variables_*
pytest tests/test_higher_order.py # each measure passes a case and fails one
```
