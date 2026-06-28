"""Testes da Base de Conhecimento (kb) e do Motor de Fertilidade."""

from __future__ import annotations

from dataclasses import replace

from agro_engine import kb, recommend_amendments
from agro_engine.fertility import liming, phosphorus, potassium
from agro_engine.models import SoilTexture


def test_kb_loads_with_sources():
    # coeficientes-chave existem e têm fonte citada
    assert kb.param("calagem.v_alvo_soja") == 65.0
    assert kb.source("nutricao.p_suficiente_ppm")  # string não vazia
    assert "map" in kb.inputs()
    assert kb.get_input("calcario_dolomitico")["prnt_pct"] == 80.0


def test_reference_synced_with_kb():
    from agro_engine import reference as ref
    # reference foi sincronizado a partir da KB (mesmos valores)
    assert ref.P_SUFFICIENT_PPM == kb.param("nutricao.p_suficiente_ppm")
    assert ref.DISEASE_PRESSURE == kb.param("fitossanidade.disease_pressure")


def test_liming_recommended_for_acid_soil(base_scenario):
    base_scenario.soil = replace(base_scenario.soil, ph=5.2, base_saturation_pct=48, cec=15.0)
    rec = liming(base_scenario)
    assert rec is not None
    assert rec.dose > 0                  # precisa de calcário
    assert rec.delta_yield_sc_ha >= 0    # corrigir não reduz produtividade
    assert rec.product  # nome do insumo


def test_liming_not_recommended_for_good_soil(base_scenario):
    base_scenario.soil = replace(base_scenario.soil, ph=6.2, base_saturation_pct=70)
    assert liming(base_scenario) is None


def test_phosphorus_dose_scales_with_deficit(base_scenario):
    low = replace(base_scenario, soil=replace(base_scenario.soil, phosphorus_ppm=4.0))
    mid = replace(base_scenario, soil=replace(base_scenario.soil, phosphorus_ppm=9.0))
    r_low, r_mid = phosphorus(low), phosphorus(mid)
    assert r_low is not None and r_mid is not None
    assert r_low.dose > r_mid.dose       # mais deficiência → mais adubo
    assert r_low.investment_per_ha > r_mid.investment_per_ha


def test_recommendations_ranked_by_net(base_scenario):
    base_scenario.soil = replace(
        base_scenario.soil, ph=5.2, base_saturation_pct=46, phosphorus_ppm=5.0, potassium_ppm=80.0, cec=14.0
    )
    recs = recommend_amendments(base_scenario)
    assert len(recs) >= 2
    nets = [r.net_per_ha for r in recs]
    assert nets == sorted(nets, reverse=True)   # ranqueado por rentabilidade
