"""Testes do Motor de Acurácia por Talhão (de onde vem cada dado / como melhorar)."""

from __future__ import annotations

from agro_engine import accuracy_report


def test_relatorio_estrutura_e_indice(base_scenario):
    r = accuracy_report(base_scenario)
    assert 0.0 <= r["precision_index"] <= 1.0
    assert r["precision_label"] in {"alta", "média", "baixa"}
    assert len(r["variables"]) >= 5
    for v in r["variables"]:
        for key in ("group", "label", "current_label", "quality", "is_local", "how_to_improve", "source"):
            assert key in v
    assert isinstance(r["resumo"], str) and len(r["resumo"]) > 30


def test_dado_real_eleva_precisao(base_scenario):
    """Informar solo e clima reais deve aumentar o índice de precisão."""
    baixa = accuracy_report(base_scenario, {"solo": "estimado", "clima": "estimado"})
    alta = accuracy_report(base_scenario, {"solo": "real", "clima": "climatologia_real"})
    assert alta["precision_index"] > baixa["precision_index"]


def test_solo_real_marca_local_e_zera_alavancagem(base_scenario):
    r = accuracy_report(base_scenario, {"solo": "real"})
    solo = next(v for v in r["variables"] if v["group"] == "solo")
    assert solo["is_local"] is True
    assert solo["leverage_sc_ha"] == 0.0
    assert solo["current_tier"] == "analise_talhao"


def test_clima_safra_corrente_entre_climatologia_e_real(base_scenario):
    """A escala do clima reflete o quanto da safra é conhecido."""
    hist = accuracy_report(base_scenario, {"clima": "climatologia_real"})
    corrente = accuracy_report(base_scenario, {"clima": "safra_corrente"})
    realizada = accuracy_report(base_scenario, {"clima": "safra_realizada"})
    qh = next(v["quality"] for v in hist["variables"] if v["group"] == "clima")
    qc = next(v["quality"] for v in corrente["variables"] if v["group"] == "clima")
    qr = next(v["quality"] for v in realizada["variables"] if v["group"] == "clima")
    assert qh < qc < qr


def test_alavancagem_clima_encolhe_com_safra_conhecida(base_scenario):
    """Safra já conhecida não tem incerteza climática a 'medir' — alavancagem cai."""
    full = accuracy_report(base_scenario, {"clima": "safra_corrente"}, climate_known_fraction=0.0)
    quase = accuracy_report(base_scenario, {"clima": "safra_corrente"}, climate_known_fraction=1.0)
    lev_full = next(v["leverage_sc_ha"] for v in full["variables"] if v["group"] == "clima")
    lev_quase = next(v["leverage_sc_ha"] for v in quase["variables"] if v["group"] == "clima")
    assert lev_full > lev_quase
    assert lev_quase == 0.0


def test_melhorias_priorizadas_por_alavancagem(base_scenario):
    r = accuracy_report(base_scenario, {})
    imps = r["top_improvements"]
    levs = [i["leverage_sc_ha"] for i in imps]
    assert levs == sorted(levs, reverse=True)
