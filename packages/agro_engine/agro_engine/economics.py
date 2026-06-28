"""Motor econômico — custo, receita, lucro, ROI e pontos de equilíbrio.

Produtividade alta não significa lucro: este motor traduz a produtividade estimada
em resultado financeiro por hectare, sempre exibindo break-even (produtividade e
preço mínimos) para apoiar decisões de investimento de manejo.
"""

from __future__ import annotations

from .models import EconomicsResult, Scenario


def compute(scenario: Scenario, expected_sc_ha: float) -> EconomicsResult:
    cost = scenario.total_cost_per_ha
    price = scenario.soybean_price_per_sc
    revenue = expected_sc_ha * price
    profit = revenue - cost
    margin = (profit / revenue) if revenue > 0 else 0.0
    roi = (profit / cost) if cost > 0 else 0.0
    breakeven_yield = (cost / price) if price > 0 else 0.0
    breakeven_price = (cost / expected_sc_ha) if expected_sc_ha > 0 else 0.0
    return EconomicsResult(
        total_cost_per_ha=round(cost, 2),
        revenue_per_ha=round(revenue, 2),
        profit_per_ha=round(profit, 2),
        margin_pct=round(margin * 100, 1),
        roi=round(roi, 2),
        breakeven_yield_sc_ha=round(breakeven_yield, 1),
        breakeven_price_per_sc=round(breakeven_price, 2),
    )
