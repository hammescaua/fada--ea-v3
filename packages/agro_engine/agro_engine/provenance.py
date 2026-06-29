"""Motor de Veracidade dos Dados — honestidade e coerência da plataforma.

Uma estimativa só é tão boa quanto os dados que a alimentam. Este motor torna isso
EXPLÍCITO para o agricultor: separa o que é dado **real** (informado/observado) do que é
**suposto** (default regional), calcula um **índice de confiança dos dados** do talhão e,
o mais útil, ranqueia as **lacunas por valor-da-informação** — quanto a estimativa poderia
mudar se aquele dado fosse o real. É a metodologia de captação: diz ao produtor *o que
medir primeiro* para a recomendação ficar mais verídica.

Tudo é calculado pelo próprio modelo (perturbando cada entrada incerta e medindo o
quanto o resultado oscila), não por regras fixas — então a orientação é coerente com o
que a plataforma de fato simula.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from .decision import _profit_and_yield
from .models import Scenario
from .montecarlo import run_montecarlo

# Peso de cada grupo na confiança (≈ influência na produtividade/decisão).
GROUP_WEIGHT = {
    "clima": 0.30,
    "solo": 0.25,
    "data_semeadura": 0.10,
    "cultivar": 0.10,
    "manejo": 0.10,
    "populacao": 0.07,
    "preco": 0.08,
}
# Quão "real" é cada nível de fonte. Para o clima há uma escala própria: 'safra_realizada'
# (observado de toda a safra) > 'safra_corrente' (observado+previsão+climatologia) >
# 'climatologia_real' (média histórica do ponto, não a safra corrente) > 'estimado'.
SOURCE_SCORE = {
    "real": 1.0,
    "safra_realizada": 0.95,
    "safra_corrente": 0.85,
    "climatologia_real": 0.7,
    "parcial": 0.6,
    "estimado": 0.2,
    "default": 0.2,
}

_HOW_TO = {
    "clima": "Ligar o clima histórico real da localização (NASA POWER / Open-Meteo / estação INMET).",
    "solo": "Fazer/importar a análise de solo do talhão (laboratório).",
    "cultivar": "Informar a cultivar realmente usada (grupo de maturação e tolerância).",
    "manejo": "Registrar o programa de manejo (datas, produtos, doses).",
    "populacao": "Informar a população/estande real (plantas/ha).",
    "preco": "Informar o preço real de venda da soja e dos insumos.",
    "data_semeadura": "Confirmar a data de semeadura planejada/realizada.",
}


@dataclass
class DataGap:
    group: str
    current_source: str
    leverage_sc_ha: float   # quanto a produtividade pode oscilar por causa desta incerteza
    como_obter: str


def _yield_of(scn: Scenario) -> float:
    return _profit_and_yield(scn)[1]


def _swing(scenario: Scenario, variants: list[Scenario]) -> float:
    ys = [_yield_of(v) for v in variants]
    return round((max(ys) - min(ys)) / 2.0, 1)


def _soil_leverage(scenario: Scenario) -> float:
    s = scenario.soil
    lo = replace(scenario, soil=replace(s, ph=5.2, base_saturation_pct=46, phosphorus_ppm=5, potassium_ppm=80))
    hi = replace(scenario, soil=replace(s, ph=6.2, base_saturation_pct=70, phosphorus_ppm=18, potassium_ppm=160))
    return _swing(scenario, [lo, hi])


def _cultivar_leverage(scenario: Scenario) -> float:
    c = scenario.cultivar
    lo = replace(scenario, cultivar=replace(c, base_potential_sc_ha=c.base_potential_sc_ha - 8, disease_tolerance=0.3))
    hi = replace(scenario, cultivar=replace(c, base_potential_sc_ha=c.base_potential_sc_ha + 8, disease_tolerance=0.7))
    return _swing(scenario, [lo, hi])


def _population_leverage(scenario: Scenario) -> float:
    lo = replace(scenario, population_k_per_ha=200.0)
    hi = replace(scenario, population_k_per_ha=320.0)
    return _swing(scenario, [lo, hi])


def _climate_leverage(scenario: Scenario) -> float:
    """A incerteza climática = metade da faixa p10–p90 do Monte Carlo (anos secos↔úmidos)."""
    mc = run_montecarlo(scenario, n=400, seed=3)
    return round((mc["yield"]["p90"] - mc["yield"]["p10"]) / 2.0, 1)


def assess(scenario: Scenario, provenance: dict | None = None) -> dict:
    """Avalia a veracidade dos dados do talhão e ranqueia as lacunas por impacto.

    ``provenance`` informa a fonte de cada grupo: 'real' | 'parcial' | 'estimado'.
    Quando ausente, assume 'estimado' (postura conservadora/honesta).
    """
    prov = {g: "estimado" for g in GROUP_WEIGHT}
    prov.update(provenance or {})

    # índice de confiança dos dados (0..1)
    confidence = sum(GROUP_WEIGHT[g] * SOURCE_SCORE.get(prov.get(g, "estimado"), 0.2) for g in GROUP_WEIGHT)

    # lacunas: grupos não-reais, com alavancagem calculada pelo modelo
    leverage_fn = {
        "clima": _climate_leverage,
        "solo": _soil_leverage,
        "cultivar": _cultivar_leverage,
        "populacao": _population_leverage,
    }
    gaps: list[DataGap] = []
    for group, fn in leverage_fn.items():
        if prov.get(group) == "real":
            continue
        gaps.append(DataGap(group, prov.get(group, "estimado"), fn(scenario), _HOW_TO[group]))
    # grupos sem cálculo de alavancagem específico (manejo, preço, data) entram com peso menor
    for group in ("manejo", "preco", "data_semeadura"):
        if prov.get(group) != "real":
            gaps.append(DataGap(group, prov.get(group, "estimado"), 0.0, _HOW_TO[group]))

    gaps.sort(key=lambda g: g.leverage_sc_ha, reverse=True)

    return {
        "data_confidence": round(confidence, 2),
        "sources": prov,
        "gaps": [g.__dict__ for g in gaps],
        "resumo": _resumo(confidence, gaps),
    }


def _resumo(confidence: float, gaps: list[DataGap]) -> str:
    nivel = "alta" if confidence >= 0.75 else "média" if confidence >= 0.5 else "baixa"
    top = next((g for g in gaps if g.leverage_sc_ha > 0), None)
    msg = f"Confiança dos dados deste talhão: {nivel} ({confidence * 100:.0f}%)."
    if top:
        msg += (
            f" O dado que mais aumentaria a precisão é '{top.group}' "
            f"(pode mudar a estimativa em ±{top.leverage_sc_ha:.0f} sc/ha): {top.como_obter}"
        )
    return msg
