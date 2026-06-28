"""Testes do orçamento/fluxo de caixa e do impacto por manejo."""

from __future__ import annotations

from agro_engine import operations_impact, season_budget, simulate


def test_budget_sums_and_working_capital(base_scenario):
    sim = simulate(base_scenario)
    b = season_budget(base_scenario, sim.yield_result.expected_sc_ha)

    # total por categoria bate com a soma de custos + operações
    expected_total = base_scenario.total_cost_per_ha
    assert abs(b["total_cost_per_ha"] - expected_total) < 0.5
    assert abs(b["profit_per_ha"] - (b["revenue_per_ha"] - b["total_cost_per_ha"])) < 0.5
    # capital de giro é positivo e não maior que o custo total
    assert 0 < b["working_capital_per_ha"] <= b["total_cost_per_ha"] + 1
    # o fluxo termina positivo (após o faturamento)
    assert b["cashflow"][-1]["balance"] > 0
    assert b["cashflow"][-1]["label"] == "Faturamento dos grãos"


def test_cashflow_is_chronological(base_scenario):
    sim = simulate(base_scenario)
    b = season_budget(base_scenario, sim.yield_result.expected_sc_ha)
    days = [e["day"] for e in b["cashflow"]]
    assert days == sorted(days)


def test_operations_impact_fungicide_positive(base_scenario):
    impacts = operations_impact(base_scenario)
    assert len(impacts) == len(base_scenario.operations)
    fung = [i for i in impacts if i.kind == "fungicida"]
    # numa região de alta pressão de ferrugem, o fungicida agrega produtividade
    assert all(i.delta_yield_sc_ha > 0 for i in fung)
    # net pode ser positivo ou negativo, mas o valor bruto é coerente
    for i in impacts:
        assert abs(i.value_per_ha - i.delta_yield_sc_ha * base_scenario.soybean_price_per_sc) < 1.0


def test_operations_impact_sorted_by_net(base_scenario):
    impacts = operations_impact(base_scenario)
    nets = [i.net_per_ha for i in impacts]
    assert nets == sorted(nets, reverse=True)
