"use client";

import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ScenarioIn } from "@/lib/types";

const brl = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });

export function CounterfactualPanel({ scenario }: { scenario: ScenarioIn }) {
  const cf = useMutation({ mutationFn: () => api.counterfactual(scenario) });
  const d = cf.data;

  return (
    <div>
      <div className="mb-1 flex items-baseline justify-between">
        <h3 className="text-sm font-semibold text-stone-600">🔀 E se… (universos paralelos)</h3>
        <span className="text-xs text-stone-400">simulação causal</span>
      </div>
      <p className="mb-3 text-xs text-stone-500">
        Re-simula a safra mudando UMA decisão por vez — "e se eu não tivesse aplicado o fungicida?",
        "e se tivesse plantado antes?" — e mede o quanto cada escolha pesou, em sc/ha e R$.
      </p>

      <button
        onClick={() => cf.mutate()}
        disabled={cf.isPending}
        className="rounded-md bg-leaf px-3 py-1.5 text-sm font-medium text-white hover:bg-leafdark disabled:opacity-60"
      >
        {cf.isPending ? "Rodando universos…" : "Explorar cenários alternativos"}
      </button>

      {d && (
        <ul className="mt-3 space-y-2">
          {d.counterfactuals.map((x) => {
            const up = x.delta_profit_per_ha >= 0;
            return (
              <li key={x.key} className="rounded-lg border border-stone-200 p-2.5">
                <div className="flex items-start justify-between gap-3">
                  <span className="text-sm text-stone-800">{x.label}</span>
                  <span className={`shrink-0 text-right text-sm font-semibold ${up ? "text-leaf" : "text-orange-700"}`}>
                    {x.delta_yield_sc_ha >= 0 ? "+" : ""}
                    {x.delta_yield_sc_ha.toFixed(1)} sc/ha
                    <div className="text-xs font-normal">
                      {up ? "+" : ""}
                      {brl(x.delta_profit_per_ha)}/ha
                    </div>
                  </span>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
