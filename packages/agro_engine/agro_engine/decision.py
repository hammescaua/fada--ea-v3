"""Motor de Decisão — o "sexto motor" que junta tudo.

A premissa do produto (do briefing): **não vender previsão, e sim capacidade de
decisão**. Em vez de só dizer "você vai colher X", este motor responde *"o que
acontece SE eu tomar tal decisão?"* e **prioriza as intervenções pelo retorno
esperado**.

Para cada decisão candidata (aplicar/remover fungicida, antecipar semeadura, corrigir
fósforo, calagem, ajustar população...):
  1. transforma o cenário (já embutindo o custo da ação),
  2. re-simula e mede Δprodutividade e Δlucro vs. a linha de base,
  3. estima a **probabilidade de retorno positivo** via Monte Carlo *pareado*
     (números aleatórios comuns — mesmo clima/preço nos dois cenários), e
  4. devolve uma justificativa técnica.

O resultado alimenta o cockpit ("Hoje → ação → +2,4 sc/ha → 78% → ROI 3,6x") e, no
futuro, o LLM (Nível 3) apenas narra estes números — nunca os inventa.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, replace
from datetime import date, timedelta
from typing import Callable

from . import economics, phenology, sowing_window, water_balance, yield_model
from . import reference as ref
from .models import CostItem, Operation, Scenario
from .montecarlo import _synth_weather


@dataclass
class DecisionResult:
    key: str
    label: str
    description: str
    category: str
    added_cost_per_ha: float
    delta_yield_sc_ha: float
    delta_profit_per_ha: float
    action_roi: float | None       # Δlucro / custo da ação (None se ação sem custo)
    probability_positive: float    # 0..1 — chance de a ação melhorar o lucro
    justification: str


# --- avaliação determinística de um cenário (mesmo pipeline do orquestrador) ---
def _profit_and_yield(scenario: Scenario, weather=None, price: float | None = None) -> tuple[float, float]:
    stages = phenology.stage_dates(scenario.cultivar, scenario.sowing_date, weather or scenario.weather)
    water = water_balance.water_stress(scenario, stages, weather or scenario.weather)
    sowing = sowing_window.evaluate(scenario.municipality, scenario.sowing_date)
    yres = yield_model.decompose(scenario, water, sowing)
    scen = scenario if price is None else replace(scenario, soybean_price_per_sc=price)
    econ = economics.compute(scen, yres.expected_sc_ha)
    return econ.profit_per_ha, yres.expected_sc_ha


def _fungicidas(s: Scenario) -> list[Operation]:
    return [o for o in s.operations if o.kind.lower() == "fungicida"]


# --- catálogo de transformações de cenário (cada uma embute seu custo) ---------
def _add_fungicide(s: Scenario) -> Scenario:
    n = len(_fungicidas(s))
    op_date = date(s.sowing_date.year + 1, 1, 10) + timedelta(days=n * 14)
    op = Operation(kind="fungicida", op_date=op_date, cost_per_ha=180.0, quality=0.9)
    return replace(s, operations=[*s.operations, op])


def _remove_fungicide(s: Scenario) -> Scenario:
    fung = _fungicidas(s)
    if not fung:
        return s
    last = fung[-1]
    return replace(s, operations=[o for o in s.operations if o is not last])


def _advance_sowing(s: Scenario) -> Scenario:
    rec = sowing_window.recommend(s.municipality, s.sowing_date.year if s.sowing_date.month >= 7 else s.sowing_date.year - 1)
    target = date.fromisoformat(rec["optimal_start"])
    return replace(s, sowing_date=target)


def _increase_population(s: Scenario) -> Scenario:
    lo, _ = ref.POPULATION_OPTIMAL_K
    target = (lo + ref.POPULATION_OPTIMAL_K[1]) / 2
    return replace(s, population_k_per_ha=target)


def _correct_phosphorus(s: Scenario) -> Scenario:
    soil = replace(s.soil, phosphorus_ppm=max(s.soil.phosphorus_ppm, ref.P_SUFFICIENT_PPM + 2))
    cost = CostItem(category="fertilizante", description="Correção de fósforo", cost_per_ha=240.0)
    return replace(s, soil=soil, costs=[*s.costs, cost])


def _liming(s: Scenario) -> Scenario:
    soil = replace(
        s.soil,
        ph=max(s.soil.ph, 6.0),
        base_saturation_pct=max(s.soil.base_saturation_pct, ref.V_SUFFICIENT_PCT + 5),
    )
    # calagem amortizada por safra (calcário + aplicação)
    cost = CostItem(category="corretivo", description="Calagem (amortizada)", cost_per_ha=180.0)
    return replace(s, soil=soil, costs=[*s.costs, cost])


@dataclass
class _Candidate:
    key: str
    label: str
    description: str
    category: str
    added_cost_per_ha: float
    transform: Callable[[Scenario], Scenario]
    justification: str
    applicable: Callable[[Scenario], bool]


def _catalog() -> list[_Candidate]:
    return [
        _Candidate(
            "add_fungicide", "Adicionar 1 aplicação de fungicida",
            "Inclui mais uma aplicação no programa fitossanitário.", "fitossanitario", 180.0,
            _add_fungicide,
            "Pressão de ferrugem alta no Noroeste do RS; aplicação adicional reduz a perda por doença no enchimento de grãos.",
            lambda s: len(_fungicidas(s)) < 3,
        ),
        _Candidate(
            "remove_fungicide", "Remover 1 aplicação de fungicida",
            "Reduz o programa em uma aplicação para economizar.", "fitossanitario", -180.0,
            _remove_fungicide,
            "Avalia se a última aplicação se paga: se a cultivar é tolerante e a pressão é baixa, o custo pode não retornar.",
            lambda s: len(_fungicidas(s)) >= 1,
        ),
        _Candidate(
            "advance_sowing", "Antecipar semeadura para o núcleo ótimo (ZARC)",
            "Move a semeadura para o início da janela de menor risco.", "semeadura", 0.0,
            _advance_sowing,
            "A data atual está após o núcleo ótimo do ZARC; antecipar recupera potencial perdido por janela.",
            lambda s: sowing_window.evaluate(s.municipality, s.sowing_date)["deviation_days"] > 0,
        ),
        _Candidate(
            "increase_population", "Ajustar população para o ótimo",
            "Eleva o estande para a faixa ótima da cultura.", "populacao", 60.0,
            _increase_population,
            "População abaixo do ideal limita o número de vagens; ajustar o estande aumenta o teto produtivo.",
            lambda s: s.population_k_per_ha < ref.POPULATION_OPTIMAL_K[0],
        ),
        _Candidate(
            "correct_phosphorus", "Corrigir fósforo do solo",
            "Adubação fosfatada para sair da faixa de deficiência.", "nutricao", 240.0,
            _correct_phosphorus,
            "Fósforo abaixo da suficiência limita o desenvolvimento radicular e a produtividade; a correção tende a ter alto retorno.",
            lambda s: s.soil.phosphorus_ppm < ref.P_SUFFICIENT_PPM,
        ),
        _Candidate(
            "liming", "Fazer calagem (corrigir pH/V%)",
            "Calagem para elevar pH e saturação por bases.", "corretivo", 180.0,
            _liming,
            "Acidez e baixa saturação por bases reduzem a disponibilidade de nutrientes; a calagem é base de fertilidade.",
            lambda s: s.soil.ph < 5.7 or s.soil.base_saturation_pct < ref.V_SUFFICIENT_PCT,
        ),
    ]


def _probability_positive(base: Scenario, action: Scenario, n: int, seed: int) -> float:
    """P(ação melhora o lucro) via Monte Carlo pareado (números aleatórios comuns).

    Usa o MESMO clima e o MESMO preço sorteados para os dois cenários em cada
    iteração — isola o efeito da decisão e reduz drasticamente o ruído.
    """
    rng = random.Random(seed)
    base_price = base.soybean_price_per_sc
    wins = 0
    for _ in range(n):
        weather = _synth_weather(base, rng)
        price = max(1.0, rng.gauss(base_price, base_price * 0.12))
        pb, _ = _profit_and_yield(base, weather, price)
        pa, _ = _profit_and_yield(action, weather, price)
        if pa > pb:
            wins += 1
    return round(wins / n, 3) if n else 0.0


@dataclass
class OperationImpact:
    kind: str
    op_date: str
    cost_per_ha: float
    delta_yield_sc_ha: float       # quanto este manejo agrega à produtividade
    value_per_ha: float            # valor bruto agregado (Δprodutividade × preço)
    net_per_ha: float              # valor líquido (valor − custo) — "quanto representa"
    roi: float | None


def operations_impact(scenario: Scenario) -> list[OperationImpact]:
    """Para cada manejo no plano, mede QUANTO ele representa na safra.

    Compara o cenário com e sem cada operação: a diferença é a contribuição daquele
    manejo (produtividade ganha, valor bruto e valor líquido descontando o custo).
    É o que deixa claro ao agricultor o retorno de cada ação.
    """
    base_profit, base_yield = _profit_and_yield(scenario)
    price = scenario.soybean_price_per_sc
    out: list[OperationImpact] = []

    for op in scenario.operations:
        without = replace(scenario, operations=[o for o in scenario.operations if o is not op])
        _, y_without = _profit_and_yield(without)
        d_yield = round(base_yield - y_without, 2)
        value = round(d_yield * price, 0)
        net = round(value - op.cost_per_ha, 0)
        roi = round(value / op.cost_per_ha, 2) if op.cost_per_ha > 0 else None
        out.append(
            OperationImpact(
                kind=op.kind, op_date=op.op_date.isoformat(), cost_per_ha=op.cost_per_ha,
                delta_yield_sc_ha=d_yield, value_per_ha=value, net_per_ha=net, roi=roi,
            )
        )
    out.sort(key=lambda o: o.net_per_ha, reverse=True)
    return out


def recommend_decisions(
    scenario: Scenario,
    n_prob: int = 400,
    seed: int = 12345,
    top: int | None = None,
) -> list[DecisionResult]:
    """Avalia o catálogo de decisões e devolve as ações ordenadas por Δlucro esperado."""
    base_profit, base_yield = _profit_and_yield(scenario)
    results: list[DecisionResult] = []

    for cand in _catalog():
        if not cand.applicable(scenario):
            continue
        action_scn = cand.transform(scenario)
        act_profit, act_yield = _profit_and_yield(action_scn)
        d_profit = round(act_profit - base_profit, 0)
        d_yield = round(act_yield - base_yield, 2)
        prob = _probability_positive(scenario, action_scn, n_prob, seed)
        roi = None
        if cand.added_cost_per_ha > 0:
            roi = round(d_profit / cand.added_cost_per_ha, 2)
        results.append(
            DecisionResult(
                key=cand.key, label=cand.label, description=cand.description,
                category=cand.category, added_cost_per_ha=cand.added_cost_per_ha,
                delta_yield_sc_ha=d_yield, delta_profit_per_ha=d_profit,
                action_roi=roi, probability_positive=prob, justification=cand.justification,
            )
        )

    results.sort(key=lambda r: r.delta_profit_per_ha, reverse=True)
    return results[:top] if top else results
