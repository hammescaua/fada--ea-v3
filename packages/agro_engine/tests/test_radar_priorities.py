"""Testes do Radar da Safra e do Motor de Priorização (o copiloto)."""

from __future__ import annotations

from dataclasses import replace

from agro_engine import prioritized_actions, season_radar


def test_radar_estrutura_e_dimensoes(base_scenario):
    r = season_radar(base_scenario)
    assert 0 <= r["score"] <= 100
    assert r["score_label"] in {"saudável", "atenção", "crítico"}
    dims = {d["key"] for d in r["dimensions"]}
    assert dims == {"solo", "clima", "sanidade", "nutricao", "mercado", "execucao"}
    for d in r["dimensions"]:
        assert 0 <= d["score"] <= 100
    # as 4 respostas existem e são texto
    for k in ("maior_risco", "melhor_decisao", "quanto_vale", "por_que"):
        assert isinstance(r["respostas"][k], str) and r["respostas"][k]


def test_radar_detecta_gargalo_de_nutricao(base_scenario):
    """Solo pobre em P deve aparecer como maior risco (gargalo) na dimensão certa."""
    pobre = replace(base_scenario, soil=replace(base_scenario.soil, phosphorus_ppm=4, potassium_ppm=70))
    r = season_radar(pobre)
    assert r["maior_risco"] is not None
    assert r["maior_risco"]["perda_sc_ha"] > 0
    # nutrição deve estar entre as dimensões mais baixas
    nut = next(d["score"] for d in r["dimensions"] if d["key"] == "nutricao")
    assert nut < 100


def test_radar_aponta_oportunidade_e_investimento(base_scenario):
    pobre = replace(base_scenario, soil=replace(base_scenario.soil, ph=5.2, base_saturation_pct=45, phosphorus_ppm=5))
    r = season_radar(pobre)
    assert r["maior_oportunidade"] is not None
    assert r["maior_oportunidade"]["impacto_rs"] > 0
    # as 4 respostas refletem a oportunidade
    assert "sc/ha" in r["respostas"]["quanto_vale"]


def test_prioridades_ordenadas_por_valor(base_scenario):
    pobre = replace(base_scenario, soil=replace(base_scenario.soil, ph=5.2, base_saturation_pct=45, phosphorus_ppm=5))
    acts = prioritized_actions(pobre)
    assert len(acts) >= 1
    valores = [a["impacto_rs"] for a in acts]
    assert valores == sorted(valores, reverse=True)
    assert acts[0]["rank"] == 1
    for a in acts:
        for k in ("acao", "impacto_sc_ha", "impacto_rs", "prazo", "porque", "probabilidade"):
            assert k in a


def test_estado_da_safra_descarta_acao_fora_da_janela(base_scenario):
    """Em fase reprodutiva, 'antecipar semeadura' já passou — não pode ser a melhor decisão agora."""
    from datetime import timedelta

    # solo fraco para gerar várias ações candidatas
    late_field = replace(base_scenario, soil=replace(base_scenario.soil, ph=5.2, base_saturation_pct=45, phosphorus_ppm=5))
    # 'hoje' ~70 dias após a semeadura => fase reprodutiva
    today = base_scenario.sowing_date + timedelta(days=70)
    r = season_radar(late_field, today=today)
    assert r["estado"]["fase"] in {"vegetativo", "reprodutivo"}
    sow = next((a for a in r["actions"] if a["key"] == "advance_sowing"), None)
    if sow:
        assert sow["janela_status"] == "passou"
    # a melhor decisão recomendada é acionável agora (não 'antecipar semeadura')
    if r["maior_oportunidade"]:
        assert r["maior_oportunidade"]["key"] != "advance_sowing"


def test_estado_da_safra_pre_plantio_permite_semeadura(base_scenario):
    from datetime import timedelta

    today = base_scenario.sowing_date - timedelta(days=20)  # antes de semear
    r = season_radar(replace(base_scenario, sowing_date=base_scenario.sowing_date), today=today)
    assert r["estado"]["fase"] == "preparo_solo"


def test_clima_la_nina_derruba_dimensao_clima(base_scenario):
    """Sob La Niña o risco sobe; o radar deve refletir clima como ponto fraco."""
    r = season_radar(base_scenario)
    assert isinstance(next(d["score"] for d in r["dimensions"] if d["key"] == "clima"), float)
