"use client";

import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ScenarioIn } from "@/lib/types";

const brl = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });

export function SeasonReviewPanel({
  fieldId,
  scenario,
}: {
  fieldId: string | null;
  scenario: ScenarioIn;
}) {
  const rev = useMutation({ mutationFn: () => api.seasonReview(fieldId!, scenario) });
  const d = rev.data;

  if (!fieldId) {
    return (
      <div>
        <h3 className="mb-1 text-sm font-semibold text-stone-600">⚖️ Plano vs. Realidade</h3>
        <p className="text-xs text-stone-500">
          Selecione um talhão e registre evidências (aplicação, chuva, emergência…). O gêmeo
          realimenta o que de fato aconteceu no modelo — ex.: uma aplicação lavada por chuva passa
          a valer menos — e mostra como o resultado mudou, com fonte.
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-1 flex items-baseline justify-between">
        <h3 className="text-sm font-semibold text-stone-600">⚖️ Plano vs. Realidade</h3>
        <span className="text-xs text-stone-400">o que as evidências mudaram</span>
      </div>
      <p className="mb-3 text-xs text-stone-500">
        Compara o plano com o que aconteceu de fato no talhão (a partir das evidências) e ajusta o
        modelo à realidade — cada ajuste é fundamentado e citado.
      </p>

      <button
        onClick={() => rev.mutate()}
        disabled={rev.isPending}
        className="rounded-md bg-leaf px-3 py-1.5 text-sm font-medium text-white hover:bg-leafdark disabled:opacity-60"
      >
        {rev.isPending ? "Revisando a safra…" : "Comparar plano com a realidade"}
      </button>

      {d && (
        <div className="mt-3 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-lg bg-stone-50 p-2.5">
              <div className="text-[11px] uppercase text-stone-400">Plano</div>
              <div className="text-sm font-semibold text-stone-700">
                {d.plano.expected_sc_ha.toFixed(0)} sc/ha
              </div>
              <div className="text-xs text-stone-500">{brl(d.plano.profit_per_ha)}/ha</div>
            </div>
            <div className="rounded-lg bg-green-50 p-2.5">
              <div className="text-[11px] uppercase text-stone-400">Realidade (ajustada)</div>
              <div className="text-sm font-semibold text-leafdark">
                {d.realidade.expected_sc_ha.toFixed(0)} sc/ha
              </div>
              <div className="text-xs text-stone-500">{brl(d.realidade.profit_per_ha)}/ha</div>
            </div>
          </div>

          {d.adjustments.length === 0 ? (
            <p className="text-xs text-stone-500">
              Nenhuma evidência alterou o resultado — o plano segue coerente com o observado.
            </p>
          ) : (
            <>
              <div
                className={`text-sm font-semibold ${d.delta_sc_ha >= 0 ? "text-leaf" : "text-orange-700"}`}
              >
                Efeito da realidade: {d.delta_sc_ha >= 0 ? "+" : ""}
                {d.delta_sc_ha.toFixed(1)} sc/ha · {d.delta_profit_per_ha >= 0 ? "+" : ""}
                {brl(d.delta_profit_per_ha)}/ha
              </div>
              <ul className="space-y-1.5">
                {d.adjustments.map((a, i) => (
                  <li key={i} className="rounded-lg border border-stone-200 p-2 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-stone-700">
                        {a.factor} · {a.manejo}
                      </span>
                      <span className="text-stone-400">
                        {a.before} → {a.after} · conf {Math.round(a.confidence * 100)}%
                      </span>
                    </div>
                    <p className="mt-0.5 text-stone-600">{a.reason}</p>
                    <p className="mt-0.5 text-[10px] text-stone-400">fonte: {a.source}</p>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  );
}
