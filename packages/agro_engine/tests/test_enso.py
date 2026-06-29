"""Testes do driver ENSO (El Niño/La Niña) — matriz climática nº1 do NO-RS."""

from __future__ import annotations

from dataclasses import replace

from agro_engine import run_montecarlo


def test_la_nina_aumenta_risco_e_reduz_produtividade(base_scenario):
    neutro = run_montecarlo(replace(base_scenario, enso="neutro"), n=600, seed=1)
    la_nina = run_montecarlo(replace(base_scenario, enso="la_nina"), n=600, seed=1)
    # La Niña (seca) derruba a produtividade mediana e eleva a probabilidade de prejuízo
    assert la_nina["yield"]["p50"] < neutro["yield"]["p50"]
    assert la_nina["probabilities"]["loss"] >= neutro["probabilities"]["loss"]
    assert la_nina["enso"] == "la_nina"


def test_el_nino_melhora_em_relacao_a_neutro(base_scenario):
    neutro = run_montecarlo(replace(base_scenario, enso="neutro"), n=600, seed=2)
    el_nino = run_montecarlo(replace(base_scenario, enso="el_nino"), n=600, seed=2)
    assert el_nino["yield"]["p50"] >= neutro["yield"]["p50"]
