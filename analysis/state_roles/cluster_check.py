"""
Clustering check for the state role taxonomy (post-hoc, exploratory).

Asks whether rule-free grouping recovers the rule-based roles. Two views per
survey year:

  Profile clusters: k-means (k = 4..8) and Ward clustering on the standardized
  measures the rules use (eigenvector, out-degree and betweenness ranks,
  places above GDP, log pull, log signature location quotient, signature
  share).

  Structural equivalence (after Maoz et al. 2006): states grouped by the
  similarity of their partner profiles, each state's outbound shares and
  inbound shares across all partners, with Ward clustering on unit-length
  vectors.

Agreement with the rule roles is the adjusted Rand index (0 = chance,
1 = identical). Reads the frozen evolution cache read-only; writes to output/.
"""

import importlib.util
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler, normalize

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("run_state_roles", HERE / "run_state_roles.py")
roles = importlib.util.module_from_spec(spec)
spec.loader.exec_module(roles)

SEED = 42
K_RANGE = range(4, 9)
K_MAIN = 6


def profile_features(df):
    feats = pd.DataFrame(index=df.index)
    feats["eig"] = df["rank_eigenvector"]
    feats["out"] = df["rank_out_degree"]
    feats["btw"] = df["rank_betweenness"].fillna(len(df) + 1)
    feats["gap"] = df["places_above_gdp"]
    feats["pull"] = np.log(df["pull"])
    feats["lq"] = np.log(df["sig_lq"].fillna(1.0))
    feats["share"] = df["sig_share"].fillna(0.0)
    return StandardScaler().fit_transform(feats)


def partner_profiles(year, states):
    with open(roles.CACHE / f"cfs_{year}_full.pkl", "rb") as f:
        bundle = pickle.load(f)
    labels = bundle["centralities"].set_index("state_id")["label"]
    e = bundle["edges"].assign(
        src=lambda d: d.ORIG_STATE.map(labels), dst=lambda d: d.DEST_STATE.map(labels)
    )
    w = e.pivot_table(
        index="src", columns="dst", values="SHIPMT_VALUE", aggfunc="sum", fill_value=0
    )
    w = w.reindex(index=states, columns=states, fill_value=0)
    out_share = w.div(w.sum(axis=1), axis=0).fillna(0)
    in_share = w.div(w.sum(axis=0), axis=1).fillna(0).T
    return normalize(np.hstack([out_share.values, in_share.values]))


def crosstab(clusters, rule_roles):
    t = pd.crosstab(pd.Series(clusters, index=rule_roles.index, name="cluster"), rule_roles)
    return {str(c): {r: int(n) for r, n in row.items() if n} for c, row in t.iterrows()}


def members(clusters, index):
    out = {}
    for c, s in sorted(zip(clusters, index)):
        out.setdefault(str(c), []).append(s)
    return out


def main():
    cfg = roles.load_config()
    results, assignments = {}, {}
    for year in roles.YEARS:
        df = roles.year_profile(year, cfg)
        rule = roles.assign_roles(df, cfg)[0].loc[df.index]
        x = profile_features(df)

        sweep = {}
        for k in K_RANGE:
            km = KMeans(n_clusters=k, n_init=50, random_state=SEED).fit_predict(x)
            sweep[str(k)] = {
                "silhouette": round(float(silhouette_score(x, km)), 3),
                "ari_vs_rules": round(float(adjusted_rand_score(rule, km)), 3),
            }
        km6 = KMeans(n_clusters=K_MAIN, n_init=50, random_state=SEED).fit_predict(x)
        ward6 = AgglomerativeClustering(n_clusters=K_MAIN, linkage="ward").fit_predict(x)
        se = partner_profiles(year, list(df.index))
        se6 = AgglomerativeClustering(n_clusters=K_MAIN, linkage="ward").fit_predict(se)
        assignments[year] = km6

        results[str(year)] = {
            "kmeans_sweep": sweep,
            "ari_vs_rules": {
                "kmeans_k6": round(float(adjusted_rand_score(rule, km6)), 3),
                "ward_k6": round(float(adjusted_rand_score(rule, ward6)), 3),
                "structural_equivalence_k6": round(float(adjusted_rand_score(rule, se6)), 3),
            },
            "kmeans_k6_vs_rules": crosstab(km6, rule),
            "kmeans_k6_members": members(km6, df.index),
            "structural_equivalence_k6_members": members(se6, df.index),
        }

    stability = {
        f"{a}-{b}": round(float(adjusted_rand_score(assignments[a], assignments[b])), 3)
        for a, b in [(2012, 2017), (2017, 2022), (2012, 2022)]
    }
    payload = {
        "note": "Post-hoc exploratory analysis, not pre-registered. See README.md.",
        "seed": SEED,
        "years": results,
        "kmeans_k6_ari_across_years": stability,
    }
    (HERE / "output" / "cluster_check.json").write_text(json.dumps(payload, indent=1) + "\n")
    for y, r in results.items():
        best = max(r["kmeans_sweep"].items(), key=lambda kv: kv[1]["silhouette"])
        print(y, r["ari_vs_rules"], "best silhouette k =", best[0], best[1])
    print("k-means k=6 across years:", stability)


if __name__ == "__main__":
    main()
