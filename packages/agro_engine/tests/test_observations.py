"""Testes da integração de dados medidos na lavoura (sensores)."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

from agro_engine import overlay_observed_rain, stage_dates, water_stress
from agro_engine.observations import daily_mean, daily_sum

from conftest import make_weather


def test_overlay_observed_rain_replaces_days(base_scenario):
    series = make_weather(base_scenario.sowing_date, 30, rain_mm=2.0)
    d5 = base_scenario.sowing_date + timedelta(days=5)
    out = overlay_observed_rain(series, {d5: 40.0})
    byday = {d.day: d.rain_mm for d in out.days}
    assert byday[d5] == 40.0
    assert byday[base_scenario.sowing_date] == 2.0  # dias sem leitura inalterados


def test_soil_moisture_anchor_changes_stress(base_scenario):
    stages = stage_dates(base_scenario.cultivar, base_scenario.sowing_date, base_scenario.weather)
    dry_days = {
        (base_scenario.sowing_date + timedelta(days=i)).isoformat(): 0.1  # solo quase seco medido
        for i in range(40, 90)
    }
    wet_days = {k: 0.95 for k in dry_days}  # solo medido perto da capacidade de campo

    s_dry = replace(base_scenario, soil_moisture_obs=dry_days)
    s_wet = replace(base_scenario, soil_moisture_obs=wet_days)
    stress_dry = water_stress(s_dry, stages, base_scenario.weather)
    stress_wet = water_stress(s_wet, stages, base_scenario.weather)

    assert stress_dry["overall_stress"] > stress_wet["overall_stress"]
    assert stress_dry["soil_moisture_measured_days"] == len(dry_days)


def test_daily_aggregators():
    from datetime import date

    readings = [(date(2025, 11, 1), 5.0), (date(2025, 11, 1), 3.0), (date(2025, 11, 2), 10.0)]
    assert daily_sum(readings)[date(2025, 11, 1)] == 8.0     # chuva acumulada
    assert daily_mean(readings)[date(2025, 11, 1)] == 4.0    # umidade média
