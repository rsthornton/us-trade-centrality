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

## RA, log-linear models and gravity

`run_equivalence.py` checks on the data that reconstructability analysis and
gravity-style Poisson regression with fixed effects fit the same model. Table:
origin division x destination division x commodity, 2017, interstate shipment
records (2,943,533 records, 3,240 cells).

| Model | Largest difference in fitted counts, IPF vs Poisson | 2 N ln 2 x RA loss | Poisson deviance |
|---|---|---|---|
| O:D:C (exporter and importer effects only) | 1.9e-10 (cells up to 9,871) | 1,183,247.9 | 1,183,247.9 |
| OD:OC:DC (pair, exporter-product, importer-product) | 1.6e-9 (cells up to 18,302) | 202,120.8 | 202,120.8 |

Gravity specifications estimated by Poisson pseudo-maximum likelihood with only
fixed effects are hierarchical log-linear models. Their fitted values match the
observed fixed-effect margins (Arvis and Shepherd 2013, p. 6 of the World Bank
manuscript; Fally 2015, Lemma 2) and, when the estimate exists, equal the
maximum-entropy reconstruction from those margins (the log-linear literature,
e.g. Bishop, Fienberg and Holland 1975). That makes them points in RA's lattice
of structures: exporter + importer effects is independence; adding pair,
exporter-product and importer-product effects is OD:OC:DC. Pair covariates such
as distance take a specification outside the lattice. Cells with a zero kept
margin are fitted as zero, where the estimate sits on the boundary (Fally 2015,
fn 13). The three-way part reported above is what the full fixed-effect
specification leaves out.

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

## Dependence follow-ups

`run_dependence.py`, writing `output/dependence_*`. Dollar-weighted unless
stated. A **sole-supplier link** is a destination-commodity pair whose largest
origin sends more than 50% of its inbound interstate value; it is
**persistent** if the same origin holds it in 2012, 2017 and 2022.

### Mode groups

| Group | 2012 and 2017 codes | 2022 codes |
|---|---|---|
| truck | 03, 04, 05 | 111, 112, 113 |
| rail | 06 | 12 |
| water | 07, 08, 09, 10, 101 | 131, 132, 133 |
| pipeline | 12 | 15 |
| air/parcel | 11, 14 | 14, 21 |
| multiple/other | 00, 02, 13, 15 to 20 | 16, 22 to 25, 30 |

No code book was at hand, so each code was placed by its median shipment
weight, median distance and leading commodities (for example, 2017 code 14:
6 lb median, 531 miles, SCTG 40/35/30, so parcel; 2022 code 15: SCTG 20/13/17
over 12 miles, so pipeline). Uncertain: 2022 code 113 (a truck subtype, but
which one is unclear; it stays in truck either way), 2022 code 16 (84 records,
coal over 7 miles, placed in other), and the deep-sea codes (2017 10, 2022 133),
whose profiles are odd for deep sea but stay in water either way. The shipper
groups use the first two NAICS digits (2012, 2017) or SECTOR (2022): wholesale
42, manufacturing 31 to 33, mining 21, other (retail 45 or 44-45, transport and
warehousing 49 or 48-49, information 51, management 55).

### H3. Are persistent sole-supplier links physical rather than commercial?

| | 2012 | 2017 | 2022 |
|---|---|---|---|
| Sole-supplier links | 502 | 441 | 435 |
| Persistent (all three years) | 60 | 60 | 60 |
| Median records behind the link, persistent / transient | 51 / 12.5 | 53 / 21 | 73 / 18 |
| Links under 10 records, persistent / transient | 10% / 42% | 7% / 34% | 8% / 42% |
| Median records behind the destination-commodity pair, persistent / transient | 94 / 62 | 139 / 66 | 240 / 88 |
| Median shipment value per record ($), persistent / transient | 19,875 / 16,254 | 16,489 / 12,817 | 12,520 / 10,831 |

Mode mix (share of link value):

| | truck | rail | water | pipeline | air/parcel | multiple/other |
|---|---|---|---|---|---|---|
| 2012 persistent | 39% | 7% | 8% | 26% | 16% | 3% |
| 2012 transient | 66% | 11% | 7% | 4% | 11% | 2% |
| 2017 persistent | 52% | 3% | 5% | 14% | 17% | 10% |
| 2017 transient | 48% | 3% | 9% | 11% | 23% | 6% |
| 2022 persistent | 60% | 5% | 5% | 22% | 2% | 6% |
| 2022 transient | 69% | 13% | 4% | 5% | 5% | 5% |

