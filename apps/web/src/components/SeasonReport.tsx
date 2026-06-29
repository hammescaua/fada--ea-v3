"use client";

import type { AccuracyOut, BriefingOut, SimulationOut, ScenarioIn } from "@/lib/types";

const brl = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });
const dt = (iso: string) => new Date(iso).toLocaleDateString("pt-BR");

const ENSO_LABEL: Record<string, string> = {
  el_nino: "El Niño (chuvoso)",
  neutro: "Neutro",
  la_nina: "La Niña (seca)",
};

/** Relatório de safra de uma página — visível só na impressão (print:block). */
export function SeasonReport({
  scenario,
  briefing,
  sim,
  accuracy,
}: {
  scenario: ScenarioIn;
  briefing?: BriefingOut;
  sim?: SimulationOut;
  accuracy?: AccuracyOut;
}) {
  if (!sim) return null;
  const y = sim.yield_result;
  const e = sim.economics;

  return (
    <div className="hidden print:block">
      <div className="mb-4 border-b border-stone-300 pb-2">
        <h1 className="text-xl font-bold text-leafdark">FADA — Relatório da Safra</h1>
        <p className="text-sm text-stone-600">
          Talhão em {scenario.municipality} · cultivar {scenario.cultivar.name} · semeadura{" "}
          {dt(scenario.sowing_date)} · gerado em {new Date().toLocaleDateString("pt-BR")}
        </p>
      </div>

      {briefing && (
        <section className="mb-4">
          <h2 className="mb-1 text-sm font-bold uppercase text-stone-500">Resumo</h2>
          <p className="text-sm text-stone-800">{briefing.veredito}</p>
        </section>
      )}

      <section className="mb-4 grid grid-cols-4 gap-3">
        <Box t="Produtividade" v={`${y.expected_sc_ha.toFixed(0)} sc/ha`} s={`± ${y.uncertainty_sc_ha.toFixed(0)}`} />
        <Box t="Lucro" v={`${brl(e.profit_per_ha)}/ha`} s={`ROI ${e.roi.toFixed(1)}x`} />
        <Box t="Break-even" v={`${e.breakeven_yield_sc_ha.toFixed(0)} sc/ha`} s={brl(e.breakeven_price_per_sc) + "/sc"} />
        <Box t="Outlook (ENSO)" v={ENSO_LABEL[scenario.enso ?? "neutro"]} s={briefing ? `risco prejuízo ${Math.round(briefing.prob_loss * 100)}%` : ""} />
      </section>

      <section className="mb-4">
        <h2 className="mb-1 text-sm font-bold uppercase text-stone-500">Por que esta produtividade (decomposição)</h2>
        <table className="w-full text-xs">
          <tbody>
            <tr className="border-b border-stone-200">
              <td className="py-0.5 font-medium">Potencial da cultivar</td>
              <td className="py-0.5 text-right">{y.base_potential_sc_ha.toFixed(0)} sc/ha</td>
            </tr>
            {y.contributions.map((c, i) => (
              <tr key={i} className="border-b border-stone-100">
                <td className="py-0.5">{c.label} <span className="text-stone-400">— {c.detail}</span></td>
                <td className={`py-0.5 text-right ${c.delta_sc_ha < 0 ? "text-orange-700" : "text-leaf"}`}>
                  {c.delta_sc_ha >= 0 ? "+" : ""}
                  {c.delta_sc_ha.toFixed(1)}
                </td>
              </tr>
            ))}
            <tr className="border-t-2 border-stone-300 font-bold">
              <td className="py-0.5">Produtividade esperada</td>
              <td className="py-0.5 text-right">{y.expected_sc_ha.toFixed(1)} sc/ha</td>
            </tr>
          </tbody>
        </table>
      </section>

      {briefing && briefing.actions.length > 0 && (
        <section className="mb-4">
          <h2 className="mb-1 text-sm font-bold uppercase text-stone-500">Ações prioritárias</h2>
          <ol className="ml-4 list-decimal text-xs text-stone-800">
            {briefing.actions.map((a) => (
              <li key={a.key} className="mb-0.5">
                {a.label}: <strong>+{a.delta_yield_sc_ha.toFixed(1)} sc/ha · +{brl(a.delta_profit_per_ha)}/ha</strong>{" "}
                ({Math.round(a.probability_positive * 100)}% de chance de melhorar o lucro)
              </li>
            ))}
          </ol>
        </section>
      )}

      {accuracy && (
        <section className="mb-4">
          <h2 className="mb-1 text-sm font-bold uppercase text-stone-500">Confiança dos dados</h2>
          <p className="text-xs text-stone-700">{accuracy.resumo}</p>
        </section>
      )}

      <p className="mt-6 border-t border-stone-300 pt-2 text-[10px] text-stone-400">
        Gerado pelo FADA — Gêmeo Digital da Soja (Noroeste do RS). Estimativas determinísticas e
        explicáveis, baseadas em Embrapa, CQFS-RS/SC, ZARC/MAPA e FAO-56, personalizadas ao talhão.
        Não substitui a avaliação de um agrônomo a campo.
      </p>
    </div>
  );
}

function Box({ t, v, s }: { t: string; v: string; s: string }) {
  return (
    <div className="rounded border border-stone-200 p-2">
      <div className="text-[10px] uppercase text-stone-400">{t}</div>
      <div className="text-sm font-bold text-stone-800">{v}</div>
      <div className="text-[10px] text-stone-500">{s}</div>
    </div>
  );
}
