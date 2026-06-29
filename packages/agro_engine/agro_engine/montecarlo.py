"""Motor Monte Carlo — distribuição de resultados da safra.

Em vez de uma única previsão, roda o motor determinístico N vezes variando as
fontes de incerteza mais relevantes (clima e preço) e devolve a **distribuição** de
produtividade e de lucro. Responde perguntas como "qual a chance de lucro acima de
R$ X/ha?" e "qual a chance de prejuízo?" — muito mais útil para decisão sob risco.

Mantido sem dependências externas (apenas ``random``/``statistics``) para preservar o
isolamento do pacote.
"""

from __future__ import annotations

import random
import statistics
from dataclasses import replace
from datetime import timedelta

from . import economics, phenology, sowing_window, water_balance, yield_model
from .models import DailyWeather, Scenario, WeatherSeries

# Climatologia de verão do Noroeste do RS (defaults estocásticos do clima sintético).
SEASON_RAIN_MEAN_MM = 650.0   # chuva acumulada média no ciclo (~150 dias)
SEASON_RAIN_SD_MM = 180.0     # desvio (captura de anos secos a chuvosos)
TEMP_ANOMALY_SD = 1.5         # °C de anomalia térmica sazonal
P_WET_DAY = 0.42              # probabilidade de dia com chuva
OTHER_NOISE_SD = 0.04         # ruído multiplicativo (pragas/granizo/fatores não modelados)

# Efeito ENSO no regime de chuva do verão do NO-RS (Berlato & Cordeiro; Embrapa Clima).
# La Niña → déficit e maior variância (veranicos/quebra); El Niño → chuva acima da média.
ENSO_RAIN_FACTOR = {"el_nino": 1.18, "neutro": 1.0, "la_nina": 0.74}
ENSO_SD_FACTOR = {"el_nino": 1.0, "neutro": 1.0, "la_nina": 1.25}


def _synth_weather(scenario: Scenario, rng: random.Random) -> WeatherSeries:
    """Gera uma série climática sintética para UMA safra possível."""
    cycle = scenario.cultivar.cycle_days + 25
    enso = getattr(scenario, "enso", "neutro")
    rain_mean = SEASON_RAIN_MEAN_MM * ENSO_RAIN_FACTOR.get(enso, 1.0)
    rain_sd = SEASON_RAIN_SD_MM * ENSO_SD_FACTOR.get(enso, 1.0)
    total_rain = max(120.0, rng.gauss(rain_mean, rain_sd))
    temp_anom = rng.gauss(0.0, TEMP_ANOMALY_SD)

    expected_wet_days = max(1.0, cycle * P_WET_DAY)
    mean_per_wet = total_rain / expected_wet_days

    days: list[DailyWeather] = []
    for i in range(cycle):
        day = scenario.sowing_date + timedelta(days=i)
        if rng.random() < P_WET_DAY:
            rain = rng.expovariate(1.0 / mean_per_wet)
        else:
            rain = 0.0
        tmin = 17.5 + temp_anom + rng.gauss(0, 1.0)
        tmax = 29.5 + temp_anom + rng.gauss(0, 1.5)
        days.append(
            DailyWeather(day=day, tmin=tmin, tmax=max(tmax, tmin + 2), rain_mm=rain, radiation_mj=20.0)
        )
    return WeatherSeries(days=days)


def _percentile(sorted_vals: list[float], q: float) -> float:
    if not sorted_vals:
        return 0.0
    idx = min(len(sorted_vals) - 1, max(0, int(round(q * (len(sorted_vals) - 1)))))
    return sorted_vals[idx]


def _histogram(values: list[float], bins: int = 24) -> list[dict]:
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi <= lo:
        return [{"start": lo, "end": lo, "count": len(values)}]
    width = (hi - lo) / bins
    counts = [0] * bins
    for v in values:
        b = min(bins - 1, int((v - lo) / width))
        counts[b] += 1
    return [
        {"start": round(lo + i * width, 1), "end": round(lo + (i + 1) * width, 1), "count": c}
        for i, c in enumerate(counts)
    ]


def run_montecarlo(
    scenario: Scenario,
    n: int = 2000,
    seed: int | None = None,
    price_sd_pct: float = 0.12,
    profit_target_per_ha: float = 0.0,
    yield_target_sc_ha: float | None = None,
) -> dict:
    """Roda N safras possíveis e resume a distribuição de produtividade e lucro.

    - ``price_sd_pct``: volatilidade do preço da soja (desvio relativo).
    - ``profit_target_per_ha``: alvo para calcular P(lucro ≥ alvo).
    - ``yield_target_sc_ha``: alvo para P(produtividade ≥ alvo); default = média esperada.
    """
    rng = random.Random(seed)
    base_price = scenario.soybean_price_per_sc

    yields: list[float] = []
    profits: list[float] = []

    for _ in range(n):
        weather = _synth_weather(scenario, rng)
        stages = phenology.stage_dates(scenario.cultivar, scenario.sowing_date, weather)
        water = water_balance.water_stress(scenario, stages, weather)
        sowing = sowing_window.evaluate(scenario.municipality, scenario.sowing_date)
        yres = yield_model.decompose(scenario, water, sowing)

        noise = max(0.5, rng.gauss(1.0, OTHER_NOISE_SD))
        y = max(0.0, yres.expected_sc_ha * noise)

        price = max(1.0, rng.gauss(base_price, base_price * price_sd_pct))
        scen_priced = replace(scenario, soybean_price_per_sc=price)
        econ = economics.compute(scen_priced, y)

        yields.append(y)
        profits.append(econ.profit_per_ha)

    ys, ps = sorted(yields), sorted(profits)
    mean_yield = statistics.fmean(ys)
    y_threshold = yield_target_sc_ha if yield_target_sc_ha is not None else mean_yield

    def prob(vals: list[float], threshold: float, *, above: bool = True) -> float:
        if not vals:
            return 0.0
        hits = sum(1 for v in vals if (v >= threshold if above else v < threshold))
        return round(hits / len(vals), 3)

    return {
        "iterations": n,
        "enso": getattr(scenario, "enso", "neutro"),
        "yield": {
            "mean": round(mean_yield, 1),
            "p10": round(_percentile(ys, 0.10), 1),
            "p50": round(_percentile(ys, 0.50), 1),
            "p90": round(_percentile(ys, 0.90), 1),
            "histogram": _histogram(ys),
        },
        "profit": {
            "mean": round(statistics.fmean(ps), 0),
            "p10": round(_percentile(ps, 0.10), 0),
            "p50": round(_percentile(ps, 0.50), 0),
            "p90": round(_percentile(ps, 0.90), 0),
            "histogram": _histogram(ps),
        },
        "probabilities": {
            "yield_above_target": prob(ys, y_threshold),
            "yield_target": round(y_threshold, 1),
            "profit_above_target": prob(ps, profit_target_per_ha),
            "profit_target": round(profit_target_per_ha, 0),
            "loss": prob(ps, 0.0, above=False),
        },
    }
