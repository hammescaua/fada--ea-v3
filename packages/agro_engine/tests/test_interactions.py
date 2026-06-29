"""Testes do Motor de Interações (consequência conectada na linha do tempo)."""

from __future__ import annotations

from agro_engine import Observation, interactions_report
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


def test_report_resumo():
    obs = [
        _o("aplicacao", "nota_fiscal", "2026-01-10", {}),
        _o("chuva", "api_clima", "2026-01-11", {"mm": 25}),
    ]
    rep = interactions_report(obs)
    assert rep["n_interactions"] >= 1
    assert isinstance(rep["resumo"], str) and rep["resumo"]
