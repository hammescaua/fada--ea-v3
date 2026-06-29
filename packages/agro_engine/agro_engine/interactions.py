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

from dataclasses import dataclass
from datetime import date

from . import kb
from .evidence import Observation

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
    )


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
