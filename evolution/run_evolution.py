"""
Three-survey evolution study runner.

Builds the 2012/2017/2022 interstate trade networks, runs the go/no-go
gates, evaluates the pre-registered H1-H3 forecasts (H4-H5 are exploratory:
metrics reported, no verdict) for the retrodiction
pair (2017 -> 2012) and the prediction pair (2017 -> 2022), and writes an
auditable results bundle (report.md + results.json + the exact thresholds
used) under results/.

Usage:
    python run_evolution.py                  # full data, all years present
    python run_evolution.py --sample 200000  # smoke run on first N records
    python run_evolution.py --years 2017 2022
"""

import argparse
import hashlib
import json
import logging
import pickle
import shutil
from datetime import datetime
from pathlib import Path

import yaml

from src.loaders import load_year, load_year_config
from src.gates import run_gates, any_hard_failure
from src.hypotheses import run_pair

log = logging.getLogger("evolution")

EVOLUTION_DIR = Path(__file__).resolve().parent
CACHE_DIR = EVOLUTION_DIR / "cache"
RESULTS_DIR = EVOLUTION_DIR / "results"


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_or_load(year, sample_size, truncation_value, refresh=False):
    CACHE_DIR.mkdir(exist_ok=True)
    tag = f"s{sample_size}" if sample_size else "full"
    cache_path = CACHE_DIR / f"cfs_{year}_{tag}.pkl"
    if cache_path.exists() and not refresh:
        log.info(f"{year}: loading cached bundle {cache_path.name}")
        with open(cache_path, "rb") as f:
            return pickle.load(f)
    bundle = load_year(year, sample_size=sample_size, truncation_value=truncation_value)
    with open(cache_path, "wb") as f:
        pickle.dump(bundle, f)
    return bundle


def verdict_rows(pair_results):
    rows = []
    for pair in pair_results:
        suffix = "R" if pair["pair"] == "retrodiction" else "P"
        arc = f"{pair['base_year']} -> {pair['target_year']}"
        for h in ["H1", "H2", "H3", "H4", "H5"]:
            result = pair[h]
            holds = result.get("holds")
            if h in ("H4", "H5"):
                verdict = "EXPLORATORY"
            else:
                verdict = "HOLD" if holds else ("BREAK" if holds is not None else "N/A")
            if h == "H1":
                detail = ", ".join(
                    f"{m}: rho={v['spearman']:.3f} ({v['forecast']})"
                    for m, v in result["measures"].items()
                ) + f"; top10 {result['top10_overlap']['count']}/10"
            elif h == "H2":
                detail = f"jaccard={result['jaccard']:.3f} ({result['forecast']})"
            elif h == "H3" and holds is not None:
                detail = (f"pharma={result['pharma_delta']:.3f}, "
                          f"ag={result['agriculture_delta']:.3f} ({result['forecast']})")
            elif h == "H4":
                detail = f"nmi={result['nmi']:.3f} ({result['forecast']})"
            elif h == "H5":
                detail = (f"gini {result['gini_base']:.3f} -> {result['gini_target']:.3f} "
                          f"({result['forecast']})")
            else:
                detail = result.get("note", "")
            rows.append({"id": f"{h}-{suffix}", "arc": arc, "detail": detail, "verdict": verdict})
    return rows


