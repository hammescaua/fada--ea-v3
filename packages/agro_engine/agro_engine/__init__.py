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
from .briefing import season_briefing
from .budget import season_budget
from .counterfactual import run_counterfactuals
from .crop_plan import crop_plan
from .data_sources import accuracy_report, infer_provenance
from .evidence import Observation, confidence_for, corroborate, data_quality
from .manejo_science import manejo_evidence
from .personality import FieldSeason, personality
from .decision import operations_impact, recommend_decisions
from .fertility import recommend_amendments
from .knowledge import (
    Calibration,
    SeasonRecord,
    apply_correction,
    calibrate,
    season_features,
)
from .montecarlo import run_montecarlo
from .phenology import stage_dates
from .provenance import assess as assess_data_quality
from .scenario_search import optimize_season
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
    "FieldSeason",
    "Observation",
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
    "accuracy_report",
    "apply_correction",
    "assess_data_quality",
    "crop_plan",
    "calibrate",
    "compute_economics",
    "confidence_for",
    "corroborate",
    "data_quality",
    "decompose_yield",
    "evaluate_sowing_window",
    "infer_provenance",
    "manejo_evidence",
    "operations_impact",
    "personality",
    "run_counterfactuals",
    "optimize_season",
    "recommend_amendments",
    "recommend_decisions",
    "recommend_sowing_window",
    "season_briefing",
    "season_budget",
    "run_montecarlo",
    "season_features",
    "simulate",
    "stage_dates",
    "water_stress",
]
