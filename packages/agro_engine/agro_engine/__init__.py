"""agro_engine — motor agronômico determinístico do Gêmeo Digital da soja.

Camada científica e explicável que sustenta as simulações. A IA personalizada
(fases futuras) atua *acima* desta camada, como correção, nunca a substituindo.
"""

from .economics import compute as compute_economics
from .models import (
    Cultivar,
    CostItem,
    DailyWeather,
    EconomicsResult,
    FactorContribution,
    Operation,
    Scenario,
    SimulationResult,
    SoilProfile,
    SoilTexture,
    WeatherSeries,
    YieldResult,
)
from .montecarlo import run_montecarlo
from .phenology import stage_dates
from .simulate import simulate
from .sowing_window import evaluate as evaluate_sowing_window
from .sowing_window import recommend as recommend_sowing_window
from .water_balance import water_stress
from .yield_model import decompose as decompose_yield

__version__ = "0.1.0"

__all__ = [
    "Cultivar",
    "CostItem",
    "DailyWeather",
    "EconomicsResult",
    "FactorContribution",
    "Operation",
    "Scenario",
    "SimulationResult",
    "SoilProfile",
    "SoilTexture",
    "WeatherSeries",
    "YieldResult",
    "compute_economics",
    "decompose_yield",
    "evaluate_sowing_window",
    "recommend_sowing_window",
    "run_montecarlo",
    "simulate",
    "stage_dates",
    "water_stress",
]
