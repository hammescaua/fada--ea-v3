"""Testes dos motores do núcleo: State, Missing Information, Memory, urgência."""

from __future__ import annotations

from dataclasses import replace

from agro_engine import (
    PastSeason,
    missing_information,
    prioritized_actions,
    similar_seasons,
    world_state,
)


# --- Missing Information Engine ----------------------------------------------
def test_missing_info_pede_o_dado_de_maior_valor(base_scenario):
    mi = missing_information(base_scenario, {"solo": "estimado", "clima": "estimado"})
    assert mi["pedidos"]
    valores = [p["reduz_incerteza_sc_ha"] for p in mi["pedidos"]]
    assert valores == sorted(valores, reverse=True)
    assert isinstance(mi["resumo"], str) and mi["resumo"]


def test_missing_info_some_quando_dados_reais(base_scenario):
    poucos = missing_information(base_scenario, {"solo": "estimado", "clima": "estimado"})
    muitos = missing_information(base_scenario, {"solo": "real", "clima": "real", "cultivar": "real"})
    assert len(muitos["pedidos"]) < len(poucos["pedidos"])


# --- Memory Engine ------------------------------------------------------------
def _feat(**kw):
    base = {"sowing_deviation_days": 0, "water_overall_stress": 0.2, "soil_p_ppm": 12,
            "soil_k_ppm": 140, "soil_ph": 5.8, "n_fungicidas": 2, "maturity_group": 5.5}
    base.update(kw)
    return base


def test_memory_acha_safra_parecida():
    atual = _feat(water_overall_stress=0.4)
    passado = [
        PastSeason("2023/24", _feat(water_overall_stress=0.42), 80, 72),  # parecida (seca)
        PastSeason("2022/23", _feat(water_overall_stress=0.05), 80, 88),  # diferente (úmida)
    ]
    m = similar_seasons(atual, passado)
    assert m["similares"]
    assert m["similares"][0]["crop_year"] == "2023/24"
    assert m["similares"][0]["semelhanca"] > 0.7
    assert "2023/24" in m["resumo"]


def test_memory_sem_historico():
    m = similar_seasons(_feat(), [])
    assert m["similares"] == []
    assert "sem safras" in m["resumo"].lower()


# --- Decision Queue (urgência) -----------------------------------------------
def test_fila_tem_urgencia(base_scenario):
    pobre = replace(base_scenario, soil=replace(base_scenario.soil, ph=5.1, base_saturation_pct=42, phosphorus_ppm=5))
    acts = prioritized_actions(pobre)
    assert all(0 <= a["urgencia"] <= 100 for a in acts)


# --- State Engine -------------------------------------------------------------
def test_world_state_unifica_tudo(base_scenario):
    st = world_state(base_scenario)
    for k in ("fase", "score", "dimensoes", "confianca", "incerteza", "gargalo",
              "fila_decisao", "diagnostico", "pedidos_de_dado", "respostas"):
        assert k in st
    # a fila de decisão vem ordenada por urgência
    urg = [a["urgencia"] for a in st["fila_decisao"]]
    assert urg == sorted(urg, reverse=True)
