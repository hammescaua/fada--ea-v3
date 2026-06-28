"""Cliente de clima — Open-Meteo (padrão) e NASA POWER, com cache simples.

Nunca consulta a API a cada request: o resultado é memoizado por chave de grade
(lat/lon arredondados) durante a vida do processo. Em produção, o cache vai para a
tabela ``weather_cache`` (PostGIS). Open-Meteo é CC-BY (uso comercial ok, sem chave).
"""

from __future__ import annotations

from datetime import date

import httpx

from agro_engine.models import DailyWeather, WeatherSeries

_CACHE: dict[str, WeatherSeries] = {}


def _grid_key(lat: float, lon: float, start: date, end: date) -> str:
    return f"{round(lat, 2)}_{round(lon, 2)}_{start}_{end}"


def fetch_open_meteo(lat: float, lon: float, start: date, end: date) -> WeatherSeries:
    """Busca histórico diário no Open-Meteo Archive API."""
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": ",".join(
            [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "shortwave_radiation_sum",
                "et0_fao_evapotranspiration",
            ]
        ),
        "timezone": "America/Sao_Paulo",
    }
    with httpx.Client(timeout=30) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()["daily"]

    days: list[DailyWeather] = []
    for i, day_str in enumerate(data["time"]):
        days.append(
            DailyWeather(
                day=date.fromisoformat(day_str),
                tmin=data["temperature_2m_min"][i],
                tmax=data["temperature_2m_max"][i],
                rain_mm=data["precipitation_sum"][i] or 0.0,
                radiation_mj=(data["shortwave_radiation_sum"][i] or 18.0),
                et0_mm=data["et0_fao_evapotranspiration"][i],
            )
        )
    return WeatherSeries(days=days)


def get_weather(lat: float, lon: float, start: date, end: date) -> WeatherSeries:
    """Retorna série climática (cache em memória → Open-Meteo)."""
    key = _grid_key(lat, lon, start, end)
    if key in _CACHE:
        return _CACHE[key]
    series = fetch_open_meteo(lat, lon, start, end)
    _CACHE[key] = series
    return series
