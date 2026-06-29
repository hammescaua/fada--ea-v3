"""Testes do Motor de Plano de Safra ao Vivo (passo-a-passo por fase)."""

from __future__ import annotations

from datetime import date

from agro_engine import crop_plan


def test_plano_tem_cinco_fases_em_ordem(base_scenario):
    p = crop_plan(base_scenario)
    keys = [f["key"] for f in p["phases"]]
    assert keys == ["preparo_solo", "semeadura", "vegetativo", "reprodutivo", "colheita"]
    for f in p["phases"]:
        assert f["start"] <= f["end"]
        assert f["status"] in {"concluida", "em_andamento", "futura"}


def test_janelas_encadeiam_ate_a_colheita(base_scenario):
    p = crop_plan(base_scenario)
    assert p["sowing_date"] < p["harvest_date"]
    assert p["cycle_days"] > 100
    # a fase reprodutiva deve carregar o(s) fungicida(s) planejado(s)
    repro = next(f for f in p["phases"] if f["key"] == "reprodutivo")
    fungis = [m for m in repro["manejos"] if m["kind"] == "fungicida" and m["planned"]]
    assert len(fungis) >= 1
    assert all(m["impact_sc_ha"] is not None for m in fungis)


def test_status_relativo_a_hoje(base_scenario):
    # 'hoje' logo após a semeadura: preparo concluído, semeadura em andamento
    today = date.fromisoformat(base_scenario.sowing_date.isoformat())
    p = crop_plan(base_scenario, today=today)
    by_key = {f["key"]: f for f in p["phases"]}
    assert by_key["preparo_solo"]["status"] == "concluida"
    assert by_key["semeadura"]["status"] == "em_andamento"
    assert by_key["colheita"]["status"] == "futura"
    assert 0 <= p["progress_pct"] <= 100


def test_cada_fase_explica_de_onde_vem_o_dado(base_scenario):
    p = crop_plan(base_scenario)
    for f in p["phases"]:
        assert len(f["data_basis"]) >= 1
        for d in f["data_basis"]:
            assert "how_to_improve" in d and d["how_to_improve"]


def test_manejos_recomendados_faltantes_aparecem(base_scenario):
    """Sem fungicida no plano, a fase reprodutiva recomenda incluí-lo (com referência)."""
    from dataclasses import replace

    no_fungi = replace(
        base_scenario,
        operations=[o for o in base_scenario.operations if o.kind != "fungicida"],
    )
    p = crop_plan(no_fungi)
    repro = next(f for f in p["phases"] if f["key"] == "reprodutivo")
    rec = [m for m in repro["manejos"] if m["kind"] == "fungicida" and not m["planned"]]
    assert len(rec) >= 1
    assert rec[0]["funcao"]
