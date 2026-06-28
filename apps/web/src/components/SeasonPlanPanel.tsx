"use client";

import type { SeasonPlanOut } from "@/lib/types";

const brl = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });

const CAT_LABEL: Record<string, string> = {
  semente: "Semente",
  fertilizante: "Fertilizante",
  corretivo: "Corretivo",
  defensivo: "Defensivo",
  herbicida: "Herbicida",
  inseticida: "Inseticida",
  fungicida: "Fungicida",
  diesel: "Diesel/operações",
  outros: "Outros",
};

export function SeasonPlanPanel({ plan }: { plan: SeasonPlanOut }) {
  const b = plan.budget;
  const cats = Object.entries(b.cost_by_category);
  const maxCat = Math.max(...cats.map(([, v]) => v), 1);

  return (
    <div className="space-y-4">
      <div className="flex items-baseline justify-between">
        <h3 className="text-sm font-semibold text-stone-600">📋 Plano &amp; orçamento da safra</h3>
        <span className="text-xs text-stone-500">planejamento → colheita → faturamento</span>
      </div>

      {/* Indicadores */}
      <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
        {[
          ["Custo total", brl(b.total_cost_per_ha), false],
          ["Faturamento", brl(b.revenue_per_ha), false],
          ["Lucro", brl(b.profit_per_ha), true],
          ["Capital de giro", brl(b.working_capital_per_ha), false],
        ].map(([label, value, accent]) => (
          <div key={label as string} className="rounded-lg bg-stone-100 px-3 py-2">
            <div className="text-[11px] uppercase tracking-wide text-stone-500">{label}</div>
            <div className={`text-base font-semibold ${accent ? "text-leafdark" : "text-stone-800"}`}>{value}</div>
          </div>
        ))}
      </div>

      {/* Custo por categoria */}
      <div>
        <div className="mb-1 text-xs font-medium text-stone-500">Custo por categoria (R$/ha)</div>
        <div className="space-y-1">
          {cats.map(([cat, v]) => (
            <div key={cat} className="flex items-center gap-2">
              <span className="w-28 shrink-0 text-xs text-stone-600">{CAT_LABEL[cat] ?? cat}</span>
              <div className="h-3 flex-1 overflow-hidden rounded bg-stone-100">
                <div className="h-full bg-soil/70" style={{ width: `${(v / maxCat) * 100}%` }} />
              </div>
              <span className="w-16 shrink-0 text-right text-xs text-stone-700">{brl(v)}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Impacto por manejo */}
      <div>
        <div className="mb-1 text-xs font-medium text-stone-500">
          Quanto cada manejo representa na safra (vs. não fazer)
        </div>
        <div className="overflow-hidden rounded-lg border border-stone-200">
          <table className="w-full text-xs">
            <thead className="bg-stone-50 text-stone-500">
              <tr>
                <th className="px-2 py-1 text-left font-medium">Manejo</th>
                <th className="px-2 py-1 text-right font-medium">Custo</th>
                <th className="px-2 py-1 text-right font-medium">Agrega</th>
                <th className="px-2 py-1 text-right font-medium">Líquido</th>
                <th className="px-2 py-1 text-right font-medium">ROI</th>
              </tr>
            </thead>
            <tbody>
              {plan.operations_impact.map((o, i) => (
                <tr key={i} className="border-t border-stone-100">
                  <td className="px-2 py-1 capitalize text-stone-700">
                    {o.kind}
                    <span className="ml-1 text-stone-400">
                      {new Date(o.op_date).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" })}
                    </span>
                  </td>
                  <td className="px-2 py-1 text-right text-stone-500">{brl(o.cost_per_ha)}</td>
                  <td className="px-2 py-1 text-right text-leafdark">+{o.delta_yield_sc_ha.toFixed(1)} sc</td>
                  <td className={`px-2 py-1 text-right font-medium ${o.net_per_ha >= 0 ? "text-leaf" : "text-orange-700"}`}>
                    {o.net_per_ha >= 0 ? "+" : ""}
                    {brl(o.net_per_ha)}
                  </td>
                  <td className="px-2 py-1 text-right text-stone-600">{o.roi != null ? `${o.roi.toFixed(1)}x` : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-1 text-[11px] text-stone-400">
          "Agrega" = produtividade que se perderia sem aquela aplicação. Colheita prevista em{" "}
          {new Date(b.harvest_date).toLocaleDateString("pt-BR")}.
        </p>
      </div>
    </div>
  );
}
