"""
Build state_gdp_<year>.csv from the BEA SQGDP1 all-areas table.

Source: https://apps.bea.gov/regional/zip/SQGDP.zip (SQGDP1__ALL_AREAS CSV,
LineCode 3 = current-dollar GDP, millions). Output matches the schema of
data/state_gdp_2017.csv used by the thesis pipeline:

    state_abbrev,state_name,gdp_<year>_q4_millions

Usage:
    python build_state_gdp.py 2012 2022 \
        --source /Users/home/Desktop/halcyonic-projects/archive/reference/SQGDP1__ALL_AREAS_2005_2025.csv
"""

import argparse
import csv
from pathlib import Path

STATE_ABBREVS = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "District of Columbia": "DC", "Florida": "FL", "Georgia": "GA", "Hawaii": "HI",
    "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY",
}


def build(source, year, out_dir):
    column = f"{year}:Q4"
    rows = []
    with open(source, newline="", encoding="latin-1") as f:
        for record in csv.DictReader(f):
            name = (record.get("GeoName") or "").strip().rstrip("*")
            if record.get("LineCode") != "3" or name not in STATE_ABBREVS:
                continue
            value = float(record[column])
            rows.append((STATE_ABBREVS[name], name, round(value)))

    if len(rows) != 51:
        raise SystemExit(f"{year}: expected 51 areas (50 states + DC), got {len(rows)}")

    out_path = out_dir / f"state_gdp_{year}.csv"
    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["state_abbrev", "state_name", f"gdp_{year}_q4_millions"])
        for row in sorted(rows):
            writer.writerow(row)
    print(f"wrote {out_path} ({len(rows)} states)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("years", type=int, nargs="+")
    parser.add_argument("--source", required=True)
    args = parser.parse_args()
    out_dir = Path(__file__).resolve().parent
    for year in args.years:
        build(args.source, year, out_dir)


if __name__ == "__main__":
    main()
