# Three-Survey Evolution Run
*2026-08-08 09:36*

- sample_size: full
- years: 2012, 2017, 2022
- thresholds.yaml sha256: `cd25810026b8053aad446aa0a6e3a3050642c1cf492d988dc02e3db185bc30e1`

## Gates

| Gate | Year | Value | Status | Note |
|---|---|---|---|---|
| national_total | 2012 | 13,852,108,524,033 | PASS |  |
| sctg16_excluded | 2012 | 856 | PASS | 856 records dropped before network construction |
| grouped_sctg_share | 2012 | 0.002713922607687776 | PASS |  |
| national_total | 2017 | 14,517,252,205,728 | PASS |  |
| sctg16_excluded | 2017 | 1099 | PASS | 1,099 records dropped before network construction |
| grouped_sctg_share | 2017 | 0.0023410464424072634 | PASS |  |
| national_total | 2022 | 17,939,292,158,431 | PASS |  |
| sctg16_excluded | 2022 | 1759 | PASS | 1,759 records dropped before network construction |
| grouped_sctg_share | 2022 | 0.0012990550009572461 | PASS |  |
| truncation_share | 2022 | 2.102375242258828e-06 | PASS |  |

## Verdicts

| Forecast | Arc | Result | Verdict |
|---|---|---|---|
| H1-R | 2017 -> 2012 | eigenvector: rho=0.988 (rho >= 0.9), out_degree: rho=0.985 (rho >= 0.9), betweenness: rho=0.783 (rho < 0.85); top10 9/10 | **HOLD** |
| H2-R | 2017 -> 2012 | jaccard=0.804 (jaccard >= 0.8) | **HOLD** |
| H3-R | 2017 -> 2012 | pharma=0.245, ag=0.180 (|delta_pharma - delta_ag| <= 0.1) | **HOLD** |
| H4-R | 2017 -> 2012 | nmi=0.881 (reference: nmi >= 0.8) | **EXPLORATORY** |
| H5-R | 2017 -> 2012 | gini 0.746 -> 0.738 (reference: |gini shift| <= 0.05) | **EXPLORATORY** |
| H1-P | 2017 -> 2022 | eigenvector: rho=0.985 (rho >= 0.9), out_degree: rho=0.984 (rho >= 0.9), betweenness: rho=0.742 (rho < 0.85); top10 9/10 | **HOLD** |
| H2-P | 2017 -> 2022 | jaccard=0.809 (jaccard >= 0.8) | **HOLD** |
| H3-P | 2017 -> 2022 | pharma=0.401, ag=0.142 (delta_pharma > delta_ag) | **HOLD** |
| H4-P | 2017 -> 2022 | nmi=0.881 (reference: nmi >= 0.8) | **EXPLORATORY** |
| H5-P | 2017 -> 2022 | gini 0.746 -> 0.735 (reference: gini growth >= 0.05) | **EXPLORATORY** |

## Reading the table

Hn-R is the retrodiction arc (2017 -> 2012), expected to HOLD.
Hn-P is the prediction arc (2017 -> 2022), the live forecast.
A pattern of R holding while P breaks quantifies COVID-era structural disruption.

## Year stats

- **2012**: 4,547,661 records loaded, $13,852,108,524,033 weighted total, 2539 interstate edges, grouped SCTG share 0.0027
- **2017**: 5,978,523 records loaded, $14,517,252,205,728 weighted total, 2534 interstate edges, grouped SCTG share 0.0023
- **2022**: 37,576,546 records loaded, $17,939,292,158,431 weighted total, 2547 interstate edges, grouped SCTG share 0.0013
