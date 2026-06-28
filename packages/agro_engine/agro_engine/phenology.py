"""Motor fenológico — graus-dia (GDD) → estádios da soja.

Estima a data de cada estádio (VE, V1, R1..R8) a partir da data de semeadura e do
clima diário, acumulando GDD (Tbase 10 °C, com teto fisiológico). Quando não há
clima disponível, cai num modo "normal climatológico" usando uma temperatura média
típica do Noroeste do RS para o verão.
"""

from __future__ import annotations

from datetime import date, timedelta

from . import reference as ref
from .models import Cultivar, WeatherSeries


def daily_gdd(tmin: float, tmax: float) -> float:
    """GDD do dia com teto em ``TUPPER_C`` (método com cap de temperatura)."""
    tmax_c = min(tmax, ref.TUPPER_C)
    tmin_c = max(min(tmin, ref.TUPPER_C), ref.TBASE_C)
    tmean = (tmax_c + tmin_c) / 2.0
    return max(0.0, tmean - ref.TBASE_C)


def _gdd_for_day(weather: WeatherSeries | None, day: date) -> float:
    if weather is not None:
        for d in weather.days:
            if d.day == day:
                return daily_gdd(d.tmin, d.tmax)
    # Fallback climatológico: verão do NO do RS, ~14/30 °C → ~12 GDD/dia.
    return 12.0


def stage_dates(
    cultivar: Cultivar,
    sowing_date: date,
    weather: WeatherSeries | None = None,
) -> dict[str, date]:
    """Retorna {estádio: data} percorrendo o ciclo dia a dia acumulando GDD."""
    gdd_total = ref.gdd_total_for(cultivar.maturity_group)
    # alvos absolutos de GDD (a partir da emergência) por estádio
    targets = {
        stage: frac * gdd_total for stage, frac in ref.STAGE_GDD_FRACTION.items()
    }

    result: dict[str, date] = {}
    cursor = sowing_date

    # 1) semeadura → emergência (VE)
    acc = 0.0
    while acc < ref.GDD_PLANTING_TO_EMERGENCE:
        acc += _gdd_for_day(weather, cursor)
        cursor += timedelta(days=1)
        if (cursor - sowing_date).days > 40:  # guarda de segurança
            break
    result["VE"] = cursor

    # 2) emergência → R8, marcando cada estádio quando atinge seu alvo
    pending = sorted(
        ((s, t) for s, t in targets.items() if s != "VE"), key=lambda x: x[1]
    )
    acc = 0.0
    emergence = cursor
    while pending:
        acc += _gdd_for_day(weather, cursor)
        cursor += timedelta(days=1)
        while pending and acc >= pending[0][1]:
            stage, _ = pending.pop(0)
            result[stage] = cursor
        if (cursor - emergence).days > 220:  # guarda de segurança
            for stage, _ in pending:
                result[stage] = cursor
            break
    return result
