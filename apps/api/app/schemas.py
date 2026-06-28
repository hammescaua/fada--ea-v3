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
