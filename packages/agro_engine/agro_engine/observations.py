"""Observações da lavoura — integra dados medidos no talhão ao modelo.

A fonte mais verídica de todas é a medição no próprio talhão (miniestação/sensores).
Este módulo converte leituras de campo em entradas do motor:

- **chuva medida** (pluviômetro) sobrepõe a chuva da reanálise/climatologia (a chuva é
  pontual e a grade de reanálise não captura bem);
- **umidade do solo medida** (sensor) ancora o balanço hídrico no estado real (ver
  ``water_balance``), substituindo a estimativa do modelo nos dias com leitura.

Hierarquia de fontes de clima (da mais para a menos verídica):
``sensor_lavoura`` > ``estacao_inmet`` > ``reanalise`` (Open-Meteo/NASA POWER) > ``sintetico``.
"""

from __future__ import annotations

from datetime import date

from .models import DailyWeather, WeatherSeries

CLIMATE_TIERS = ["sensor_lavoura", "estacao_inmet", "reanalise", "sintetico"]


def _as_date(d) -> date:
    return d if isinstance(d, date) else date.fromisoformat(str(d))


def overlay_observed_rain(series: WeatherSeries, observed_rain: dict) -> WeatherSeries:
    """Devolve uma cópia da série com a chuva medida sobrepondo os dias disponíveis."""
    obs = {_as_date(k): float(v) for k, v in observed_rain.items()}
    days = [
        DailyWeather(
            day=d.day, tmin=d.tmin, tmax=d.tmax,
            rain_mm=obs.get(d.day, d.rain_mm), radiation_mj=d.radiation_mj, et0_mm=d.et0_mm,
        )
        for d in series.days
    ]
    return WeatherSeries(days=days)


def daily_mean(readings: list[tuple]) -> dict:
    """Agrega leituras (data, valor) em média diária — para chuva acumulada some, para
    umidade use a média. Aqui devolve a MÉDIA por dia (uso: umidade do solo 0..1)."""
    acc: dict[date, list[float]] = {}
    for ts, val in readings:
        acc.setdefault(_as_date(ts), []).append(float(val))
    return {d: sum(v) / len(v) for d, v in acc.items()}


def daily_sum(readings: list[tuple]) -> dict:
    """Soma por dia (uso: chuva acumulada a partir de leituras sub-diárias)."""
    acc: dict[date, float] = {}
    for ts, val in readings:
        acc[_as_date(ts)] = acc.get(_as_date(ts), 0.0) + float(val)
    return acc
