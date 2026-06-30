"""Motor de Raciocínio Agronômico — o núcleo que pensa como um agrônomo.

Em vez de só dizer "a produtividade é X", este motor DIAGNOSTICA *por que* o talhão está
abaixo do potencial — gerando **hipóteses** ranqueadas, cada uma com a sua **cadeia de
impacto** (causa → efeito → … → produtividade, do Impact Graph), a **probabilidade** de ser
a limitação, a **confiança do dado** que a sustenta e **o que mede para confirmar**.

É a diferença entre um sistema que responde perguntas e um que descobre problemas. Cada
hipótese não é inventada: vem da decomposição IPPD (quanto cada fator derruba) cruzada com
o conhecimento causal e a proveniência dos dados. Quando o dado é um default regional, a
hipótese vem marcada como "a confirmar" — exatamente como um agrônomo raciocinaria.
"""

from __future__ import annotations

from . import kb
from . import reference as ref
from .data_sources import accuracy_report
from .models import Scenario
from .simulate import simulate

# Fator da cascata → causa no Impact Graph (alguns dependem do solo do talhão).
_DIRECT_CAUSE = {
    "Água": "deficit_hidrico",
    "Calor": "calor",
    "Compactação": "compactacao",
    "Doenças": "ferrugem",
    "Pragas": "pragas",
    "Daninhas": "daninhas",
    "População": "populacao_baixa",
    "Janela de semeadura": "janela",
    "Nematoides": "nematoides",
    "Solo": "acidez",
}


def _cause_for(label: str, scenario: Scenario) -> str | None:
    if label == "Nutrição":
        s = scenario.soil
        p_def = max(0.0, (ref.P_SUFFICIENT_PPM - s.phosphorus_ppm) / ref.P_SUFFICIENT_PPM)
        k_def = max(0.0, (ref.K_SUFFICIENT_PPM - s.potassium_ppm) / ref.K_SUFFICIENT_PPM)
        return "baixo_fosforo" if p_def >= k_def else "baixo_potassio"
    return _DIRECT_CAUSE.get(label)


def impact_chain(cause_key: str) -> dict | None:
    """A cadeia de impacto (causa → … → produtividade) de uma limitação."""
    return kb.impact_graph().get(cause_key)


def diagnose(scenario: Scenario, provenance: dict | None = None, observations=None) -> dict:
    """Hypothesis Engine: ranqueia as causas prováveis do talhão estar abaixo do potencial."""
    sim = simulate(scenario)
    y = sim.yield_result
    potential = y.base_potential_sc_ha
    gap = round(potential - y.expected_sc_ha, 1)

    acc = accuracy_report(scenario, provenance)
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
        prob = min(0.97, (loss / potential) / 0.12) if potential else 0.0
        # evidência observada do mesmo tipo reforça a hipótese
        prob = min(0.99, prob + obs_sev.get(cause_key, 0.0))
        certeza = round(conf_by_group.get(node.get("grupo_dado", ""), 0.4), 2)
        hypotheses.append({
            "causa": node["label"],
            "fator": node["fator"],
            "perda_sc_ha": loss,
            "perda_rs_ha": round(loss * scenario.soybean_price_per_sc, 0),
            "probabilidade": round(prob, 2),
            "certeza_do_dado": certeza,
            "a_confirmar": certeza < 0.7,
            "cadeia": node["cadeia"],
            "confirma_se": node["confirma_se"],
            "acao": node["acao"],
            "fonte": node["fonte"],
        })

    hypotheses.sort(key=lambda h: h["perda_sc_ha"], reverse=True)
    return {
        "potencial_sc_ha": round(potential, 1),
        "esperado_sc_ha": round(y.expected_sc_ha, 1),
        "gap_sc_ha": gap,
        "hipoteses": hypotheses,
        "resumo": _resumo(gap, hypotheses),
    }


_OBS_TO_CAUSE = {"ferrugem": "ferrugem", "praga": "pragas", "daninha": "daninhas"}
_SEV = {"baixa": 0.1, "media": 0.25, "média": 0.25, "alta": 0.4, "severa": 0.5}


def _observed_severity(observations) -> dict:
    """Boost de probabilidade por observações de campo (o agrônomo viu o sintoma)."""
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
