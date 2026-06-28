"""Orquestrador — roda todos os motores e devolve o resultado do Laboratório Virtual.

Pipeline:
    fenologia → balanço hídrico → janela de semeadura (ZARC) → IPPD → econômico
"""

from __future__ import annotations

from . import economics, phenology, sowing_window, water_balance, yield_model
from .models import Scenario, SimulationResult


def simulate(scenario: Scenario) -> SimulationResult:
    """Simula um cenário completo de safra para um talhão."""
    stages = phenology.stage_dates(
        scenario.cultivar, scenario.sowing_date, scenario.weather
    )
    water = water_balance.water_stress(scenario, stages, scenario.weather)
    sowing = sowing_window.evaluate(scenario.municipality, scenario.sowing_date)
    yield_result = yield_model.decompose(scenario, water, sowing)
    econ = economics.compute(scenario, yield_result.expected_sc_ha)

    return SimulationResult(
        yield_result=yield_result,
        economics=econ,
        phenology={k: v.isoformat() for k, v in stages.items()},
        water=water,
        sowing_window=sowing,
    )
