"use client";

import { useState } from "react";
import type { FertilityRec } from "@/lib/types";

const brl = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });

function Row({ r }: { r: FertilityRec }) {
  const [open, setOpen] = useState(false);
  const good = r.net_per_ha >= 0;
  return (
    <li className="rounded-lg border border-stone-200">
      <button onClick={() => setOpen((v) => !v)} className="flex w-full items-center gap-3 px-3 py-2 text-left">
        <span className="min-w-0 flex-1">
          <span className="block text-sm font-medium text-stone-800">{r.label}</span>
          <span className="block text-[11px] text-stone-500">
            {r.product} · {r.dose.toLocaleString("pt-BR", { maximumFractionDigits: 1 })} {r.dose_unit} · invest{" "}
            {brl(r.investment_per_ha)} ({r.residual_years}a)
          </span>
        </span>
        <span className="text-right">
          <span className={`block text-sm font-semibold ${good ? "text-leafdark" : "text-orange-700"}`}>
            {good ? "+" : ""}
            {brl(r.net_per_ha)}/ano
          </span>
          <span className="block text-[11px] text-stone-500">
            +{r.delta_yield_sc_ha.toFixed(1)} sc · ROI {r.roi != null ? `${r.roi.toFixed(1)}x` : "—"}
          </span>
        </span>
      </button>
      {open && <p className="border-t border-stone-100 px-3 py-2 text-xs text-stone-600">{r.rationale}</p>}
    </li>
  );
}

export function FertilityPanel({ recs, loading }: { recs?: FertilityRec[]; loading: boolean }) {
  return (
    <div>
      <div className="mb-1 flex items-baseline justify-between">
        <h3 className="text-sm font-semibold text-stone-600">🧪 Fertilidade — corretivos &amp; adubação</h3>
        {loading && <span className="text-xs text-stone-400">avaliando…</span>}
      </div>
      <p className="mb-3 text-xs text-stone-500">
        A partir da análise de solo do talhão, a dose certa (método CQFS-RS/SC), o investimento
        (preço de referência) e o retorno — ranqueado por rentabilidade (custo amortizado pelo
        efeito residual). Clique para ver o porquê.
      </p>
      {!recs || recs.length === 0 ? (
        <p className="text-sm text-stone-400">
          {loading ? "Calculando…" : "Solo dentro das faixas de suficiência — sem correção necessária."}
        </p>
      ) : (
        <ul className="space-y-2">
          {recs.map((r) => (
            <Row key={r.key} r={r} />
          ))}
        </ul>
      )}
    </div>
  );
}
