"""Testes do Motor de Cenários (otimização combinatória do plano da safra)."""

from __future__ import annotations

from agro_engine import optimize_season


def test_optimize_returns_best_and_ranking(base_scenario):
    out = optimize_season(base_scenario, top=5)
    assert out["combinacoes_avaliadas"] > 0
    assert "melhor_plano" in out and "ranking" in out
    # o melhor é o de maior lucro do ranking
    profits = [r["profit_per_ha"] for r in out["ranking"]]
    assert profits == sorted(profits, reverse=True)
    assert out["melhor_plano"]["profit_per_ha"] == out["ranking"][0]["profit_per_ha"]


def test_best_not_worse_than_current(base_scenario):
    out = optimize_season(base_scenario)
    # o melhor plano encontrado não pode ser pior que o cenário atual em lucro
    assert out["melhor_plano"]["profit_per_ha"] >= out["atual"]["profit_per_ha"] - 1


def test_explanation_present(base_scenario):
    out = optimize_season(base_scenario)
    assert out["porques"]                       # razões textuais
    assert out["decomposicao"]                  # cascata IPPD do vencedor
    assert "delta_profit_vs_atual" in out["melhor_plano"]
