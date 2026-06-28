"""Testes do motor Monte Carlo (distribuição de resultados)."""

from __future__ import annotations

from agro_engine import run_montecarlo


def test_distribution_is_ordered_and_bounded(base_scenario):
    r = run_montecarlo(base_scenario, n=500, seed=42)
    y = r["yield"]
    assert y["p10"] <= y["p50"] <= y["p90"]
    assert r["profit"]["p10"] <= r["profit"]["p50"] <= r["profit"]["p90"]
    probs = r["probabilities"]
    for key in ("yield_above_target", "profit_above_target", "loss"):
        assert 0.0 <= probs[key] <= 1.0
    assert r["iterations"] == 500


def test_reproducible_with_seed(base_scenario):
    a = run_montecarlo(base_scenario, n=300, seed=7)
    b = run_montecarlo(base_scenario, n=300, seed=7)
    assert a["yield"]["mean"] == b["yield"]["mean"]
    assert a["profit"]["p50"] == b["profit"]["p50"]


def test_higher_price_volatility_widens_profit_spread(base_scenario):
    low = run_montecarlo(base_scenario, n=600, seed=1, price_sd_pct=0.02)
    high = run_montecarlo(base_scenario, n=600, seed=1, price_sd_pct=0.30)
    low_spread = low["profit"]["p90"] - low["profit"]["p10"]
    high_spread = high["profit"]["p90"] - high["profit"]["p10"]
    assert high_spread > low_spread


def test_histogram_counts_sum_to_iterations(base_scenario):
    r = run_montecarlo(base_scenario, n=400, seed=3)
    assert sum(b["count"] for b in r["yield"]["histogram"]) == 400


def test_profit_target_probability_monotonic(base_scenario):
    """P(lucro ≥ alvo) deve cair conforme o alvo sobe."""
    easy = run_montecarlo(base_scenario, n=600, seed=5, profit_target_per_ha=0.0)
    hard = run_montecarlo(base_scenario, n=600, seed=5, profit_target_per_ha=4000.0)
    assert easy["probabilities"]["profit_above_target"] >= hard["probabilities"]["profit_above_target"]
