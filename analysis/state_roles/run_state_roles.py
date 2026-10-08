"""
Post-hoc exploratory state role taxonomy (NOT pre-registered).

Classifies each state by the main way it powers the interstate commodity
network, for each CFS survey year (2012, 2017, 2022), using the thresholds
in roles.yaml. All three years come from the evolution cache so they share
one pipeline (SCTG 16 excluded everywhere). See README.md for the rules,
their counterfactuals and the caveats.

Reads the frozen evolution cache read-only; writes to output/ here.
"""

import json
import pickle
from collections import Counter
from pathlib import Path

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
CACHE = ROOT / "evolution" / "cache"
OUT = HERE / "output"

YEARS = [2012, 2017, 2022]
BASE_YEAR = 2017
GDP_FILES = {
    2012: ROOT / "evolution" / "data" / "state_gdp_2012.csv",
    2017: ROOT / "data" / "state_gdp_2017.csv",
    2022: ROOT / "evolution" / "data" / "state_gdp_2022.csv",
}


def load_config():
    return yaml.safe_load((HERE / "roles.yaml").read_text())


def load_sctg_names():
    meta = json.loads((ROOT / "web" / "public" / "data" / "metadata.json").read_text())
    return meta["sctg_names"]


def load_gdp(year):
    df = pd.read_csv(GDP_FILES[year])
    col = f"gdp_{year}_q4_millions"
    df = df.set_index("state_abbrev")
    return df[col], df["state_name"]


def signatures(commodity_edges, labels, cfg):
    """Highest location-quotient commodity per state, among single SCTG codes."""
    ce = commodity_edges.copy()
    ce["SCTG"] = ce["SCTG"].astype(str)
    ce = ce[~ce["SCTG"].str.contains("-") & (ce["SCTG"] != "00")]
    ce["state"] = ce["ORIG_STATE"].map(labels)
    out = ce.groupby(["state", "SCTG"])["weighted_value"].sum().unstack(fill_value=0)
    share = out.div(out.sum(axis=0), axis=1)
    lq = out.div(out.sum(axis=1), axis=0).div(out.sum(axis=0) / out.values.sum(), axis=1)

    rows = {}
    for state in out.index:
        for floor in (cfg["min_national_share"], cfg["fallback_min_national_share"]):
            eligible = lq.loc[state][share.loc[state] >= floor]
            if not eligible.empty:
                code = eligible.idxmax()
                rows[state] = (code, float(lq.loc[state, code]), float(share.loc[state, code]))
                break
        else:
            rows[state] = (None, None, None)
    return pd.DataFrame.from_dict(rows, orient="index", columns=["sig_code", "sig_lq", "sig_share"])


def year_profile(year, cfg):
    with open(CACHE / f"cfs_{year}_full.pkl", "rb") as f:
        bundle = pickle.load(f)
    cent = bundle["centralities"].set_index("label")
    labels = bundle["centralities"].set_index("state_id")["label"]

    df = pd.DataFrame(index=cent.index)
    df["rank_eigenvector"] = cent["eigenvector"].rank(ascending=False, method="min")
    df["rank_out_degree"] = cent["out_degree"].rank(ascending=False, method="min")
    btw = cent["betweenness"].where(cent["betweenness"] > 0)
    df["rank_betweenness"] = btw.rank(ascending=False, method="min")

    gdp, _ = load_gdp(year)
    df["rank_gdp"] = gdp.rank(ascending=False, method="min").reindex(df.index)
    df["places_above_gdp"] = df["rank_gdp"] - df["rank_eigenvector"]

    edges = bundle["edges"]
    out_total = edges.groupby("ORIG_STATE")["SHIPMT_VALUE"].sum().rename(index=labels)
    in_total = edges.groupby("DEST_STATE")["SHIPMT_VALUE"].sum().rename(index=labels)
    df["out_total"] = out_total.reindex(df.index)
    df["in_total"] = in_total.reindex(df.index)
    df["pull"] = df["in_total"] / df["out_total"]

    df = df.join(signatures(bundle["commodity_edges"], labels, cfg["signature"]))
    return df


