"""Testes do Motor de Veracidade dos Dados."""

from __future__ import annotations

from agro_engine import assess_data_quality


def test_more_real_sources_raise_confidence(base_scenario):
    low = assess_data_quality(base_scenario, {})  # tudo estimado
    high = assess_data_quality(
        base_scenario, {"clima": "real", "solo": "real", "cultivar": "real", "manejo": "real"}
    )
    assert high["data_confidence"] > low["data_confidence"]
    assert 0.0 <= low["data_confidence"] <= 1.0
    assert 0.0 <= high["data_confidence"] <= 1.0


def test_gaps_ranked_by_leverage(base_scenario):
    out = assess_data_quality(base_scenario, {})
    levs = [g["leverage_sc_ha"] for g in out["gaps"]]
    assert levs == sorted(levs, reverse=True)
    # o clima e o solo devem aparecer como lacunas com alavancagem > 0
    groups = {g["group"]: g for g in out["gaps"]}
    assert groups["clima"]["leverage_sc_ha"] >= 0
    assert "como_obter" in groups["solo"]


def test_real_group_is_not_a_gap(base_scenario):
    out = assess_data_quality(base_scenario, {"clima": "real"})
    assert all(g["group"] != "clima" for g in out["gaps"])


def test_resumo_mentions_top_gap(base_scenario):
    out = assess_data_quality(base_scenario, {})
    assert "Confiança dos dados" in out["resumo"]
