"""Testes do Motor de Decisão (recomendações priorizadas por retorno)."""

from __future__ import annotations

from datetime import date

from agro_engine import recommend_decisions

from conftest import make_weather


def test_recommendations_sorted_by_profit(base_scenario):
    recs = recommend_decisions(base_scenario, n_prob=120, seed=1)
    assert len(recs) >= 1
    profits = [r.delta_profit_per_ha for r in recs]
    assert profits == sorted(profits, reverse=True)
    for r in recs:
        assert 0.0 <= r.probability_positive <= 1.0


def test_low_phosphorus_triggers_correction(base_scenario):
    base_scenario.soil.phosphorus_ppm = 5.0
    recs = recommend_decisions(base_scenario, n_prob=120, seed=2)
    keys = {r.key for r in recs}
    assert "correct_phosphorus" in keys
    p = next(r for r in recs if r.key == "correct_phosphorus")
    assert p.delta_yield_sc_ha > 0  # corrigir P aumenta produtividade


def test_sufficient_soil_does_not_offer_phosphorus(base_scenario):
    base_scenario.soil.phosphorus_ppm = 20.0
    recs = recommend_decisions(base_scenario, n_prob=80, seed=3)
    assert "correct_phosphorus" not in {r.key for r in recs}


def test_late_sowing_offers_advance(base_scenario):
    base_scenario.sowing_date = date(2026, 1, 5)
    base_scenario.weather = make_weather(base_scenario.sowing_date, 170)
    recs = recommend_decisions(base_scenario, n_prob=80, seed=4)
    assert "advance_sowing" in {r.key for r in recs}


def test_action_roi_present_for_costly_actions(base_scenario):
    base_scenario.soil.phosphorus_ppm = 5.0
    recs = recommend_decisions(base_scenario, n_prob=80, seed=5)
    p = next(r for r in recs if r.key == "correct_phosphorus")
    assert p.action_roi is not None
