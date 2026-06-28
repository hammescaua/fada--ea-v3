"""Testes do motor hídrico (FAO-56 simplificado)."""

from __future__ import annotations

from datetime import date

from agro_engine import stage_dates, water_stress

from conftest import make_weather


def test_drought_increases_stress(base_scenario):
    stages = stage_dates(base_scenario.cultivar, base_scenario.sowing_date, base_scenario.weather)

    wet = make_weather(base_scenario.sowing_date, 160, rain_mm=7.0)
    dry = make_weather(base_scenario.sowing_date, 160, rain_mm=0.0, tmax=34.0)

    base_scenario.weather = wet
    stress_wet = water_stress(base_scenario, stages, wet)["overall_stress"]
    base_scenario.weather = dry
    stress_dry = water_stress(base_scenario, stages, dry)["overall_stress"]

    assert stress_dry > stress_wet
    assert 0.0 <= stress_wet <= 1.0
    assert 0.0 <= stress_dry <= 1.0


def test_clay_soil_holds_more_water_than_sandy(base_scenario):
    from agro_engine.models import SoilTexture

    stages = stage_dates(base_scenario.cultivar, base_scenario.sowing_date, base_scenario.weather)
    dry = make_weather(base_scenario.sowing_date, 160, rain_mm=1.0, tmax=33.0)
    base_scenario.weather = dry

    base_scenario.soil.texture = SoilTexture.ARGILOSO
    stress_clay = water_stress(base_scenario, stages, dry)["overall_stress"]
    base_scenario.soil.texture = SoilTexture.ARENOSO
    stress_sand = water_stress(base_scenario, stages, dry)["overall_stress"]

    assert stress_sand >= stress_clay


def test_reports_critical_stage(base_scenario):
    stages = stage_dates(base_scenario.cultivar, base_scenario.sowing_date, base_scenario.weather)
    dry = make_weather(base_scenario.sowing_date, 160, rain_mm=0.0, tmax=34.0)
    result = water_stress(base_scenario, stages, dry)
    assert result["critical_stage"] is not None
