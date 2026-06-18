"""
Go/no-go gates for the evolution study.

Each gate returns PASS, FAIL, or REVIEW. REVIEW means the gate could not
be evaluated automatically (e.g. no published total on file) and the
computed value needs a manual check against Census publications.
"""


def run_gates(bundle, gate_config):
    year = bundle["year"]
    stats = bundle["stats"]
    results = []

    published = (gate_config.get("published_totals") or {}).get(year)
    tolerance = gate_config["national_total_tolerance"]
    if published:
        delta = abs(stats["raw_weighted_total"] - published) / published
        results.append({
            "gate": "national_total",
            "year": year,
            "value": stats["raw_weighted_total"],
            "published": published,
            "relative_delta": delta,
            "status": "PASS" if delta <= tolerance else "FAIL",
        })
    else:
        results.append({
            "gate": "national_total",
            "year": year,
            "value": stats["raw_weighted_total"],
            "published": None,
            "status": "REVIEW",
            "note": "no published total in thresholds.yaml; check against Census CFS publication",
        })

    results.append({
        "gate": "sctg16_excluded",
        "year": year,
        "value": stats["sctg16_records_dropped"],
        "status": "PASS" if stats["sctg16_records_dropped"] >= 0 else "FAIL",
        "note": f"{stats['sctg16_records_dropped']:,} records dropped before network construction",
    })

    grouped_max = gate_config["grouped_sctg_share_max"]
    results.append({
        "gate": "grouped_sctg_share",
        "year": year,
        "value": stats["grouped_sctg_share"],
        "threshold": grouped_max,
        "status": "PASS" if stats["grouped_sctg_share"] <= grouped_max else "REVIEW",
        "note": "above threshold: document uncertainty, consider grouped-code unit of analysis"
        if stats["grouped_sctg_share"] > grouped_max else "",
    })

    if year == 2022:
        trunc_max = gate_config["truncation_share_max"]
        results.append({
            "gate": "truncation_share",
            "year": year,
            "value": stats["truncation_share"],
            "threshold": trunc_max,
            "status": "PASS" if stats["truncation_share"] <= trunc_max else "REVIEW",
            "note": "values at/above $30M are truncated in the 2022 PUMS; check top corridors"
            if stats["truncation_share"] > trunc_max else "",
        })

    return results


def any_hard_failure(gate_results):
    return any(g["status"] == "FAIL" for g in gate_results)
