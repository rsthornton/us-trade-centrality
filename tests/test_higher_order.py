"""Tests for the post-hoc higher-order study (analysis/higher_order/).

Each measure gets a case it must pass and a case it must fail, so a measure that
cannot fail would show up here.
"""

import importlib.util
import sys
from pathlib import Path

import numpy as np

HO_DIR = Path(__file__).resolve().parent.parent / "analysis" / "higher_order"
sys.path.insert(0, str(HO_DIR))


def load(name):
    spec = importlib.util.spec_from_file_location(name, HO_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


three_way = load("run_three_way")
states_as_variables = load("run_states_as_variables")


def synthetic(rng, n=6, c=4):
    band = rng.integers(0, 3, (n, n))
    band[np.arange(n), np.arange(n)] = -1
    offdiag = (band >= 0)[..., None]
    base = (
        rng.gamma(2, 1, (n, n, 1))
        * rng.gamma(2, 1, (n, 1, c))
        * rng.gamma(2, 1, (1, n, c))
        * offdiag
    )
    return band, base, offdiag


def test_pairs_model_is_exact_without_three_way_structure():
    band, base, _ = synthetic(np.random.default_rng(0))
    p = base / base.sum()
    assert three_way.kl(p, three_way.fit_pairs(p)) < 1e-9


def test_distance_term_removes_a_band_by_commodity_effect():
    rng = np.random.default_rng(1)
    band, base, offdiag = synthetic(rng)
    effect = np.exp(rng.normal(0, 1, (3, 4)))[np.where(band >= 0, band, 0)] * offdiag
    p = base * effect / (base * effect).sum()
    assert three_way.kl(p, three_way.fit_pairs(p)) > 0.01
    assert three_way.kl(p, three_way.fit_pairs(p, band)) < 1e-6


def test_distance_term_leaves_unrelated_three_way_structure():
    rng = np.random.default_rng(2)
    band, base, offdiag = synthetic(rng)
    t = base * np.exp(rng.normal(0, 1, base.shape)) * offdiag
    p = t / t.sum()
    assert three_way.kl(p, three_way.fit_pairs(p, band)) > 0.5 * three_way.kl(
        p, three_way.fit_pairs(p)
    )


def test_o_information_signs():
    rng = np.random.default_rng(3)
    x = rng.normal(size=(20000, 2))
    total = x.sum(1) + 0.3 * rng.normal(size=20000)
    common = rng.normal(size=20000)
    copies = np.column_stack([common + 0.3 * rng.normal(size=20000) for _ in range(3)])
    independent = rng.normal(size=(20000, 3))
    oi = states_as_variables.o_information
    assert oi(np.corrcoef(np.column_stack([x, total]).T)) < -0.5
    assert oi(np.corrcoef(copies.T)) > 0.5
    assert abs(oi(np.corrcoef(independent.T))) < 0.01


dependence = load("run_dependence")


def test_sole_supplier_link_needs_a_majority():
    import pandas as pd

    cells = pd.DataFrame({
        "d": ["X", "X", "Y", "Y", "Y"],
        "SCTG": ["02"] * 5,
        "o": ["A", "B", "A", "B", "C"],
        "usd": [60.0, 40.0, 40.0, 35.0, 25.0],
        "records": [6, 4, 4, 3, 2],
    })
    links = dependence.sole_supplier_links(cells)
    assert list(zip(links.d, links.o)) == [("X", "A")]
    assert links.records.tolist() == [6] and links.dc_records.tolist() == [10]


def test_mode_groups_reject_unknown_codes():
    import pandas as pd
    import pytest

    assert dependence.mode_group(2022, pd.Series([111, 21, 15])).tolist() == [
        "truck", "air/parcel", "pipeline"
    ]
    assert dependence.mode_group(2017, pd.Series([4, 14, 12])).tolist() == [
        "truck", "air/parcel", "pipeline"
    ]
    with pytest.raises(KeyError):
        dependence.mode_group(2022, pd.Series([4]))


def test_hhi_bounds():
    import pandas as pd

    w = pd.Series([1.0, 1.0, 1.0, 1.0, 5.0])
    keys = pd.Series(["even"] * 4 + ["single"])
    h = dependence.hhi(w, keys)
    assert abs(h["even"] - 0.25) < 1e-12 and h["single"] == 1.0


def test_groups_without_three_way_structure_pool_into_some():
    rng = np.random.default_rng(4)
    _, a, _ = synthetic(rng)
    _, b, _ = synthetic(rng)
    for t in (a, b):
        assert three_way.kl(t / t.sum(), three_way.fit_pairs(t / t.sum())) < 1e-9
    pooled_t = a + b
    pooled = three_way.cell_terms(pooled_t / pooled_t.sum(), three_way.fit_pairs(
        pooled_t / pooled_t.sum()
    ))
    assert pooled.sum() > 0.01
    shares = [dependence.attributed_share(pooled, pooled_t, t) for t in (a, b)]
    assert abs(sum(shares) - 1) < 1e-9
    _, c, offdiag = synthetic(rng)
    c = c * np.exp(rng.normal(0, 1, c.shape)) * offdiag
    assert three_way.kl(c / c.sum(), three_way.fit_pairs(c / c.sum())) > 0.01
