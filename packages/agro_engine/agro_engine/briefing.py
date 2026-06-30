"""Motor de Resumo da Safra (Briefing) — a resposta única do Gêmeo Digital.

Os outros motores respondem cada um a UMA pergunta (quanto colho, qual risco, qual a
melhor ação, meus dados são confiáveis). O agricultor, porém, precisa de UMA resposta
priorizada: *"plante em tal data, deve colher X ± , lucro Y, seu risco é Z, e a ação
nº 1 agora é K — por isso"*.

Este motor **não calcula nada novo**: ele compõe os motores determinísticos já
existentes (simulate, montecarlo, decisão, janela ZARC, veracidade dos dados) em um
veredito coerente, com um **status de saúde** (verde/amarelo/vermelho) e uma **lista
de ações priorizada por retorno**. É o que alimenta o painel principal do cockpit e,
nas fases de IA, o que o LLM apenas narra — nunca inventa.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .data_sources import accuracy_report
from .decision import recommend_decisions
from .models import Scenario
from .montecarlo import run_montecarlo
from .simulate import simulate

# Limiares do status de saúde da safra (calibrados para a realidade do NO-RS).
_LOSS_OK = 0.20          # P(prejuízo) abaixo disto é confortável
_LOSS_ALERT = 0.40       # acima disto é crítico


@dataclass
class BriefingAction:
    """Uma ação recomendada, já quantificada em sc/ha e R$/ha."""

    rank: int
    key: str
    label: str
    delta_yield_sc_ha: float
    delta_profit_per_ha: float
    action_roi: float | None
    probability_positive: float
    justification: str


@dataclass
class SeasonBriefing:
    """O resumo executivo da safra do talhão."""

    status: str                       # "saudavel" | "atencao" | "critico"
    status_label: str
    municipality: str
    sowing_date: str
    expected_sc_ha: float
    uncertainty_sc_ha: float
    p10_sc_ha: float
    p90_sc_ha: float
    profit_per_ha: float
    roi: float
    breakeven_yield_sc_ha: float
    prob_loss: float
    sowing_position: str
    sowing_penalty_sc_ha: float
    data_confidence: float
    top_data_gap: dict | None
    actions: list[BriefingAction] = field(default_factory=list)
    veredito: str = ""
    alertas: list[str] = field(default_factory=list)


def _status(profit_per_ha: float, prob_loss: float, sowing_penalty: float) -> tuple[str, str]:
    """Semáforo de saúde da safra a partir de lucro, risco e janela."""
    if profit_per_ha <= 0 or prob_loss >= _LOSS_ALERT:
        return "critico", "Atenção crítica"
    if prob_loss > _LOSS_OK or sowing_penalty > 2.0:
        return "atencao", "Requer atenção"
    return "saudavel", "Safra saudável"


_POSITION_TXT = {
    "otimo": "na janela ótima do ZARC",
    "dentro_da_janela": "dentro da janela do ZARC",
    "antes_da_janela": "ANTES da janela do ZARC",
    "depois_da_janela": "DEPOIS da janela do ZARC",
}


def season_briefing(scenario: Scenario, provenance: dict | None = None) -> dict:
    """Compõe o resumo executivo da safra do talhão (a resposta única do gêmeo).

    Reutiliza os motores determinísticos; nenhuma constante de impacto é inventada aqui.
    O Monte Carlo roda com N reduzido (resposta rápida no cockpit); a análise de risco
    completa continua disponível no painel dedicado.
    """
    result = simulate(scenario)
    y = result.yield_result
    econ = result.economics

    mc = run_montecarlo(scenario, n=600, seed=7, profit_target_per_ha=0.0)
    prob_loss = mc["probabilities"]["loss"]
    p10 = mc["yield"]["p10"]
    p90 = mc["yield"]["p90"]

    sowing = result.sowing_window
    position = str(sowing.get("position", ""))
    penalty = float(sowing.get("penalty_sc_ha", 0.0) or 0.0)

    status, status_label = _status(econ.profit_per_ha, prob_loss, penalty)

    # Confiança dos dados: motor único de acurácia (data_sources).
    dq = accuracy_report(scenario, provenance)
    data_confidence = dq["precision_index"]
    top_var = next((v for v in dq["variables"] if v["leverage_sc_ha"] > 0), None)
    top_gap = (
        {"group": top_var["group"], "leverage_sc_ha": top_var["leverage_sc_ha"], "como_obter": top_var["how_to_improve"]}
        if top_var else None
    )

    # Ações: só as que aumentam o lucro, ranqueadas pelo Δlucro (motor de decisão).
    raw = recommend_decisions(scenario, n_prob=250, seed=7, top=None)
    actions: list[BriefingAction] = []
    for i, d in enumerate([r for r in raw if r.delta_profit_per_ha > 0][:3]):
        actions.append(
            BriefingAction(
                rank=i + 1,
                key=d.key,
                label=d.label,
                delta_yield_sc_ha=d.delta_yield_sc_ha,
                delta_profit_per_ha=d.delta_profit_per_ha,
                action_roi=d.action_roi,
                probability_positive=d.probability_positive,
                justification=d.justification,
            )
        )

    alertas = _alertas(econ, prob_loss, position, penalty, data_confidence)
    veredito = _veredito(scenario, y, econ, mc, position, actions, dq, top_gap)

    briefing = SeasonBriefing(
        status=status,
        status_label=status_label,
        municipality=scenario.municipality,
        sowing_date=scenario.sowing_date.isoformat(),
        expected_sc_ha=round(y.expected_sc_ha, 1),
        uncertainty_sc_ha=round(y.uncertainty_sc_ha, 1),
        p10_sc_ha=p10,
        p90_sc_ha=p90,
        profit_per_ha=round(econ.profit_per_ha, 0),
        roi=round(econ.roi, 2),
        breakeven_yield_sc_ha=round(econ.breakeven_yield_sc_ha, 1),
        prob_loss=prob_loss,
        sowing_position=position,
        sowing_penalty_sc_ha=round(penalty, 1),
        data_confidence=data_confidence,
        top_data_gap=top_gap,
        actions=actions,
        veredito=veredito,
        alertas=alertas,
    )
    return _to_dict(briefing)


def _alertas(econ, prob_loss: float, position: str, penalty: float, confidence: float) -> list[str]:
    out: list[str] = []
    if econ.profit_per_ha <= 0:
        out.append("Lucro projetado negativo: revise custos, preço de venda ou o plano de manejo.")
    if prob_loss >= _LOSS_ALERT:
        out.append(f"Risco alto de prejuízo ({prob_loss * 100:.0f}% das safras simuladas dão prejuízo).")
    if position in ("antes_da_janela", "depois_da_janela") and penalty > 0:
        out.append(
            f"Semeadura fora da janela ZARC — penalidade estimada de {penalty:.1f} sc/ha."
        )
    if confidence < 0.5:
        out.append(
            f"Confiança dos dados baixa ({confidence * 100:.0f}%): a estimativa ainda usa muitos defaults regionais."
        )
    return out


def _veredito(scenario, y, econ, mc, position, actions, dq, top_gap) -> str:
    pos_txt = _POSITION_TXT.get(position, "na data informada")
    profit = econ.profit_per_ha
    profit_txt = (
        f"lucro de cerca de R$ {profit:,.0f}/ha (ROI {econ.roi:.1f}x)".replace(",", ".")
        if profit > 0
        else f"PREJUÍZO de cerca de R$ {abs(profit):,.0f}/ha".replace(",", ".")
    )
    msg = (
        f"Em {scenario.municipality}, semeando {pos_txt}, a expectativa é colher "
        f"{y.expected_sc_ha:.0f} sc/ha (entre {mc['yield']['p10']:.0f} e {mc['yield']['p90']:.0f} "
        f"conforme o clima) e {profit_txt}. "
        f"O risco de prejuízo é de {mc['probabilities']['loss'] * 100:.0f}%."
    )
    if actions:
        a = actions[0]
        prob = a.probability_positive * 100
        msg += (
            f" A ação de maior retorno agora é '{a.label.lower()}': "
            f"{_sc(a.delta_yield_sc_ha)} sc/ha e {_rs(a.delta_profit_per_ha)}/ha "
            f"({prob:.0f}% de chance de melhorar o lucro)."
        )
    else:
        msg += " Nenhuma intervenção avaliada melhora o resultado — o plano atual já está bem ajustado."
    if top_gap:
        msg += (
            f" Para deixar a estimativa mais verídica, o dado a medir primeiro é "
            f"'{top_gap['group']}' (pode mudar o resultado em ±{top_gap['leverage_sc_ha']:.0f} sc/ha)."
        )
    return msg


def _sc(v: float) -> str:
    return f"{'+' if v >= 0 else ''}{v:.1f}"


def _rs(v: float) -> str:
    s = f"R$ {abs(v):,.0f}".replace(",", ".")
    return f"{'+' if v >= 0 else '−'}{s}"


def _to_dict(b: SeasonBriefing) -> dict:
    d = b.__dict__.copy()
    d["actions"] = [a.__dict__ for a in b.actions]
    return d
