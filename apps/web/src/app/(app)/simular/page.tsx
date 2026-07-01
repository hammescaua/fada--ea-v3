"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import dynamic from "next/dynamic";
import { api } from "@/lib/api";
import { useScenario } from "@/lib/store";
import { useSim, useDecisions, useMunicipalities } from "@/lib/queries";
import type { ScenarioIn, SimulationOut } from "@/lib/types";
import { PageHeader } from "@/components/PageHeader";
import { SimulateGuided } from "@/components/SimulateGuided";
import { LabControls } from "@/components/LabControls";
import { BestPlanPanel } from "@/components/BestPlanPanel";
import { AssistantPanel } from "@/components/AssistantPanel";
import { YieldWaterfall } from "@/components/YieldWaterfall";
import { DecisionPanel } from "@/components/DecisionPanel";
import { EconomicsCard } from "@/components/EconomicsCard";
import { RiskDistribution } from "@/components/RiskDistribution";
import { FarmManager } from "@/components/FarmManager";

const FieldMap = dynamic(() => import("@/components/FieldMap").then((m) => m.FieldMap), {
  ssr: false,
  loading: () => <div className="h-[260px] animate-pulse rounded-xl bg-stone-200" />,
});

const brl = (v: number) => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });

export default function SimularPage() {
  const { scenario, debounced, setScenario, patchScenario, setSoilReal, setSelectedFieldId } = useScenario();
  const [advanced, setAdvanced] = useState(false);
  const [baseline, setBaseline] = useState<SimulationOut | null>(null);
  const [profitTarget, setProfitTarget] = useState(3500);
  const { data: sim } = useSim(debounced);
  const { data: decisions, isFetching: decisionsLoading } = useDecisions(debounced, advanced);
  const { data: municipalities = [] } = useMunicipalities();

  const mc = useMutation({
    mutationFn: () =>
      api.montecarlo({ ...scenario, iterations: 3000, seed: null, price_sd_pct: 0.12, profit_target_per_ha: profitTarget, yield_target_sc_ha: null }),
  });

  const profitDelta = sim && baseline ? sim.economics.profit_per_ha - baseline.economics.profit_per_ha : null;
  const yieldDelta = sim && baseline ? sim.yield_result.expected_sc_ha - baseline.yield_result.expected_sc_ha : null;

  return (
    <div className="space-y-8">
      <PageHeader title="Simular decisão" subtitle="teste uma mudança antes de executar no campo" />

      <div className="flex gap-1 rounded-lg bg-stone-100 p-1">
        <button onClick={() => setAdvanced(false)} className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition ${!advanced ? "bg-white text-leafdark shadow-sm" : "text-stone-500 hover:text-stone-700"}`}>
          Guiado
        </button>
        <button onClick={() => setAdvanced(true)} className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition ${advanced ? "bg-white text-leafdark shadow-sm" : "text-stone-500 hover:text-stone-700"}`}>
          Modo avançado
        </button>
      </div>

      {!advanced ? (
        <SimulateGuided scenario={debounced} baseSim={sim ?? undefined} onApply={patchScenario} />
      ) : (
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-[360px_1fr]">
          <div className="space-y-4 rounded-2xl border border-stone-200 bg-white p-6">
            <FarmManager
              scenario={scenario}
              onFieldChange={setSelectedFieldId}
              onLoadField={(patch) => { patchScenario(patch); if (patch.soil) setSoilReal(true); }}
            />
            <hr className="border-stone-100" />
            <FieldMap lat={scenario.latitude} lon={scenario.longitude} onPick={(lat, lon) => patchScenario({ latitude: lat, longitude: lon })} />
            <LabControls scenario={scenario} municipalities={municipalities} onChange={setScenario} />
            <button onClick={() => sim && setBaseline(sim)} className="w-full rounded-md bg-leaf px-3 py-1.5 text-sm font-medium text-white hover:bg-leafdark">
              Fixar cenário atual como base
            </button>
            {baseline && (
              <button onClick={() => setBaseline(null)} className="w-full rounded-md border border-stone-300 px-3 py-1.5 text-sm text-stone-600">
                Limpar comparação
              </button>
            )}
          </div>

          <div className="space-y-6">
            {sim && (
              <>
                <div className="rounded-2xl border border-leaf/30 bg-white p-6 shadow-sm">
                  <BestPlanPanel scenario={debounced} onApply={patchScenario} />
                </div>
                <div className="rounded-2xl border border-leaf/30 bg-white p-6 shadow-sm">
                  <AssistantPanel scenario={debounced} />
                </div>
                <div className="rounded-2xl border border-stone-200 bg-white p-6">
                  <YieldWaterfall y={sim.yield_result} />
                  {baseline && yieldDelta !== null && (
                    <p className="mt-1 text-center text-xs text-stone-500">
                      vs base: <span className={yieldDelta >= 0 ? "text-leaf" : "text-orange-700"}>{yieldDelta >= 0 ? "+" : ""}{yieldDelta.toFixed(1)} sc/ha</span>
                    </p>
                  )}
                </div>
                <div className="rounded-2xl border border-stone-200 bg-white p-6">
                  <DecisionPanel decisions={decisions} loading={decisionsLoading} />
                </div>
                <div className="rounded-2xl border border-stone-200 bg-white p-6">
                  <EconomicsCard e={sim.economics} />
                  {baseline && profitDelta !== null && (
                    <p className="mt-2 text-sm">
                      Impacto no lucro:{" "}
                      <span className={`font-semibold ${profitDelta >= 0 ? "text-leaf" : "text-orange-700"}`}>
                        {profitDelta >= 0 ? "+" : ""}{brl(profitDelta)}/ha
                      </span>
                    </p>
                  )}
                </div>
                <div className="rounded-2xl border border-stone-200 bg-white p-6">
                  {mc.data ? (
                    <RiskDistribution mc={mc.data} />
                  ) : (
                    <div className="text-sm text-stone-600">
                      <h3 className="mb-1 text-sm font-semibold text-stone-600">Análise de risco (Monte Carlo)</h3>
                      <p className="text-stone-500">Simule milhares de safras variando clima e preço para ver a distribuição de lucro e a probabilidade de prejuízo.</p>
                    </div>
                  )}
                  <div className="mt-3 flex flex-wrap items-end gap-3">
                    <label className="flex flex-col gap-1 text-xs">
                      <span className="font-medium text-stone-600">Meta de lucro (R$/ha)</span>
                      <input type="number" step={250} value={profitTarget} onChange={(e) => setProfitTarget(Number(e.target.value))} className="w-32 rounded-md border border-stone-300 px-2 py-1 text-sm focus:border-leaf focus:outline-none" />
                    </label>
                    <label className="flex flex-col gap-1 text-xs">
                      <span className="font-medium text-stone-600">Outlook climático (ENSO)</span>
                      <select value={scenario.enso ?? "neutro"} onChange={(e) => patchScenario({ enso: e.target.value as ScenarioIn["enso"] })} className="w-40 rounded-md border border-stone-300 px-2 py-1 text-sm focus:border-leaf focus:outline-none">
                        <option value="el_nino">El Niño (chuvoso)</option>
                        <option value="neutro">Neutro</option>
                        <option value="la_nina">La Niña (seca)</option>
                      </select>
                    </label>
                    <button onClick={() => mc.mutate()} disabled={mc.isPending} className="rounded-md bg-leaf px-3 py-1.5 text-sm font-medium text-white hover:bg-leafdark disabled:opacity-60">
                      {mc.isPending ? "Simulando 3.000 safras…" : "Rodar análise de risco"}
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
