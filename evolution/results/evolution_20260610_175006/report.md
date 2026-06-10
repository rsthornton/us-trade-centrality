# Three-Survey Evolution Run
*2026-06-10 17:50*

- sample_size: 200000
- years: 2012, 2017, 2022
- thresholds.yaml sha256: `a3a6b77b689cb4e0ad370cd94d9d58f587ad01d89e9e06a78135073b6f9a53e4`

## Gates

| Gate | Year | Value | Status | Note |
|---|---|---|---|---|
| national_total | 2012 | 622,484,933,625 | REVIEW | no published total in thresholds.yaml; check against Census CFS publication |
| sctg16_excluded | 2012 | 48 | PASS | 48 records dropped before network construction |
| grouped_sctg_share | 2012 | 0.002705 | PASS |  |
| national_total | 2017 | 480,913,654,524 | REVIEW | no published total in thresholds.yaml; check against Census CFS publication |
| sctg16_excluded | 2017 | 41 | PASS | 41 records dropped before network construction |
| grouped_sctg_share | 2017 | 0.002505 | PASS |  |
| national_total | 2022 | 94,517,965,758 | REVIEW | no published total in thresholds.yaml; check against Census CFS publication |
| sctg16_excluded | 2022 | 17 | PASS | 17 records dropped before network construction |
| grouped_sctg_share | 2022 | 0.00135 | PASS |  |
| truncation_share | 2022 | 0.0 | PASS |  |

## Verdicts

| Forecast | Arc | Result | Verdict |
|---|---|---|---|
| H1-R | 2017 -> 2012 | eigenvector: rho=0.961 (rho >= 0.9), out_degree: rho=0.967 (rho >= 0.9), betweenness: rho=0.661 (rho < 0.85); top10 9/10 | **HOLD** |
| H2-R | 2017 -> 2012 | jaccard=0.636 (jaccard >= 0.8) | **BREAK** |
| H3-R | 2017 -> 2012 | pharma=0.559, ag=0.478 (|delta_pharma - delta_ag| <= 0.1) | **HOLD** |
| H4-R | 2017 -> 2012 | nmi=0.765 (nmi >= 0.8) | **BREAK** |
| H5-R | 2017 -> 2012 | gini 0.746 -> 0.757 (|gini shift| <= 0.05) | **HOLD** |
| H1-P | 2017 -> 2022 | eigenvector: rho=0.936 (rho >= 0.9), out_degree: rho=0.951 (rho >= 0.9), betweenness: rho=0.759 (rho < 0.85); top10 8/10 | **HOLD** |
| H2-P | 2017 -> 2022 | jaccard=0.614 (jaccard >= 0.8) | **BREAK** |
| H3-P | 2017 -> 2022 | pharma=0.737, ag=0.796 (delta_pharma > delta_ag) | **BREAK** |
| H4-P | 2017 -> 2022 | nmi=0.538 (nmi >= 0.8) | **BREAK** |
| H5-P | 2017 -> 2022 | gini 0.746 -> 0.801 (gini growth >= 0.05) | **HOLD** |

## Reading the table

Hn-R is the retrodiction arc (2017 -> 2012), expected to HOLD.
Hn-P is the prediction arc (2017 -> 2022), the live forecast.
A pattern of R holding while P breaks quantifies COVID-era structural disruption.

## Year stats

- **2012**: 200,000 records loaded, $622,484,933,625 weighted total, 2373 interstate edges, grouped SCTG share 0.0027
- **2017**: 200,000 records loaded, $480,913,654,524 weighted total, 2357 interstate edges, grouped SCTG share 0.0025
- **2022**: 200,000 records loaded, $94,517,965,758 weighted total, 2323 interstate edges, grouped SCTG share 0.0014
