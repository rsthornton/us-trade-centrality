# Eigenvector direction

**Post-hoc check, not pre-registered.** Answers a question from the thesis
defense (April 2026) on left versus right eigenvectors in a directed network.
Corrections to the thesis text: `paper/ERRATA.md`.

With `A[i, j]` the flow from state i to state j there are two eigenvector
centralities:

| Version | Equation | A state scores high when |
|---|---|---|
| In-flow (left eigenvector of A) | x = Aᵀx / λ | it receives large shipments from states that score high |
| Out-flow (right eigenvector of A) | x = Ax / λ | it ships heavily to states that score high |

## Result

`check_direction.py` → `output/direction.json`.

- Every eigenvector value in the repo is the **in-flow** version: the thesis and
  dashboard data and all three evolution caches match it exactly. It is
  NetworkX's default for `eigenvector_centrality_numpy` on a `DiGraph`, which
  `cfs_toolkit` calls.
- Thesis Equation 3.2, `C_E(i) = (1/λ) Σ_j W_ij C_E(j)` with `W_ij` the flow from
  i to j, writes the **out-flow** version. The computed values and the equation
  disagree in direction.
- The two versions agree closely overall (Spearman 0.945 to 0.954 across the
  four networks) but 15 to 18 states move 5 or more ranks. Largest in 2017:
  FL 5 → 17, MN 26 → 16, MD 20 → 29, LA 17 → 25, NM 38 → 46, IA 31 → 23.
- Structural undervaluation (2017, GDP rank minus eigenvector rank, in-flow /
  out-flow): KY +14 / +13, MS +10 / +9, IN +6 / +8, TN +6 / +8, MI +6 / +5,
  SC +7 / +7 hold under both. **LA +7 / −1 and MT +8 / +1 hold only under the
  in-flow version.**

Reading: the in-flow version measures how strongly a state draws from
well-connected suppliers. Claims about a state "enabling output elsewhere" fit
the out-flow version better; where the two differ, cite the one computed.

```
python analysis/eigenvector_direction/check_direction.py
```
