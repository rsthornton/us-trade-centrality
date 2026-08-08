"""
Post-hoc exploratory rank-dynamics analysis (NOT pre-registered).

Extends the committee-response permutation test (May 2026, boundary
comparison) to the temporal arcs of the evolution study. Two analyses
per centrality measure, per arc (2017->2012 retrodiction, 2017->2022
prediction), following the random-displacement null suggested at the
defense and the rank-dynamics framework of Morales et al. 2018
(10.3389/fphy.2018.00045) and Iniguez et al. 2022 (10.1038/s41467-022-29256-x):

N1  Displacement calibration: how many random single-element
    displacements of the 2017 ranking reproduce the observed Spearman
    rho against the target year? Reported as m* with a spread.

N2  Mobility profile: |rank change| vs 2017 starting rank, observed
    against the displacement null at m*, testing the zero-flux
    prediction that extremes are stable and mid-ranks churn.

Reads the frozen evolution cache read-only; writes to output/ here.
"""

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
CACHE = HERE.parent.parent / "evolution" / "cache"
OUT = HERE / "output"

MEASURES = ["eigenvector", "out_degree", "betweenness"]
ARCS = {"retrodiction": 2012, "prediction": 2022}
BASE_YEAR = 2017
N_STATES = 51
REPS = 500
M_MAX = 400
SEED = 42


def load_ranks(year):
    with open(CACHE / f"cfs_{year}_full.pkl", "rb") as f:
        bundle = pickle.load(f)
    c = bundle["centralities"].set_index("label")
    ranks = {}
    ties = {}
    for m in MEASURES:
        ranks[m] = c[m].rank(ascending=False, method="average")
        ties[m] = int((c[m] == 0).sum())
    return pd.DataFrame(ranks), ties


def displace(order, rng):
    i = rng.integers(len(order))
    j = rng.integers(len(order))
    x = order.pop(i)
    order.insert(j, x)
    return order


def rho_curve(n, m_max, reps, rng):
    """Mean and sd of Spearman rho between the identity ranking and a
    ranking hit by m successive random displacements, for m = 1..m_max."""
    base = np.arange(n)
    rhos = np.zeros((reps, m_max))
    for r in range(reps):
        order = list(range(n))
        for m in range(m_max):
            order = displace(order, rng)
            perm = np.empty(n)
            perm[order] = np.arange(n)
            rhos[r, m] = spearmanr(base, perm).statistic
    return rhos


def calibrate(rhos, rho_obs):
    """Smallest m whose mean rho falls at or below the observed rho,
    plus the interquartile range of per-rep crossing points."""
    mean = rhos.mean(axis=0)
    below = np.nonzero(mean <= rho_obs)[0]
    m_star = int(below[0]) + 1 if len(below) else None
    crossings = []
    for r in range(rhos.shape[0]):
        b = np.nonzero(rhos[r] <= rho_obs)[0]
        if len(b):
            crossings.append(int(b[0]) + 1)
    q = np.percentile(crossings, [25, 50, 75]) if crossings else [None] * 3
    return m_star, [float(x) for x in q]


def mobility_profile(base_rank, target_rank):
    df = pd.DataFrame({"start": base_rank, "shift": (target_rank - base_rank).abs()})
    return df.sort_values("start")


def null_profile(n, m_star, reps, rng):
    """Expected |rank change| by starting position under m* displacements."""
    shifts = np.zeros((reps, n))
    for r in range(reps):
        order = list(range(n))
        for _ in range(m_star):
            order = displace(order, rng)
        perm = np.empty(n)
        perm[order] = np.arange(n)
        shifts[r] = np.abs(perm - np.arange(n))
    return shifts.mean(axis=0)


def main():
    OUT.mkdir(exist_ok=True)
    rng = np.random.default_rng(SEED)
    loaded = {y: load_ranks(y) for y in [BASE_YEAR, *ARCS.values()]}
    ranks = {y: v[0] for y, v in loaded.items()}
    zero_counts = {y: v[1] for y, v in loaded.items()}
    curve = rho_curve(N_STATES, M_MAX, REPS, rng)

    results = {"seed": SEED, "reps": REPS, "m_max": M_MAX, "arcs": {}}
    for arc, target_year in ARCS.items():
        arc_out = {}
        for m in MEASURES:
            base = ranks[BASE_YEAR][m]
            target = ranks[target_year][m].reindex(base.index)
            rho_obs = float(spearmanr(base, target).statistic)
            m_star, quartiles = calibrate(curve, rho_obs)
            profile = mobility_profile(base, target)
            bottom = profile[profile["start"] > 41]["shift"]
            arc_out[m] = {
                "rho_observed": rho_obs,
                "m_star": m_star,
                "m_crossing_quartiles": quartiles,
                # zero-valued states share one tied average rank, so the
                # extreme-bottom bucket can be empty for betweenness
                "zero_valued_states": {str(BASE_YEAR): zero_counts[BASE_YEAR][m],
                                       str(target_year): zero_counts[target_year][m]},
                "mean_abs_shift": float(profile["shift"].mean()),
                "max_abs_shift": float(profile["shift"].max()),
                "top10_mean_shift": float(profile[profile["start"] <= 10]["shift"].mean()),
                "mid_mean_shift": float(
                    profile[(profile["start"] > 15) & (profile["start"] <= 35)]["shift"].mean()
                ),
                "bottom10_mean_shift": float(bottom.mean()) if len(bottom) else None,
                "null_profile_at_m_star": (
                    null_profile(N_STATES, m_star, REPS, rng).tolist() if m_star else None
                ),
                "observed_shifts_by_state": {
                    s: float(v) for s, v in profile["shift"].items()
                },
            }
        results["arcs"][arc] = {"base": BASE_YEAR, "target": target_year, "measures": arc_out}

    with open(OUT / "rank_dynamics.json", "w") as f:
        json.dump(results, f, indent=1)

    for arc, data in results["arcs"].items():
        print(f"\n{arc} ({data['base']} -> {data['target']})")
        for m, r in data["measures"].items():
            b = r["bottom10_mean_shift"]
            bs = f"{b:.1f}" if b is not None else "tied-zero"
            print(
                f"  {m:12s} rho={r['rho_observed']:.3f}  m*={r['m_star']}"
                f"  (IQR {r['m_crossing_quartiles'][0]:.0f}-{r['m_crossing_quartiles'][2]:.0f})"
                f"  shift top10/mid/bottom10: {r['top10_mean_shift']:.1f}"
                f"/{r['mid_mean_shift']:.1f}/{bs}"
            )


if __name__ == "__main__":
    main()