Commodity class of the links (2017): persistent 38% bulk minerals, 25% farm
and food, 20% fuels, 10% chemicals, 7% scrap and mixed, none in machinery,
vehicles or wood and paper; transient 33%, 20%, 18%, 7%, 5%, with 12% wood and
paper and 3% machinery and vehicles. The 60 persistent links are coal from
Wyoming to nine states, fuels mostly between neighbours (Louisiana to
Mississippi and Texas, Massachusetts to New Hampshire, Illinois to Indiana),
food from Maryland to DC and from California to Hawaii, Arizona and Oregon,
pharmaceuticals between neighbours (Massachusetts to New Hampshire and
Vermont, California to Nevada, Arizona to New Mexico, Illinois to Wisconsin),
and mixed freight between Washington and Oregon and to Alaska and
Hawaii. Market states (8 of 51) receive 21 of the 60.

Persistence under a minimum-records threshold on the destination-commodity
pair (applied in every year):

| Minimum records | 1 | 5 | 10 | 30 | 100 | 300 |
|---|---|---|---|---|---|---|
| 2017 links supported in all years | 390 | 337 | 303 | 237 | 124 | 47 |
| of which also links in 2012 | 32% | 34% | 35% | 35% | 30% | 30% |
| of which links in all three years | 15% | 17% | 17% | 17% | 17% | 15% |

- Partly supported. Persistent links lean toward pipeline (26% and 22% of
  value in 2012 and 2022 against 4% and 5% for transient links; 2017 is
  14% against 11%) and toward bulk minerals, fuels and food, but truck still
  carries 39 to 60% of their value. "Physical" fits coal, fuels and
  pharmaceuticals poorly as a single story: the common thread is proximity
  and isolated destinations (DC, Hawaii, Alaska, New Hampshire).
- Thin cells are not what makes links transient. Transient links rest on
  fewer records (a third to two-fifths under 10), but raising the support
  threshold to 300 records leaves the persistence rate flat at 15 to 17%.
  Most sole-supplier links turn over between surveys even where the share is
  well estimated.

### H4. What the three-way part is made of, by shipper group

Three-way part (loss of OD:OC:DC) fitted within each group, in bits; records
columns use record counts, with the sampling null for that count.
"Attributed" splits each pooled cell's term by the group's share of the
cell's value, so attributed shares sum to 1.

| Year | Group | Value share | Three-way, dollars | Three-way, records (null) | Attributed share of pooled | Top-5 origins / top-25 pairs share |
|---|---|---|---|---|---|---|
| 2012 | pooled | 100% | 0.411 | 0.160 | 100% | |
| 2012 | wholesale | 34% | 0.541 | 0.271 (0.068) | 35% | 26% / 9% |
| 2012 | manufacturing | 49% | 0.425 | 0.177 (0.035) | 44% | 22% / 9% |
| 2012 | mining | 0.7% | 0.133 | 0.482 (0.079) | 1.7% | 34% / 23% |
| 2012 | other | 16% | 0.608 | 0.402 (0.141) | 20% | 27% / 10% |
| 2017 | pooled | 100% | 0.362 | 0.155 | 100% | |
| 2017 | wholesale | 37% | 0.500 | 0.258 (0.053) | 38% | 25% / 9% |
| 2017 | manufacturing | 47% | 0.398 | 0.182 (0.031) | 43% | 22% / 8% |
| 2017 | mining | 0.5% | 0.195 | 0.479 (0.071) | 1.4% | 30% / 26% |
| 2017 | other | 16% | 0.513 | 0.306 (0.089) | 17% | 23% / 12% |
| 2022 | pooled | 100% | 0.373 | 0.169 | 100% | |
| 2022 | wholesale | 36% | 0.550 | 0.297 (0.007) | 42% | 25% / 10% |
| 2022 | manufacturing | 47% | 0.423 | 0.213 (0.007) | 45% | 23% / 9% |
| 2022 | mining | 0.4% | 0.146 | 0.195 (0.021) | 0.7% | 37% / 26% |
| 2022 | other | 17% | 0.389 | 0.144 (0.004) | 12% | 25% / 14% |

Top cells by within-group term, 2017 (origin to destination, SCTG):

