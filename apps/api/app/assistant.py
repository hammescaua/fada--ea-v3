"""Assistente de decisão (Nível 3) — o "ChatGPT da fazenda".

Princípio do briefing: **o LLM nunca faz contas**. Ele interpreta a pergunta, chama os
motores determinísticos (via *tool use*) que calculam de verdade, e narra os números
retornados em linguagem natural. Nunca inventa valores.

- Modelo: Claude Opus 4.8 (`claude-opus-4-8`) via SDK oficial `anthropic`, com
  *adaptive thinking* e *tool use* (loop agêntico manual).
- Sem chave de API (`ANTHROPIC_API_KEY` ausente) ou sem rede, cai para um **narrador
  determinístico** que monta a resposta a partir dos mesmos motores — então o recurso
  funciona e é testável mesmo offline.

As ferramentas expostas ao modelo apenas **leem** os motores do agro_engine; toda a
matemática (IPPD, Monte Carlo, decisão) acontece no Python determinístico.
"""

from __future__ import annotations

import json
import os
from dataclasses import replace
from datetime import date, timedelta

from agro_engine import (
    recommend_amendments,
    recommend_decisions,
    run_montecarlo,
    simulate,
)
from agro_engine.models import Operation, Scenario

MODEL = "claude-opus-4-8"

SYSTEM_PROMPT = """Você é o assistente agronômico do FADA, um Gêmeo Digital de lavouras \
de soja do Noroeste do Rio Grande do Sul. Você apoia o agricultor a decidir o manejo da safra.

REGRAS ABSOLUTAS:
- Você NUNCA calcula nem inventa números. Para qualquer estimativa de produtividade, \
lucro, risco ou recomendação, você DEVE chamar as ferramentas disponíveis, que rodam os \
modelos agronômicos determinísticos (fenologia, balanço hídrico FAO-56, decomposição IPPD, \
Monte Carlo, motor de decisão). Use SOMENTE os números retornados pelas ferramentas.
- Responda em português do Brasil, de forma objetiva e prática, como um agrônomo de confiança.
- Sempre que citar produtividade, mostre a faixa de incerteza; sempre que citar uma decisão, \
cite o impacto no lucro (R$/ha) e a probabilidade de retorno.
- Se a pergunta envolver "e se" (mudar data, população, fungicida, adubação), use a \
ferramenta de simulação com os ajustes para comparar com o cenário atual.
- Seja transparente sobre o porquê: explique qual fator pesou (água, janela, nutrição, sanidade)."""


