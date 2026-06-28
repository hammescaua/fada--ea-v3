"""Endpoints do motor: simulação, janela de semeadura, catálogos de apoio."""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter

from agro_engine import recommend_sowing_window, run_montecarlo, simulate
from agro_engine.models import (
    CostItem,
    Cultivar,
    Operation,
    Scenario,
    SoilProfile,
    SoilTexture,
)
from agro_engine.reference import NO_RS_MUNICIPALITIES

from .. import weather
from ..schemas import MonteCarloIn, ScenarioIn, SimulationOut

router = APIRouter(tags=["motor"])


def _to_scenario(payload: ScenarioIn) -> Scenario:
    soil = SoilProfile(
        texture=SoilTexture(payload.soil.texture),
        clay_pct=payload.soil.clay_pct,
        organic_matter_pct=payload.soil.organic_matter_pct,
        ph=payload.soil.ph,
        cec=payload.soil.cec,
        base_saturation_pct=payload.soil.base_saturation_pct,
        phosphorus_ppm=payload.soil.phosphorus_ppm,
        potassium_ppm=payload.soil.potassium_ppm,
        compaction=payload.soil.compaction,
        rooting_depth_m=payload.soil.rooting_depth_m,
    )
    cultivar = Cultivar(
        name=payload.cultivar.name,
        maturity_group=payload.cultivar.maturity_group,
        base_potential_sc_ha=payload.cultivar.base_potential_sc_ha,
        cycle_days=payload.cultivar.cycle_days,
        disease_tolerance=payload.cultivar.disease_tolerance,
    )
    scenario = Scenario(
        soil=soil,
        cultivar=cultivar,
        sowing_date=payload.sowing_date,
        municipality=payload.municipality,
        latitude=payload.latitude,
        longitude=payload.longitude,
        population_k_per_ha=payload.population_k_per_ha,
        row_spacing_cm=payload.row_spacing_cm,
        operations=[
            Operation(
                kind=o.kind, op_date=o.op_date, product=o.product,
                dose=o.dose, cost_per_ha=o.cost_per_ha, quality=o.quality,
            )
            for o in payload.operations
        ],
        costs=[
            CostItem(category=c.category, description=c.description, cost_per_ha=c.cost_per_ha)
            for c in payload.costs
        ],
        soybean_price_per_sc=payload.soybean_price_per_sc,
    )

    if payload.use_live_weather:
        end = payload.sowing_date + timedelta(days=cultivar.cycle_days + 20)
        try:
            scenario.weather = weather.get_weather(
                payload.latitude, payload.longitude, payload.sowing_date, end
            )
        except Exception:  # noqa: BLE001 — degrada para clima climatológico
            scenario.weather = None
    return scenario


@router.post("/simulate", response_model=SimulationOut)
def post_simulate(payload: ScenarioIn) -> SimulationOut:
    """Roda o pipeline completo (fenologia→água→ZARC→IPPD→econômico)."""
    scenario = _to_scenario(payload)
    result = simulate(scenario)
    return SimulationOut(
        yield_result={
            "base_potential_sc_ha": result.yield_result.base_potential_sc_ha,
            "contributions": [c.__dict__ for c in result.yield_result.contributions],
            "expected_sc_ha": result.yield_result.expected_sc_ha,
            "uncertainty_sc_ha": result.yield_result.uncertainty_sc_ha,
            "confidence": result.yield_result.confidence,
        },
        economics=result.economics.__dict__,
        phenology=result.phenology,
        water=result.water,
        sowing_window=result.sowing_window,
    )


@router.post("/simulate/montecarlo")
def post_montecarlo(payload: MonteCarloIn) -> dict:
    """Roda N safras possíveis (clima + preço estocásticos) e devolve a distribuição
    de produtividade e lucro, com probabilidades de atingir metas e de prejuízo."""
    payload.use_live_weather = False  # Monte Carlo sintetiza o próprio clima
    scenario = _to_scenario(payload)
    return run_montecarlo(
        scenario,
        n=payload.iterations,
        seed=payload.seed,
        price_sd_pct=payload.price_sd_pct,
        profit_target_per_ha=payload.profit_target_per_ha,
        yield_target_sc_ha=payload.yield_target_sc_ha,
    )


@router.get("/sowing-window")
def get_sowing_window(municipality: str, year: int | None = None) -> dict:
    year = year or date.today().year
    return recommend_sowing_window(municipality, year)


@router.get("/municipalities")
def get_municipalities() -> list[str]:
    return NO_RS_MUNICIPALITIES


@router.get("/cultivars/sample")
def get_sample_cultivars() -> list[dict]:
    """Catálogo de exemplo (grupos de maturação típicos do NO do RS)."""
    return [
        {"name": "GMR 5.2 precoce", "maturity_group": 5.2, "base_potential_sc_ha": 92, "cycle_days": 120, "disease_tolerance": 0.5},
        {"name": "GMR 5.5 média", "maturity_group": 5.5, "base_potential_sc_ha": 95, "cycle_days": 130, "disease_tolerance": 0.6},
        {"name": "GMR 6.2 tardia", "maturity_group": 6.2, "base_potential_sc_ha": 98, "cycle_days": 140, "disease_tolerance": 0.4},
    ]
