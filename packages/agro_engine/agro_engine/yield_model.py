"""Motor de produtividade — Índice de Potencial Produtivo Dinâmico (IPPD).

Em vez de uma regressão "caixa-preta", parte do **potencial genético** da cultivar
e aplica fatores sequenciais e transparentes (solo, janela, água, nutrição,
população, sanidade, compactação). Cada fator é um multiplicador; a cascata é
decomposta em contribuições aditivas (± sc/ha) que somam exatamente ao resultado —
é o que a UI mostra como gráfico waterfall.

Filosofia: explicar *por que* a produtividade é aquela, com intervalo de confiança,
em vez de prometer um número exato.
"""

from __future__ import annotations

from . import reference as ref
from .models import (
    FactorContribution,
    Scenario,
    SoilProfile,
    YieldResult,
)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _soil_factor(soil: SoilProfile) -> tuple[float, float, str]:
    """pH, saturação por bases, CTC e MO → multiplicador estrutural do solo."""
    score = 1.0
    notes = []
    lo, hi = ref.PH_OPTIMAL
    if soil.ph < lo:
        score *= 1.0 - _clamp((lo - soil.ph) * 0.04, 0, 0.12)
        notes.append(f"pH {soil.ph} abaixo do ideal")
    elif soil.ph > hi + 0.5:
        score *= 0.98
    if soil.base_saturation_pct < ref.V_SUFFICIENT_PCT:
        deficit = ref.V_SUFFICIENT_PCT - soil.base_saturation_pct
        score *= 1.0 - _clamp(deficit * 0.003, 0, 0.10)
        notes.append(f"V% {soil.base_saturation_pct}")
    if soil.organic_matter_pct >= 4.0:
        score *= 1.02  # solo "vivo" tampona estresses
    return _clamp(score, 0.7, 1.05), 0.80, "; ".join(notes) or "solo equilibrado"


def _nutrition_factor(soil: SoilProfile) -> tuple[float, float, str]:
    """Fósforo e potássio disponíveis → multiplicador nutricional."""
    score = 1.0
    notes = []
    if soil.phosphorus_ppm < ref.P_SUFFICIENT_PPM:
        deficit = (ref.P_SUFFICIENT_PPM - soil.phosphorus_ppm) / ref.P_SUFFICIENT_PPM
        score *= 1.0 - _clamp(deficit * 0.10, 0, 0.10)
        notes.append(f"P baixo ({soil.phosphorus_ppm} ppm)")
    if soil.potassium_ppm < ref.K_SUFFICIENT_PPM:
        deficit = (ref.K_SUFFICIENT_PPM - soil.potassium_ppm) / ref.K_SUFFICIENT_PPM
        score *= 1.0 - _clamp(deficit * 0.08, 0, 0.08)
        notes.append(f"K baixo ({soil.potassium_ppm} ppm)")
    return _clamp(score, 0.78, 1.0), 0.82, "; ".join(notes) or "nutrição suficiente"


def _population_factor(scenario: Scenario) -> tuple[float, float, str]:
    lo, hi = ref.POPULATION_OPTIMAL_K
    pop = scenario.population_k_per_ha
    if lo <= pop <= hi:
        return 1.0, 0.85, f"população ótima ({pop:.0f} mil/ha)"
    if pop < lo:
        pen = _clamp((lo - pop) / lo * 0.20, 0, 0.12)
        return 1.0 - pen, 0.80, f"população baixa ({pop:.0f} mil/ha)"
    pen = _clamp((pop - hi) / hi * 0.10, 0, 0.06)
    return 1.0 - pen, 0.80, f"população alta ({pop:.0f} mil/ha)"


def _compaction_factor(soil: SoilProfile) -> tuple[float, float, str]:
    table = {"nenhuma": 1.0, "leve": 0.98, "moderada": 0.93, "severa": 0.85}
    m = table.get(soil.compaction, 0.98)
    return m, 0.7, f"compactação {soil.compaction}"


def _water_factor(overall_stress: float, critical_stage: str | None) -> tuple[float, float, str]:
    """Estresse hídrico ponderado (0..1) → multiplicador. Estresse total ~ -45%."""
    m = 1.0 - _clamp(overall_stress, 0, 1) * 0.45
    detail = "sem déficit relevante"
    if overall_stress > 0.05 and critical_stage:
        detail = f"déficit hídrico, crítico em {critical_stage}"
    return _clamp(m, 0.5, 1.0), 0.75, detail


def _sanity_factor(scenario: Scenario) -> tuple[float, float, str]:
    """Pressão de doença (ferrugem) vs. tolerância da cultivar e qualidade dos fungicidas."""
    base_disease_pressure = 0.18  # NO do RS: pressão alta de ferrugem
    tolerance = scenario.cultivar.disease_tolerance
    fungicidas = [o for o in scenario.operations if o.kind.lower() == "fungicida"]
    # cada aplicação de fungicida de boa qualidade reduz a pressão remanescente
    remaining = base_disease_pressure * (1.0 - 0.5 * tolerance)
    for op in fungicidas:
        remaining *= (1.0 - 0.55 * _clamp(op.quality, 0, 1))
    m = 1.0 - _clamp(remaining, 0, 0.25)
    detail = f"{len(fungicidas)} aplicação(ões) de fungicida"
    return _clamp(m, 0.75, 1.0), 0.78, detail


def decompose(scenario: Scenario, water: dict, sowing: dict) -> YieldResult:
    """Constrói a cascata IPPD e devolve produtividade esperada ± incerteza."""
    potential = scenario.cultivar.base_potential_sc_ha
    running = potential
    contributions: list[FactorContribution] = []
    confidences: list[float] = []

    def apply(label: str, factor: tuple[float, float, str]) -> None:
        nonlocal running
        m, conf, detail = factor
        before = running
        running = before * m
        contributions.append(
            FactorContribution(
                label=label,
                delta_sc_ha=round(running - before, 2),
                confidence=conf,
                detail=detail,
            )
        )
        confidences.append(conf)

    apply("Solo", _soil_factor(scenario.soil))
    apply("Nutrição", _nutrition_factor(scenario.soil))
    apply("Compactação", _compaction_factor(scenario.soil))

    # Janela de semeadura: penalidade vem em sc/ha → vira multiplicador.
    penalty = sowing.get("penalty_sc_ha", 0.0)
    sow_m = 1.0 - (penalty / running if running else 0.0)
    apply(
        "Janela de semeadura",
        (_clamp(sow_m, 0.6, 1.0), 0.8, sowing.get("position", "")),
    )

    apply("Água", _water_factor(water.get("overall_stress", 0.0), water.get("critical_stage")))
    apply("Sanidade", _sanity_factor(scenario))

    expected = round(running, 1)
    # Incerteza: combina a confiança média com o nº de fatores limitantes.
    mean_conf = sum(confidences) / len(confidences) if confidences else 0.6
    spread = (1.0 - mean_conf) * expected * 0.5 + 2.0
    return YieldResult(
        base_potential_sc_ha=potential,
        contributions=contributions,
        expected_sc_ha=expected,
        uncertainty_sc_ha=round(spread, 1),
        confidence=round(mean_conf, 2),
    )
