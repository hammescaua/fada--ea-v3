"""Testes do Knowledge Engine (calibração por talhão + feature engineering)."""

from __future__ import annotations

from agro_engine import (
    SeasonRecord,
    apply_correction,
    calibrate,
    season_features,
    simulate,
)


def test_empty_history_is_identity():
    cal = calibrate([])
    assert cal.n_seasons == 0
    assert cal.bias_sc_ha == 0.0
    assert cal.confidence == 0.0
    corrected, unc = apply_correction(80.0, 6.0, cal)
    assert corrected == 80.0 and unc == 6.0


def test_consistent_underprediction_learns_positive_bias():
    # o motor sempre previu 5 sc/ha a menos que o realizado
    recs = [SeasonRecord(f"202{i}", 80.0, 85.0) for i in range(5)]
    cal = calibrate(recs)
    assert cal.raw_bias_sc_ha == 5.0
    assert 0 < cal.bias_sc_ha < 5.0  # encolhido, mas positivo
    assert cal.mae_after < cal.mae_before  # correção reduz o erro


def test_confidence_grows_with_more_seasons():
    few = calibrate([SeasonRecord("2025", 80, 84)])
    many = calibrate([SeasonRecord(f"20{i}", 80, 84) for i in range(8)])
    assert many.confidence > few.confidence
    # com mais safras, a correção converge para o viés bruto
    assert abs(many.bias_sc_ha - many.raw_bias_sc_ha) < abs(few.bias_sc_ha - few.raw_bias_sc_ha)


def test_apply_correction_moves_toward_actual_and_shrinks_uncertainty():
    recs = [SeasonRecord(f"20{i}", 70, 76) for i in range(6)]
    cal = calibrate(recs)
    corrected, unc = apply_correction(70.0, 8.0, cal)
    assert corrected > 70.0          # puxa para cima (talhão rende mais que o previsto)
    assert unc < 8.0                 # incerteza diminui com o aprendizado


def test_season_features_extracts_attributes(base_scenario):
    sim = simulate(base_scenario)
    feats = season_features(base_scenario, sim)
    for key in ("sowing_deviation_days", "water_overall_stress", "soil_ph", "n_fungicidas"):
        assert key in feats
    assert feats["n_fungicidas"] == 2
