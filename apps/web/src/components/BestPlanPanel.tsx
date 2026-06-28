"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ScenarioIn } from "@/lib/types";

const brl = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });
const ddmm = (iso: string) =>
  new Date(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });

export function BestPlanPanel({
  scenario,
  onApply,
}: {
  scenario: ScenarioIn;
  onApply: (patch: Partial<ScenarioIn>) => void;
}) {
  const [open, setOpen] = useState(false);
  const opt = useMutation({ mutationFn: () => api.optimizeSeason(scenario) });
  const d = opt.data;

  return (
    <div>
      <div className="mb-1 flex items-baseline justify-between">
        <h3 className="text-sm font-semibold text-stone-600">🎯 Melhor plano para o talhão</h3>
        <span className="text-xs text-stone-500">combina e simula vários cenários</span>
      </div>
      <p className="mb-3 text-xs text-stone-500">
        O motor varre combinações de data de semeadura, população e programa de fungicida,
        simula todas e escolhe a de maior lucro para o perfil deste talhão — explicando o porquê.
      </p>

      <button
        onClick={() => opt.mutate()}
        disabled={opt.isPending}
        className="rounded-md bg-leaf px-3 py-1.5 text-sm font-medium text-white hover:bg-leafdark disabled:opacity-60"
      >
        {opt.isPending ? "Simulando combinações…" : "Encontrar o melhor plano"}
      </button>

      {d && (
        <div className="mt-3 space-y-3">
          <div className="rounded-lg bg-green-50 p-3">
            <div className="text-xs text-stone-500">
              {d.combinacoes_avaliadas} cenários avaliados · plano recomendado:
            </div>
            <div className="text-sm font-semibold text-leafdark">
              Plantar {ddmm(d.melhor_plano.sowing_date)} · {d.melhor_plano.population_k_per_ha.toFixed(0)} mil/ha ·{" "}
              {d.melhor_plano.num_fungicidas} fungicida(s)
            </div>
            <div className="text-sm text-stone-700">
              {d.melhor_plano.expected_sc_ha.toFixed(1)} sc/ha · lucro {brl(d.melhor_plano.profit_per_ha)}/ha{" "}
              <span className={d.melhor_plano.delta_profit_vs_atual >= 0 ? "text-leaf" : "text-orange-700"}>
                ({d.melhor_plano.delta_profit_vs_atual >= 0 ? "+" : ""}
                {brl(d.melhor_plano.delta_profit_vs_atual)} vs. atual)
              </span>
            </div>
            <button
              onClick={() =>
                onApply({
                  sowing_date: d.melhor_plano.sowing_date,
                  population_k_per_ha: d.melhor_plano.population_k_per_ha,
                })
              }
              className="mt-2 rounded-md border border-leaf px-2.5 py-1 text-xs font-medium text-leafdark hover:bg-green-100"
            >
              Aplicar este plano no laboratório
            </button>
          </div>

          <div>
            <div className="mb-1 text-xs font-medium text-stone-500">Por que este plano</div>
            <ul className="list-disc space-y-0.5 pl-4 text-xs text-stone-600">
              {d.porques.map((p, i) => (
                <li key={i}>{p}</li>
              ))}
            </ul>
          </div>

          <button onClick={() => setOpen((v) => !v)} className="text-xs text-stone-500 underline">
            {open ? "ocultar" : "ver"} alternativas avaliadas
          </button>
          {open && (
            <table className="w-full text-xs">
              <thead className="text-stone-400">
                <tr>
                  <th className="py-1 text-left font-medium">Data</th>
                  <th className="text-right font-medium">Pop.</th>
                  <th className="text-right font-medium">Fung.</th>
                  <th className="text-right font-medium">sc/ha</th>
                  <th className="text-right font-medium">Lucro/ha</th>
                </tr>
              </thead>
              <tbody>
                {d.ranking.map((r, i) => (
                  <tr key={i} className="border-t border-stone-100">
                    <td className="py-1 text-stone-700">{ddmm(r.sowing_date)}</td>
                    <td className="text-right text-stone-600">{r.population_k_per_ha.toFixed(0)}</td>
                    <td className="text-right text-stone-600">{r.num_fungicidas}</td>
                    <td className="text-right text-stone-600">{r.expected_sc_ha.toFixed(1)}</td>
                    <td className="text-right font-medium text-stone-800">{brl(r.profit_per_ha)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
