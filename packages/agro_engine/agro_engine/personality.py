"""Genética do Talhão — a personalidade APRENDIDA de cada lavoura.

Não são atributos cadastrados; são traços que emergem das safras e das evidências:
*"este talhão responde muito ao fósforo", "tem alto risco de ferrugem", "é sensível ao
atraso no plantio", "tem produtividade estável"*. Cada traço carrega uma **confiança** e a
**base** que o sustenta, e o talhão tem um **% de conhecimento** que cresce com o histórico.

Honestidade: com poucas safras, os traços vêm marcados como "aprendendo" e com confiança
baixa — a ferramenta nunca finge saber mais do que a evidência permite.
"""

from __future__ import annotations

import statistics
from collections import Counter
from dataclasses import dataclass

from .evidence import Observation
from .interactions import detect_interactions
from . import reference as ref


@dataclass
class FieldSeason:
    """Uma safra encerrada do talhão, com previsto, realizado e os atributos extraídos."""

    crop_year: str
    predicted_sc_ha: float
    actual_sc_ha: float
    features: dict


@dataclass
class Trait:
    key: str
    label: str
    level: str            # categoria legível (ex.: "alta", "responsivo", "sensível")
    value: float          # 0..1 normalizado (para a UI desenhar barras)
    confidence: float     # 0..1 — quanto a evidência sustenta o traço
    basis: str            # de onde o traço foi aprendido
    learning: bool        # True quando ainda há pouca evidência


def _knowledge_pct(n_seasons: int, n_obs: int) -> float:
    return round(min(0.95, 0.18 * n_seasons + 0.02 * n_obs), 2)


def _stability(actuals: list[float]) -> Trait | None:
    if len(actuals) < 2:
        return None
    mean = statistics.fmean(actuals)
    cv = (statistics.pstdev(actuals) / mean) if mean else 0.0
    stable = max(0.0, min(1.0, 1.0 - cv / 0.25))  # cv 0 -> 1.0 ; cv>=0.25 -> 0
    level = "alta" if stable >= 0.7 else "média" if stable >= 0.4 else "baixa"
    return Trait(
        "estabilidade_produtiva", "Estabilidade produtiva", level, round(stable, 2),
        confidence=round(min(0.9, 0.3 + 0.15 * len(actuals)), 2),
        basis=f"{len(actuals)} safras: variação de {cv * 100:.0f}% na produtividade colhida",
        learning=len(actuals) < 3,
    )


def _bias_vs_model(seasons: list[FieldSeason]) -> Trait | None:
    if not seasons:
        return None
    res = [s.actual_sc_ha - s.predicted_sc_ha for s in seasons]
    bias = statistics.fmean(res)
    level = "colhe acima do previsto" if bias > 1 else "colhe abaixo do previsto" if bias < -1 else "alinhado ao modelo"
    return Trait(
        "vies_vs_modelo", "Tendência vs. modelo", level, round(max(0.0, min(1.0, 0.5 + bias / 20)), 2),
        confidence=round(min(0.9, 0.3 + 0.15 * len(seasons)), 2),
        basis=f"viés médio de {bias:+.1f} sc/ha em {len(seasons)} safras (previsto vs. colhido)",
        learning=len(seasons) < 2,
    )


def _phosphorus_response(seasons: list[FieldSeason]) -> Trait | None:
    ps = [s.features.get("soil_p_ppm") for s in seasons if s.features.get("soil_p_ppm") is not None]
    if not ps:
        return None
    mean_p = statistics.fmean(ps)
    # P consistentemente baixo => alto POTENCIAL de resposta à adubação fosfatada.
    deficit = max(0.0, (ref.P_SUFFICIENT_PPM - mean_p) / ref.P_SUFFICIENT_PPM)
    level = "muito responsivo" if deficit > 0.4 else "responsivo" if deficit > 0.15 else "baixa resposta"
    return Trait(
        "resposta_fosforo", "Resposta ao fósforo", level, round(min(1.0, deficit + 0.2), 2),
        confidence=round(min(0.8, 0.3 + 0.1 * len(ps)), 2),
        basis=f"P médio de {mean_p:.0f} ppm (crítico {ref.P_SUFFICIENT_PPM:.0f}) ao longo das safras",
        learning=len(ps) < 2,
    )


def _ferrugem_risk(seasons: list[FieldSeason], observations: list[Observation]) -> Trait | None:
    sev_map = {"baixa": 0.25, "media": 0.55, "média": 0.55, "alta": 0.85, "severa": 1.0}
    sev = [sev_map.get(str(o.value.get("severidade", "")).lower()) for o in observations if o.kind == "ferrugem"]
    sev = [x for x in sev if x is not None]
    if sev:
        risk = statistics.fmean(sev)
        basis = f"{len(sev)} observação(ões) de ferrugem no talhão"
        conf = round(min(0.9, 0.5 + 0.1 * len(sev)), 2)
    else:
        tols = [s.features.get("maturity_group") and s.features.get("base_potential_sc_ha") for s in seasons]
        # sem observação direta, usa a região (NO-RS = pressão alta) como prior
        risk = ref.DISEASE_PRESSURE / 0.18 * 0.7  # ~0.7 (prior regional alto)
        basis = "prior regional do NO-RS (pressão de ferrugem alta) — registre observações para refinar"
        conf = 0.4
    level = "alto" if risk >= 0.66 else "médio" if risk >= 0.33 else "baixo"
    return Trait("risco_ferrugem", "Risco de ferrugem", level, round(risk, 2), conf, basis, learning=not sev)


