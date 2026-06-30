"""Primitivas de veracidade dos dados — base do motor de acurácia.

Fornece os blocos que o motor de acurácia (``data_sources.py``) usa para medir a confiança
dos dados de um talhão: o **peso de cada grupo** na confiança, o **score de cada nível de
fonte** e o cálculo de **alavancagem por perturbação** (quanto a produtividade oscila se um
dado incerto fosse o real). A montagem do relatório de acurácia (tiers, "como melhorar",
índice de precisão) fica em ``data_sources.accuracy_report`` — fonte única.

Tudo é calculado pelo próprio modelo (perturbando cada entrada incerta e medindo o quanto
o resultado oscila), não por regras fixas — coerente com o que a plataforma de fato simula.
"""

from __future__ import annotations

from dataclasses import replace

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


def _yield_of(scn: Scenario) -> float:
    return _profit_and_yield(scn)[1]


def _swing(scenario: Scenario, variants: list[Scenario]) -> float:
    """Meia-amplitude da produtividade entre as variantes (a alavancagem do dado incerto)."""
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
