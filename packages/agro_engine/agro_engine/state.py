"""State Engine — o estado VIVO da safra, fonte única de verdade.

Hoje cada painel reconstruía "qual é a situação da safra". Aqui existe **uma resposta**: um
objeto de estado que reúne, num instante, a fase do ciclo, a saúde em dimensões, a
confiança (4 níveis), o gargalo, a fila de decisão priorizada por urgência e os dados que
faltam para decidir com mais certeza. Os motores compõem este estado; a interface apenas o
apresenta.

É a base do "copiloto da manhã": abrir e ver as decisões críticas, o maior risco, a maior
oportunidade e a maior incerteza — nada mais.
"""

from __future__ import annotations

from datetime import date

from .missing_info import missing_information
from .models import Scenario
from .radar import season_radar
from .reasoning import diagnose


def world_state(
    scenario: Scenario,
    today: date | None = None,
    provenance: dict | None = None,
    observations=None,
) -> dict:
    """Compõe o estado unificado da safra (fonte única para todas as vistas)."""
    radar = season_radar(scenario, today)
    diag = diagnose(scenario, provenance, observations)
    missing = missing_information(scenario, provenance)

    # Fila de decisão: as ações ordenadas por URGÊNCIA (o que fazer primeiro).
    fila = sorted(radar["actions"], key=lambda a: a.get("urgencia", 0), reverse=True)

    return {
        "fase": radar.get("estado"),
        "score": radar["score"],
        "score_label": radar["score_label"],
        "dimensoes": radar["dimensions"],
        "confianca": diag["niveis_confianca"],
        "incerteza": diag["principal_incerteza"],
        "gargalo": radar["maior_risco"],
        "oportunidade": radar["maior_oportunidade"],
        "fila_decisao": fila,
        "diagnostico": diag["hipoteses"][:3],
        "pedidos_de_dado": missing["pedidos"][:3],
        "respostas": radar["respostas"],
        "expected_sc_ha": radar["expected_sc_ha"],
        "profit_per_ha": radar["profit_per_ha"],
        "gap_sc_ha": diag["gap_sc_ha"],
    }
