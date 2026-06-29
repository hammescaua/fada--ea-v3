"""Testes da camada de evidências: confiança, corroboração, personalidade, contrafactual."""

from __future__ import annotations

from agro_engine import (
    FieldSeason,
    Observation,
    confidence_for,
    corroborate,
    data_quality,
    personality,
    run_counterfactuals,
)


# --- Reality Engine: confiança por fonte e corroboração ----------------------
def test_confianca_por_fonte_e_corroboracao():
    assert confidence_for("manual") < confidence_for("api_clima") < confidence_for("drone")
    # corroboração eleva a confiança (reduz a incerteza pela metade por fonte extra)
    base = confidence_for("api_clima", 0)
    corr = confidence_for("api_clima", 1)
    assert corr > base
    assert corr == round(1 - (1 - base) * 0.5, 3)


def test_corroborate_eleva_quando_fontes_independentes_concordam():
    obs = [
        Observation(kind="chuva", source="api_clima", observed_at="2025-11-03", value={"mm": 21}),
        Observation(kind="chuva", source="estacao_inmet", observed_at="2025-11-03", value={"mm": 20}),
    ]
    out = corroborate(obs)
    assert all(o.confidence > confidence_for("api_clima", 0) for o in out)


def test_data_quality_por_grupo():
    obs = [
        Observation("colheita", "monitor_colheita", "2026-04-10", {"sc_ha": 58}, confidence=0.96),
        Observation("chuva", "api_clima", "2025-12-01", {"mm": 10}, confidence=0.9),
    ]
    scores = data_quality(obs)
    assert scores["produtividade"] > 0
    assert scores["mercado"] == 0.0  # sem evidência -> nota zero (honesto)


# --- Personalidade do talhão --------------------------------------------------
def _season(year, pred, actual, **feat):
    base = {"soil_p_ppm": 8.0, "water_overall_stress": 0.2, "sowing_deviation_days": 0,
            "maturity_group": 5.5, "base_potential_sc_ha": 95}
    base.update(feat)
    return FieldSeason(year, pred, actual, base)


def test_personalidade_cresce_com_historico():
    poucos = personality([_season("2024/25", 80, 84)])
    muitos = personality([_season(f"y{i}", 80, 84) for i in range(5)])
    assert muitos["knowledge_pct"] > poucos["knowledge_pct"]
    assert muitos["traits"]


def test_personalidade_detecta_resposta_ao_fosforo():
    seasons = [_season(f"y{i}", 80, 85, soil_p_ppm=4.0) for i in range(3)]
    p = personality(seasons)
    resp = next(t for t in p["traits"] if t["key"] == "resposta_fosforo")
    assert resp["level"] in {"responsivo", "muito responsivo"}


def test_personalidade_estabilidade_alta_quando_constante():
    seasons = [_season(f"y{i}", 80, 84) for i in range(4)]
    p = personality(seasons)
    est = next(t for t in p["traits"] if t["key"] == "estabilidade_produtiva")
    assert est["level"] == "alta"


def test_recorrencia_de_lavagem_vira_traco():
    """Lavagem recorrente na história do talhão vira traço aprendido com recomendação."""
    obs = []
    for d in ("2024-01-10", "2025-01-12"):
        obs.append(Observation("aplicacao", "nota_fiscal", d, {"tipo": "fungicida"}, 0.9))
        rain_day = d[:-2] + str(int(d[-2:]) + 1)
        obs.append(Observation("chuva", "api_clima", rain_day, {"mm": 25}, 0.9))
    p = personality([_season("2024/25", 80, 82)], obs)
    rec = next((t for t in p["traits"] if t["key"] == "recorrencia_lavagem_pos_aplicacao"), None)
    assert rec is not None
    assert rec["level"] == "recorrente"
    assert "rainfast" in rec["basis"].lower() or "resistência à chuva" in rec["basis"].lower()


# --- Counterfactual Engine ----------------------------------------------------
def test_contrafactual_remover_fungicida_reduz(base_scenario):
    out = run_counterfactuals(base_scenario)
    keys = [c["key"] for c in out["counterfactuals"]]
    assert "sem_fungicida" in keys
    semf = next(c for c in out["counterfactuals"] if c["key"] == "sem_fungicida")
    # sem fungicida, num cenário de pressão alta, a produtividade cai
    assert semf["delta_yield_sc_ha"] <= 0
    assert semf["narrative"]


def test_contrafactual_ordenado_por_impacto(base_scenario):
    out = run_counterfactuals(base_scenario)
    impacts = [abs(c["delta_profit_per_ha"]) for c in out["counterfactuals"]]
    assert impacts == sorted(impacts, reverse=True)
