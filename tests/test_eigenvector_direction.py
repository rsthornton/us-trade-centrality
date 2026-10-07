"""The stored eigenvector values are the in-flow version (committed output only)."""

import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "analysis/eigenvector_direction/output/direction.json"


def test_every_source_is_in_flow():
    results = json.loads(OUT.read_text())["results"]
    assert len(results) >= 1
    assert {r["stored_matches"] for r in results} == {"in_flow"}


def test_kentucky_gap_holds_in_both_directions():
    thesis = json.loads(OUT.read_text())["results"][0]["watch"]["KY"]
    assert thesis == {"in_flow": 14, "out_flow": 15}
