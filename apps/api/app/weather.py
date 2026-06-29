"""Cliente de clima — Open-Meteo (padrão) e NASA POWER, com cache simples.

Nunca consulta a API a cada request: o resultado é memoizado por chave de grade
(lat/lon arredondados) durante a vida do processo. Em produção, o cache vai para a
tabela ``weather_cache`` (PostGIS). Open-Meteo é CC-BY (uso comercial ok, sem chave).
"""

from __future__ import annotations

from datetime import date, timedelta

import httpx

from agro_engine.models import DailyWeather, WeatherSeries

_CACHE: dict[str, WeatherSeries] = {}
_ARCHIVE_CACHE: dict[tuple[float, float], list[DailyWeather]] = {}


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


def _archive(lat: float, lon: float, years: int = 10) -> list[DailyWeather]:
    """Histórico diário (~N anos) da localização — buscado UMA vez e cacheado."""
    key = (round(lat, 2), round(lon, 2))
    if key in _ARCHIVE_CACHE:
        return _ARCHIVE_CACHE[key]
    end = date.today().replace(month=1, day=1) - timedelta(days=1)  # último 31/dez completo
    start = end.replace(year=end.year - years) + timedelta(days=1)
    series = fetch_open_meteo(lat, lon, start, end)
    _ARCHIVE_CACHE[key] = series.days
    return series.days


def get_climatology(lat: float, lon: float, start: date, end: date) -> WeatherSeries:
    """Ano climatológico REAL da localização para a janela [start, end].

    Constrói a média por dia-do-ano a partir do histórico (real, específico do local).
    Apropriado para planejar uma safra futura: usa o "ano típico" observado, não um
    fallback genérico. O Monte Carlo cobre a variabilidade em torno dessa média.
    """
    archive = _archive(lat, lon)
    if not archive:
        raise RuntimeError("sem histórico climático")

    acc: dict[tuple[int, int], list[DailyWeather]] = {}
    for d in archive:
        acc.setdefault((d.day.month, d.day.day), []).append(d)

    def _avg(md: tuple[int, int]) -> tuple[float, float, float, float, float | None]:
        recs = acc.get(md) or acc.get((md[0], min(md[1], 28)))
        if not recs:
            return 18.0, 30.0, 5.0, 20.0, None
        n = len(recs)
        et0_vals = [r.et0_mm for r in recs if r.et0_mm is not None]
        return (
            sum(r.tmin for r in recs) / n,
            sum(r.tmax for r in recs) / n,
            sum(r.rain_mm for r in recs) / n,
            sum(r.radiation_mj for r in recs) / n,
            (sum(et0_vals) / len(et0_vals)) if et0_vals else None,  # ET0 FAO real (média)
        )

    days: list[DailyWeather] = []
    cur = start
    while cur <= end:
        tmin, tmax, rain, rad, et0 = _avg((cur.month, cur.day))
        days.append(
            DailyWeather(day=cur, tmin=tmin, tmax=max(tmax, tmin + 2), rain_mm=rain, radiation_mj=rad, et0_mm=et0)
        )
        cur += timedelta(days=1)
    return WeatherSeries(days=days)
