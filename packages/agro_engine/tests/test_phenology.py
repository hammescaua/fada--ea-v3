"""Testes do motor fenológico (GDD → estádios)."""

from __future__ import annotations

from datetime import date

from agro_engine import stage_dates
from agro_engine.phenology import daily_gdd

from conftest import make_weather


def test_daily_gdd_caps_at_upper_threshold():
    # Tmax muito alta é limitada ao teto fisiológico (30 °C).
    assert daily_gdd(20, 40) == daily_gdd(20, 30)


def test_daily_gdd_zero_when_cold():
    assert daily_gdd(2, 9) == 0.0


def test_stage_order_is_monotonic(base_cultivar):
    sowing = date(2025, 11, 5)
    weather = make_weather(sowing, 170)
    stages = stage_dates(base_cultivar, sowing, weather)
    order = ["VE", "V1", "R1", "R3", "R5", "R6", "R8"]
    dates = [stages[s] for s in order]
    assert dates == sorted(dates)
    assert stages["VE"] > sowing


def test_later_maturity_group_has_longer_cycle(base_cultivar):
    sowing = date(2025, 11, 5)
    weather = make_weather(sowing, 200)
    early = stage_dates(base_cultivar, sowing, weather)
    base_cultivar.maturity_group = 7.0
    late = stage_dates(base_cultivar, sowing, weather)
    assert late["R8"] > early["R8"]
