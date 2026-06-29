"""Motor de Interações — a CONSEQUÊNCIA conectada na linha do tempo de evidências.

O gêmeo não aprende só com o resultado final, mas com a **sequência de eventos** que
levou a ele. Este motor varre as observações do talhão e detecta padrões agronômicos
fundamentados (regras citadas em ``interaction_rules.json``): *aplicou fungicida → choveu
22 mm no dia seguinte → provável lavagem, eficácia reduzida*. Cada interação detectada
vira um **aprendizado** com confiança, mensagem e recomendação — exatamente a "memória"
da lavoura.

Tudo é derivado das evidências reais (com a confiança de cada uma), não de suposição: é
honesto sobre o que de fato foi observado.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date

from . import kb
from .evidence import Observation
from .models import Scenario

# Ordem de severidade para comparações ("baixa" < "media" < "alta" < "severa").
_SEV_ORDER = {"baixa": 1, "media": 2, "média": 2, "alta": 3, "severa": 4}


@dataclass
class Interaction:
    rule: str
    label: str
    when: str               # data do evento-gatilho (ISO)
    positive: bool          # True = consequência boa (confirma um acerto)
    description: str
    recomendacao: str
    confidence: float       # herda a confiança das evidências envolvidas
    efficacy_loss: float | None
    source: str
    effect: dict | None = None       # como a interação muda o modelo (efficacy_loss/population_loss)
    trigger_tipo: str | None = None  # tipo do manejo-gatilho (ex.: 'fungicida'), p/ casar com a operação


def _d(iso: str) -> date:
    return date.fromisoformat(iso)


def _rain_mm(o: Observation) -> float:
    v = o.value or {}
    try:
        return float(v.get("mm", 0) or 0)
    except (TypeError, ValueError):
        return 0.0


def _severity(o: Observation) -> int:
    return _SEV_ORDER.get(str((o.value or {}).get("severidade", "")).lower(), 0)


def _within(a: Observation, b: Observation, days: int, direction: str = "after") -> bool:
    """``b`` está dentro de ``days`` de ``a``? 'after' = depois do gatilho; 'before' = antes."""
    delta = (_d(b.observed_at) - _d(a.observed_at)).days
    if direction == "before":
        return -days <= delta <= 0
    return 0 <= delta <= days


def detect_interactions(observations: list[Observation]) -> list[Interaction]:
    """Detecta interações evento→consequência na linha do tempo de evidências."""
    rules = kb.interaction_rules()
    obs = sorted(observations, key=lambda o: o.observed_at)
    out: list[Interaction] = []

    for key, r in rules.items():
        trig_kind = r.get("trigger_kind")
        window = int(r.get("window_days", 1))
        triggers = [o for o in obs if o.kind == trig_kind]

        for t in triggers:
            # filtro de severidade no próprio gatilho (ex.: ferrugem >= media)
            if r.get("severity_min") and _severity(t) < _SEV_ORDER.get(r["severity_min"], 0):
                continue

            followed = r.get("followed_by")
            absence = r.get("requires_absence_of")
            rain_th = r.get("rain_mm_threshold")

            if followed:
                cands = [o for o in obs if o.kind == followed and _within(t, o, window) and o is not t]
                if followed == "chuva" and rain_th is not None:
                    cands = [o for o in cands if _rain_mm(o) >= rain_th]
                if followed == "ferrugem" and r.get("severity_max"):
                    cands = [o for o in cands if _severity(o) <= _SEV_ORDER.get(r["severity_max"], 99)]
                if not cands:
                    continue
                conf = round(min(t.confidence, max(c.confidence for c in cands)), 3)
                detail = _detail(r, t, cands[0])
                out.append(_mk(key, r, t, conf, detail))

            elif absence:
                direction = r.get("absence_direction", "after")
                in_window = [o for o in obs if o.kind == absence and _within(t, o, window, direction) and o is not t]
                if absence == "chuva" and rain_th is not None:
                    total = sum(_rain_mm(o) for o in in_window)
                    if total >= rain_th:
                        continue  # houve chuva suficiente -> sem risco
                elif in_window:
                    continue  # houve o evento -> regra não dispara
                conf = round(t.confidence * 0.9, 3)
                out.append(_mk(key, r, t, conf, r.get("mensagem", "")))

    out.sort(key=lambda i: (i.when, -i.confidence))
    return out


def _detail(rule: dict, trigger: Observation, other: Observation) -> str:
    msg = rule.get("mensagem", "")
    if rule.get("followed_by") == "chuva":
        return f"{msg} (registro: {_rain_mm(other):.0f} mm em {other.observed_at})"
    return msg


def _mk(key: str, r: dict, t: Observation, conf: float, detail: str) -> Interaction:
    return Interaction(
        rule=key,
        label=r.get("label", key),
        when=t.observed_at,
        positive=bool(r.get("positive", False)),
        description=detail,
        recomendacao=r.get("recomendacao", ""),
        confidence=conf,
        efficacy_loss=r.get("efficacy_loss"),
        source=r.get("source", ""),
        effect=r.get("effect"),
        trigger_tipo=str((t.value or {}).get("tipo", "")) or None,
    )


_FACTOR_OF_KIND = {"fungicida": "Doenças", "inseticida": "Pragas", "herbicida": "Daninhas", "dessecacao": "Daninhas"}


def _factor_of(kind: str) -> str:
    return _FACTOR_OF_KIND.get(kind.lower(), kind)


def _match_op_index(ops: list, when: str, tipo: str | None) -> int | None:
    """Índice da operação mais próxima da data do gatilho (±3 dias), casando o tipo se houver."""
    target = _d(when)
    best, best_dist = None, 4
    for i, op in enumerate(ops):
        if tipo and op.kind.lower() != tipo.lower():
            continue
        dist = abs((op.op_date - target).days)
        if dist <= 3 and dist < best_dist:
            best, best_dist = i, dist
    return best


def apply_interactions(scenario: Scenario, observations: list[Observation]) -> tuple[Scenario, list[dict]]:
    """Realimenta as consequências observadas NO MODELO: uma aplicação lavada vale menos
    (qualidade efetiva menor → menos proteção na cascata), o estande observado sobrepõe o
    planejado, etc. Devolve o cenário ajustado à REALIDADE + o log de ajustes (com fonte).

    Cada ajuste é escalado pela CONFIANÇA da evidência — dado fraco move pouco o número.
    """
    interactions = detect_interactions(observations)
    ops = list(scenario.operations)
    pop = scenario.population_k_per_ha
    adjustments: list[dict] = []

    # 1) estande observado (emergência) sobrepõe a população planejada
    for o in observations:
        if o.kind == "emergencia":
            v = o.value or {}
            obs_pop = v.get("plantas_mil") or v.get("populacao_mil")
            if obs_pop and abs(float(obs_pop) - pop) > 1:
                adjustments.append(_adj("População", "estande", pop, float(obs_pop),
                                        "Estande medido na emergência difere do planejado.",
                                        "Embrapa Soja — estande e componentes de produtividade", o.confidence))
                pop = float(obs_pop)

    # 2) interações da linha do tempo que alteram o modelo
    for it in interactions:
        eff = it.effect or {}
        if eff.get("type") == "efficacy_loss":
            loss = float(eff.get("value", 0.0)) * it.confidence
            idx = _match_op_index(ops, it.when, it.trigger_tipo)
            if idx is not None and loss > 0:
                old = ops[idx]
                new_q = round(max(0.0, old.quality * (1.0 - loss)), 3)
                ops[idx] = replace(old, quality=new_q)
                adjustments.append(_adj(_factor_of(old.kind), old.kind, old.quality, new_q,
                                        it.description, it.source, it.confidence))
        elif eff.get("type") == "population_loss":
            loss = float(eff.get("value", 0.0)) * it.confidence
            if loss > 0:
                new_pop = round(pop * (1.0 - loss), 1)
                adjustments.append(_adj("População", "estande", pop, new_pop, it.description, it.source, it.confidence))
                pop = new_pop

    adjusted = replace(scenario, operations=ops, population_k_per_ha=pop)
    return adjusted, adjustments


def _adj(factor: str, manejo: str, before: float, after: float, reason: str, source: str, confidence: float) -> dict:
    return {
        "factor": factor, "manejo": manejo,
        "before": round(before, 3), "after": round(after, 3),
        "reason": reason, "source": source, "confidence": round(confidence, 3),
    }


def interactions_report(observations: list[Observation]) -> dict:
    """Resumo dos aprendizados (interações) detectados no talhão."""
    items = detect_interactions(observations)
    alertas = [i for i in items if not i.positive]
    return {
        "n_interactions": len(items),
        "interactions": [i.__dict__ for i in items],
        "resumo": _resumo(items, alertas),
    }


def _resumo(items: list[Interaction], alertas: list[Interaction]) -> str:
    if not items:
        return "Sem interações detectadas ainda — registre eventos (aplicação, chuva, ferrugem) para o gêmeo aprender a sequência da safra."
    if alertas:
        a = alertas[0]
        return f"{len(items)} aprendizado(s) na linha do tempo. Atenção: {a.label.lower()} em {a.when}."
    return f"{len(items)} aprendizado(s) — nenhum alerta; manejos e clima jogaram a favor."
