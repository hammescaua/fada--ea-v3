"""Schemas Pydantic — contrato da API com o frontend.

Os schemas de simulação espelham o ``Scenario`` do agro_engine para que o
Laboratório Virtual envie um cenário e receba a decomposição IPPD + econômico.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


# --- Simulação ---------------------------------------------------------------
class SoilIn(BaseModel):
    texture: str = "argiloso"
    clay_pct: float = 60.0
    organic_matter_pct: float = 3.5
    ph: float = 5.8
    cec: float = 14.0
    base_saturation_pct: float = 60.0
    phosphorus_ppm: float = 12.0
    potassium_ppm: float = 140.0
    compaction: str = "leve"
    rooting_depth_m: float = 0.6


class CultivarIn(BaseModel):
    name: str = "Genérica RR 5.5"
    maturity_group: float = 5.5
    base_potential_sc_ha: float = 95.0
    cycle_days: int = 130
    disease_tolerance: float = 0.5
    nematode_tolerance: float = 0.5


class OperationIn(BaseModel):
    kind: str
    op_date: date
    product: str = ""
    dose: float = 0.0
    cost_per_ha: float = 0.0
    quality: float = 1.0


class CostItemIn(BaseModel):
    category: str
    description: str
    cost_per_ha: float


class ScenarioIn(BaseModel):
    soil: SoilIn = Field(default_factory=SoilIn)
    cultivar: CultivarIn = Field(default_factory=CultivarIn)
    sowing_date: date
    municipality: str = "Santo Ângelo"
    latitude: float = -28.30
    longitude: float = -54.26
    population_k_per_ha: float = 300.0
    row_spacing_cm: float = 45.0
    operations: list[OperationIn] = Field(default_factory=list)
    costs: list[CostItemIn] = Field(default_factory=list)
    soybean_price_per_sc: float = 120.0
    use_live_weather: bool = False  # se True, busca clima histórico real
    enso: str = "neutro"            # "el_nino" | "neutro" | "la_nina" — outlook climático da safra
    nematode_pressure: str = "nenhuma"  # nenhuma | baixa | media | alta
    previous_crop: str = "soja"         # soja | milho | trigo | cobertura | pousio
    # Calibração aprendida do talhão (a UI injeta a partir de /fields/{id}/calibration).
    calibration_bias_sc_ha: float = 0.0
    calibration_confidence: float = 0.0
    calibration_seasons: int = 0


class MonteCarloIn(ScenarioIn):
    iterations: int = Field(default=2000, ge=100, le=20000)
    seed: int | None = None
    price_sd_pct: float = Field(default=0.12, ge=0, le=1)
    profit_target_per_ha: float = 0.0
    yield_target_sc_ha: float | None = None


class AssistantIn(BaseModel):
    question: str
    scenario: ScenarioIn


class BriefingIn(BaseModel):
    scenario: ScenarioIn
    provenance: dict[str, str] = Field(default_factory=dict)


class AccuracyIn(BaseModel):
    scenario: ScenarioIn
    provenance: dict[str, str] = Field(default_factory=dict)


class CropPlanIn(BaseModel):
    scenario: ScenarioIn
    provenance: dict[str, str] = Field(default_factory=dict)
    today: date | None = None


class CounterfactualIn(BaseModel):
    scenario: ScenarioIn


class SeasonReviewIn(BaseModel):
    scenario: ScenarioIn


class ObservationIn(BaseModel):
    kind: str
    source: str
    observed_at: date
    value: dict = Field(default_factory=dict)
    unit: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    consequence: str | None = None
    season_id: str | None = None
    confidence: float | None = None  # se ausente, o Reality Engine deriva da fonte


class ObservationOut(BaseModel):
    id: str
    field_id: str
    observed_at: date
    kind: str
    source: str
    value: dict
    unit: str | None = None
    confidence: float
    latitude: float | None = None
    longitude: float | None = None
    consequence: str | None = None


class SeasonOutcomeIn(BaseModel):
    crop_year: str
    predicted_sc_ha: float
    actual_sc_ha: float


class CalibrationComputeIn(BaseModel):
    records: list[SeasonOutcomeIn] = Field(default_factory=list)


class CalibrationOut(BaseModel):
    n_seasons: int
    bias_sc_ha: float
    confidence: float
    mae_before: float
    mae_after: float
    raw_bias_sc_ha: float


class SeasonRecordIn(BaseModel):
    crop_year: str
    scenario: ScenarioIn
    actual_yield_sc_ha: float | None = None


class FactorOut(BaseModel):
    label: str
    delta_sc_ha: float
    confidence: float
    detail: str


class YieldOut(BaseModel):
    base_potential_sc_ha: float
    contributions: list[FactorOut]
    expected_sc_ha: float
    uncertainty_sc_ha: float
    confidence: float


class EconomicsOut(BaseModel):
    total_cost_per_ha: float
    revenue_per_ha: float
    profit_per_ha: float
    margin_pct: float
    roi: float
    breakeven_yield_sc_ha: float
    breakeven_price_per_sc: float


class SimulationOut(BaseModel):
    yield_result: YieldOut
    economics: EconomicsOut
    phenology: dict[str, str]
    water: dict
    sowing_window: dict


# --- CRUD básico -------------------------------------------------------------
class FarmIn(BaseModel):
    name: str
    municipality: str


class FarmOut(BaseModel):
    id: str
    name: str
    municipality: str


class FieldIn(BaseModel):
    name: str
    municipality: str
    geojson: dict | None = None  # Polygon GeoJSON desenhado no mapa
    centroid_lat: float | None = None
    centroid_lon: float | None = None
    area_ha: float | None = None


class FieldOut(BaseModel):
    id: str
    farm_id: str
    name: str
    municipality: str
    area_ha: float | None
    centroid_lat: float | None
    centroid_lon: float | None


class SoilTestIn(BaseModel):
    sampled_at: date | None = None
    clay_pct: float | None = None
    organic_matter_pct: float | None = None
    ph: float | None = None
    cec: float | None = None
    base_saturation_pct: float | None = None
    phosphorus_ppm: float | None = None
    potassium_ppm: float | None = None


class SoilTestOut(SoilTestIn):
    id: str
    field_id: str


class SeasonSummaryOut(BaseModel):
    id: str
    crop_year: str
    cultivar_name: str | None
    sowing_date: date | None
    predicted_yield_sc_ha: float | None
    actual_yield_sc_ha: float | None
