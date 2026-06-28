"use client";

import type { EconomicsOut } from "@/lib/types";

const brl = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });

function Metric({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="rounded-lg bg-stone-100 px-3 py-2">
      <div className="text-[11px] uppercase tracking-wide text-stone-500">{label}</div>
      <div className={`text-lg font-semibold ${accent ? "text-leafdark" : "text-stone-800"}`}>
        {value}
      </div>
    </div>
  );
}

export function EconomicsCard({ e }: { e: EconomicsOut }) {
  return (
    <div>
      <h3 className="mb-2 text-sm font-semibold text-stone-600">Resultado econômico (por ha)</h3>
      <div className="grid grid-cols-2 gap-2 md:grid-cols-3">
        <Metric label="Lucro líquido" value={brl(e.profit_per_ha)} accent />
        <Metric label="ROI" value={`${e.roi.toFixed(2)}x`} />
        <Metric label="Margem" value={`${e.margin_pct.toFixed(0)}%`} />
        <Metric label="Custo total" value={brl(e.total_cost_per_ha)} />
        <Metric label="Receita" value={brl(e.revenue_per_ha)} />
        <Metric label="Break-even" value={`${e.breakeven_yield_sc_ha.toFixed(1)} sc`} />
      </div>
      <p className="mt-2 text-xs text-stone-500">
        Preço mínimo de equilíbrio: {brl(e.breakeven_price_per_sc)}/saca.
      </p>
    </div>
  );
}
