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

# Em que fases do ciclo cada ação ainda é acionável (estado da safra).
_ACTION_PHASES = {
    "advance_sowing": ["preparo_solo", "semeadura"],
    "increase_population": ["preparo_solo", "semeadura"],
    "correct_phosphorus": ["preparo_solo", "semeadura"],
    "liming": ["preparo_solo"],
    "add_fungicide": ["semeadura", "vegetativo", "reprodutivo"],
    "remove_fungicide": ["vegetativo", "reprodutivo"],
}
_PHASE_ORDER = ["preparo_solo", "semeadura", "vegetativo", "reprodutivo", "colheita"]

# Decision Value Engine: antes de recomendar, "vale a pena?". Evita recomendação irrelevante.
_VALUE_RECOMENDAR_RS = 200.0   # ganho líquido que justifica recomendar com convicção
_VALUE_AVALIAR_RS = 60.0       # abaixo disto, é ruído (não recomendar)
_VALUE_MIN_PROB = 0.55         # confiança mínima para sair de "não recomendar"


def _decision_value(delta_profit: float, prob: float) -> str:
    """'recomendar' | 'avaliar' | 'nao_recomendar' — o retorno justifica a ação?"""
    if delta_profit >= _VALUE_RECOMENDAR_RS and prob >= 0.6:
        return "recomendar"
    if delta_profit >= _VALUE_AVALIAR_RS and prob >= _VALUE_MIN_PROB:
        return "avaliar"
    return "nao_recomendar"


def _janela_status(key: str, phase: str | None) -> str:
    """'agora' (acionável), 'em breve' (fase ainda não chegou) ou 'passou' (perdeu a janela)."""
    if phase is None:
        return "agora"
    windows = _ACTION_PHASES.get(key)
    if not windows:
        return "agora"
    cur = _PHASE_ORDER.index(phase) if phase in _PHASE_ORDER else 0
    idxs = [_PHASE_ORDER.index(p) for p in windows]
    if cur < min(idxs):
        return "em breve"
    if cur > max(idxs):
        return "passou"
    return "agora"


def prioritized_actions(scenario: Scenario, top: int = 6, n_prob: int = 200, phase: str | None = None) -> list[dict]:
    """Ações ordenadas por Δlucro esperado (só as que aumentam o resultado).

    Quando ``phase`` é informada (estado da safra), cada ação ganha ``janela_status``
    (agora/em breve/passou) e as acionáveis agora vêm primeiro — o copiloto recomenda o
    que dá para fazer NESTE momento, não o que já passou."""
    decisions = recommend_decisions(scenario, n_prob=n_prob)
    items: list[dict] = []
    for d in decisions:
        if d.delta_profit_per_ha <= 0:
            continue
        veredito = _decision_value(d.delta_profit_per_ha, d.probability_positive)
        if veredito == "nao_recomendar":
            continue  # Decision Value Engine: filtra recomendações sem retorno real
        items.append({
            "key": d.key,
            "acao": d.label,
            "categoria": d.category,
            "impacto_sc_ha": d.delta_yield_sc_ha,
            "impacto_rs": d.delta_profit_per_ha,
            "custo_per_ha": d.added_cost_per_ha,
            "roi": d.action_roi,
            "probabilidade": d.probability_positive,
            "veredito": veredito,
            "prazo": _PRAZO.get(d.key, "na safra"),
            "porque": d.justification,
            "janela_status": _janela_status(d.key, phase),
        })
    # acionáveis agora primeiro; dentro de cada grupo, por valor esperado
    order = {"agora": 0, "em breve": 1, "passou": 2}
    items.sort(key=lambda x: (order.get(x["janela_status"], 0), -x["impacto_rs"]))
    items = items[:top]
    for i, it in enumerate(items):
        it["rank"] = i + 1
    return items
