"""Missing Information Engine — o sistema busca reduzir a PRÓPRIA incerteza.

Inversão de quem pede: em vez de só receber dados, o sistema identifica **qual dado que
falta reduziria mais a incerteza** das recomendações e o solicita — como um especialista
que, antes de concluir, pede a análise de solo ou a inspeção de ferrugem.

Reaproveita o que já é calculado: a alavancagem (quanto a estimativa oscila se aquele dado
fosse real) e a proveniência (o que ainda é default). Ordena os pedidos por ganho real de
confiança, não por capricho — só pede o que muda a decisão.
"""

from __future__ import annotations

from .data_sources import accuracy_report
from .models import Scenario
from .provenance import GROUP_WEIGHT


def missing_information(scenario: Scenario, provenance: dict | None = None) -> dict:
    """Lista priorizada de dados a coletar para aumentar a confiança das recomendações."""
    acc = accuracy_report(scenario, provenance)
    pedidos: list[dict] = []
    for v in acc["variables"]:
        if v["quality"] >= 0.85:
            continue  # já é específico/real o suficiente
        ganho_pp = round(GROUP_WEIGHT.get(v["group"], 0.0) * (1.0 - v["quality"]) * 100, 1)
        if v["leverage_sc_ha"] <= 0 and ganho_pp <= 0:
            continue
        pedidos.append({
            "dado": v["label"],
            "grupo": v["group"],
            "fonte_atual": v["current_label"],
            "reduz_incerteza_sc_ha": v["leverage_sc_ha"],
            "ganho_confianca_pp": ganho_pp,
            "como_obter": v["how_to_improve"],
        })
    # ordena por quanto a estimativa pode oscilar (valor da informação) e ganho de confiança
    pedidos.sort(key=lambda p: (p["reduz_incerteza_sc_ha"], p["ganho_confianca_pp"]), reverse=True)
    return {
        "precisao_atual": acc["precision_index"],
        "pedidos": pedidos,
        "resumo": _resumo(acc["precision_index"], pedidos),
    }


def _resumo(precisao: float, pedidos: list[dict]) -> str:
    if not pedidos:
        return f"Confiança boa ({precisao * 100:.0f}%) — sem dados críticos faltando."
    top = pedidos[0]
    alvo = top["dado"].lower()
    if top["reduz_incerteza_sc_ha"] > 0:
        return (
            f"Para decidir com mais certeza, o dado que mais ajuda é {alvo} "
            f"(pode mudar a estimativa em ±{top['reduz_incerteza_sc_ha']:.0f} sc/ha): {top['como_obter']}"
        )
    return f"Para aumentar a confiança, informe {alvo}: {top['como_obter']}"
