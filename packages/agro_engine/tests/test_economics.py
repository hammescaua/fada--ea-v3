"""Testes do motor econômico."""

from __future__ import annotations

from agro_engine import compute_economics


def test_profit_and_breakeven(base_scenario):
    econ = compute_economics(base_scenario, expected_sc_ha=80.0)
    expected_cost = base_scenario.total_cost_per_ha
    assert econ.total_cost_per_ha == round(expected_cost, 2)
    assert econ.revenue_per_ha == round(80.0 * base_scenario.soybean_price_per_sc, 2)
    assert econ.profit_per_ha == round(econ.revenue_per_ha - econ.total_cost_per_ha, 2)
    # break-even em produtividade = custo / preço
    assert econ.breakeven_yield_sc_ha == round(expected_cost / 120.0, 1)


def test_zero_yield_does_not_crash(base_scenario):
    econ = compute_economics(base_scenario, expected_sc_ha=0.0)
    assert econ.revenue_per_ha == 0.0
    assert econ.profit_per_ha < 0  # só custo


def test_higher_yield_increases_roi(base_scenario):
    low = compute_economics(base_scenario, 50.0).roi
    high = compute_economics(base_scenario, 90.0).roi
    assert high > low
