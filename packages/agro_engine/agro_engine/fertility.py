"""Motor de Fertilidade — recomenda corretivos/adubação para O SEU solo.

Responde, com método rastreável (CQFS-RS/SC) e preços do catálogo, às perguntas:
"se eu esparramar calcário / adubar, vale a pena para o meu tipo de solo? quanto
preciso aplicar? qual o retorno? existe insumo mais rentável?".

Para cada recomendação calcula:
  - a **dose** pela fórmula oficial (ex.: calagem por saturação por bases),
  - o **custo** (dose × preço de referência do insumo, do catálogo),
  - o **impacto na produtividade** re-simulando o talhão com o solo corrigido (mesmo
    motor IPPD — então o impacto é coerente e auditável), e
  - o **valor líquido e o ROI**, permitindo **ranquear as alternativas** por rentabilidade.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from . import kb
from .decision import _profit_and_yield
from .models import Scenario, SoilProfile

_LIME_FALLBACK = {"label": "Calcário dolomítico", "price": 150.0, "prnt_pct": 80.0}
_MAP_FALLBACK = {"label": "MAP (11-52-00)", "price": 4899.0, "p2o5_pct": 52.0}
_KCL_FALLBACK = {"label": "KCl (0-0-60)", "price": 2880.0, "k2o_pct": 60.0}


@dataclass
class Recommendation:
    key: str
    label: str
    product: str
    dose: float                  # quantidade do produto por ha
    dose_unit: str
    investment_per_ha: float     # investimento total (à vista)
    residual_years: int          # anos de efeito residual
    annual_cost_per_ha: float    # custo anualizado (investimento / anos)
    delta_yield_sc_ha: float
    value_per_ha: float          # produtividade ganha × preço (por safra)
    net_per_ha: float            # valor − custo anualizado
    roi: float | None            # valor / custo anualizado
    rationale: str               # por que (com base na análise do solo + fonte)


def _yield_of(scenario: Scenario) -> float:
    return _profit_and_yield(scenario)[1]


def _result(key, label, product, dose, unit, investment, years, base_y, corrected, price, rationale) -> Recommendation:
    dy = round(_yield_of(corrected) - base_y, 2)
    value = round(dy * price, 0)            # ganho por safra
    annual = investment / max(1, years)     # investimento amortizado pelo residual
    net = round(value - annual, 0)
    roi = round(value / annual, 2) if annual > 0 else None
    return Recommendation(
        key, label, product, round(dose, 2), unit, round(investment, 0), years,
        round(annual, 0), dy, value, net, roi, rationale,
    )


def liming(scenario: Scenario) -> Recommendation | None:
    soil = scenario.soil
    target_v = kb.param("calagem.v_alvo_soja", 65.0)
    ph_thr = kb.param("calagem.indicada_se_ph_abaixo", 5.5)
    if soil.ph >= ph_thr and soil.base_saturation_pct >= target_v:
        return None  # solo já corrigido — calagem não indicada

    lime = kb.get_input("calcario_dolomitico") or _LIME_FALLBACK
    prnt = lime.get("prnt_pct", 80.0)
    nc100 = max(0.0, target_v - soil.base_saturation_pct) * soil.cec / 100.0  # t/ha PRNT 100%
    dose = nc100 * (100.0 / prnt)
    cost = dose * lime["price"]

    corrected = replace(
        scenario,
        soil=replace(soil, ph=max(soil.ph, 6.0), base_saturation_pct=max(soil.base_saturation_pct, target_v)),
    )
    rationale = (
        f"Solo com pH {soil.ph:.1f} e V {soil.base_saturation_pct:.0f}% (abaixo do alvo {target_v:.0f}% "
        f"para soja). Dose pela saturação por bases (CQFS-RS/SC), calcário PRNT {prnt:.0f}%."
    )
    years = int(kb.param("amortizacao.calagem_anos", 4))
    return _result("calagem", "Calagem (corrigir pH/V%)", lime.get("label", "Calcário"),
                   dose, "t/ha", cost, years, _yield_of(scenario), corrected, scenario.soybean_price_per_sc, rationale)


def phosphorus(scenario: Scenario) -> Recommendation | None:
    soil = scenario.soil
    suff = kb.param("nutricao.p_suficiente_ppm", 12.0)
    deficit = max(0.0, suff - soil.phosphorus_ppm)
    if deficit <= 0:
        return None

    p2o5 = deficit * kb.param("adubacao.p2o5_por_ppm_deficit", 12.0) + kb.param("adubacao.p2o5_manutencao", 60.0)
    src = kb.get_input("map") or _MAP_FALLBACK
    qty_t = p2o5 / 1000.0 / (src.get("p2o5_pct", 52.0) / 100.0)
    cost = qty_t * src["price"]

    corrected = replace(scenario, soil=replace(soil, phosphorus_ppm=max(soil.phosphorus_ppm, suff + 2)))
    rationale = (
        f"P do solo {soil.phosphorus_ppm:.0f} mg/dm³ abaixo da suficiência ({suff:.0f}). "
        f"Dose de P2O5 = construção + manutenção (CQFS); fonte {src.get('label', 'MAP')}."
    )
    years = int(kb.param("amortizacao.fosforo_anos", 2))
    return _result("fosforo", "Adubação fosfatada (corrigir P)", src.get("label", "MAP"),
                   qty_t * 1000.0, "kg/ha", cost, years, _yield_of(scenario), corrected, scenario.soybean_price_per_sc, rationale)


def potassium(scenario: Scenario) -> Recommendation | None:
    soil = scenario.soil
    suff = kb.param("nutricao.k_suficiente_ppm", 120.0)
    deficit = max(0.0, suff - soil.potassium_ppm)
    if deficit <= 0:
        return None

    k2o = deficit * kb.param("adubacao.k2o_por_ppm_deficit", 2.0) + kb.param("adubacao.k2o_manutencao", 60.0)
    src = kb.get_input("kcl") or _KCL_FALLBACK
    qty_t = k2o / 1000.0 / (src.get("k2o_pct", 60.0) / 100.0)
    cost = qty_t * src["price"]

    corrected = replace(scenario, soil=replace(soil, potassium_ppm=max(soil.potassium_ppm, suff + 5)))
    rationale = (
        f"K do solo {soil.potassium_ppm:.0f} mg/dm³ abaixo da suficiência ({suff:.0f}). "
        f"Dose de K2O = reposição + manutenção (CQFS); fonte {src.get('label', 'KCl')}."
    )
    years = int(kb.param("amortizacao.potassio_anos", 1))
    return _result("potassio", "Adubação potássica (corrigir K)", src.get("label", "KCl"),
                   qty_t * 1000.0, "kg/ha", cost, years, _yield_of(scenario), corrected, scenario.soybean_price_per_sc, rationale)


def recommend_amendments(scenario: Scenario) -> list[Recommendation]:
    """Avalia calagem, fósforo e potássio para o solo do talhão e ranqueia por retorno.

    O ranking responde diretamente "qual investimento é mais rentável para o meu solo".
    """
    recs = [f(scenario) for f in (liming, phosphorus, potassium)]
    recs = [r for r in recs if r is not None]
    recs.sort(key=lambda r: r.net_per_ha, reverse=True)
    return recs
