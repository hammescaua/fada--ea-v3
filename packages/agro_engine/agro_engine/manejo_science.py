"""Motor de Evidência de Manejo — a base científica do impacto de cada ação, personalizada.

Para cada manejo, junta três camadas e as torna legíveis ao agricultor:
  1. **mecanismo** agronômico (por que a ação afeta a produtividade),
  2. o **coeficiente de resposta** citado (de ``agronomic_responses.json``, com fonte), e
  3. a **leitura personalizada** para AQUELE talhão — a pressão/déficit efetivos calculados
     a partir do perfil real (cultivar, solo, posição na janela ZARC).

Assim o número de cada manejo deixa de ser "mágico": é rastreável a literatura
(Embrapa, CQFS, ZARC, FAO-56) E específico daquela lavoura. A calibração por talhão
(Knowledge Engine) ajusta tudo isso com as safras reais ao longo do tempo.
"""

from __future__ import annotations

from . import kb
from . import reference as ref
from .models import Scenario

_PCT = lambda x: f"{x * 100:.0f}%"  # noqa: E731


def _coef(node: dict) -> dict | None:
    """Resolve {ref: 'grupo.chave'} -> {value, source, key}."""
    path = node.get("ref") if node else None
    if not path:
        return None
    return {"key": path, "value": kb.param(path), "source": kb.source(path)}


def _personalize(scenario: Scenario, alvo: str) -> str:
    """Leitura do coeficiente para o perfil real do talhão (a parte 'verdadeira p/ você')."""
    s = scenario.soil
    if alvo == "doencas":
        tol = scenario.cultivar.disease_tolerance
        pressure = ref.DISEASE_PRESSURE * (1.0 - 0.5 * tol)
        n = sum(1 for o in scenario.operations if o.kind.lower() == "fungicida")
        return (
            f"Sua cultivar tem tolerância à ferrugem de {_PCT(tol)}, então a pressão efetiva "
            f"de doença cai para ~{_PCT(pressure)} da perda potencial. Cada aplicação remove "
            f"~{_PCT(ref.DISEASE_CONTROL_EFF)} da perda restante; seu plano tem {n} aplicação(ões)."
        )
    if alvo == "pragas":
        n = sum(1 for o in scenario.operations if o.kind.lower() == "inseticida")
        return (
            f"Pressão de referência de pragas ~{_PCT(ref.PEST_PRESSURE)} da perda potencial; "
            f"cada inseticida bem aplicado controla ~{_PCT(ref.PEST_CONTROL_EFF)} do que resta. "
            f"Seu plano tem {n} aplicação(ões) — a decisão final é por monitoramento."
        )
    if alvo == "daninhas":
        n = sum(1 for o in scenario.operations if "herbicida" in o.kind.lower() or o.kind.lower() == "dessecacao")
        return (
            f"Competição de daninhas ~{_PCT(ref.WEED_PRESSURE)} da perda potencial; controle bem "
            f"manejado remove ~{_PCT(ref.WEED_CONTROL_EFF)}. Seu plano tem {n} operação(ões) de daninhas."
        )
    if alvo == "nutricao":
        notes = []
        if s.phosphorus_ppm < ref.P_SUFFICIENT_PPM:
            notes.append(
                f"P do talhão em {s.phosphorus_ppm:.0f} ppm, ABAIXO do crítico ({ref.P_SUFFICIENT_PPM:.0f}) "
                f"— há resposta esperada à adubação fosfatada"
            )
        else:
            notes.append(f"P do talhão em {s.phosphorus_ppm:.0f} ppm, na faixa suficiente — resposta menor")
        if s.potassium_ppm < ref.K_SUFFICIENT_PPM:
            notes.append(
                f"K em {s.potassium_ppm:.0f} ppm, ABAIXO do crítico ({ref.K_SUFFICIENT_PPM:.0f}) — repor"
            )
        else:
            notes.append(f"K em {s.potassium_ppm:.0f} ppm, suficiente")
        return ". ".join(notes) + "."
    if alvo == "solo":
        lo, hi = ref.PH_OPTIMAL
        parts = [f"pH atual {s.ph:.1f} (ideal {lo:.1f}–{hi:.1f})", f"V% {s.base_saturation_pct:.0f} (alvo soja 65%)"]
        gap = max(0.0, 65.0 - s.base_saturation_pct)
        if gap > 0:
            parts.append(f"faltam ~{gap:.0f} pontos de V% — a calagem (dose pela CTC {s.cec:.0f}) tende a se pagar")
        else:
            parts.append("saturação já adequada — calagem só de manutenção")
        return ", ".join(parts) + "."
    if alvo == "janela":
        return (
            "O impacto depende da janela ZARC do município e do ciclo da cultivar; "
            f"a penalidade de referência é {kb.param('semeadura.penalidade_sc_por_dia_fora_otimo')} sc/ha "
            "por dia fora do núcleo ótimo (veja o painel de janela de semeadura)."
        )
    if alvo == "populacao":
        lo, hi = ref.POPULATION_OPTIMAL_K
        return (
            f"Estande do talhão em {scenario.population_k_per_ha:.0f} mil/ha "
            f"(faixa ótima {lo:.0f}–{hi:.0f}); o tratamento/qualidade da semeadura preserva esse estande."
        )
    return ""


def manejo_evidence(scenario: Scenario, kind: str) -> dict | None:
    """Evidência científica personalizada de um manejo para o talhão.

    Retorna ``None`` quando não há ficha para o manejo (degrada sem quebrar)."""
    ev = kb.manejo_evidence().get(kind.lower())
    if not ev:
        return None
    coef = _coef(ev.get("coeficiente", {}))
    secundario = ev.get("coeficiente", {}).get("secundario")
    return {
        "kind": kind,
        "alvo": ev.get("alvo", ""),
        "mecanismo": ev.get("mecanismo", ""),
        "coeficiente": coef,
        "coeficiente_secundario": {"key": secundario, "value": kb.param(secundario), "source": kb.source(secundario)} if secundario else None,
        "personaliza_por": ev.get("personaliza_por", []),
        "leitura_talhao": _personalize(scenario, ev.get("alvo", "")),
        "fonte": ev.get("fonte", ""),
    }
