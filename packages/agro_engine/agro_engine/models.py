"""Estruturas de dados do motor agronômico (Gêmeo Digital da lavoura de soja).

Todos os modelos são `dataclasses` puras, sem dependência de framework, para que o
motor possa ser testado, versionado e reutilizado de forma isolada (CLI, API, batch).

Unidades adotadas (padronizadas em todo o motor):
- produtividade: sacas de 60 kg por hectare (``sc_ha``)
- temperatura: °C            - chuva / lâmina d'água / ET: mm
- radiação: MJ/m²/dia        - valores monetários: R$/ha
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class SoilTexture(str, Enum):
    """Classe textural simplificada — define capacidade de água disponível (AWC)."""

    ARENOSO = "arenoso"
    MEDIO = "medio"
    ARGILOSO = "argiloso"


@dataclass
class SoilProfile:
    """Perfil do talhão. Atributos opcionais usam defaults regionais quando ausentes."""

    texture: SoilTexture = SoilTexture.ARGILOSO
    clay_pct: float = 60.0          # teor de argila (%)
    organic_matter_pct: float = 3.5  # matéria orgânica (%)
    ph: float = 5.8                  # pH em água
    cec: float = 14.0                # CTC (cmolc/dm³)
    base_saturation_pct: float = 60.0  # V%
    phosphorus_ppm: float = 12.0     # P (mg/dm³)
    potassium_ppm: float = 140.0     # K (mg/dm³)
    compaction: str = "leve"         # nenhuma | leve | moderada | severa
    rooting_depth_m: float = 0.6     # profundidade efetiva de raízes (m)


@dataclass
class Cultivar:
    """Cultivar de soja. ``base_potential_sc_ha`` é o teto produtivo do genótipo
    em condições não limitantes (usado como ponto de partida da cascata IPPD)."""

    name: str = "Genérica RR 5.5"
    maturity_group: float = 5.5      # grupo de maturação relativa
    base_potential_sc_ha: float = 95.0
    cycle_days: int = 130            # ciclo total aproximado (semeadura→R8)
    disease_tolerance: float = 0.5   # 0 (suscetível) .. 1 (tolerante) — ferrugem etc.


@dataclass
class DailyWeather:
    """Registro climático diário (fonte: NASA POWER / Open-Meteo / INMET)."""

    day: date
    tmin: float
    tmax: float
    rain_mm: float
    radiation_mj: float = 18.0       # radiação solar incidente
    et0_mm: Optional[float] = None   # evapotranspiração de referência (opcional)

    @property
    def tmean(self) -> float:
        return (self.tmin + self.tmax) / 2.0


@dataclass
class WeatherSeries:
    """Série diária ordenada. Métodos utilitários para fatiar por intervalo."""

    days: list[DailyWeather] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.days)

    def between(self, start: date, end: date) -> list[DailyWeather]:
        return [d for d in self.days if start <= d.day <= end]


@dataclass
class Operation:
    """Evento de manejo (semeadura, fungicida, cobertura, colheita...).

    ``quality`` (0..1) representa a qualidade efetiva da aplicação considerando
    condições (temperatura, vento, umidade) — usado pelo fator sanidade.
    """

    kind: str                        # ex.: "fungicida", "herbicida", "cobertura"
    op_date: date
    product: str = ""
    dose: float = 0.0
    cost_per_ha: float = 0.0
    quality: float = 1.0


@dataclass
class CostItem:
    """Item de custo da safra (R$/ha)."""

    category: str                    # semente | fertilizante | defensivo | diesel | ...
    description: str
    cost_per_ha: float


@dataclass
class Scenario:
    """Cenário completo a ser simulado pelo Laboratório Virtual."""

    soil: SoilProfile
    cultivar: Cultivar
    sowing_date: date
    municipality: str
    latitude: float
    longitude: float
    population_k_per_ha: float = 300.0   # plantas/ha em milhares
    row_spacing_cm: float = 45.0
    weather: Optional[WeatherSeries] = None
    operations: list[Operation] = field(default_factory=list)
    costs: list[CostItem] = field(default_factory=list)
    soybean_price_per_sc: float = 120.0  # R$ por saca de 60 kg

    @property
    def total_cost_per_ha(self) -> float:
        base = sum(c.cost_per_ha for c in self.costs)
        return base + sum(o.cost_per_ha for o in self.operations)


@dataclass
class FactorContribution:
    """Uma fatia da cascata de decomposição de produtividade (IPPD)."""

    label: str
    delta_sc_ha: float               # impacto sobre o teto (negativo = perda)
    confidence: float                # 0..1 — confiança do motor neste fator
    detail: str = ""


@dataclass
class YieldResult:
    """Resultado da decomposição IPPD."""

    base_potential_sc_ha: float
    contributions: list[FactorContribution]
    expected_sc_ha: float
    uncertainty_sc_ha: float         # ± em sacas
    confidence: float                # 0..1 — confiança agregada


@dataclass
class EconomicsResult:
    total_cost_per_ha: float
    revenue_per_ha: float
    profit_per_ha: float
    margin_pct: float
    roi: float
    breakeven_yield_sc_ha: float
    breakeven_price_per_sc: float


@dataclass
class SimulationResult:
    """Saída completa de ``simulate``: o que o Laboratório Virtual exibe."""

    yield_result: YieldResult
    economics: EconomicsResult
    phenology: dict          # estádio -> data ISO
    water: dict              # resumo do balanço hídrico por estádio
    sowing_window: dict      # janela ZARC e penalidade aplicada