| Group | Cells |
|---|---|
| wholesale | NY to KY pharmaceuticals (21); IN to OH mixed freight (43); TN to GA mixed freight; PA to NY pharmaceuticals |
| manufacturing | CA to OH pharmaceuticals; WI to MD motor vehicles (36); CT to TN transport equipment (37); CT to NY machinery (34) |
| other | GA to FL mixed freight; IN to GA pharmaceuticals; KY to TN mixed freight; PA to NJ mixed freight |
| mining | UT to TX nonmetallic minerals (13); KY to LA gravel (12); MO to TX nonmetallic mineral products (31) |

- Each group's own three-way part is larger than the pooled one (except
  mining in dollars): pooling groups with different pairwise patterns hides
  some of each group's specificity. The test file has a constructed case
  where two groups with no three-way structure pool into some.
- Wholesale carries slightly more than its value share (35 to 42% of the
  pooled part on 34 to 37% of value) and has the largest per-record excess
  over the null; manufacturing carries slightly less (43 to 45% on 47 to 49%).
  Neither dominates: the pooled part is spread across groups roughly in
  proportion to value.
- The hubs-versus-corridors hypothesis is not supported by these
  concentration measures: wholesale and manufacturing put about the same
  share of their three-way part on their top five origins (22 to 26%) and top
  25 origin-destination pairs (8 to 10%). The top origin is Texas for
  manufacturing in all three years and Illinois (2012, 2022) or Texas (2017)
  for wholesale.
- Top cells rarely repeat: of the top ten cells per group and year, only
  Illinois to Wisconsin wholesale pharmaceuticals appears in all three
  years. Mining's top cells often rest on a handful of records (2 to 6 in
  several 2012 and 2022 cells).

### H5. Buyer concentration versus supplier concentration

For each origin and commodity, the HHI of its shipments over destinations
(buyer concentration); for each destination and commodity, the HHI of its
receipts over origins (supplier concentration). Cells with fewer than 30
records are dropped; each state's figure is the value-weighted mean over
commodities. Asymmetry is buyer minus supplier HHI.

| Role | Buyer HHI 2012 / 2017 / 2022 | Supplier HHI 2012 / 2017 / 2022 | Asymmetry 2012 / 2017 / 2022 |
|---|---|---|---|
| Engine | 0.077 / 0.079 / 0.079 | 0.100 / 0.095 / 0.095 | -0.023 / -0.016 / -0.017 |
| Router | 0.113 / 0.111 / 0.115 | 0.159 / 0.118 / 0.115 | -0.046 / -0.007 / 0.000 |
| Generalist | 0.152 / 0.141 / 0.151 | 0.174 / 0.153 / 0.169 | -0.022 / -0.012 / -0.017 |
| Sustainer | 0.153 / 0.144 / 0.116 | 0.195 / 0.167 / 0.168 | -0.043 / -0.023 / -0.053 |
| Specialist | 0.257 / 0.185 / 0.169 | 0.227 / 0.214 / 0.208 | 0.030 / -0.028 / -0.039 |
| Market | 0.260 / 0.270 / 0.275 | 0.237 / 0.279 / 0.234 | 0.023 / -0.010 / 0.041 |

- Destinations depend on fewer origins than origins depend on destinations:
  supplier HHI exceeds buyer HHI in 40, 35 and 39 of 51 states.
- Both concentrations track size (Engines lowest, Markets highest).
  Sustainers are among the two most negative roles in all three years
  (concentrated sourcing, spread-out selling). Markets have positive
  asymmetry in 2012 and 2022 (sales as concentrated as sourcing or more);
  Specialists only in 2012. Role means over 5 to 17 states are noisy.

### Caveats for these follow-ups

- Concentration of observed flows is not non-substitutability. A destination
  that buys 80% of a commodity from one state may have many potential
  suppliers; the survey records where goods came from, not what else was
  possible.
- Survey design: links and HHIs use weighted value, which has no sample
  size; the record counts are only a guide to support. The per-group null is
  a multinomial on record counts, not the survey design.
- 2022 is a different sample (PUMS, about 7.5 times the records, different
  mode and sector codes), so thresholds on record counts bind differently by
  year, and part of the turnover in links may be sample, not economy.
- Shipper groups are the shipper's industry, not the trade's purpose: a
  manufacturer's sales office and a wholesaler can ship the same goods.
- The mode mapping is inferred from shipment profiles (see above).

## Reproduce

```bash
cd analysis/higher_order
python run_three_way.py           # writes output/three_way_*
python run_states_as_variables.py # writes output/states_as_variables_*
python run_dependence.py          # writes output/dependence_*
pytest tests/test_higher_order.py # each measure passes a case and fails one
```
