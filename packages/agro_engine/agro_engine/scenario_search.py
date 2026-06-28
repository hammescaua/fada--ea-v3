"""Motor de Cenários — combina os manejos e acha o melhor plano para o talhão.

Este é o ápice do método: em vez de o agricultor testar uma combinação por vez, o motor
**varre o espaço de decisões** (data de semeadura × população × programa de fungicida),
simula cada combinação com o modelo determinístico e **ranqueia por lucro**, devolvendo
o **melhor plano para aquele talhão** + a explicação transparente de *por que* ele vence.

Tudo reusa o mesmo método único: cada manejo é um fator no IPPD, com preço do catálogo e
impacto medido pela simulação — então o resultado é coerente e auditável, não um chute.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta

from . import reference as ref
from . import sowing_window
from .decision import _profit_and_yield
from .fertility import recommend_amendments
from .models import Operation, Scenario
from .simulate import simulate


def _candidate(base: Scenario, sdate: date, pop: float, n_fung: int) -> Scenario:
    """Constrói um cenário candidato variando data, população e nº de fungicidas."""
    ops = [o for o in base.operations if o.kind.lower() != "fungicida"]
    # fungicidas posicionados no período reprodutivo (≈ R1 em diante)
    ops = ops + [
        Operation(kind="fungicida", op_date=sdate + timedelta(days=66 + i * 14), cost_per_ha=180.0, quality=0.9)
        for i in range(n_fung)
    ]
    return replace(base, sowing_date=sdate, population_k_per_ha=pop, operations=ops)


def _default_sowing_dates(scenario: Scenario) -> list[date]:
    """Datas candidatas dentro/à volta da janela ZARC do município."""
    year = scenario.sowing_date.year if scenario.sowing_date.month >= 7 else scenario.sowing_date.year - 1
    rec = sowing_window.recommend(scenario.municipality, year)
    start = date.fromisoformat(rec["window_start"])
    end = date.fromisoformat(rec["window_end"])
    span = (end - start).days
    steps = sorted({0, span // 4, span // 2, (3 * span) // 4, span})
    return [start + timedelta(days=d) for d in steps]


def optimize_season(
    scenario: Scenario,
    sowing_dates: list[date] | None = None,
    populations: list[float] | None = None,
    fungicida_counts: list[int] | None = None,
    top: int = 5,
) -> dict:
    """Varre as combinações de manejo e devolve o melhor plano para o talhão + explicação."""
    sowing_dates = sowing_dates or _default_sowing_dates(scenario)
    populations = populations or [240.0, 280.0, 320.0]
    fungicida_counts = fungicida_counts or [1, 2, 3]

    base_profit, base_yield = _profit_and_yield(scenario)
    results: list[dict] = []
    for sd in sowing_dates:
        for pop in populations:
            for nf in fungicida_counts:
                cand = _candidate(scenario, sd, pop, nf)
                profit, yld = _profit_and_yield(cand)
                results.append(
                    {
                        "sowing_date": sd.isoformat(),
                        "population_k_per_ha": pop,
                        "num_fungicidas": nf,
                        "expected_sc_ha": yld,
                        "profit_per_ha": profit,
                        "_scenario": cand,
                    }
                )

    results.sort(key=lambda r: r["profit_per_ha"], reverse=True)
    best = results[0]
    best_scn: Scenario = best["_scenario"]

    # explicação do vencedor: decomposição IPPD + por que cada escolha
    sim = simulate(best_scn)
    sow_eval = sowing_window.evaluate(best_scn.municipality, best_scn.sowing_date)
    lo, hi = ref.POPULATION_OPTIMAL_K
    porques: list[str] = []
    if sow_eval.get("position") in ("otimo", "dentro_da_janela"):
        porques.append("Data dentro da janela do ZARC — menor perda por época de semeadura.")
    if lo <= best["population_k_per_ha"] <= hi:
        porques.append(f"População de {best['population_k_per_ha']:.0f} mil/ha na faixa ótima da cultura.")
    porques.append(
        f"{best['num_fungicidas']} aplicação(ões) de fungicida para a pressão de ferrugem da região "
        f"(retorno marginal decrescente acima disso)."
    )

    amendments = recommend_amendments(scenario)

    def _clean(r: dict) -> dict:
        return {k: v for k, v in r.items() if k != "_scenario"}

    return {
        "combinacoes_avaliadas": len(results),
        "atual": {"expected_sc_ha": round(base_yield, 1), "profit_per_ha": round(base_profit, 0)},
        "melhor_plano": {
            **_clean(best),
            "delta_profit_vs_atual": round(best["profit_per_ha"] - base_profit, 0),
            "delta_yield_vs_atual": round(best["expected_sc_ha"] - base_yield, 1),
        },
        "ranking": [_clean(r) for r in results[:top]],
        "decomposicao": [
            {"fator": c.label, "delta_sc_ha": c.delta_sc_ha, "detalhe": c.detail}
            for c in sim.yield_result.contributions
        ],
        "porques": porques,
        "fertilidade": [
            {"acao": a.label, "investimento_por_ha": a.investment_per_ha, "liquido_por_ano": a.net_per_ha, "roi": a.roi}
            for a in amendments
        ],
    }
