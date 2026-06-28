"""Teste de integração do orquestrador (pipeline completo do Laboratório Virtual)."""

from __future__ import annotations

from datetime import date

from agro_engine import simulate

from conftest import make_weather


def test_simulate_returns_full_result(base_scenario):
    result = simulate(base_scenario)
    assert result.yield_result.expected_sc_ha > 0
    assert "VE" in result.phenology and "R8" in result.phenology
    assert "overall_stress" in result.water
    assert "window_start" in result.sowing_window
    assert result.economics.total_cost_per_ha > 0


def test_scenario_comparison_planting_dates(base_scenario):
    """Comparar duas datas de plantio (núcleo do Laboratório Virtual)."""
    base_scenario.sowing_date = date(2025, 11, 5)
    base_scenario.weather = make_weather(date(2025, 11, 5), 170)
    a = simulate(base_scenario)

    base_scenario.sowing_date = date(2025, 12, 28)
    base_scenario.weather = make_weather(date(2025, 12, 28), 170)
    b = simulate(base_scenario)

    # Plantio na janela ótima deve render mais que muito tardio.
    assert a.yield_result.expected_sc_ha >= b.yield_result.expected_sc_ha
    assert a.economics.profit_per_ha >= b.economics.profit_per_ha
