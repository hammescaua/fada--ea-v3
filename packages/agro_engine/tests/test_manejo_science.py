"""Testes do Motor de Evidência de Manejo (base científica personalizada)."""

from __future__ import annotations

from dataclasses import replace

from agro_engine import crop_plan, manejo_evidence


def test_evidencia_traz_mecanismo_coeficiente_e_fonte(base_scenario):
    ev = manejo_evidence(base_scenario, "fungicida")
    assert ev is not None
    assert ev["alvo"] == "doencas"
    assert ev["mecanismo"]
    assert ev["coeficiente"]["value"] is not None
    assert ev["coeficiente"]["source"]  # rastreável a fonte
    assert ev["fonte"]
    assert ev["leitura_talhao"]


def test_leitura_personaliza_por_tolerancia_da_cultivar(base_scenario):
    tol_baixa = replace(base_scenario, cultivar=replace(base_scenario.cultivar, disease_tolerance=0.2))
    tol_alta = replace(base_scenario, cultivar=replace(base_scenario.cultivar, disease_tolerance=0.8))
    a = manejo_evidence(tol_baixa, "fungicida")["leitura_talhao"]
    b = manejo_evidence(tol_alta, "fungicida")["leitura_talhao"]
    assert a != b  # a leitura muda com o perfil da cultivar
    assert "20%" in a and "80%" in b


def test_nutricao_reflete_solo_do_talhao(base_scenario):
    pobre = replace(base_scenario, soil=replace(base_scenario.soil, phosphorus_ppm=5))
    rico = replace(base_scenario, soil=replace(base_scenario.soil, phosphorus_ppm=20))
    assert "ABAIXO" in manejo_evidence(pobre, "adubacao_p")["leitura_talhao"]
    assert "suficiente" in manejo_evidence(rico, "adubacao_p")["leitura_talhao"]


def test_manejo_desconhecido_retorna_none(base_scenario):
    assert manejo_evidence(base_scenario, "inexistente") is None


def test_crop_plan_anexa_evidencia_aos_manejos(base_scenario):
    p = crop_plan(base_scenario)
    repro = next(f for f in p["phases"] if f["key"] == "reprodutivo")
    fungi = next(m for m in repro["manejos"] if m["kind"] == "fungicida")
    assert fungi["evidencia"] is not None
    assert fungi["evidencia"]["coeficiente"]["source"]
