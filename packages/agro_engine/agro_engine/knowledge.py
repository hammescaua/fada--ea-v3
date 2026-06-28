"""Knowledge Engine (Nível 2) — o talhão aprende a cada safra.

Princípio do briefing: *não existe uma IA, existem milhares — uma por talhão*. A cada
safra registramos **previsto vs. realizado**; o erro vira uma **correção** que
personaliza as próximas previsões daquele talhão específico.

Este v0 usa **estatística robusta com encolhimento (shrinkage)** em vez de um modelo
de ML pesado — porque com 1–3 safras um CatBoost superajustaria. Conforme as safras se
acumulam, a correção converge para o viés real do talhão e a incerteza diminui. Quando
houver dezenas de talhões × safras, esta mesma interface alimenta o Nível 2 com ML
(CatBoost/LightGBM) — recebendo **atributos** (`season_features`), nunca dados crus.

A correção é **aditiva com encolhimento bayesiano**:
    bias_efetivo = média(real − previsto) · n / (n + k)      (k = força do prior)
    confiança    = n / (n + k)
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass

PRIOR_STRENGTH_K = 3.0  # nº de "safras virtuais" do prior (correção 0). Encolhe poucos dados.


@dataclass
class SeasonRecord:
    """Uma safra encerrada: o que o motor previu e o que o talhão realmente colheu."""

    crop_year: str
    predicted_sc_ha: float
    actual_sc_ha: float

    @property
    def residual(self) -> float:
        return self.actual_sc_ha - self.predicted_sc_ha


@dataclass
class Calibration:
    """Modelo de correção aprendido para um talhão."""

    n_seasons: int
    bias_sc_ha: float        # correção aditiva a aplicar nas próximas previsões
    confidence: float        # 0..1 — cresce com o nº de safras
    mae_before: float        # erro médio absoluto histórico (sem correção)
    mae_after: float         # erro médio absoluto histórico (com correção, in-sample)
    raw_bias_sc_ha: float    # viés bruto, sem encolhimento (diagnóstico)


def calibrate(records: list[SeasonRecord]) -> Calibration:
    """Aprende a correção do talhão a partir do histórico previsto-vs-real."""
    n = len(records)
    if n == 0:
        return Calibration(0, 0.0, 0.0, 0.0, 0.0, 0.0)

    residuals = [r.residual for r in records]
    raw_bias = statistics.fmean(residuals)
    confidence = n / (n + PRIOR_STRENGTH_K)
    bias = raw_bias * confidence  # encolhimento: poucos dados → correção tímida

    mae_before = statistics.fmean(abs(r) for r in residuals)
    mae_after = statistics.fmean(abs(r - bias) for r in residuals)

    return Calibration(
        n_seasons=n,
        bias_sc_ha=round(bias, 2),
        confidence=round(confidence, 3),
        mae_before=round(mae_before, 2),
        mae_after=round(mae_after, 2),
        raw_bias_sc_ha=round(raw_bias, 2),
    )


def apply_correction(
    expected_sc_ha: float,
    base_uncertainty_sc_ha: float,
    calibration: Calibration,
) -> tuple[float, float]:
    """Aplica a correção aprendida: ajusta a produtividade e ENCURTA a incerteza.

    Retorna ``(produtividade_corrigida, incerteza_corrigida)``. Quanto mais o talhão
    aprendeu (maior confiança), mais a incerteza diminui.
    """
    corrected = expected_sc_ha + calibration.bias_sc_ha
    # a incerteza encolhe até 50% conforme a confiança do talhão sobe
    shrink = 1.0 - 0.5 * calibration.confidence
    return round(corrected, 1), round(base_uncertainty_sc_ha * shrink, 1)


def season_features(scenario, simulation) -> dict:
    """Feature engineering: extrai ATRIBUTOS de uma safra (nunca dados crus).

    É exatamente o que o briefing pede: a IA não recebe "100 dias de chuva", e sim
    "déficit hídrico em R3", "desvio da janela", etc. Este vetor é persistido por safra
    e, no futuro, alimenta o modelo de ML do Nível 2.
    """
    water = simulation.water if hasattr(simulation, "water") else simulation["water"]
    sowing = simulation.sowing_window if hasattr(simulation, "sowing_window") else simulation["sowing_window"]
    by_stage = water.get("by_stage", {})
    n_fung = sum(1 for o in scenario.operations if o.kind.lower() == "fungicida")
    return {
        "sowing_deviation_days": sowing.get("deviation_days", 0),
        "water_overall_stress": water.get("overall_stress", 0.0),
        "water_stress_R3": by_stage.get("R3", 0.0),
        "water_stress_R4": by_stage.get("R4", 0.0),
        "water_stress_R5": by_stage.get("R5", 0.0),
        "critical_stage": water.get("critical_stage"),
        "soil_ph": scenario.soil.ph,
        "soil_p_ppm": scenario.soil.phosphorus_ppm,
        "soil_k_ppm": scenario.soil.potassium_ppm,
        "soil_v_pct": scenario.soil.base_saturation_pct,
        "population_k_per_ha": scenario.population_k_per_ha,
        "n_fungicidas": n_fung,
        "maturity_group": scenario.cultivar.maturity_group,
        "base_potential_sc_ha": scenario.cultivar.base_potential_sc_ha,
    }
