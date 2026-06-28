"""Fixtures compartilhadas: clima sintético e cenário-base do Noroeste do RS."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from agro_engine.models import (
    CostItem,
    Cultivar,
    DailyWeather,
    Operation,
    Scenario,
    SoilProfile,
    SoilTexture,
    WeatherSeries,
)


def make_weather(
    start: date,
    days: int,
    tmin: float = 18.0,
    tmax: float = 29.0,
    rain_mm: float = 5.0,
) -> WeatherSeries:
    """Série climática sintética homogênea para testes determinísticos."""
    recs = [
        DailyWeather(
            day=start + timedelta(days=i),
            tmin=tmin,
            tmax=tmax,
            rain_mm=rain_mm,
            radiation_mj=20.0,
        )
        for i in range(days)
    ]
    return WeatherSeries(days=recs)


@pytest.fixture
def base_cultivar() -> Cultivar:
    return Cultivar(
        name="Teste GMR 5.5",
        maturity_group=5.5,
        base_potential_sc_ha=95.0,
        cycle_days=130,
        disease_tolerance=0.5,
    )


@pytest.fixture
def good_soil() -> SoilProfile:
    return SoilProfile(
        texture=SoilTexture.ARGILOSO,
        clay_pct=62.0,
        organic_matter_pct=4.2,
        ph=6.0,
        cec=16.0,
        base_saturation_pct=65.0,
        phosphorus_ppm=16.0,
        potassium_ppm=160.0,
        compaction="nenhuma",
        rooting_depth_m=0.6,
    )


@pytest.fixture
def base_scenario(base_cultivar, good_soil) -> Scenario:
    sowing = date(2025, 11, 5)  # dentro da janela ZARC de Santo Ângelo
    weather = make_weather(sowing, 160, tmin=18.0, tmax=29.0, rain_mm=5.0)
    return Scenario(
        soil=good_soil,
        cultivar=base_cultivar,
        sowing_date=sowing,
        municipality="Santo Ângelo",
        latitude=-28.30,
        longitude=-54.26,
        population_k_per_ha=300.0,
        weather=weather,
        operations=[
            Operation(kind="herbicida", op_date=date(2025, 11, 20), cost_per_ha=160.0, quality=0.9),
            Operation(kind="inseticida", op_date=date(2026, 1, 5), cost_per_ha=120.0, quality=0.9),
            Operation(kind="fungicida", op_date=date(2026, 1, 10), cost_per_ha=180.0, quality=0.9),
            Operation(kind="fungicida", op_date=date(2026, 1, 25), cost_per_ha=180.0, quality=0.9),
        ],
        costs=[
            CostItem(category="semente", description="semente RR", cost_per_ha=520.0),
            CostItem(category="fertilizante", description="MAP+KCl", cost_per_ha=1450.0),
            CostItem(category="defensivo", description="herbicidas+inseticidas", cost_per_ha=650.0),
            CostItem(category="diesel", description="operações", cost_per_ha=380.0),
            CostItem(category="outros", description="frete+secagem+admin", cost_per_ha=620.0),
        ],
        soybean_price_per_sc=120.0,
    )
