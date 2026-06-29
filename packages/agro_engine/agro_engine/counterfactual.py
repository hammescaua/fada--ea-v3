"""Counterfactual Engine — os universos paralelos da safra ("E se...").

Hoje o motor simula um cenário. Aqui ele responde perguntas **causais e contrafactuais**
sobre a safra real: *e se eu não tivesse aplicado o último fungicida? e se tivesse
plantado 8 dias antes? e se a cultivar fosse mais tolerante?* Cada pergunta re-simula o
talhão com a mudança e mede o Δ em produtividade e lucro contra o cenário de referência.

Reaproveita o mesmo pipeline determinístico (re-simulação com/sem a mudança), então as
respostas são coerentes com tudo que a plataforma calcula — não são chutes.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import timedelta

from . import reference as ref
from . import sowing_window
from .decision import _fungicidas, _profit_and_yield
from .models import CostItem, Scenario


@dataclass
class CounterfactualResult:
    key: str
    label: str
    delta_yield_sc_ha: float
    delta_profit_per_ha: float
    expected_sc_ha: float
    profit_per_ha: float
    narrative: str


def _shift_sowing(s: Scenario, days: int) -> Scenario:
    return replace(s, sowing_date=s.sowing_date + timedelta(days=days))


def _remove_last_fungicide(s: Scenario) -> Scenario:
    fung = _fungicidas(s)
    if not fung:
        return s
    last = fung[-1]
    return replace(s, operations=[o for o in s.operations if o is not last])


def _remove_all(s: Scenario, kind: str) -> Scenario:
    return replace(s, operations=[o for o in s.operations if o.kind.lower() != kind])


def _more_tolerant_cultivar(s: Scenario) -> Scenario:
    c = s.cultivar
    return replace(s, cultivar=replace(c, disease_tolerance=min(1.0, c.disease_tolerance + 0.2)))


def _correct_phosphorus(s: Scenario) -> Scenario:
    soil = replace(s.soil, phosphorus_ppm=max(s.soil.phosphorus_ppm, ref.P_SUFFICIENT_PPM + 2))
    cost = CostItem(category="fertilizante", description="Correção de P (contrafactual)", cost_per_ha=240.0)
    return replace(s, soil=soil, costs=[*s.costs, cost])


def _optimal_population(s: Scenario) -> Scenario:
    lo, hi = ref.POPULATION_OPTIMAL_K
    return replace(s, population_k_per_ha=(lo + hi) / 2)


def _default_specs(scenario: Scenario) -> list[tuple[str, str, object]]:
    """Conjunto de contrafactuais relevantes para o cenário (só os aplicáveis)."""
    specs: list[tuple[str, str, object]] = []
    if _fungicidas(scenario):
        specs.append(("sem_ultimo_fungicida", "E se eu não tivesse feito a última aplicação de fungicida?", _remove_last_fungicide))
        specs.append(("sem_fungicida", "E se eu não tivesse usado nenhum fungicida?", lambda s: _remove_all(s, "fungicida")))
    dev = sowing_window.evaluate(scenario.municipality, scenario.sowing_date).get("deviation_days", 0)
    specs.append(("plantio_8_antes", "E se eu tivesse plantado 8 dias antes?", lambda s: _shift_sowing(s, -8)))
    specs.append(("plantio_8_depois", "E se eu tivesse plantado 8 dias depois?", lambda s: _shift_sowing(s, 8)))
    if scenario.population_k_per_ha < ref.POPULATION_OPTIMAL_K[0] or scenario.population_k_per_ha > ref.POPULATION_OPTIMAL_K[1]:
        specs.append(("populacao_otima", "E se a população estivesse na faixa ótima?", _optimal_population))
    if scenario.soil.phosphorus_ppm < ref.P_SUFFICIENT_PPM:
        specs.append(("corrige_fosforo", "E se o fósforo do solo estivesse corrigido?", _correct_phosphorus))
    if scenario.cultivar.disease_tolerance < 0.7:
        specs.append(("cultivar_tolerante", "E se a cultivar fosse mais tolerante à ferrugem?", _more_tolerant_cultivar))
    return specs


def run_counterfactuals(scenario: Scenario, specs=None) -> dict:
    """Roda os contrafactuais e devolve o Δ de cada 'universo paralelo' vs. o real."""
    base_profit, base_yield = _profit_and_yield(scenario)
    specs = specs or _default_specs(scenario)
    results: list[CounterfactualResult] = []
    for key, label, transform in specs:
        scn = transform(scenario)
        profit, yld = _profit_and_yield(scn)
        d_yield = round(yld - base_yield, 1)
        d_profit = round(profit - base_profit, 0)
        results.append(
            CounterfactualResult(
                key=key, label=label,
                delta_yield_sc_ha=d_yield, delta_profit_per_ha=d_profit,
                expected_sc_ha=round(yld, 1), profit_per_ha=round(profit, 0),
                narrative=_narrate(label, d_yield, d_profit),
            )
        )
    # ordena pelo módulo do impacto (os universos que mais mudam a safra primeiro)
    results.sort(key=lambda r: abs(r.delta_profit_per_ha), reverse=True)
    return {
        "base_expected_sc_ha": round(base_yield, 1),
        "base_profit_per_ha": round(base_profit, 0),
        "counterfactuals": [r.__dict__ for r in results],
    }


def _narrate(label: str, d_yield: float, d_profit: float) -> str:
    if abs(d_yield) < 0.1 and abs(d_profit) < 1:
        return "Praticamente não mudaria o resultado."
    direc = "subiria" if d_yield >= 0 else "cairia"
    return (
        f"A produtividade {direc} {abs(d_yield):.1f} sc/ha e o lucro mudaria "
        f"{'+' if d_profit >= 0 else '−'}R$ {abs(d_profit):,.0f}/ha.".replace(",", ".")
    )
