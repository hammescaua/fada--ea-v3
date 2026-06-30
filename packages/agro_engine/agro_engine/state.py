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

from .data_sources import accuracy_report
from .missing_info import missing_information
from .models import Scenario
from .radar import season_radar
from .reasoning import diagnose
from .simulate import simulate


def world_state(
    scenario: Scenario,
    today: date | None = None,
    provenance: dict | None = None,
    observations=None,
) -> dict:
    """Compõe o estado unificado da safra (fonte única para todas as vistas).

    Roda a simulação e a análise de acurácia UMA vez e as compartilha entre os motores —
    garante que todas as vistas vejam exatamente os mesmos números e evita recálculo."""
    sim = simulate(scenario)
    acc = accuracy_report(scenario, provenance)
    radar = season_radar(scenario, today, sim=sim)
    diag = diagnose(scenario, provenance, observations, sim=sim, acc=acc)
    missing = missing_information(scenario, provenance, acc=acc)

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
