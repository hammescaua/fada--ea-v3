"""Motor de Plano de Safra ao Vivo — o passo-a-passo do talhão, do preparo à colheita.

Compõe a fenologia (datas dos estádios), o mapa CANÔNICO de manejos
(``operations_catalog.json``: janela, fator IPPD alvo, insumo) e os motores de água,
impacto e acurácia num **guia por fases** que o agricultor acompanha ao longo da safra:

    Preparo do solo → Semeadura → Vegetativo → Reprodutivo → Colheita

Cada fase traz: a janela de datas, o status (concluída/em andamento/futura) em relação a
*hoje*, os manejos planejados e os recomendados que faltam, o impacto de cada manejo em
sc/ha e R$, o fator de produtividade que a fase governa e **de onde vêm os dados** que a
sustentam (e como torná-los mais precisos para aquele talhão). É a base da tela de
acompanhamento e a resposta a "o que faço em cada etapa e por quê".
"""

from __future__ import annotations

from datetime import date, timedelta

from . import kb
from . import phenology
from .data_sources import accuracy_report
from .decision import operations_impact
from .manejo_science import manejo_evidence
from .models import Scenario
from .simulate import simulate

# Fases reconhecíveis pelo agricultor e os manejos canônicos típicos de cada uma.
_PHASES = [
    {
        "key": "preparo_solo",
        "label": "Preparo e correção do solo",
        "factor": "Solo / Nutrição",
        "catalog": ["calagem", "gessagem"],
        "data_groups": ["solo"],
        "orientacao": "Corrigir acidez e fertilidade ANTES da semeadura — a calagem precisa de meses para reagir.",
    },
    {
        "key": "semeadura",
        "label": "Semeadura e implantação",
        "factor": "Janela / População / Nutrição",
        "catalog": ["tratamento_sementes", "inoculacao", "adubacao_base", "adubacao_p", "herbicida_pre", "semeadura"],
        "data_groups": ["data_semeadura", "cultivar", "populacao", "solo"],
        "orientacao": "Semear na janela ZARC, na população certa, com adubação de base e fixação biológica de N.",
    },
    {
        "key": "vegetativo",
        "label": "Desenvolvimento vegetativo (V)",
        "factor": "Daninhas / Nutrição",
        "catalog": ["herbicida", "cobertura", "adubacao_foliar"],
        "data_groups": ["manejo", "clima"],
        "orientacao": "Manter a lavoura no limpo e nutrida até o florescimento — controle de daninhas em pós e reforço de K.",
    },
    {
        "key": "reprodutivo",
        "label": "Período reprodutivo (R)",
        "factor": "Doenças / Pragas / Água",
        "catalog": ["fungicida", "inseticida"],
        "data_groups": ["clima", "manejo", "cultivar"],
        "orientacao": "Fase crítica: proteger contra ferrugem e percevejos e torcer pela água em R3–R5 (enchimento de grãos).",
    },
    {
        "key": "colheita",
        "label": "Maturação e colheita",
        "factor": "Janela de colheita",
        "catalog": ["colheita"],
        "data_groups": ["preco", "clima"],
        "orientacao": "Colher na umidade certa (~14%) para reduzir perdas; acompanhar o preço de venda.",
    },
]

# A qual fase cada manejo informado (por 'kind') pertence.
_KIND_TO_PHASE = {
    "calagem": "preparo_solo", "gessagem": "preparo_solo", "corretivo": "preparo_solo",
    "semeadura": "semeadura", "adubacao_base": "semeadura", "adubacao_p": "semeadura",
    "adubacao_k": "semeadura", "fertilizante": "semeadura", "inoculacao": "semeadura",
    "tratamento_sementes": "semeadura", "herbicida_pre": "semeadura", "dessecacao": "semeadura",
    "herbicida": "vegetativo", "cobertura": "vegetativo", "adubacao_foliar": "vegetativo",
    "regulador": "vegetativo",
    "fungicida": "reprodutivo", "inseticida": "reprodutivo",
    "colheita": "colheita",
}


def _phase_windows(stages: dict[str, date], sowing: date, harvest: date) -> dict[str, tuple[date, date]]:
    """Janela de datas de cada fase, ancorada nos estádios fenológicos."""
    def g(stage: str, fallback: date) -> date:
        return stages.get(stage, fallback)

    v4 = g("V4", sowing + timedelta(days=25))
    r1 = g("R1", sowing + timedelta(days=50))
    r7 = g("R7", harvest - timedelta(days=12))
    return {
        "preparo_solo": (sowing - timedelta(days=90), sowing - timedelta(days=1)),
        "semeadura": (sowing, v4),
        "vegetativo": (v4, r1),
        "reprodutivo": (r1, r7),
        "colheita": (r7, harvest),
    }


