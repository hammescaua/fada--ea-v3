"""Motor de Raciocínio Agronômico — o núcleo que pensa como um agrônomo.

Diagnostica *por que* o talhão está abaixo do potencial gerando **hipóteses** ranqueadas,
cada uma com a sua **cadeia de impacto** (Impact Graph PONDERADO), a **probabilidade** de
ser a limitação, a **força científica** da relação (pesos das ligações), a **confiança do
dado** que a sustenta, a **controlabilidade** (dá para agir?) e **o que medir para
confirmar**. Marca como "a confirmar" quando o dado é um default regional.

Devolve também os **quatro níveis de confiança** (dados → modelo → recomendação →
resultado) e o **principal motivo da incerteza** — separando o que sabemos do que supomos.
Nada é inventado: tudo vem da decomposição IPPD cruzada com o conhecimento causal (com
peso/condição/evidência) e a proveniência dos dados.
"""

from __future__ import annotations

from . import kb
from . import reference as ref
from .data_sources import accuracy_report
from .models import Scenario
from .simulate import simulate

_DIRECT_CAUSE = {
    "Água": "deficit_hidrico", "Calor": "calor", "Compactação": "compactacao",
    "Doenças": "ferrugem", "Pragas": "pragas", "Daninhas": "daninhas",
    "População": "populacao_baixa", "Janela de semeadura": "janela",
    "Nematoides": "nematoides", "Solo": "acidez",
}
_OPS = {">": lambda a, b: a > b, "<": lambda a, b: a < b, ">=": lambda a, b: a >= b, "<=": lambda a, b: a <= b}


def _cause_for(label: str, scenario: Scenario) -> str | None:
    if label == "Nutrição":
        s = scenario.soil
        p_def = max(0.0, (ref.P_SUFFICIENT_PPM - s.phosphorus_ppm) / ref.P_SUFFICIENT_PPM)
        k_def = max(0.0, (ref.K_SUFFICIENT_PPM - s.potassium_ppm) / ref.K_SUFFICIENT_PPM)
        return "baixo_fosforo" if p_def >= k_def else "baixo_potassio"
    return _DIRECT_CAUSE.get(label)


def impact_chain(cause_key: str) -> dict | None:
    return kb.impact_graph().get(cause_key)


def _read(scenario: Scenario, path: str):
    obj = scenario
    for part in path.split("."):
        obj = getattr(obj, part, None)
        if obj is None:
            return None
    return obj


def _condition_factor(scenario: Scenario, cond: dict | None) -> float:
    """1.0 se a condição da cadeia é satisfeita (ou inexistente); 0.4 se não (cadeia menos provável)."""
    if not cond:
        return 1.0
    val = _read(scenario, cond.get("campo", ""))
    op = _OPS.get(cond.get("op", ">"))
    if val is None or op is None:
        return 1.0
    return 1.0 if op(val, cond.get("valor", 0)) else 0.4


def _chain_force(node: dict) -> float:
    pesos = [e.get("peso", 1.0) for e in node.get("cadeia", []) if isinstance(e, dict)]
    return round(sum(pesos) / len(pesos), 2) if pesos else 1.0


def _steps(node: dict) -> list[str]:
    return [e.get("passo", "") if isinstance(e, dict) else str(e) for e in node.get("cadeia", [])]


