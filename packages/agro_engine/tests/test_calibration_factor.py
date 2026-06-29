"""Testes: calibração do talhão como fator transparente da cascata IPPD."""

from __future__ import annotations

from dataclasses import replace

from agro_engine import infer_provenance, simulate
from agro_engine.knowledge import SeasonRecord, calibrate


def test_calibracao_aparece_no_waterfall_e_corrige_produtividade(base_scenario):
    base = simulate(base_scenario)
    cal = replace(
        base_scenario,
        calibration_bias_sc_ha=5.0,
        calibration_confidence=0.5,
        calibration_seasons=3,
    )
    out = simulate(cal)
    labels = [c.label for c in out.yield_result.contributions]
    assert "Calibração do talhão" in labels
    # a correção aditiva move a produtividade na direção certa
    assert out.yield_result.expected_sc_ha > base.yield_result.expected_sc_ha
    delta = out.yield_result.expected_sc_ha - base.yield_result.expected_sc_ha
    assert abs(delta - 5.0) < 0.2


def test_calibracao_encurta_incerteza(base_scenario):
    base = simulate(base_scenario)
    cal = simulate(replace(base_scenario, calibration_bias_sc_ha=3.0, calibration_confidence=0.6, calibration_seasons=4))
    assert cal.yield_result.uncertainty_sc_ha < base.yield_result.uncertainty_sc_ha


def test_sem_historico_nao_altera_nada(base_scenario):
    base = simulate(base_scenario)
    same = simulate(replace(base_scenario, calibration_bias_sc_ha=0.0, calibration_seasons=0))
    assert same.yield_result.expected_sc_ha == base.yield_result.expected_sc_ha
    assert "Calibração do talhão" not in [c.label for c in same.yield_result.contributions]


def test_calibracao_de_historico_real(base_scenario):
    """Fecha o loop: histórico previsto-vs-real -> bias -> previsão corrigida."""
    records = [
        SeasonRecord("2023/24", 80.0, 86.0),
        SeasonRecord("2024/25", 78.0, 85.0),
    ]
    cal = calibrate(records)
    assert cal.bias_sc_ha > 0  # o talhão colhe mais do que o motor previa
    scn = replace(
        base_scenario,
        calibration_bias_sc_ha=cal.bias_sc_ha,
        calibration_confidence=cal.confidence,
        calibration_seasons=cal.n_seasons,
    )
    out = simulate(scn)
    assert "Calibração do talhão" in [c.label for c in out.yield_result.contributions]


def test_infer_provenance_reconhece_dados_reais(base_scenario):
    prov = infer_provenance(base_scenario)
    # cultivar não-genérica informada => real
    assert prov["cultivar"] == "real"
    # operações sem produto preenchido => programa apenas planejado
    assert prov["manejo"] in {"parcial", "real"}
    # cultivar genérica => estimado
    generic = replace(base_scenario, cultivar=replace(base_scenario.cultivar, name="Genérica RR 5.5"))
    assert infer_provenance(generic)["cultivar"] == "estimado"