PHASE_ORDER = ["preparo_solo", "semeadura", "vegetativo", "reprodutivo", "colheita"]
PHASE_LABEL = {
    "preparo_solo": "Preparo do solo", "semeadura": "Semeadura", "vegetativo": "Vegetativo",
    "reprodutivo": "Reprodutivo", "colheita": "Colheita",
}


def current_phase(scenario: Scenario, today: date | None = None) -> str:
    """A fase do ciclo em que a safra está HOJE — base do 'estado da safra'."""
    today = today or date.today()
    stages = phenology.stage_dates(scenario.cultivar, scenario.sowing_date, scenario.weather)
    sowing = scenario.sowing_date
    harvest = stages.get("R8", sowing + timedelta(days=scenario.cultivar.cycle_days))
    if today < sowing:
        return "preparo_solo"
    if today >= harvest:
        return "colheita"
    windows = _phase_windows(stages, sowing, harvest)
    for key in PHASE_ORDER:
        start, end = windows[key]
        if start <= today <= end:
            return key
    return "reprodutivo"


def _status(start: date, end: date, today: date) -> str:
    if end < today:
        return "concluida"
    if start <= today <= end:
        return "em_andamento"
    return "futura"


def _phase_of_op(kind: str, op_date: date, windows: dict[str, tuple[date, date]]) -> str:
    """Resolve a fase de uma operação: por tipo (catálogo) ou, se desconhecido, pela data."""
    k = kind.lower()
    if k in _KIND_TO_PHASE:
        return _KIND_TO_PHASE[k]
    for key, (start, end) in windows.items():
        if start <= op_date <= end:
            return key
    return "vegetativo"