def diagnose(scenario: Scenario, provenance: dict | None = None, observations=None, *, sim=None, acc=None) -> dict:
    """Hypothesis Engine: ranqueia as causas prováveis do talhão estar abaixo do potencial.

    ``sim``/``acc`` podem ser pré-computados (pelo State Engine) para não recalcular —
    garante consistência e evita rodar simulate/accuracy duas vezes no mesmo estado."""
    sim = sim or simulate(scenario)
    y = sim.yield_result
    potential = y.base_potential_sc_ha
    gap = round(potential - y.expected_sc_ha, 1)

    acc = acc if acc is not None else accuracy_report(scenario, provenance)
    conf_by_group = {v["group"]: v["quality"] for v in acc["variables"]}
    graph = kb.impact_graph()
    obs_sev = _observed_severity(observations)

    hypotheses: list[dict] = []
    for c in y.contributions:
        if c.delta_sc_ha >= -0.1 or c.label == "Calibração do talhão":
            continue
        cause_key = _cause_for(c.label, scenario)
        node = graph.get(cause_key or "")
        if not node:
            continue
        loss = round(abs(c.delta_sc_ha), 1)
        cond_factor = _condition_factor(scenario, node.get("condicao"))
        prob = min(0.97, (loss / potential) / 0.12) * cond_factor if potential else 0.0
        prob = min(0.99, prob + obs_sev.get(cause_key, 0.0))
        certeza = round(conf_by_group.get(node.get("grupo_dado", ""), 0.4), 2)
        hypotheses.append({
            "causa": node["label"],
            "fator": node["fator"],
            "perda_sc_ha": loss,
            "perda_rs_ha": round(loss * scenario.soybean_price_per_sc, 0),
            "probabilidade": round(prob, 2),
            "forca_cientifica": _chain_force(node),
            "confianca_cientifica": node.get("confianca_cientifica", 0.7),
            "nivel_evidencia": node.get("nivel_evidencia", "medio"),
            "controlabilidade": node.get("controlabilidade", "parcial"),
            "certeza_do_dado": certeza,
            "a_confirmar": certeza < 0.7,
            "cadeia": _steps(node),
            "confirma_se": node["confirma_se"],
            "acao": node["acao"],
            "fonte": node["fonte"],
        })

    hypotheses.sort(key=lambda h: h["perda_sc_ha"], reverse=True)
    niveis = _niveis_confianca(acc, hypotheses, y)
    return {
        "potencial_sc_ha": round(potential, 1),
        "esperado_sc_ha": round(y.expected_sc_ha, 1),
        "incerteza_sc_ha": round(y.uncertainty_sc_ha, 1),
        "gap_sc_ha": gap,
        "hipoteses": hypotheses,
        "niveis_confianca": niveis,
        "principal_incerteza": _principal_incerteza(acc),
        "resumo": _resumo(gap, hypotheses),
    }


def _niveis_confianca(acc: dict, hypotheses: list[dict], y) -> dict:
    """Quatro níveis: Dados → Modelo → Recomendação → Resultado (incerteza acumula a cada etapa)."""
    dados = acc["precision_index"]
    if hypotheses:
        wsum = sum(h["perda_sc_ha"] for h in hypotheses) or 1.0
        modelo = sum(h["confianca_cientifica"] * h["perda_sc_ha"] for h in hypotheses) / wsum
    else:
        modelo = y.confidence
    recomendacao = dados * modelo
    spread = y.uncertainty_sc_ha / y.expected_sc_ha if y.expected_sc_ha else 0.3
    resultado = recomendacao * (1.0 - min(0.3, spread))
    return {
        "dados": round(dados, 2),
        "modelo": round(modelo, 2),
        "recomendacao": round(recomendacao, 2),
        "resultado": round(resultado, 2),
    }


def _principal_incerteza(acc: dict) -> dict | None:
    top = next((v for v in acc["variables"] if v["leverage_sc_ha"] > 0), None)
    if not top:
        return None
    return {"variavel": top["label"], "amplitude_sc_ha": top["leverage_sc_ha"], "como_reduzir": top["how_to_improve"]}


_OBS_TO_CAUSE = {"ferrugem": "ferrugem", "praga": "pragas", "daninha": "daninhas"}
_SEV = {"baixa": 0.1, "media": 0.25, "média": 0.25, "alta": 0.4, "severa": 0.5}


def _observed_severity(observations) -> dict:
    out: dict[str, float] = {}
    for o in observations or []:
        kind = getattr(o, "kind", None) or (o.get("kind") if isinstance(o, dict) else None)
        val = getattr(o, "value", None) or (o.get("value") if isinstance(o, dict) else {}) or {}
        cause = _OBS_TO_CAUSE.get(kind)
        if cause:
            sev = _SEV.get(str(val.get("severidade", "")).lower(), 0.0)
            out[cause] = max(out.get(cause, 0.0), sev)
    return out


def _resumo(gap: float, hypotheses: list[dict]) -> str:
    if not hypotheses or gap <= 1:
        return "O talhão está próximo do seu potencial — sem limitação relevante a investigar."
    top = hypotheses[0]
    msg = (
        f"O talhão está {gap:.0f} sc/ha abaixo do potencial. A maior limitação provável é "
        f"{top['causa'].lower()} (explica ~{top['perda_sc_ha']:.0f} sc/ha)."
    )
    if top["a_confirmar"]:
        msg += f" Dado de baixa confiança — confirme: {top['confirma_se']}."
    return msg
