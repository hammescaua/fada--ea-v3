"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Hypothesis, ScenarioIn } from "@/lib/types";

function HypothesisRow({ h }: { h: Hypothesis }) {
  const prob = Math.round(h.probabilidade * 100);
  return (
    <details className="rounded-lg border border-stone-200 p-2.5">
      <summary className="flex cursor-pointer items-center justify-between gap-2">
        <span className="flex items-center gap-2">
          <span
            className={`flex h-7 w-9 shrink-0 items-center justify-center rounded text-xs font-bold ${
              prob >= 70 ? "bg-orange-100 text-orange-700" : prob >= 40 ? "bg-amber-100 text-amber-700" : "bg-stone-100 text-stone-500"
            }`}
          >
            {prob}%
          </span>
          <span className="text-sm font-medium text-stone-800">{h.causa}</span>
          {h.a_confirmar && (
            <span className="rounded bg-amber-100 px-1 py-0.5 text-[10px] font-medium uppercase text-amber-700">a confirmar</span>
          )}
        </span>
        <span className="shrink-0 text-xs font-semibold text-orange-700">−{h.perda_sc_ha.toFixed(1)} sc/ha</span>
      </summary>
      <div className="mt-2 space-y-1.5 text-xs">
        <div>
          <span className="text-stone-400">Como limita (cadeia de impacto):</span>
          <div className="mt-1 flex flex-wrap items-center gap-1 text-stone-600">
            {h.cadeia.map((step, i) => (
              <span key={i} className="flex items-center gap-1">
                <span className="rounded bg-stone-100 px-1.5 py-0.5">{step}</span>
                {i < h.cadeia.length - 1 && <span className="text-stone-300">→</span>}
              </span>
            ))}
          </div>
        </div>
        <div className="rounded bg-leaf/5 px-2 py-1 text-stone-700">
          <span className="font-medium">O que fazer:</span> {h.acao}
        </div>
        <div className="text-stone-500">
          <span className="font-medium">Para confirmar:</span> {h.confirma_se} · confiança do dado {Math.round(h.certeza_do_dado * 100)}%
        </div>
        <div className="text-[10px] text-stone-400">fonte: {h.fonte}</div>
      </div>
    </details>
  );
}

export function DiagnosisPanel({ scenario }: { scenario: ScenarioIn }) {
  const { data } = useQuery({
    queryKey: ["diagnose", scenario],
    queryFn: () => api.diagnose(scenario),
    placeholderData: (prev) => prev,
  });
  if (!data) return null;

  return (
    <div>
      <div className="mb-1 flex items-baseline justify-between">
        <h3 className="text-sm font-semibold text-stone-600">🔬 Diagnóstico — por que não colho mais?</h3>
        {data.gap_sc_ha > 0 && (
          <span className="text-xs text-stone-400">gap de {data.gap_sc_ha.toFixed(0)} sc/ha vs. potencial</span>
        )}
      </div>
      <p className="mb-3 text-xs text-stone-500">{data.resumo}</p>
      {data.hipoteses.length === 0 ? (
        <p className="rounded-lg bg-green-50 p-3 text-xs text-leafdark">Talhão próximo do potencial — nada relevante a investigar.</p>
      ) : (
        <div className="space-y-1.5">
          {data.hipoteses.slice(0, 5).map((h, i) => (
            <HypothesisRow key={i} h={h} />
          ))}
        </div>
      )}
    </div>
  );
}
