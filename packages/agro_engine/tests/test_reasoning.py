"""Testes do Motor de Raciocínio (Hypothesis Engine + Impact Graph)."""

from __future__ import annotations

from dataclasses import replace

from agro_engine import Observation, diagnose, impact_chain


def test_impact_chain_traz_cadeia_e_fonte():
    ch = impact_chain("baixo_fosforo")
    assert ch is not None
    assert ch["fator"] == "Nutrição"
    assert len(ch["cadeia"]) >= 4
    assert "produtividade" in ch["cadeia"][-1].lower()
    assert ch["fonte"] and ch["confirma_se"] and ch["acao"]


def test_diagnose_estrutura(base_scenario):
    d = diagnose(base_scenario)
    assert d["potencial_sc_ha"] >= d["esperado_sc_ha"]
    assert d["gap_sc_ha"] >= 0
    for h in d["hipoteses"]:
        for k in ("causa", "fator", "perda_sc_ha", "probabilidade", "certeza_do_dado", "cadeia", "confirma_se", "acao", "fonte"):
            assert k in h
    assert isinstance(d["resumo"], str) and d["resumo"]


def test_diagnose_ranqueia_maior_limitacao_primeiro(base_scenario):
    pobre = replace(base_scenario, soil=replace(base_scenario.soil, ph=5.1, base_saturation_pct=42, phosphorus_ppm=4))
    d = diagnose(pobre)
    perdas = [h["perda_sc_ha"] for h in d["hipoteses"]]
    assert perdas == sorted(perdas, reverse=True)
    assert d["hipoteses"][0]["perda_sc_ha"] > 0


def test_fosforo_baixo_gera_hipotese_de_fosforo(base_scenario):
    pobre = replace(base_scenario, soil=replace(base_scenario.soil, phosphorus_ppm=3, potassium_ppm=200))
    d = diagnose(pobre)
    causas = [h["causa"] for h in d["hipoteses"]]
    assert any("fósforo" in c.lower() for c in causas)


def test_dado_default_marca_a_confirmar(base_scenario):
    """Sem clima real, a hipótese de déficit hídrico deve vir como 'a confirmar'."""
    d = diagnose(base_scenario, provenance={"clima": "estimado"})
    agua = next((h for h in d["hipoteses"] if h["fator"] == "Água"), None)
    if agua:
        assert agua["a_confirmar"] is True


def test_observacao_de_ferrugem_reforca_hipotese(base_scenario):
    obs = [Observation("ferrugem", "agronomo", "2026-01-15", {"severidade": "alta"}, 0.95)]
    base = diagnose(base_scenario)
    comobs = diagnose(base_scenario, observations=obs)
    pb = next((h["probabilidade"] for h in base["hipoteses"] if h["fator"] == "Doenças"), 0)
    pc = next((h["probabilidade"] for h in comobs["hipoteses"] if h["fator"] == "Doenças"), 0)
    assert pc >= pb