def assign_roles(df, cfg):
    rules = {
        "Engine": (df["rank_eigenvector"] <= cfg["engine"]["max_eigenvector_rank"])
        & (df["rank_out_degree"] <= cfg["engine"]["max_out_degree_rank"]),
        "Sustainer": df["places_above_gdp"] >= cfg["sustainer"]["min_places_above_gdp"],
        "Router": df["rank_betweenness"] <= cfg["router"]["max_betweenness_rank"],
        "Specialist": (df["sig_lq"] >= cfg["specialist"]["min_location_quotient"])
        & (df["sig_share"] >= cfg["specialist"]["min_national_share"]),
        "Market": df["pull"] >= cfg["market"]["min_pull"],
    }
    rules = {k: v.fillna(False) for k, v in rules.items()}

    def primary(state):
        for role in cfg["priority"]:
            if rules[role][state]:
                return role
        return "Generalist"

    role = pd.Series({s: primary(s) for s in df.index})
    secondary = pd.Series({
        s: [r for r in cfg["priority"] if rules[r][s] and r != role[s]] for s in df.index
    })
    return role, secondary, rules["Router"]


def optional(value, cast, digits=None):
    if value is None or pd.isna(value):
        return None
    return round(cast(value), digits) if digits is not None else cast(value)


def decade_role(roles):
    counts = Counter(roles.values())
    top = max(counts.values())
    tied = [r for r, n in counts.items() if n == top]
    return roles[BASE_YEAR] if len(tied) > 1 else tied[0]


def main():
    cfg = load_config()
    names = load_sctg_names()
    _, state_names = load_gdp(BASE_YEAR)

    per_year = {}
    for year in YEARS:
        df = year_profile(year, cfg)
        df["role"], df["also"], df["router_flag"] = assign_roles(df, cfg)
        per_year[year] = df

    states = sorted(per_year[BASE_YEAR].index)
    records, rows = [], []
    for s in states:
        years = {}
        for year in YEARS:
            r = per_year[year].loc[s]
            entry = {
                "role": r["role"],
                "also": r["also"],
                "rank_eigenvector": int(r["rank_eigenvector"]),
                "rank_out_degree": int(r["rank_out_degree"]),
                "rank_betweenness": optional(r["rank_betweenness"], int),
                "rank_gdp": int(r["rank_gdp"]),
                "places_above_gdp": int(r["places_above_gdp"]),
                "pull": round(float(r["pull"]), 3),
                "signature_sctg": r["sig_code"],
                "signature": names.get(r["sig_code"], r["sig_code"]) if r["sig_code"] else None,
                "signature_lq": optional(r["sig_lq"], float, 2),
                "signature_share": optional(r["sig_share"], float, 4),
            }
            years[str(year)] = entry
            flat = {**entry, "also": ", ".join(entry["also"])}
            rows.append({"state": s, "year": year, **flat})

        role_by_year = {y: years[str(y)]["role"] for y in YEARS}
        eig = [years[str(y)]["rank_eigenvector"] for y in YEARS]
        router_years = int(sum(per_year[y].loc[s, "router_flag"] for y in YEARS))
        records.append({
            "state": s,
            "name": state_names.get(s, s),
            "years": years,
            "decade": {
                "role": decade_role(role_by_year),
                "consistent": len(set(role_by_year.values())) == 1,
                "router_years": router_years,
                "router_decade": router_years >= cfg["router"]["min_years_for_decade_flag"],
                "eigenvector_rank_range": max(eig) - min(eig),
            },
        })

    OUT.mkdir(exist_ok=True)
    payload = {
        "meta": {
            "note": "Post-hoc exploratory analysis, not pre-registered. See README.md.",
            "years": YEARS,
            "source": "evolution/cache (CFS 2012 PUMF, 2017 PUF, 2022 PUMS; SCTG 16 excluded)",
            "thresholds": cfg,
        },
        "states": records,
    }
    (OUT / "state_roles.json").write_text(json.dumps(payload, indent=1) + "\n")
    pd.DataFrame(rows).to_csv(OUT / "state_roles.csv", index=False)

    counts = {y: per_year[y]["role"].value_counts() for y in YEARS}
    summary = pd.DataFrame(counts).fillna(0).astype(int)
    print(summary.to_string())


if __name__ == "__main__":
    main()
