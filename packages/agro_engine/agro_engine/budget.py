"""Motor de Orçamento e Fluxo de Caixa da safra.

Traduz o plano da safra (custos por categoria + operações datadas) num **fluxo de
caixa** ao longo do ciclo: saídas nas datas de cada manejo/insumo e a entrada na
colheita (produtividade × preço). Calcula o **capital de giro** necessário (pico de
caixa negativo) — informação central para o agricultor planejar o financiamento da safra.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from . import phenology
from .models import Scenario


@dataclass
class CashflowEntry:
    day: str
    label: str
    category: str
    amount: float  # negativo = saída (custo); positivo = entrada (receita)


def season_budget(scenario: Scenario, expected_sc_ha: float) -> dict:
    """Monta o orçamento por categoria e o fluxo de caixa datado da safra."""
    stages = phenology.stage_dates(scenario.cultivar, scenario.sowing_date, scenario.weather)
    harvest = stages.get("R8", scenario.sowing_date)
    # Insumos/preparo: caixa sai ~30 dias antes da semeadura (compra antecipada).
    pre_season = date.fromordinal(scenario.sowing_date.toordinal() - 30)

    # Custo por categoria (itens fixos + operações).
    by_category: dict[str, float] = {}
    entries: list[CashflowEntry] = []

    for c in scenario.costs:
        by_category[c.category] = round(by_category.get(c.category, 0.0) + c.cost_per_ha, 2)
        entries.append(CashflowEntry(pre_season.isoformat(), c.description, c.category, -c.cost_per_ha))

    for o in scenario.operations:
        cat = o.kind
        by_category[cat] = round(by_category.get(cat, 0.0) + o.cost_per_ha, 2)
        label = f"{o.kind}{(' — ' + o.product) if o.product else ''}"
        entries.append(CashflowEntry(o.op_date.isoformat(), label, cat, -o.cost_per_ha))

    total_cost = round(sum(by_category.values()), 2)
    revenue = round(expected_sc_ha * scenario.soybean_price_per_sc, 2)
    entries.append(CashflowEntry(harvest.isoformat(), "Faturamento dos grãos", "receita", revenue))

    entries.sort(key=lambda e: e.day)

    # Fluxo acumulado → pico de caixa negativo = capital de giro necessário.
    running = 0.0
    cumulative: list[dict] = []
    peak_negative = 0.0
    for e in entries:
        running += e.amount
        peak_negative = min(peak_negative, running)
        cumulative.append({"day": e.day, "label": e.label, "amount": e.amount, "balance": round(running, 2)})

    return {
        "cost_by_category": dict(sorted(by_category.items(), key=lambda kv: -kv[1])),
        "total_cost_per_ha": total_cost,
        "revenue_per_ha": revenue,
        "profit_per_ha": round(revenue - total_cost, 2),
        "working_capital_per_ha": round(-peak_negative, 2),  # pico de financiamento
        "harvest_date": harvest.isoformat(),
        "cashflow": cumulative,
    }