def write_report(out_dir, args, gate_results, pair_results, thresholds_hash, year_stats):
    rows = verdict_rows(pair_results)
    lines = [
        "# Three-Survey Evolution Run",
        f"*{datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        f"- sample_size: {args.sample or 'full'}",
        f"- years: {', '.join(str(y) for y in sorted(year_stats))}",
        f"- thresholds.yaml sha256: `{thresholds_hash}`",
        "",
        "## Gates",
        "",
        "| Gate | Year | Value | Status | Note |",
        "|---|---|---|---|---|",
    ]
    for g in gate_results:
        value = g.get("value")
        value_str = f"{value:,.0f}" if isinstance(value, float) and value > 1000 else str(value)
        lines.append(f"| {g['gate']} | {g['year']} | {value_str} | {g['status']} | {g.get('note', '')} |")

    lines += ["", "## Verdicts", "", "| Forecast | Arc | Result | Verdict |", "|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['id']} | {r['arc']} | {r['detail']} | **{r['verdict']}** |")

    lines += [
        "",
        "## Reading the table",
        "",
        "Hn-R is the retrodiction arc (2017 -> 2012), expected to HOLD.",
        "Hn-P is the prediction arc (2017 -> 2022), the live forecast.",
        "A pattern of R holding while P breaks quantifies COVID-era structural disruption.",
        "",
        "## Year stats",
        "",
    ]
    for year in sorted(year_stats):
        s = year_stats[year]
        lines.append(
            f"- **{year}**: {s['raw_records']:,} records loaded, "
            f"${s['raw_weighted_total']:,.0f} weighted total, "
            f"{s['edge_count']} interstate edges, "
            f"grouped SCTG share {s['grouped_sctg_share']:.4f}"
        )

    (out_dir / "report.md").write_text("\n".join(lines) + "\n")
    return rows


def main():
    parser = argparse.ArgumentParser(description="Run the three-survey evolution study")
    parser.add_argument("--sample", type=int, default=None, help="first N records per year (smoke runs)")
    parser.add_argument("--years", type=int, nargs="+", default=[2012, 2017, 2022])
    parser.add_argument("--refresh-cache", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    thresholds_path = EVOLUTION_DIR / "thresholds.yaml"
    with open(thresholds_path) as f:
        thresholds = yaml.safe_load(f)
    thresholds_hash = file_sha256(thresholds_path)

    anchor = thresholds["anchor_year"]
    if anchor not in args.years:
        raise SystemExit(f"anchor year {anchor} must be among --years")

    available = []
    for year in args.years:
        if Path(load_year_config(year)["source_file"]).exists():
            available.append(year)
        else:
            log.warning(f"{year}: source file missing, skipping (see data/fetch scripts)")

    truncation_value = thresholds["gates"]["truncation_value"]
    bundles = {
        year: build_or_load(year, args.sample, truncation_value, refresh=args.refresh_cache)
        for year in available
    }

    gate_results = []
    for year in available:
        gate_results.extend(run_gates(bundles[year], thresholds["gates"]))
    if any_hard_failure(gate_results):
        log.error("hard gate failure; stopping before hypothesis tests")
        for g in gate_results:
            log.error(f"  {g['gate']} {g['year']}: {g['status']}")
        raise SystemExit(1)

    pair_results = []
    for label, pair in thresholds["pairs"].items():
        if pair["base"] in bundles and pair["target"] in bundles:
            pair_results.append(run_pair(label, bundles[pair["base"]], bundles[pair["target"]], thresholds))
        else:
            log.warning(f"{label}: missing year, skipped")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = RESULTS_DIR / f"evolution_{timestamp}"
    out_dir.mkdir(parents=True)
    shutil.copy2(thresholds_path, out_dir / "thresholds.yaml")

    year_stats = {year: bundles[year]["stats"] for year in bundles}
    rows = write_report(out_dir, args, gate_results, pair_results, thresholds_hash, year_stats)

    results = {
        "generated": timestamp,
        "sample_size": args.sample,
        "thresholds_sha256": thresholds_hash,
        "years": year_stats,
        "gates": gate_results,
        "pairs": pair_results,
        "verdicts": rows,
    }
    with open(out_dir / "results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n{'Forecast':<8} {'Arc':<14} {'Verdict':<8}")
    for r in rows:
        print(f"{r['id']:<8} {r['arc']:<14} {r['verdict']:<8}")
    print(f"\nArtifacts: {out_dir}")


if __name__ == "__main__":
    main()
