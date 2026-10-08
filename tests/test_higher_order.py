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
