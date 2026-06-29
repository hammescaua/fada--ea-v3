"""Motor hídrico — balanço de água no solo (FAO-56 simplificado).

Faz a contabilidade diária da água disponível no solo durante o ciclo e calcula o
**estresse hídrico por estádio fenológico** — a variável que mais determina quebra
de produtividade na soja. A saída alimenta o fator "água" da decomposição IPPD.

Modelo (FAO-56, abordagem de depleção da zona radicular):
    TAW = AWC · profundidade_efetiva           (água total disponível)
    RAW = p · TAW                              (água facilmente disponível)
    ETc = Kc(estádio) · ET0                    (evapotranspiração da cultura)
    Dr_i = Dr_(i-1) + ETc - (P - escoamento) - irrigação   (depleção)
    Ks = (TAW - Dr) / (TAW - RAW)  se Dr > RAW, senão 1     (coef. de estresse)
"""

from __future__ import annotations

from datetime import date, timedelta

from . import reference as ref
from .models import DailyWeather, Scenario, SoilProfile, WeatherSeries


def _et0(d: DailyWeather) -> float:
    """ET0 diária: usa o valor informado ou estima por Hargreaves simplificado."""
    if d.et0_mm is not None:
        return d.et0_mm
    # Hargreaves: ET0 ≈ 0.0023 · Ra · (Tmean+17.8) · sqrt(Tmax-Tmin)
    tr = max(0.0, d.tmax - d.tmin)
    ra = d.radiation_mj  # aproximação: usa radiação incidente como proxy de Ra
    return max(0.0, 0.0023 * ra * (d.tmean + 17.8) * (tr ** 0.5))


def _stage_at(day: date, stages: dict[str, date]) -> str:
    """Estádio fenológico vigente em ``day`` (último estádio já atingido)."""
    current = "VE"
    for stage, sdate in sorted(stages.items(), key=lambda x: x[1]):
        if sdate <= day:
            current = stage
        else:
            break
    return current


def water_stress(
    scenario: Scenario,
    stages: dict[str, date],
    weather: WeatherSeries | None = None,
) -> dict:
    """Calcula o índice de estresse hídrico ponderado por sensibilidade de estádio.

    Retorna um dict com:
      - ``overall_stress`` (0 sem estresse .. 1 estresse máximo)
      - ``by_stage`` {estádio: estresse médio}
      - ``critical_stage`` estádio com maior estresse ponderado
    """
    soil: SoilProfile = scenario.soil
    weather = weather or scenario.weather
    moisture_obs = scenario.soil_moisture_obs or {}  # {data: fração de água disponível 0..1}
    measured_days = 0

    taw = ref.AWC_MM_PER_M[soil.texture] * soil.rooting_depth_m
    raw = ref.DEPLETION_FRACTION_P * taw
    dr = 0.0  # começa com solo na capacidade de campo

    start = stages.get("VE", scenario.sowing_date)
    end = stages.get("R8", start + timedelta(days=scenario.cultivar.cycle_days))

    reproductive = {"R1", "R2", "R3", "R4", "R5", "R5.5", "R6"}
    hot_days_reproductive = 0
    accum: dict[str, list[float]] = {}
    day = start
    while day <= end:
        rec = _day_weather(weather, day)
        stage = _stage_at(day, stages)
        kc = ref.KC_BY_STAGE.get(stage, 1.0)
        etc = kc * _et0(rec)
        infiltration = max(0.0, rec.rain_mm * 0.9)  # 10% de escoamento/perda
        dr = dr + etc - infiltration
        dr = min(max(dr, 0.0), taw)  # limita entre 0 e TAW

        # ÂNCORA DE REALIDADE: se há umidade do solo MEDIDA neste dia, o estado do
        # balanço vem do sensor, não do modelo (a fonte mais verídica da água).
        obs = moisture_obs.get(day) if moisture_obs else None
        if obs is None and isinstance(moisture_obs, dict):
            obs = moisture_obs.get(day.isoformat())
        if obs is not None:
            frac = max(0.0, min(1.0, float(obs)))
            dr = (1.0 - frac) * taw
            measured_days += 1

        if dr > raw and taw > raw:
            ks = (taw - dr) / (taw - raw)
        else:
            ks = 1.0
        stress = 1.0 - max(0.0, min(1.0, ks))
        accum.setdefault(stage, []).append(stress)
        if stage in reproductive and rec.tmax > ref.HEAT_THRESHOLD_C:
            hot_days_reproductive += 1
        day += timedelta(days=1)

    by_stage = {s: sum(v) / len(v) for s, v in accum.items() if v}

    # Estresse global ponderado pela sensibilidade de cada estádio.
    num = den = 0.0
    weighted: dict[str, float] = {}
    for stage, s in by_stage.items():
        w = ref.WATER_SENSITIVITY_BY_STAGE.get(stage, 0.3)
        weighted[stage] = s * w
        num += s * w
        den += w
    overall = (num / den) if den else 0.0
    critical = max(weighted, key=weighted.get) if weighted else None

    return {
        "overall_stress": round(overall, 3),
        "by_stage": {k: round(v, 3) for k, v in by_stage.items()},
        "critical_stage": critical,
        "taw_mm": round(taw, 1),
        "raw_mm": round(raw, 1),
        "hot_days_reproductive": hot_days_reproductive,
        "soil_moisture_measured_days": measured_days,
    }


def _day_weather(weather: WeatherSeries | None, day: date) -> DailyWeather:
    if weather is not None:
        for d in weather.days:
            if d.day == day:
                return d
    # Fallback climatológico: ANO NORMAL do verão do NO-RS (~5,5 mm/dia ≈ 800 mm/ciclo,
    # com leve déficit típico). Serve só quando não há clima real; com Open-Meteo o
    # déficit é calculado da série observada, e o Monte Carlo amostra a distribuição.
    return DailyWeather(day=day, tmin=18.0, tmax=30.0, rain_mm=5.5, radiation_mj=20.0)
