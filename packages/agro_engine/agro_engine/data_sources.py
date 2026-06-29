"""Motor de Acurácia por Talhão — de onde vem cada dado e como torná-lo mais preciso.

A preocupação central do produto: *quão verídica é esta estimativa para ESTE talhão,
nesta localidade?* Este motor responde, variável por variável:
  - **qual fonte está em uso** hoje (do mais local/real ao mais genérico),
  - **quão específica** ela é (ponto exato × regional),
  - **o quanto a estimativa pode mudar** se aquele dado for o real (alavancagem, vinda do
    motor de veracidade por perturbação), e
  - **o que fazer** para deixar mais preciso para aquele talhão/local.

A ficha de fontes é externa e auditável (``data/knowledge/data_sources.json``); a
alavancagem é calculada pelo próprio modelo. Nada de número mágico: a acurácia é
explicada e rastreável.
"""

from __future__ import annotations

from . import kb
from .models import Scenario
from .provenance import (
    GROUP_WEIGHT,
    _climate_leverage,
    _cultivar_leverage,
    _population_leverage,
    _soil_leverage,
)

# Como a fonte declarada na proveniência mapeia para o tier da ficha de acurácia.
# (a proveniência usa rótulos 'real'|'parcial'|'estimado'|'climatologia_real'|...)
_TIER_BY_PROV = {
    "clima": {
        "real": "estacao_inmet",
        "climatologia_real": "climatologia_real",
        "parcial": "climatologia_real",
        "estimado": "sintetico",
        "default": "sintetico",
    },
    "solo": {"real": "analise_talhao", "parcial": "analise_propriedade", "estimado": "default_regional", "default": "default_regional"},
    "cultivar": {"real": "cultivar_real", "parcial": "grupo_maturacao", "estimado": "generica", "default": "generica"},
    "data_semeadura": {"real": "realizada", "parcial": "planejada", "estimado": "planejada", "default": "planejada"},
    "populacao": {"real": "estande_aferido", "parcial": "regulagem", "estimado": "default", "default": "default"},
    "manejo": {"real": "registrado", "parcial": "programa_padrao", "estimado": "programa_padrao", "default": "programa_padrao"},
    "preco": {"real": "negociado", "parcial": "referencia", "estimado": "referencia", "default": "referencia"},
}

_LEVERAGE_FN = {
    "clima": _climate_leverage,
    "solo": _soil_leverage,
    "cultivar": _cultivar_leverage,
    "populacao": _population_leverage,
}


def _tier(group: str, prov_value: str) -> dict:
    """Resolve o tier (qualidade/label/nota) da fonte em uso para o grupo."""
    spec = kb.data_sources().get(group, {})
    tiers = spec.get("tiers", [])
    tier_id = _TIER_BY_PROV.get(group, {}).get(prov_value, prov_value)
    for t in tiers:
        if t.get("id") == tier_id:
            return t
    return tiers[-1] if tiers else {"id": prov_value, "label": prov_value, "quality": 0.2, "note": ""}


def accuracy_report(scenario: Scenario, provenance: dict | None = None) -> dict:
    """Relatório de acurácia do talhão: por variável, fonte atual, especificidade,
    alavancagem (sc/ha) e como melhorar — mais um índice de precisão ponderado.

    ``provenance``: {grupo: fonte} ('real'|'parcial'|'estimado'|'climatologia_real').
    Ausente => 'estimado' (postura honesta/conservadora).
    """
    prov = {g: "estimado" for g in GROUP_WEIGHT}
    prov.update(provenance or {})

    groups_spec = kb.data_sources()
    variables: list[dict] = []
    precision_num = 0.0

    for group, weight in GROUP_WEIGHT.items():
        spec = groups_spec.get(group, {})
        prov_value = prov.get(group, "estimado")
        tier = _tier(group, prov_value)
        quality = float(tier.get("quality", 0.2))
        precision_num += weight * quality

        lev_fn = _LEVERAGE_FN.get(group)
        leverage = lev_fn(scenario) if (lev_fn and quality < 1.0) else 0.0

        variables.append(
            {
                "group": group,
                "label": spec.get("label", group),
                "drives": spec.get("drives", []),
                "current_tier": tier.get("id"),
                "current_label": tier.get("label"),
                "current_note": tier.get("note", ""),
                "quality": round(quality, 2),
                "is_local": quality >= 0.7,
                "locality": spec.get("locality", ""),
                "leverage_sc_ha": leverage,
                "how_to_improve": spec.get("how_to_improve", ""),
                "source": spec.get("source", ""),
                "tiers": spec.get("tiers", []),
            }
        )

    # melhorias priorizadas: o que ainda não é local e tem maior alavancagem.
    improvements = sorted(
        (v for v in variables if v["quality"] < 1.0),
        key=lambda v: (v["leverage_sc_ha"], v["quality"] * -1),
        reverse=True,
    )

    precision = round(precision_num, 2)
    return {
        "precision_index": precision,
        "precision_label": _label(precision),
        "variables": sorted(variables, key=lambda v: v["leverage_sc_ha"], reverse=True),
        "top_improvements": improvements[:3],
        "resumo": _resumo(precision, improvements),
    }


def _label(p: float) -> str:
    return "alta" if p >= 0.75 else "média" if p >= 0.5 else "baixa"


def _resumo(precision: float, improvements: list[dict]) -> str:
    msg = f"Precisão da estimativa para este talhão: {_label(precision)} ({precision * 100:.0f}%)."
    top = next((v for v in improvements if v["leverage_sc_ha"] > 0), None)
    if top:
        msg += (
            f" O dado que mais aumentaria a precisão é {top['label'].lower()} "
            f"(pode mudar o resultado em ±{top['leverage_sc_ha']:.0f} sc/ha): {top['how_to_improve']}"
        )
    return msg
