"use client";

import type { AccuracyOut, AccuracyVariable } from "@/lib/types";

const labelCls: Record<string, string> = {
  alta: "text-leaf",
  média: "text-amber-600",
  baixa: "text-orange-700",
};

function Row({ v }: { v: AccuracyVariable }) {
  return (
    <details className="rounded-lg border border-stone-200 p-2.5">
      <summary className="flex cursor-pointer items-center justify-between gap-2">
        <span className="flex items-center gap-2">
          <span
            className={`h-2 w-2 rounded-full ${
              v.quality >= 0.7 ? "bg-leaf" : v.quality >= 0.5 ? "bg-amber-400" : "bg-orange-500"
            }`}
          />
          <span className="text-sm font-medium text-stone-800">{v.label}</span>
          <span
            className={`rounded px-1 py-0.5 text-[10px] font-medium ${
              v.is_local ? "bg-green-100 text-leafdark" : "bg-amber-100 text-amber-700"
            }`}
          >
            {v.is_local ? "específico do talhão" : "default regional"}
          </span>
        </span>
        <span className="shrink-0 text-xs text-stone-400">
          {v.leverage_sc_ha > 0 ? `±${v.leverage_sc_ha.toFixed(0)} sc/ha` : "—"}
        </span>
      </summary>

      <div className="mt-2 space-y-1.5 text-xs">
        <div>
          <span className="text-stone-400">Fonte em uso:</span>{" "}
          <span className="text-stone-700">{v.current_label}</span>
          {v.current_note && <span className="text-stone-400"> — {v.current_note}</span>}
        </div>
        <div>
          <span className="text-stone-400">Influencia:</span>{" "}
          <span className="text-stone-600">{v.drives.join(" · ")}</span>
        </div>
        {!v.is_local && (
          <div className="rounded bg-amber-50 px-2 py-1 text-amber-800">
            <span className="font-medium">Como deixar mais preciso:</span> {v.how_to_improve}
          </div>
        )}
        <div className="text-[11px] text-stone-400">Fonte de referência: {v.source}</div>
      </div>
    </details>
  );
}

export function AccuracyPanel({ acc }: { acc: AccuracyOut | undefined }) {
  if (!acc) return null;
  const pct = Math.round(acc.precision_index * 100);

  return (
    <div>
      <div className="mb-1 flex items-baseline justify-between">
        <h3 className="text-sm font-semibold text-stone-600">🎯 Precisão para este talhão</h3>
        <span className={`text-sm font-bold ${labelCls[acc.precision_label] ?? "text-stone-600"}`}>
          {acc.precision_label} ({pct}%)
        </span>
      </div>
      <p className="mb-3 text-xs text-stone-500">
        A estimativa é tão boa quanto os dados que a alimentam. Veja, variável por variável, de
        onde vem cada dado, se é específico do seu talhão ou um default regional, e o que medir
        primeiro para a recomendação ficar mais verídica.
      </p>

      <div className="mb-3 h-2 w-full overflow-hidden rounded-full bg-stone-200">
        <div
          className={`h-2 rounded-full ${pct >= 75 ? "bg-leaf" : pct >= 50 ? "bg-amber-400" : "bg-orange-500"}`}
          style={{ width: `${pct}%` }}
        />
      </div>

      {acc.top_improvements.some((i) => i.leverage_sc_ha > 0) && (
        <div className="mb-3 rounded-lg bg-leaf/5 p-2.5">
          <div className="text-[11px] font-semibold uppercase tracking-wide text-stone-500">
            Para aumentar a precisão, meça primeiro
          </div>
          <ol className="mt-1 space-y-1">
            {acc.top_improvements
              .filter((i) => i.leverage_sc_ha > 0)
              .map((i, idx) => (
                <li key={i.group} className="text-xs text-stone-700">
                  <span className="font-medium">
                    {idx + 1}. {i.label}
                  </span>{" "}
                  <span className="text-stone-400">(±{i.leverage_sc_ha.toFixed(0)} sc/ha)</span> —{" "}
                  {i.how_to_improve}
                </li>
              ))}
          </ol>
        </div>
      )}

      <div className="space-y-1.5">
        {acc.variables.map((v) => (
          <Row key={v.group} v={v} />
        ))}
      </div>
    </div>
  );
}
