"""Radar da Safra — a tela que o agricultor entende em 20 segundos.

Transforma o gêmeo de "simulador" em "copiloto": em vez de esperar o produtor perguntar,
o Radar **detecta** a situação da safra e responde de cara as quatro perguntas que
importam — qual o maior risco, qual a melhor decisão agora, quanto ela vale e por quê
(com a confiança). Resume a saúde da safra em 6 dimensões (Solo, Clima, Sanidade,
Nutrição, Mercado, Execução) e aponta o **gargalo**, a **oportunidade** e o **investimento**
de maior retorno.

Tudo é derivado da decomposição IPPD (cada fator vira nota) e do Motor de Priorização —
coerente e explicável, nada inventado.
"""

from __future__ import annotations

from .priorities import prioritized_actions
from .models import Scenario
from .simulate import simulate

# Cada dimensão agrega os fatores da cascata IPPD que a compõem.
_DIMENSIONS = {
    "solo": ["Solo", "Compactação", "Nematoides", "Rotação"],
    "clima": ["Água", "Calor"],
    "sanidade": ["Daninhas", "Pragas", "Doenças"],
    "nutricao": ["Nutrição"],
    "execucao": ["Janela de semeadura", "População"],
}
_DIM_LABEL = {
    "solo": "Solo", "clima": "Clima", "sanidade": "Sanidade",
    "nutricao": "Nutrição", "mercado": "Mercado", "execucao": "Execução",
}
# Peso de cada dimensão no índice geral da safra.
_DIM_WEIGHT = {"clima": 0.24, "solo": 0.20, "sanidade": 0.20, "nutricao": 0.15, "execucao": 0.11, "mercado": 0.10}


def _factor_multipliers(base_potential: float, contributions: list) -> dict[str, float]:
    """Reconstrói o multiplicador de cada fator percorrendo a cascata aditiva."""
    running = base_potential
    mult: dict[str, float] = {}
    for c in contributions:
        before = running
        running = before + c.delta_sc_ha
        mult[c.label] = (running / before) if before else 1.0
    return mult


def _score_from_mult(labels: list[str], mult: dict[str, float]) -> float:
    m = 1.0
    for lab in labels:
        m *= mult.get(lab, 1.0)
    return round(max(0.0, min(1.0, m)) * 100, 0)


def _mercado_score(econ) -> float:
    """Saúde de mercado: folga de margem e distância do ponto de equilíbrio."""
    margin = econ.margin_pct  # fração
    score = 40 + margin * 120  # margem 50% -> 100; margem 0 -> 40
    return round(max(0.0, min(100.0, score)), 0)


def season_radar(scenario: Scenario) -> dict:
    """Monta o Radar da Safra: índice geral, 6 dimensões e os 3 destaques + as 4 respostas."""
    sim = simulate(scenario)
    y = sim.yield_result
    econ = sim.economics
    mult = _factor_multipliers(y.base_potential_sc_ha, y.contributions)

    dimensions = {k: _score_from_mult(labs, mult) for k, labs in _DIMENSIONS.items()}
    dimensions["mercado"] = _mercado_score(econ)

    score = round(sum(dimensions[k] * w for k, w in _DIM_WEIGHT.items()), 0)

    # Maior risco = o fator que mais derruba a produtividade (o gargalo da safra).
    losses = [(c.label, c.delta_sc_ha, c.detail) for c in y.contributions if c.delta_sc_ha < -0.1]
    losses.sort(key=lambda x: x[1])
    maior_risco = None
    if losses:
        lab, delta, detail = losses[0]
        maior_risco = {
            "dimensao": _dim_of(lab),
            "fator": lab,
            "perda_sc_ha": round(abs(delta), 1),
            "perda_rs_ha": round(abs(delta) * scenario.soybean_price_per_sc, 0),
            "detalhe": detail,
        }

    # Oportunidade e investimento vêm do Motor de Priorização.
    actions = prioritized_actions(scenario, top=6)
    maior_oportunidade = actions[0] if actions else None
    com_custo = [a for a in actions if (a["custo_per_ha"] or 0) > 0 and a["roi"]]
    maior_investimento = max(com_custo, key=lambda a: a["roi"]) if com_custo else None

    return {
        "score": score,
        "score_label": _label(score),
        "dimensions": [
            {"key": k, "label": _DIM_LABEL[k], "score": dimensions[k]} for k in
            ["solo", "clima", "sanidade", "nutricao", "mercado", "execucao"]
        ],
        "maior_risco": maior_risco,
        "maior_oportunidade": maior_oportunidade,
        "maior_investimento": maior_investimento,
        "actions": actions,
        "respostas": _quatro_respostas(maior_risco, maior_oportunidade),
        "expected_sc_ha": round(y.expected_sc_ha, 1),
        "profit_per_ha": round(econ.profit_per_ha, 0),
    }


def _dim_of(label: str) -> str:
    for dim, labs in _DIMENSIONS.items():
        if label in labs:
            return dim
    return "execucao"


def _label(score: float) -> str:
    return "saudável" if score >= 80 else "atenção" if score >= 60 else "crítico"


def _quatro_respostas(risco, oportunidade) -> dict:
    """As 4 perguntas que o agricultor faz ao abrir o sistema — respondidas direto."""
    r1 = "Sem gargalo relevante no momento."
    if risco:
        r1 = f"{_DIM_LABEL.get(risco['dimensao'], risco['dimensao'])} ({risco['fator']}) — perda estimada de {risco['perda_sc_ha']:.0f} sc/ha."
    r2 = r3 = r4 = "Nenhuma intervenção avaliada melhora o resultado agora — o plano está bem ajustado."
    if oportunidade:
        prob = oportunidade["probabilidade"] * 100
        r2 = f"{oportunidade['acao']} (prazo: {oportunidade['prazo']})."
        r3 = (
            f"+{oportunidade['impacto_sc_ha']:.1f} sc/ha e "
            f"{'+' if oportunidade['impacto_rs'] >= 0 else ''}R$ {oportunidade['impacto_rs']:,.0f}/ha.".replace(",", ".")
        )
        r4 = f"{oportunidade['porque']} (chance de melhorar o lucro: {prob:.0f}%)."
    return {
        "maior_risco": r1,
        "melhor_decisao": r2,
        "quanto_vale": r3,
        "por_que": r4,
    }
