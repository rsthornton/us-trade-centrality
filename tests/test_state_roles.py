"""Tests for the post-hoc state role taxonomy (analysis/state_roles/).

The output checks read the committed JSON only (standard library), so they run
without the gated CFS data or the evolution cache. The rule-logic check builds a
small synthetic frame and is skipped when pandas or PyYAML is unavailable.
"""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ROLES_DIR = ROOT / "analysis" / "state_roles"
ROLES = {"Engine", "Sustainer", "Router", "Specialist", "Market", "Generalist"}
YEARS = ("2012", "2017", "2022")


@pytest.fixture(scope="module")
def payload():
    return json.loads((ROLES_DIR / "output" / "state_roles.json").read_text())


def by_state(payload):
    return {s["state"]: s for s in payload["states"]}


def test_covers_all_states_and_years(payload):
    states = payload["states"]
    assert len(states) == 51
    for s in states:
        assert set(s["years"]) == set(YEARS)
        for entry in s["years"].values():
            assert entry["role"] in ROLES
        assert s["decade"]["role"] in ROLES


@pytest.mark.parametrize(
    "state,role",
    [("TX", "Engine"), ("CA", "Engine"), ("KY", "Sustainer"), ("MS", "Sustainer"),
     ("MA", "Router"), ("MN", "Router"), ("WY", "Specialist"), ("FL", "Market")],
)
def test_pinned_roles_hold_every_year(payload, state, role):
    entry = by_state(payload)[state]
    assert all(entry["years"][y]["role"] == role for y in YEARS)
    assert entry["decade"]["consistent"]


def test_colorado_routing_is_not_decade_stable(payload):
    co = by_state(payload)["CO"]
    assert co["decade"]["router_years"] < 2
    assert not co["decade"]["router_decade"]


def test_assign_roles_priority_and_generalist():
    pd = pytest.importorskip("pandas")
    pytest.importorskip("yaml")
    path = ROLES_DIR / "run_state_roles.py"
    spec = importlib.util.spec_from_file_location("run_state_roles", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cfg = mod.load_config()

    df = pd.DataFrame(
        {
            "rank_eigenvector": [1, 10, 30, 40, 45],
            "rank_out_degree": [2, 9, 30, 40, 45],
            "rank_betweenness": [1, None, 5, None, None],
            "places_above_gdp": [8, 9, 0, 0, 0],
            "sig_lq": [2.0, 2.0, 2.0, 40.0, 2.0],
            "sig_share": [0.3, 0.1, 0.1, 0.2, 0.01],
            "pull": [1.0, 1.0, 1.0, 1.0, 1.0],
        },
        index=["ENG", "SUS", "ROU", "SPE", "GEN"],
    )
    role, also, _ = mod.assign_roles(df, cfg)
    assert role.to_dict() == {
        "ENG": "Engine", "SUS": "Sustainer", "ROU": "Router",
        "SPE": "Specialist", "GEN": "Generalist",
    }
    assert "Sustainer" in also["ENG"]


def test_sensitivity_steps_stay_small():
    data = json.loads((ROLES_DIR / "output" / "sensitivity.json").read_text())
    assert len(data["variants"]) == 12
    for v in data["variants"]:
        assert v["of"] == 153
        assert v["changed"] <= 10, v["threshold"]
    gaps = data["undervalued_min_gap"]
    assert all(gaps[s] >= 5 for s in ("KY", "MS", "IN", "LA", "TN", "MI"))
    assert gaps["MT"] < 5


def test_clusters_recover_roles_only_weakly():
    data = json.loads((ROLES_DIR / "output" / "cluster_check.json").read_text())
    assert set(data["years"]) == set(YEARS)
    for year in YEARS:
        ari = data["years"][year]["ari_vs_rules"]
        assert all(-0.1 < value < 0.4 for value in ari.values()), (year, ari)
        clusters = data["years"][year]["kmeans_k6_members"]
        core = [c for c, members in clusters.items() if {"DC", "HI"} <= set(members)]
        assert core, year
        assert data["years"][year]["kmeans_k6_vs_rules"][core[0]] == {
            "Market": len(clusters[core[0]])
        }
