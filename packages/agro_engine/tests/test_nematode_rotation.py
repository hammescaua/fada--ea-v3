"""Testes dos drivers Nematoides e Rotação (matrizes do NO-RS)."""

from __future__ import annotations

from dataclasses import replace

from agro_engine import simulate


def _yield(scn):
    return simulate(scn).yield_result.expected_sc_ha


def test_pressao_de_nematoides_reduz_produtividade(base_scenario):
    sem = replace(base_scenario, nematode_pressure="nenhuma")
    alta = replace(base_scenario, nematode_pressure="alta")
    assert _yield(alta) < _yield(sem)
    labels = [c.label for c in simulate(alta).yield_result.contributions]
    assert "Nematoides" in labels


def test_cultivar_resistente_atenua_perda(base_scenario):
    suscet = replace(base_scenario, nematode_pressure="alta",
                     cultivar=replace(base_scenario.cultivar, nematode_tolerance=0.1))
    resist = replace(base_scenario, nematode_pressure="alta",
                     cultivar=replace(base_scenario.cultivar, nematode_tolerance=0.9))
    assert _yield(resist) > _yield(suscet)


def test_rotacao_suprime_nematoide_e_da_bonus(base_scenario):
    soja_soja = replace(base_scenario, nematode_pressure="alta", previous_crop="soja")
    apos_milho = replace(base_scenario, nematode_pressure="alta", previous_crop="milho")
    # rotação após milho suprime o nematoide e ainda traz bônus de palhada
    assert _yield(apos_milho) > _yield(soja_soja)


def test_sem_pressao_nematoide_neutro(base_scenario):
    scn = replace(base_scenario, nematode_pressure="nenhuma")
    nem = next(c for c in simulate(scn).yield_result.contributions if c.label == "Nematoides")
    assert nem.delta_sc_ha == 0.0
