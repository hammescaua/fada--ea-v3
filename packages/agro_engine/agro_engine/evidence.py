"""Reality Engine — toda informação é uma EVIDÊNCIA, com grau de confiança.

Mudança conceitual central do gêmeo: não se guarda "um registro", guarda-se *o que
aconteceu, onde, com que confiança e com qual consequência*. Cada observação (chuva,
NDVI, ferrugem, emergência, aplicação, colheita...) carrega uma **confiança** derivada da
sua fonte — e quando fontes independentes **corroboram** o mesmo fato, a confiança sobe.

Isto não é IA nem banco: é a regra que decide *o quanto acreditar em cada dado*. Os
motores de simulação/decisão consultam essa confiança para saber quando NÃO confiar.
"""

from __future__ import annotations

from dataclasses import dataclass

# Confiança-base por fonte (0..1). Quanto mais direta/instrumentada a medição, maior.
SOURCE_CONFIDENCE: dict[str, float] = {
    "drone": 0.98,
    "monitor_colheita": 0.96,
    "monitor_plantadeira": 0.95,
    "gps": 0.95,
    "agronomo": 0.95,            # observação de campo por profissional
    "laboratorio": 0.97,         # análise de solo/tecido
    "satelite": 0.92,            # NDVI/EVI (Sentinel-2)
    "nota_fiscal": 0.90,         # comprova insumo/dose/data
    "api_clima": 0.90,           # Open-Meteo observado
    "estacao_inmet": 0.88,
    "emergencia_observada": 0.85,
    "gdd_modelo": 0.70,          # inferido pelo modelo (graus-dia)
    "climatologia": 0.70,
    "produtor": 0.65,            # relato do agricultor sem comprovação
    "estimativa": 0.50,
    "manual": 0.50,
    "default": 0.40,
}

# Fontes consideradas independentes entre si para fins de corroboração.
_INDEPENDENT = {
    "api_clima", "estacao_inmet", "satelite", "drone", "monitor_colheita",
    "monitor_plantadeira", "gps", "nota_fiscal", "agronomo", "laboratorio",
    "emergencia_observada", "produtor",
}


def confidence_for(source: str, corroborations: int = 0) -> float:
    """Confiança de uma evidência: base da fonte, elevada por corroborações independentes.

    Cada fonte independente que confirma o mesmo fato reduz a incerteza pela metade
    (combinação otimista de evidências) — ex.: API de chuva (0,90) + pluviômetro no
    talhão sobe para ~0,95.
    """
    base = SOURCE_CONFIDENCE.get(source, SOURCE_CONFIDENCE["default"])
    uncertainty = (1.0 - base) * (0.5 ** max(0, corroborations))
    return round(1.0 - uncertainty, 3)


@dataclass
class Observation:
    """Uma evidência no tempo/espaço. ``value`` é livre (JSON): {'mm': 21}, {'ndvi': 0.74},
    {'severidade': 'baixa'}... ``consequence`` liga a evidência ao efeito observado."""

    kind: str                 # chuva | ndvi | ferrugem | emergencia | aplicacao | colheita | plantio | praga | daninha
    source: str
    observed_at: str          # ISO date
    value: dict
    confidence: float = 0.0
    latitude: float | None = None
    longitude: float | None = None
    unit: str | None = None
    consequence: str | None = None   # efeito observado (ex.: "eficiência do fungicida caiu")


def corroborate(observations: list[Observation]) -> list[Observation]:
    """Reavalia a confiança de um conjunto de observações do MESMO fato (kind+dia),
    elevando-a conforme o nº de fontes independentes que concordam."""
    by_fact: dict[tuple[str, str], list[Observation]] = {}
    for o in observations:
        by_fact.setdefault((o.kind, o.observed_at), []).append(o)
    out: list[Observation] = []
    for group in by_fact.values():
        indep = len({o.source for o in group if o.source in _INDEPENDENT})
        for o in group:
            o.confidence = confidence_for(o.source, corroborations=max(0, indep - 1))
            out.append(o)
    return out


def data_quality(observations: list[Observation], groups: dict[str, list[str]] | None = None) -> dict:
    """Data Quality Engine: nota 0..100 por grupo (completude × confiança × atualidade).

    A nota cresce com a quantidade de evidências do grupo e com a confiança média delas.
    Diz à IA *quando não deve confiar* num grupo de dados.
    """
    groups = groups or {
        "solo": ["analise_solo", "laboratorio"],
        "clima": ["chuva", "temperatura", "ndvi"],
        "fitossanidade": ["ferrugem", "praga", "daninha", "aplicacao"],
        "produtividade": ["colheita", "emergencia", "estande"],
        "mercado": ["preco", "venda"],
    }
    scores: dict[str, float] = {}
    for grupo, kinds in groups.items():
        obs = [o for o in observations if o.kind in kinds]
        if not obs:
            scores[grupo] = 0.0
            continue
        mean_conf = sum(o.confidence for o in obs) / len(obs)
        completeness = min(1.0, len(obs) / 3.0)  # ~3 evidências já é boa cobertura
        scores[grupo] = round(100.0 * mean_conf * (0.5 + 0.5 * completeness), 0)
    return scores
