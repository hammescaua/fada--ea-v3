"""Motor de janela de semeadura — recomendação baseada no ZARC.

Cruza a janela oficial do ZARC (município) com a data escolhida e devolve a
penalidade de produtividade por semear fora do núcleo ótimo. É a base da
recomendação de "melhor data de plantio".
"""

from __future__ import annotations

from datetime import date

from . import reference as ref


def _to_date(year: int, md: tuple[int, int]) -> date:
    month, day = md
    return date(year, month, day)


def evaluate(municipality: str, sowing_date: date) -> dict:
    """Avalia a data de semeadura contra a janela ZARC do município.

    Retorna janela (início/fim), núcleo ótimo, dias de desvio e penalidade (sc/ha).
    """
    (start_md, end_md) = ref.zarc_window(municipality)
    year = sowing_date.year if sowing_date.month >= start_md[0] else sowing_date.year - 1
    start = _to_date(year, start_md)
    end = _to_date(year + (1 if end_md[0] < start_md[0] else 0), end_md)

    # Núcleo ótimo: terço inicial da janela (maior potencial produtivo).
    span = (end - start).days
    optimal_end = start.fromordinal(start.toordinal() + max(1, span // 3))

    if sowing_date < start:
        deviation_days = (start - sowing_date).days
        position = "antes_da_janela"
    elif sowing_date > end:
        deviation_days = (sowing_date - end).days
        position = "depois_da_janela"
    elif start <= sowing_date <= optimal_end:
        deviation_days = 0
        position = "otimo"
    else:
        deviation_days = (sowing_date - optimal_end).days
        position = "dentro_da_janela"

    penalty = round(deviation_days * ref.SOWING_PENALTY_SC_PER_DAY, 2)

    return {
        "municipality": municipality,
        "window_start": start.isoformat(),
        "window_end": end.isoformat(),
        "optimal_end": optimal_end.isoformat(),
        "sowing_date": sowing_date.isoformat(),
        "position": position,
        "deviation_days": deviation_days,
        "penalty_sc_ha": penalty,
    }


def recommend(municipality: str, year: int) -> dict:
    """Recomendação direta da janela ótima de semeadura para o ano-safra."""
    (start_md, end_md) = ref.zarc_window(municipality)
    start = _to_date(year, start_md)
    end = _to_date(year + (1 if end_md[0] < start_md[0] else 0), end_md)
    span = (end - start).days
    optimal_end = start.fromordinal(start.toordinal() + max(1, span // 3))
    return {
        "municipality": municipality,
        "window_start": start.isoformat(),
        "window_end": end.isoformat(),
        "optimal_start": start.isoformat(),
        "optimal_end": optimal_end.isoformat(),
    }
