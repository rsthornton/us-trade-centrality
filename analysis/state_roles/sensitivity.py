"""
Threshold sensitivity for the state role taxonomy (post-hoc, exploratory).

Moves each threshold in roles.yaml one step down and one step up, all else
fixed, and records which state-years change role. Also reports, for the
thesis's eight structurally undervalued states, how many survey years each
qualifies as a Sustainer at cutoffs 4 to 7, and the threshold-free minimum gap
(places above GDP rank) across the three years.

Reads the frozen evolution cache read-only; writes to output/ here.
"""

import copy
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location("run_state_roles", HERE / "run_state_roles.py")
roles = importlib.util.module_from_spec(spec)
spec.loader.exec_module(roles)

VARIANTS = [
    ("engine ranks", "engine", ["max_eigenvector_rank", "max_out_degree_rank"], [6, 8]),
    ("sustainer places", "sustainer", ["min_places_above_gdp"], [4, 6]),
    ("router rank", "router", ["max_betweenness_rank"], [10, 14]),
    ("specialist LQ", "specialist", ["min_location_quotient"], [12, 18]),
    ("specialist share", "specialist", ["min_national_share"], [0.04, 0.06]),
    ("market pull", "market", ["min_pull"], [1.2, 1.4]),
]
UNDERVALUED = ["KY", "MS", "IN", "LA", "TN", "MI", "MT", "SC"]


def classify(profiles, cfg):
    return {y: roles.assign_roles(profiles[y], cfg)[0] for y in profiles}


def main():
    cfg = roles.load_config()
    profiles = {y: roles.year_profile(y, cfg) for y in roles.YEARS}
    base = classify(profiles, cfg)
    total = sum(len(base[y]) for y in base)

    variants = []
    for name, section, keys, values in VARIANTS:
        for value in values:
            alt = copy.deepcopy(cfg)
            for key in keys:
                alt[section][key] = value
            new = classify(profiles, alt)
            changes = [
                {"state": s, "year": y, "from": base[y][s], "to": new[y][s]}
                for y in roles.YEARS for s in base[y].index if new[y][s] != base[y][s]
            ]
            variants.append({
                "threshold": name, "value": value,
                "changed": len(changes), "of": total, "changes": changes,
            })

    cutoffs = {}
    for cutoff in (4, 5, 6, 7):
        alt = copy.deepcopy(cfg)
        alt["sustainer"]["min_places_above_gdp"] = cutoff
        new = classify(profiles, alt)
        cutoffs[str(cutoff)] = {
            s: int(sum(new[y][s] == "Sustainer" for y in roles.YEARS)) for s in UNDERVALUED
        }

    gaps = {
        s: {str(y): int(profiles[y].loc[s, "places_above_gdp"]) for y in roles.YEARS}
        for s in UNDERVALUED
    }
    payload = {
        "note": "Post-hoc exploratory analysis, not pre-registered. See README.md.",
        "variants": variants,
        "undervalued_sustainer_years_by_cutoff": cutoffs,
        "undervalued_gaps": gaps,
        "undervalued_min_gap": {s: min(g.values()) for s, g in gaps.items()},
    }
    (HERE / "output" / "sensitivity.json").write_text(json.dumps(payload, indent=1) + "\n")
    for v in variants:
        print(f"{v['threshold']:18} {str(v['value']):5} {v['changed']:3}/{v['of']}")


if __name__ == "__main__":
    main()
