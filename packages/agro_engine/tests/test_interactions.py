"""Testes do Motor de Interações (consequência conectada na linha do tempo)."""

from __future__ import annotations

from dataclasses import replace

from agro_engine import Observation, apply_interactions, interactions_report, simulate
from agro_engine.interactions import detect_interactions


def _o(kind, source, day, value, conf=0.9):
    return Observation(kind=kind, source=source, observed_at=day, value=value, confidence=conf)


def test_lavagem_pos_aplicacao_detectada():
    obs = [
        _o("aplicacao", "nota_fiscal", "2026-01-10", {"tipo": "fungicida"}),
        _o("chuva", "api_clima", "2026-01-11", {"mm": 22}),
    ]
    items = detect_interactions(obs)
    keys = [i.rule for i in items]
    assert "lavagem_pos_aplicacao" in keys
    lav = next(i for i in items if i.rule == "lavagem_pos_aplicacao")
    assert lav.positive is False
    assert lav.efficacy_loss and lav.efficacy_loss > 0
    assert "22 mm" in lav.description
    assert lav.source


def test_chuva_fraca_nao_dispara_lavagem():
    obs = [
        _o("aplicacao", "nota_fiscal", "2026-01-10", {}),
        _o("chuva", "api_clima", "2026-01-11", {"mm": 3}),
    ]
    assert all(i.rule != "lavagem_pos_aplicacao" for i in detect_interactions(obs))


def test_ferrugem_controlada_e_positiva():
    obs = [
        _o("aplicacao", "nota_fiscal", "2026-01-10", {"tipo": "fungicida"}),
        _o("ferrugem", "agronomo", "2026-01-20", {"severidade": "baixa"}, conf=0.95),
    ]
    items = detect_interactions(obs)
    fc = next(i for i in items if i.rule == "ferrugem_controlada")
    assert fc.positive is True


def test_ferrugem_sem_protecao_alerta():
    obs = [_o("ferrugem", "agronomo", "2026-01-20", {"severidade": "alta"})]
    items = detect_interactions(obs)
    assert any(i.rule == "ferrugem_sem_protecao" and not i.positive for i in items)


def test_ferrugem_com_aplicacao_previa_nao_alerta():
    obs = [
        _o("aplicacao", "nota_fiscal", "2026-01-12", {"tipo": "fungicida"}),
        _o("ferrugem", "agronomo", "2026-01-20", {"severidade": "alta"}),
    ]
    # houve aplicação na janela anterior -> a regra de 'sem proteção' não dispara
    assert all(i.rule != "ferrugem_sem_protecao" for i in detect_interactions(obs))


def test_confianca_herda_das_evidencias():
    obs = [
        _o("aplicacao", "manual", "2026-01-10", {}, conf=0.5),
        _o("chuva", "api_clima", "2026-01-11", {"mm": 30}, conf=0.9),
    ]
    lav = next(i for i in detect_interactions(obs) if i.rule == "lavagem_pos_aplicacao")
    assert lav.confidence == 0.5  # limitada pela evidência mais fraca


def test_lavagem_reduz_qualidade_e_produtividade(base_scenario):
    """A consequência realimenta o NÚMERO: fungicida lavado -> menos proteção -> menos sc/ha."""
    fung = next(o for o in base_scenario.operations if o.kind == "fungicida")
    obs = [
        Observation("aplicacao", "nota_fiscal", fung.op_date.isoformat(), {"tipo": "fungicida"}, 0.95),
        Observation("chuva", "api_clima", (fung.op_date.replace(day=fung.op_date.day + 1)).isoformat(), {"mm": 25}, 0.9),
    ]
    adjusted, adj = apply_interactions(base_scenario, obs)
    assert any(a["factor"] == "Doenças" for a in adj)
    # a aplicação lavada (a casada com o gatilho) teve a qualidade efetiva reduzida
    q_before = min(o.quality for o in base_scenario.operations if o.kind == "fungicida")
    q_after = min(o.quality for o in adjusted.operations if o.kind == "fungicida")
    assert q_after < q_before
    # e isso derruba a produtividade simulada
    assert simulate(adjusted).yield_result.expected_sc_ha < simulate(base_scenario).yield_result.expected_sc_ha


def test_estande_observado_sobrepoe_populacao(base_scenario):
    obs = [Observation("emergencia", "agronomo", "2025-11-20", {"plantas_mil": 240}, 0.95)]
    adjusted, adj = apply_interactions(replace(base_scenario, population_k_per_ha=300), obs)
    assert adjusted.population_k_per_ha == 240
    assert any(a["factor"] == "População" for a in adj)


def test_ajuste_escala_pela_confianca(base_scenario):
    """Evidência fraca move menos o número do que evidência forte."""
    fung = next(o for o in base_scenario.operations if o.kind == "fungicida")
    d_rain = fung.op_date.replace(day=fung.op_date.day + 1).isoformat()
    forte = [Observation("aplicacao", "nota_fiscal", fung.op_date.isoformat(), {"tipo": "fungicida"}, 0.95),
             Observation("chuva", "api_clima", d_rain, {"mm": 25}, 0.95)]
    fraca = [Observation("aplicacao", "manual", fung.op_date.isoformat(), {"tipo": "fungicida"}, 0.5),
             Observation("chuva", "produtor", d_rain, {"mm": 25}, 0.5)]
    qf = min(o.quality for o in apply_interactions(base_scenario, forte)[0].operations if o.kind == "fungicida")
    qw = min(o.quality for o in apply_interactions(base_scenario, fraca)[0].operations if o.kind == "fungicida")
    assert qf < qw  # confiança alta reduz mais a qualidade efetiva


def test_report_resumo():
    obs = [
        _o("aplicacao", "nota_fiscal", "2026-01-10", {}),
        _o("chuva", "api_clima", "2026-01-11", {"mm": 25}),
    ]
    rep = interactions_report(obs)
    assert rep["n_interactions"] >= 1
    assert isinstance(rep["resumo"], str) and rep["resumo"]