def crop_plan(
    scenario: Scenario,
    today: date | None = None,
    provenance: dict | None = None,
    climate_known_fraction: float | None = None,
) -> dict:
    """Monta o plano de safra ao vivo (passo-a-passo por fase) para o talhão."""
    today = today or date.today()
    sim = simulate(scenario)
    stages = {k: date.fromisoformat(v) for k, v in sim.phenology.items()}
    sowing = scenario.sowing_date
    harvest = stages.get("R8", sowing + timedelta(days=scenario.cultivar.cycle_days))
    windows = _phase_windows(stages, sowing, harvest)

    # operations_impact reordena por retorno; casa cada impacto ao seu manejo por atributos.
    impact_by_op = _impacts_by_op(scenario)

    catalog = kb.operations()
    inputs = kb.inputs()
    acc = accuracy_report(scenario, provenance, climate_known_fraction)
    acc_by_group = {v["group"]: v for v in acc["variables"]}

    water_by_stage = sim.water.get("by_stage", {})

    phases_out = []
    for spec in _PHASES:
        start, end = windows[spec["key"]]
        status = _status(start, end, today)

        # manejos planejados nesta fase (do plano do agricultor)
        planned = [
            op for op in scenario.operations
            if _phase_of_op(op.kind, op.op_date, windows) == spec["key"]
        ]
        manejos = []
        for op in planned:
            imp = impact_by_op.get(id(op))
            manejos.append({
                "kind": op.kind,
                "label": catalog.get(op.kind, {}).get("label", op.kind.capitalize()),
                "planned": True,
                "op_date": op.op_date.isoformat(),
                "cost_per_ha": op.cost_per_ha,
                "dose": op.dose,
                "product": op.product,
                "funcao": catalog.get(op.kind, {}).get("funcao", ""),
                "impact_sc_ha": imp.delta_yield_sc_ha if imp else None,
                "impact_rs": imp.net_per_ha if imp else None,
                "evidencia": manejo_evidence(scenario, op.kind),
            })

        # manejos recomendados do catálogo que NÃO estão no plano
        present_kinds = {op.kind.lower() for op in scenario.operations}
        for ck in spec["catalog"]:
            if ck in present_kinds or ck == "semeadura" or ck == "colheita":
                continue
            cinfo = catalog.get(ck, {})
            if not cinfo:
                continue
            insumo = inputs.get(cinfo.get("insumo") or "", {})
            manejos.append({
                "kind": ck,
                "label": cinfo.get("label", ck),
                "planned": False,
                "op_date": None,
                "cost_per_ha": None,
                "dose": None,
                "product": None,
                "funcao": cinfo.get("funcao", ""),
                "janela": cinfo.get("janela", ""),
                "cost_reference": _cost_ref(insumo),
                "impact_sc_ha": None,
                "impact_rs": None,
                "evidencia": manejo_evidence(scenario, ck),
            })

        impact_sc = round(sum(m["impact_sc_ha"] or 0.0 for m in manejos if m["planned"]), 2)
        impact_rs = round(sum(m["impact_rs"] or 0.0 for m in manejos if m["planned"]), 0)

        # de onde vêm os dados desta fase + como melhorar
        data_basis = [
            {
                "group": g,
                "label": acc_by_group.get(g, {}).get("label", g),
                "current_label": acc_by_group.get(g, {}).get("current_label", ""),
                "is_local": acc_by_group.get(g, {}).get("is_local", False),
                "leverage_sc_ha": acc_by_group.get(g, {}).get("leverage_sc_ha", 0.0),
                "how_to_improve": acc_by_group.get(g, {}).get("how_to_improve", ""),
            }
            for g in spec["data_groups"]
        ]

        phases_out.append({
            "key": spec["key"],
            "label": spec["label"],
            "factor": spec["factor"],
            "orientacao": spec["orientacao"],
            "start": start.isoformat(),
            "end": end.isoformat(),
            "status": status,
            "manejos": manejos,
            "impact_sc_ha": impact_sc,
            "impact_rs": impact_rs,
            "water_stress": _phase_water_stress(spec["key"], water_by_stage),
            "data_basis": data_basis,
        })

    current = next((p["key"] for p in phases_out if p["status"] == "em_andamento"), None)
    progress = _progress(sowing, harvest, today)

    return {
        "today": today.isoformat(),
        "sowing_date": sowing.isoformat(),
        "harvest_date": harvest.isoformat(),
        "cycle_days": (harvest - sowing).days,
        "progress_pct": progress,
        "current_phase": current,
        "expected_sc_ha": round(sim.yield_result.expected_sc_ha, 1),
        "profit_per_ha": round(sim.economics.profit_per_ha, 0),
        "precision_index": acc["precision_index"],
        "weather_source": getattr(scenario, "_weather_source", "sintetico"),
        "weather_meta": getattr(scenario, "_weather_meta", {}) or {},
        "phases": phases_out,
        "stages": [
            {"stage": k, "date": stages[k].isoformat(), "status": _stage_status(stages[k], today)}
            for k in _ordered_stages(stages)
        ],
    }


_STAGE_ORDER = ["VE", "V1", "V4", "R1", "R2", "R3", "R4", "R5", "R5.5", "R6", "R7", "R8"]
_REPRO = {"R1", "R2", "R3", "R4", "R5", "R5.5", "R6"}


def _ordered_stages(stages: dict[str, date]) -> list[str]:
    return [s for s in _STAGE_ORDER if s in stages]


def _stage_status(d: date, today: date) -> str:
    return "concluida" if d < today else "futura"


def _progress(sowing: date, harvest: date, today: date) -> float:
    total = (harvest - sowing).days or 1
    return round(max(0.0, min(1.0, (today - sowing).days / total)) * 100, 0)


def _phase_water_stress(phase_key: str, by_stage: dict[str, float]) -> float | None:
    if phase_key == "reprodutivo" and by_stage:
        vals = [v for s, v in by_stage.items() if s in _REPRO]
        return round(sum(vals) / len(vals), 2) if vals else None
    return None


def _cost_ref(insumo: dict) -> str | None:
    if not insumo:
        return None
    return f"{insumo.get('label', '')} — R$ {insumo.get('price', 0):,.0f}/{insumo.get('unit', '')} ({insumo.get('source', '')})".replace(",", ".")


def _impacts_by_op(scenario: Scenario) -> dict[int, object]:
    """Casa cada OperationImpact ao objeto Operation pela tripla (kind, data, custo)."""
    out: dict[int, object] = {}
    imps = operations_impact(scenario)
    used = set()
    for op in scenario.operations:
        for i, imp in enumerate(imps):
            if i in used:
                continue
            if imp.kind == op.kind and imp.op_date == op.op_date.isoformat() and imp.cost_per_ha == op.cost_per_ha:
                out[id(op)] = imp
                used.add(i)
                break
    return out
