"""Motor de Priorização — a tabela que vale mais que dezenas de gráficos.

O agricultor não tem tempo nem dinheiro para fazer tudo. Este motor ORDENA as ações
possíveis pelo **valor esperado** (Δlucro), e devolve, para cada uma: o impacto em sc/ha
e R$, o custo, o ROI, o prazo e o porquê — com a probabilidade de dar certo. É a resposta
direta a "qual a melhor decisão agora?" e "onde coloco meu dinheiro primeiro?".

Reaproveita o Motor de Decisão (re-simulação com/sem cada ação) — então os números são
coerentes com tudo que a plataforma calcula.
"""

from __future__ import annotations

from .decision import recommend_decisions
from .models import Scenario

# Quando cada tipo de ação precisa ser tomada (orienta o agricultor no tempo).
_PRAZO = {
    "advance_sowing": "antes de semear",
    "correct_phosphorus": "antes de semear",
    "liming": "meses antes (residual)",
    "increase_population": "na semeadura",
    "add_fungicide": "janela R1–R5",
    "remove_fungicide": "durante a safra",
}


def prioritized_actions(scenario: Scenario, top: int = 6, n_prob: int = 200) -> list[dict]:
    """Ações ordenadas por Δlucro esperado (só as que aumentam o resultado)."""
    decisions = recommend_decisions(scenario, n_prob=n_prob)
    items: list[dict] = []
    for d in decisions:
        if d.delta_profit_per_ha <= 0:
            continue
        items.append({
            "key": d.key,
            "acao": d.label,
            "categoria": d.category,
            "impacto_sc_ha": d.delta_yield_sc_ha,
            "impacto_rs": d.delta_profit_per_ha,
            "custo_per_ha": d.added_cost_per_ha,
            "roi": d.action_roi,
            "probabilidade": d.probability_positive,
            "prazo": _PRAZO.get(d.key, "na safra"),
            "porque": d.justification,
        })
    items.sort(key=lambda x: x["impacto_rs"], reverse=True)
    items = items[:top]
    for i, it in enumerate(items):
        it["rank"] = i + 1
    return items