def _window_sensitivity(seasons: list[FieldSeason]) -> Trait | None:
    pts = [
        (s.features.get("sowing_deviation_days", 0), s.actual_sc_ha - s.predicted_sc_ha)
        for s in seasons
        if s.features.get("sowing_deviation_days") is not None
    ]
    if len(pts) < 3:
        # ainda aprendendo: sem pontos suficientes para correlação confiável
        return Trait(
            "sensibilidade_janela", "Sensibilidade ao atraso no plantio", "aprendendo", 0.5,
            confidence=0.3, basis="poucas safras para medir a relação atraso × produtividade", learning=True,
        )
    devs = [d for d, _ in pts]
    res = [r for _, r in pts]
    # correlação simples (sinal): mais atraso associado a pior resultado => sensível
    cov = sum((d - statistics.fmean(devs)) * (r - statistics.fmean(res)) for d, r in pts)
    sensitive = cov < 0
    level = "sensível" if sensitive else "tolerante"
    return Trait(
        "sensibilidade_janela", "Sensibilidade ao atraso no plantio", level,
        0.75 if sensitive else 0.3, confidence=round(min(0.85, 0.4 + 0.1 * len(pts)), 2),
        basis=f"{len(pts)} safras: atraso de plantio {'reduz' if sensitive else 'pouco afeta'} o resultado",
        learning=False,
    )


def _water_sensitivity(seasons: list[FieldSeason]) -> Trait | None:
    ws = [s.features.get("water_overall_stress") for s in seasons if s.features.get("water_overall_stress") is not None]
    if not ws:
        return None
    mean_ws = statistics.fmean(ws)
    level = "sensível à seca" if mean_ws > 0.3 else "boa resiliência hídrica"
    return Trait(
        "sensibilidade_agua", "Resiliência hídrica", level, round(1.0 - mean_ws, 2),
        confidence=round(min(0.8, 0.3 + 0.12 * len(ws)), 2),
        basis=f"estresse hídrico médio de {mean_ws * 100:.0f}% nas safras observadas",
        learning=len(ws) < 2,
    )


# Recorrência de interações negativas vira um traço aprendido + viés de recomendação.
_RECURRENCE_TRAITS = {
    "lavagem_pos_aplicacao": (
        "Propensão a lavagem de aplicação",
        "Aplicações deste talhão são frequentemente lavadas por chuva — priorizar produtos com boa "
        "resistência à chuva (rainfastness) e janelas de tempo seco; considerar repasse padrão.",
    ),
    "ferrugem_sem_protecao": (
        "Histórico de ferrugem sem proteção",
        "Ferrugem recorrente sem cobertura adequada — antecipar e reforçar o programa de fungicida.",
    ),
    "seca_pos_semeadura": (
        "Risco de seca na implantação",
        "Período seco recorrente após a semeadura — ajustar a época para casar com umidade e conferir estande.",
    ),
}


def _interaction_traits(observations: list[Observation]) -> list[Trait]:
    """Traços aprendidos da RECORRÊNCIA de interações negativas (a memória vira regra)."""
    items = detect_interactions(observations)
    counts = Counter(i.rule for i in items if not i.positive)
    out: list[Trait] = []
    for rule, n in counts.items():
        if rule not in _RECURRENCE_TRAITS:
            continue
        label, recomendacao = _RECURRENCE_TRAITS[rule]
        out.append(
            Trait(
                key=f"recorrencia_{rule}",
                label=label,
                level="recorrente" if n >= 2 else "observado 1x",
                value=round(min(1.0, 0.4 + 0.2 * n), 2),
                confidence=round(min(0.85, 0.4 + 0.15 * n), 2),
                basis=f"{n} ocorrência(s) na história do talhão · {recomendacao}",
                learning=n < 2,
            )
        )
    return out


def personality(seasons: list[FieldSeason], observations: list[Observation] | None = None) -> dict:
    """Deriva a personalidade aprendida do talhão a partir das safras e evidências."""
    observations = observations or []
    builders = [
        _stability(([s.actual_sc_ha for s in seasons])),
        _bias_vs_model(seasons),
        _phosphorus_response(seasons),
        _ferrugem_risk(seasons, observations),
        _window_sensitivity(seasons),
        _water_sensitivity(seasons),
    ]
    traits = [t for t in builders if t is not None]
    traits.extend(_interaction_traits(observations))
    knowledge = _knowledge_pct(len(seasons), len(observations))
    return {
        "knowledge_pct": knowledge,
        "n_seasons": len(seasons),
        "n_observations": len(observations),
        "traits": [t.__dict__ for t in traits],
        "resumo": _resumo(knowledge, traits),
    }


def _resumo(knowledge: float, traits: list[Trait]) -> str:
    if not traits:
        return "Talhão ainda sem histórico — registre safras e observações para o gêmeo aprender a personalidade da lavoura."
    firmes = [t for t in traits if not t.learning and t.confidence >= 0.5]
    destaque = firmes[:2] or traits[:1]
    desc = "; ".join(f"{t.label.lower()}: {t.level}" for t in destaque)
    return f"Conhecimento do talhão em {knowledge * 100:.0f}%. Traços mais firmes — {desc}."
