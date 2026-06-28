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
from .budget import season_budget
from .decision import operations_impact, recommend_decisions
from .knowledge import (
    Calibration,
    SeasonRecord,
    apply_correction,
    calibrate,
    season_features,
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
    "Calibration",
    "Cultivar",
    "CostItem",
    "DailyWeather",
    "EconomicsResult",
    "FactorContribution",
    "Operation",
    "Scenario",
    "SeasonRecord",
    "SimulationResult",
    "SoilProfile",
    "SoilTexture",
    "WeatherSeries",
    "YieldResult",
    "apply_correction",
    "calibrate",
    "compute_economics",
    "decompose_yield",
    "evaluate_sowing_window",
    "operations_impact",
    "recommend_decisions",
    "recommend_sowing_window",
    "season_budget",
    "run_montecarlo",
    "season_features",
    "simulate",
    "stage_dates",
    "water_stress",
]
