"""Testes do motor de produtividade (decomposição IPPD)."""

from __future__ import annotations

from datetime import date

from agro_engine import decompose_yield, stage_dates, water_stress
from agro_engine.sowing_window import evaluate

from conftest import make_weather


def _run(scenario):
    stages = stage_dates(scenario.cultivar, scenario.sowing_date, scenario.weather)
    water = water_stress(scenario, stages, scenario.weather)
    sowing = evaluate(scenario.municipality, scenario.sowing_date)
    return decompose_yield(scenario, water, sowing)


def test_cascade_sums_to_expected(base_scenario):
    """A soma das contribuições deve bater com (potencial → esperado)."""
    result = _run(base_scenario)
    total = result.base_potential_sc_ha + sum(c.delta_sc_ha for c in result.contributions)
    assert abs(total - result.expected_sc_ha) < 0.5


def test_expected_below_potential_in_real_conditions(base_scenario):
    result = _run(base_scenario)
    assert result.expected_sc_ha < base_scenario.cultivar.base_potential_sc_ha
    assert result.expected_sc_ha > 30  # sanidade do número


def test_late_sowing_reduces_yield(base_scenario):
    """Plantar bem fora da janela ZARC deve reduzir a produtividade."""
    on_time = _run(base_scenario).expected_sc_ha
    base_scenario.sowing_date = date(2026, 1, 15)  # muito depois da janela
    base_scenario.weather = make_weather(base_scenario.sowing_date, 160)
    late = _run(base_scenario).expected_sc_ha
    assert late < on_time


def test_low_phosphorus_creates_nutrition_penalty(base_scenario):
    base_scenario.soil.phosphorus_ppm = 4.0
    result = _run(base_scenario)
    nutrition = next(c for c in result.contributions if c.label == "Nutrição")
    assert nutrition.delta_sc_ha < 0


def test_more_fungicide_improves_sanity(base_scenario):
    from agro_engine.models import Operation

    base_scenario.operations = []
    no_fung = _run(base_scenario)
    sanity_no = next(c for c in no_fung.contributions if c.label == "Sanidade").delta_sc_ha
    base_scenario.operations = [
        Operation(kind="fungicida", op_date=date(2026, 1, 10), cost_per_ha=180.0, quality=0.95),
        Operation(kind="fungicida", op_date=date(2026, 1, 24), cost_per_ha=180.0, quality=0.95),
    ]
    with_fung = _run(base_scenario)
    sanity_yes = next(c for c in with_fung.contributions if c.label == "Sanidade").delta_sc_ha
    assert sanity_yes > sanity_no  # menos perda por doença


def test_confidence_within_bounds(base_scenario):
    result = _run(base_scenario)
    assert 0.0 <= result.confidence <= 1.0
    assert result.uncertainty_sc_ha > 0
