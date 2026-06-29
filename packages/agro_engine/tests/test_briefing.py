"""Testes do Motor de Resumo da Safra (Briefing) — a resposta única do gêmeo."""

from __future__ import annotations

from dataclasses import replace

from agro_engine import season_briefing


def test_briefing_compoe_resposta_unica(base_scenario):
    b = season_briefing(base_scenario)
    # campos essenciais do veredito
    for key in (
        "status", "expected_sc_ha", "profit_per_ha", "roi", "prob_loss",
        "sowing_position", "data_confidence", "actions", "veredito",
    ):
        assert key in b
    assert b["municipality"] == "Santo Ângelo"
    assert b["expected_sc_ha"] > 0
    assert isinstance(b["veredito"], str) and len(b["veredito"]) > 40
    assert b["status"] in {"saudavel", "atencao", "critico"}


def test_briefing_coerente_com_simulate(base_scenario):
    """O briefing não pode inventar números: produtividade e lucro batem com simulate."""
    from agro_engine import simulate

    sim = simulate(base_scenario)
    b = season_briefing(base_scenario)
    assert abs(b["expected_sc_ha"] - round(sim.yield_result.expected_sc_ha, 1)) < 0.05
    assert abs(b["profit_per_ha"] - round(sim.economics.profit_per_ha, 0)) < 1.0


def test_briefing_acoes_ordenadas_e_positivas(base_scenario):
    """As ações recomendadas devem aumentar o lucro e vir ordenadas por Δlucro."""
    # cenário com solo pobre gera ações de fertilidade rentáveis
    poor_soil = replace(base_scenario.soil, ph=5.2, base_saturation_pct=45, phosphorus_ppm=5)
    scn = replace(base_scenario, soil=poor_soil)
    b = season_briefing(scn)
    actions = b["actions"]
    assert len(actions) >= 1
    deltas = [a["delta_profit_per_ha"] for a in actions]
    assert all(d > 0 for d in deltas)
    assert deltas == sorted(deltas, reverse=True)
    assert actions[0]["rank"] == 1


def test_briefing_status_critico_quando_prejuizo(base_scenario):
    """Preço de venda muito baixo => prejuízo => status crítico + alerta."""
    scn = replace(base_scenario, soybean_price_per_sc=40.0)
    b = season_briefing(scn)
    assert b["profit_per_ha"] <= 0
    assert b["status"] == "critico"
    assert any("negativo" in a.lower() or "prejuízo" in a.lower() for a in b["alertas"])


def test_briefing_marca_fora_da_janela(base_scenario):
    """Semeadura muito tardia deve aparecer como fora da janela com alerta."""
    late = replace(base_scenario, sowing_date=base_scenario.sowing_date.replace(month=2, day=1))
    b = season_briefing(late)
    assert b["sowing_position"] in {"depois_da_janela", "antes_da_janela"}
