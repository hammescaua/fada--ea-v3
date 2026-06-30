"""Memory Engine — a memória das safras (não só aprendizado, recordação).

Quando a safra atual se parece com uma vivida antes, o sistema reconhece e traz a lição:
*"esta situação é 87% parecida com a safra 2024/25 — naquele ano você colheu X; o que deu
certo / o que deu errado"*. É o que um produtor experiente faz de cabeça, agora explícito
e quantificado, gerando confiança na recomendação.

A semelhança é medida sobre os ATRIBUTOS da safra (déficit por estádio, desvio da janela,
fertilidade, programa de fungicida...), não sobre dados crus — coerente com o Knowledge
Engine.
"""

from __future__ import annotations

from dataclasses import dataclass

# Atributos comparados e a amplitude típica de cada um (para normalizar a distância).
_FEATURE_RANGE = {
    "sowing_deviation_days": 20.0,
    "water_overall_stress": 0.5,
    "water_stress_R3": 0.6,
    "water_stress_R4": 0.6,
    "water_stress_R5": 0.6,
    "soil_ph": 1.5,
    "soil_p_ppm": 15.0,
    "soil_k_ppm": 100.0,
    "soil_v_pct": 30.0,
    "population_k_per_ha": 100.0,
    "n_fungicidas": 3.0,
    "maturity_group": 1.5,
}


@dataclass
class PastSeason:
    crop_year: str
    features: dict
    predicted_sc_ha: float | None = None
    actual_sc_ha: float | None = None


def _similarity(a: dict, b: dict) -> tuple[float, str]:
    """Semelhança 0..1 entre dois conjuntos de atributos + o atributo que mais difere."""
    diffs: list[tuple[str, float]] = []
    for key, rng in _FEATURE_RANGE.items():
        if a.get(key) is None or b.get(key) is None or not rng:
            continue
        diffs.append((key, min(1.0, abs(float(a[key]) - float(b[key])) / rng)))
    if not diffs:
        return 0.0, ""
    sim = 1.0 - sum(d for _, d in diffs) / len(diffs)
    maior_dif = max(diffs, key=lambda d: d[1])[0]
    return max(0.0, sim), maior_dif


_FEATURE_LABEL = {
    "sowing_deviation_days": "data de semeadura",
    "water_overall_stress": "estresse hídrico",
    "water_stress_R3": "água em R3", "water_stress_R4": "água em R4", "water_stress_R5": "água em R5",
    "soil_ph": "pH", "soil_p_ppm": "fósforo", "soil_k_ppm": "potássio", "soil_v_pct": "saturação por bases",
    "population_k_per_ha": "população", "n_fungicidas": "programa de fungicida", "maturity_group": "ciclo da cultivar",
}


def similar_seasons(current_features: dict, past: list[PastSeason], top: int = 3, min_similarity: float = 0.5) -> dict:
    """Recupera as safras passadas mais parecidas com a atual e o que aconteceu nelas."""
    scored = []
    for p in past:
        if not p.features:
            continue
        sim, dif = _similarity(current_features, p.features)
        if sim < min_similarity:
            continue
        outcome = None
        if p.actual_sc_ha is not None:
            if p.predicted_sc_ha is not None:
                resid = p.actual_sc_ha - p.predicted_sc_ha
                tom = "acima do previsto" if resid > 1 else "abaixo do previsto" if resid < -1 else "como previsto"
            else:
                tom = ""
            outcome = {"colhido_sc_ha": round(p.actual_sc_ha, 1), "vs_previsto": tom}
        scored.append({
            "crop_year": p.crop_year,
            "semelhanca": round(sim, 2),
            "principal_diferenca": _FEATURE_LABEL.get(dif, dif),
            "resultado": outcome,
        })
    scored.sort(key=lambda s: s["semelhanca"], reverse=True)
    scored = scored[:top]
    return {"similares": scored, "resumo": _resumo(scored)}


def _resumo(similares: list[dict]) -> str:
    if not similares:
        return "Ainda sem safras parecidas no histórico deste talhão para comparar."
    s = similares[0]
    msg = f"Esta safra está {s['semelhanca'] * 100:.0f}% parecida com {s['crop_year']}"
    if s.get("resultado"):
        r = s["resultado"]
        msg += f" — naquele ano o talhão colheu {r['colhido_sc_ha']:.0f} sc/ha ({r['vs_previsto']})."
    else:
        msg += "."
    return msg