# --- Ferramentas (tool definitions) -----------------------------------------
TOOLS = [
    {
        "name": "simular_cenario",
        "description": (
            "Roda a simulação determinística do talhão (fenologia, água, IPPD, econômico) "
            "para o cenário ATUAL, opcionalmente com ajustes 'e se'. Retorna produtividade "
            "esperada ± incerteza, a decomposição por fator e o resultado econômico. Use para "
            "responder 'quanto vou colher/lucrar' e para comparar mudanças de manejo."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sowing_date": {"type": "string", "description": "Nova data de semeadura ISO (YYYY-MM-DD), opcional"},
                "population_k_per_ha": {"type": "number", "description": "Nova população em mil plantas/ha, opcional"},
                "num_fungicidas": {"type": "integer", "description": "Nº de aplicações de fungicida, opcional"},
                "phosphorus_ppm": {"type": "number", "description": "Novo P do solo em ppm, opcional"},
                "ph": {"type": "number", "description": "Novo pH do solo, opcional"},
                "price_per_sc": {"type": "number", "description": "Novo preço da saca em R$, opcional"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "analise_risco",
        "description": (
            "Roda o Monte Carlo (milhares de safras com clima e preço estocásticos) e retorna "
            "a distribuição de lucro (p10/p50/p90), a probabilidade de lucro acima de uma meta e "
            "a probabilidade de prejuízo. Use para perguntas sobre risco e probabilidade."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "profit_target_per_ha": {"type": "number", "description": "Meta de lucro R$/ha para P(lucro≥meta)"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "recomendar_fertilidade",
        "description": (
            "A partir da análise de solo do talhão, recomenda corretivos/adubação (calagem, "
            "fósforo, potássio): a dose pelo método CQFS-RS/SC, o investimento (preço de "
            "referência), o impacto na produtividade e o ROI — ranqueado por rentabilidade. "
            "Use para 'vale a pena calcário/adubar?', 'qual investimento é melhor para o meu solo?'."
        ),
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "recomendar_decisoes",
        "description": (
            "Roda o Motor de Decisão: avalia as intervenções possíveis no talhão e devolve as "
            "ações ordenadas por retorno esperado (Δprodutividade, Δlucro, ROI da ação e "
            "probabilidade de retorno positivo). Use para 'o que devo fazer' / 'o que mais compensa'."
        ),
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
]


def _apply_overrides(scenario: Scenario, args: dict) -> Scenario:
    """Aplica ajustes 'e se' a uma cópia do cenário (sem mutar o original)."""
    patch: dict = {}
    if args.get("sowing_date"):
        patch["sowing_date"] = date.fromisoformat(args["sowing_date"])
    if args.get("population_k_per_ha") is not None:
        patch["population_k_per_ha"] = float(args["population_k_per_ha"])
    if args.get("price_per_sc") is not None:
        patch["soybean_price_per_sc"] = float(args["price_per_sc"])

    soil = scenario.soil
    soil_patch: dict = {}
    if args.get("phosphorus_ppm") is not None:
        soil_patch["phosphorus_ppm"] = float(args["phosphorus_ppm"])
    if args.get("ph") is not None:
        soil_patch["ph"] = float(args["ph"])
    if soil_patch:
        patch["soil"] = replace(soil, **soil_patch)

    if args.get("num_fungicidas") is not None:
        n = int(args["num_fungicidas"])
        base = date(scenario.sowing_date.year + 1, 1, 10)
        ops = [o for o in scenario.operations if o.kind.lower() != "fungicida"]
        ops += [
            Operation(kind="fungicida", op_date=base + timedelta(days=i * 14), cost_per_ha=180.0, quality=0.9)
            for i in range(n)
        ]
        patch["operations"] = ops

    return replace(scenario, **patch) if patch else scenario


def dispatch_tool(name: str, args: dict, scenario: Scenario) -> dict:
    """Executa uma ferramenta — toda a matemática vive aqui, no motor determinístico."""
    if name == "simular_cenario":
        scn = _apply_overrides(scenario, args)
        result = simulate(scn)
        return {
            "produtividade_esperada_sc_ha": result.yield_result.expected_sc_ha,
            "incerteza_sc_ha": result.yield_result.uncertainty_sc_ha,
            "confianca": result.yield_result.confidence,
            "decomposicao": [
                {"fator": c.label, "delta_sc_ha": c.delta_sc_ha, "detalhe": c.detail}
                for c in result.yield_result.contributions
            ],
            "lucro_por_ha": result.economics.profit_per_ha,
            "roi": result.economics.roi,
            "break_even_sc_ha": result.economics.breakeven_yield_sc_ha,
            "janela_semeadura": result.sowing_window,
        }
    if name == "analise_risco":
        target = float(args.get("profit_target_per_ha", 0.0))
        mc = run_montecarlo(scenario, n=2000, seed=7, profit_target_per_ha=target)
        return {
            "lucro_p10": mc["profit"]["p10"],
            "lucro_p50": mc["profit"]["p50"],
            "lucro_p90": mc["profit"]["p90"],
            "prob_lucro_acima_meta": mc["probabilities"]["profit_above_target"],
            "meta_lucro": mc["probabilities"]["profit_target"],
            "prob_prejuizo": mc["probabilities"]["loss"],
            "produtividade_p50": mc["yield"]["p50"],
        }
    if name == "recomendar_fertilidade":
        return {
            "recomendacoes": [
                {
                    "acao": r.label, "produto": r.product, "dose": r.dose, "unidade": r.dose_unit,
                    "investimento_por_ha": r.investment_per_ha, "anos_residual": r.residual_years,
                    "custo_anual_por_ha": r.annual_cost_per_ha, "delta_produtividade_sc_ha": r.delta_yield_sc_ha,
                    "liquido_por_ano_por_ha": r.net_per_ha, "roi": r.roi, "justificativa": r.rationale,
                }
                for r in recommend_amendments(scenario)
            ]
        }
    if name == "recomendar_decisoes":
        recs = recommend_decisions(scenario, n_prob=300, seed=11, top=5)
        return {
            "decisoes": [
                {
                    "acao": r.label,
                    "delta_produtividade_sc_ha": r.delta_yield_sc_ha,
                    "delta_lucro_por_ha": r.delta_profit_per_ha,
                    "roi_acao": r.action_roi,
                    "prob_retorno_positivo": r.probability_positive,
                    "justificativa": r.justification,
                }
                for r in recs
            ]
        }
    return {"erro": f"ferramenta desconhecida: {name}"}


def _llm_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def ask(question: str, scenario: Scenario, max_iterations: int = 5) -> dict:
    """Responde à pergunta do agricultor usando o LLM + ferramentas, com fallback offline."""
    if not _llm_available():
        return _deterministic_answer(question, scenario)
    try:
        return _llm_answer(question, scenario, max_iterations)
    except Exception as exc:  # noqa: BLE001 — degrada para o narrador determinístico
        out = _deterministic_answer(question, scenario)
        out["note"] = f"LLM indisponível ({type(exc).__name__}); resposta gerada pelo narrador determinístico."
        return out


def _llm_answer(question: str, scenario: Scenario, max_iterations: int) -> dict:
    import anthropic  # import tardio: só quando há chave

    client = anthropic.Anthropic()
    messages: list[dict] = [{"role": "user", "content": question}]
    tool_trace: list[dict] = []

    for _ in range(max_iterations):
        response = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            thinking={"type": "adaptive"},
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )
        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            results = []
            for block in response.content:
                if block.type == "tool_use":
                    out = dispatch_tool(block.name, dict(block.input), scenario)
                    tool_trace.append({"tool": block.name, "input": dict(block.input), "output": out})
                    results.append(
                        {"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(out, ensure_ascii=False)}
                    )
            messages.append({"role": "user", "content": results})
            continue
        # resposta final
        text = "".join(b.text for b in response.content if b.type == "text")
        return {"answer": text, "used_llm": True, "tool_calls": tool_trace}

    return {"answer": "Não consegui concluir a análise.", "used_llm": True, "tool_calls": tool_trace}


def _deterministic_answer(question: str, scenario: Scenario) -> dict:
    """Narrador determinístico (sem LLM): roda os motores e monta uma resposta em pt-BR.

    Honra o mesmo princípio — todos os números vêm dos motores, nada é inventado.
    """
    sim = dispatch_tool("simular_cenario", {}, scenario)
    risk = dispatch_tool("analise_risco", {"profit_target_per_ha": 3500.0}, scenario)
    decisions = dispatch_tool("recomendar_decisoes", {}, scenario)
    fertility = dispatch_tool("recomendar_fertilidade", {}, scenario)

    brl = lambda v: f"R$ {v:,.0f}".replace(",", ".")
    top = decisions["decisoes"][0] if decisions["decisoes"] else None
    piores = sorted(sim["decomposicao"], key=lambda c: c["delta_sc_ha"])[:2]

    linhas = [
        f"Para este talhão, a produtividade esperada é "
        f"**{sim['produtividade_esperada_sc_ha']:.1f} ± {sim['incerteza_sc_ha']:.1f} sc/ha** "
        f"(confiança {sim['confianca'] * 100:.0f}%), com lucro de **{brl(sim['lucro_por_ha'])}/ha** "
        f"(ROI {sim['roi']:.2f}x, break-even {sim['break_even_sc_ha']:.1f} sc/ha).",
        "",
        "O que mais limitou o potencial: "
        + "; ".join(f"{c['fator']} ({c['delta_sc_ha']:+.1f} sc/ha — {c['detalhe']})" for c in piores)
        + ".",
        "",
        f"Risco (Monte Carlo): lucro provável {brl(risk['lucro_p50'])}/ha "
        f"(faixa {brl(risk['lucro_p10'])} a {brl(risk['lucro_p90'])}/ha); "
        f"chance de lucro ≥ {brl(risk['meta_lucro'])}/ha: {risk['prob_lucro_acima_meta'] * 100:.0f}%; "
        f"chance de prejuízo: {risk['prob_prejuizo'] * 100:.1f}%.",
    ]
    if top:
        roi = f", ROI {top['roi_acao']:.1f}x" if top["roi_acao"] is not None else ""
        linhas += [
            "",
            f"Ação mais recomendada: **{top['acao']}** — impacto de "
            f"{top['delta_lucro_por_ha']:+.0f} R$/ha ({top['delta_produtividade_sc_ha']:+.1f} sc/ha{roi}), "
            f"com {top['prob_retorno_positivo'] * 100:.0f}% de chance de retorno positivo. "
            f"{top['justificativa']}",
        ]

    fert = fertility.get("recomendacoes", [])
    if fert:
        f0 = fert[0]
        froi = f", ROI {f0['roi']:.1f}x" if f0["roi"] is not None else ""
        linhas += [
            "",
            f"Fertilidade do solo: a correção mais rentável é **{f0['acao']}** "
            f"({f0['dose']:.1f} {f0['unidade']} de {f0['produto']}, investimento {brl(f0['investimento_por_ha'])}/ha "
            f"em {f0['anos_residual']} ano(s)), agregando {f0['delta_produtividade_sc_ha']:+.1f} sc/ha — "
            f"líquido {brl(f0['liquido_por_ano_por_ha'])}/ano{froi}. {f0['justificativa']}",
        ]

    return {
        "answer": "\n".join(linhas),
        "used_llm": False,
        "tool_calls": [
            {"tool": "simular_cenario", "output": sim},
            {"tool": "analise_risco", "output": risk},
            {"tool": "recomendar_decisoes", "output": decisions},
        ],
    }
