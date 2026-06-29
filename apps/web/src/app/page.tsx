"use client";

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import dynamic from "next/dynamic";
import { api, defaultScenario } from "@/lib/api";
import type { ScenarioIn, SimulationOut } from "@/lib/types";
import { YieldWaterfall } from "@/components/YieldWaterfall";
import { EconomicsCard } from "@/components/EconomicsCard";
import { LabControls } from "@/components/LabControls";
import { RiskDistribution } from "@/components/RiskDistribution";
import { DecisionPanel } from "@/components/DecisionPanel";
import { LearningPanel } from "@/components/LearningPanel";
import { AssistantPanel } from "@/components/AssistantPanel";
import { FarmManager } from "@/components/FarmManager";
import { SeasonPlanPanel } from "@/components/SeasonPlanPanel";
import { FertilityPanel } from "@/components/FertilityPanel";
import { BestPlanPanel } from "@/components/BestPlanPanel";
import { DataQualityPanel } from "@/components/DataQualityPanel";

// Mapa só no cliente (MapLibre acessa window).
const FieldMap = dynamic(() => import("@/components/FieldMap").then((m) => m.FieldMap), {
  ssr: false,
  loading: () => <div className="h-[260px] animate-pulse rounded-xl bg-stone-200" />,
});

// Debounce simples para não chamar a API a cada tique de slider.
function useDebounced<T>(value: T, ms: number): T {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return v;
}

const PHENO_ORDER = ["VE", "V1", "V4", "R1", "R2", "R3", "R4", "R5", "R5.5", "R6", "R7", "R8"];

export default function Home() {
  const [scenario, setScenario] = useState<ScenarioIn>(defaultScenario);
  const [baseline, setBaseline] = useState<SimulationOut | null>(null);
  const [profitTarget, setProfitTarget] = useState(3500);
  const [soilReal, setSoilReal] = useState(false); // verdadeiro quando um talhão com análise é carregado
  const debounced = useDebounced(scenario, 350);

  const provenance = useMemo(
    () => ({ solo: soilReal ? "real" : "estimado" }),
    [soilReal],
  );

  const { data: dataQuality } = useQuery({
    queryKey: ["data-quality", debounced, provenance],
    queryFn: () => api.dataQuality(debounced, provenance),
    placeholderData: (prev) => prev,
  });

  const mc = useMutation({
    mutationFn: () =>
      api.montecarlo({
        ...scenario,
        iterations: 3000,
        seed: null,
        price_sd_pct: 0.12,
        profit_target_per_ha: profitTarget,
        yield_target_sc_ha: null,
      }),
  });

  const { data: municipalities = [] } = useQuery({
    queryKey: ["municipalities"],
    queryFn: api.municipalities,
  });

  const { data: sim, isFetching, error } = useQuery({
    queryKey: ["simulate", debounced],
    queryFn: () => api.simulate(debounced),
    placeholderData: (prev) => prev,
  });

  const { data: decisions, isFetching: decisionsLoading } = useQuery({
    queryKey: ["decisions", debounced],
    queryFn: () => api.decisions(debounced),
    placeholderData: (prev) => prev,
  });

  const { data: plan } = useQuery({
    queryKey: ["season-plan", debounced],
    queryFn: () => api.seasonPlan(debounced),
    placeholderData: (prev) => prev,
  });

  const { data: fertility, isFetching: fertilityLoading } = useQuery({
    queryKey: ["fertility", debounced],
    queryFn: () => api.fertility(debounced),
    placeholderData: (prev) => prev,
  });

  const phenoRows = useMemo(() => {
    if (!sim) return [];
    return PHENO_ORDER.filter((k) => sim.phenology[k]).map((k) => ({
      stage: k,
      date: sim.phenology[k],
    }));
  }, [sim]);

  const profitDelta =
    sim && baseline ? sim.economics.profit_per_ha - baseline.economics.profit_per_ha : null;
  const yieldDelta =
    sim && baseline
      ? sim.yield_result.expected_sc_ha - baseline.yield_result.expected_sc_ha
      : null;

  return (
    <main className="mx-auto max-w-7xl px-4 py-6">
      <header className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-leafdark">
            🌱 FADA — Gêmeo Digital da Soja
          </h1>
          <p className="text-sm text-stone-500">
            Laboratório virtual de safra — Noroeste do RS. Simule manejos e veja o
            impacto na produtividade e na rentabilidade, talhão a talhão.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {isFetching && <span className="text-xs text-stone-400">simulando…</span>}
          <button
            onClick={() => sim && setBaseline(sim)}
            className="rounded-md bg-leaf px-3 py-1.5 text-sm font-medium text-white hover:bg-leafdark"
          >
            Fixar como cenário base
          </button>
          {baseline && (
            <button
              onClick={() => setBaseline(null)}
              className="rounded-md border border-stone-300 px-3 py-1.5 text-sm text-stone-600"
            >
              Limpar
            </button>
          )}
        </div>
      </header>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[380px_1fr]">
        {/* Coluna de controles */}
        <div className="space-y-4 rounded-xl border border-stone-200 bg-white p-4">
          <FarmManager
            scenario={scenario}
            onLoadField={(patch) => {
              setScenario((s) => ({ ...s, ...patch }));
              if (patch.soil) setSoilReal(true);
            }}
          />
          <hr className="border-stone-100" />
          <FieldMap
            lat={scenario.latitude}
            lon={scenario.longitude}
            onPick={(lat, lon) => setScenario((s) => ({ ...s, latitude: lat, longitude: lon }))}
          />
          <LabControls
            scenario={scenario}
            municipalities={municipalities}
            onChange={setScenario}
          />
        </div>

        {/* Coluna de resultados */}
        <div className="space-y-5">
          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              Não foi possível simular. A API está rodando em{" "}
              <code>http://localhost:8000</code>?
            </div>
          )}

          {sim && (
            <>
              <div className="rounded-xl border border-leaf/30 bg-white p-4 shadow-sm">
                <AssistantPanel scenario={debounced} />
              </div>

              <div className="rounded-xl border border-leaf/30 bg-white p-4 shadow-sm">
                <BestPlanPanel
                  scenario={debounced}
                  onApply={(patch) => setScenario((s) => ({ ...s, ...patch }))}
                />
              </div>

              {dataQuality && (
                <div className="rounded-xl border border-stone-200 bg-white p-4">
                  <DataQualityPanel dq={dataQuality} />
                </div>
              )}

              <div className="rounded-xl border border-stone-200 bg-white p-4">
                <YieldWaterfall y={sim.yield_result} />
                {baseline && yieldDelta !== null && (
                  <p className="mt-1 text-center text-xs text-stone-500">
                    vs base:{" "}
                    <span className={yieldDelta >= 0 ? "text-leaf" : "text-orange-700"}>
                      {yieldDelta >= 0 ? "+" : ""}
                      {yieldDelta.toFixed(1)} sc/ha
                    </span>
                  </p>
                )}
              </div>

              <div className="rounded-xl border border-stone-200 bg-white p-4">
                <DecisionPanel decisions={decisions} loading={decisionsLoading} />
              </div>

              <div className="rounded-xl border border-stone-200 bg-white p-4">
                <FertilityPanel recs={fertility} loading={fertilityLoading} />
              </div>

              {plan && (
                <div className="rounded-xl border border-stone-200 bg-white p-4">
                  <SeasonPlanPanel plan={plan} />
                </div>
              )}

              <div className="rounded-xl border border-stone-200 bg-white p-4">
                <EconomicsCard e={sim.economics} />
                {baseline && profitDelta !== null && (
                  <p className="mt-2 text-sm">
                    Impacto da mudança no lucro:{" "}
                    <span
                      className={`font-semibold ${profitDelta >= 0 ? "text-leaf" : "text-orange-700"}`}
                    >
                      {profitDelta >= 0 ? "+" : ""}
                      {profitDelta.toLocaleString("pt-BR", {
                        style: "currency",
                        currency: "BRL",
                        maximumFractionDigits: 0,
                      })}
                      /ha
                    </span>
                  </p>
                )}
              </div>

              <div className="rounded-xl border border-stone-200 bg-white p-4">
                {mc.data ? (
                  <RiskDistribution mc={mc.data} />
                ) : (
                  <div className="text-sm text-stone-600">
                    <h3 className="mb-1 text-sm font-semibold text-stone-600">
                      Análise de risco (Monte Carlo)
                    </h3>
                    <p className="text-stone-500">
                      Simule milhares de safras variando clima e preço para ver a
                      distribuição de lucro e a probabilidade de prejuízo.
                    </p>
                  </div>
                )}
                <div className="mt-3 flex flex-wrap items-end gap-3">
                  <label className="flex flex-col gap-1 text-xs">
                    <span className="font-medium text-stone-600">Meta de lucro (R$/ha)</span>
                    <input
                      type="number"
                      step={250}
                      value={profitTarget}
                      onChange={(e) => setProfitTarget(Number(e.target.value))}
                      className="w-32 rounded-md border border-stone-300 px-2 py-1 text-sm focus:border-leaf focus:outline-none"
                    />
                  </label>
                  <button
                    onClick={() => mc.mutate()}
                    disabled={mc.isPending}
                    className="rounded-md bg-leaf px-3 py-1.5 text-sm font-medium text-white hover:bg-leafdark disabled:opacity-60"
                  >
                    {mc.isPending ? "Simulando 3.000 safras…" : "Rodar análise de risco"}
                  </button>
                </div>
              </div>

              <div className="rounded-xl border border-stone-200 bg-white p-4">
                <LearningPanel currentExpected={sim.yield_result.expected_sc_ha} />
              </div>

              <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
                <div className="rounded-xl border border-stone-200 bg-white p-4">
                  <h3 className="mb-2 text-sm font-semibold text-stone-600">
                    Janela de semeadura (ZARC)
                  </h3>
                  <SowingWindow data={sim.sowing_window} />
                </div>
                <div className="rounded-xl border border-stone-200 bg-white p-4">
                  <h3 className="mb-2 text-sm font-semibold text-stone-600">
                    Calendário fenológico
                  </h3>
                  <ul className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                    {phenoRows.map((r) => (
                      <li key={r.stage} className="flex justify-between">
                        <span className="font-medium text-stone-500">{r.stage}</span>
                        <span className="text-stone-700">
                          {new Date(r.date).toLocaleDateString("pt-BR")}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </main>
  );
}

function SowingWindow({ data }: { data: Record<string, unknown> }) {
  const pos = String(data.position ?? "");
  const labels: Record<string, { txt: string; cls: string }> = {
    otimo: { txt: "Janela ótima ✓", cls: "text-leaf" },
    dentro_da_janela: { txt: "Dentro da janela", cls: "text-stone-700" },
    antes_da_janela: { txt: "Antes da janela ⚠", cls: "text-orange-700" },
    depois_da_janela: { txt: "Depois da janela ⚠", cls: "text-orange-700" },
  };
  const l = labels[pos] ?? { txt: pos, cls: "text-stone-700" };
  const fmt = (s: unknown) => (s ? new Date(String(s)).toLocaleDateString("pt-BR") : "—");
  return (
    <div className="space-y-1 text-sm">
      <p className={`font-semibold ${l.cls}`}>{l.txt}</p>
      <p className="text-stone-600">
        Recomendado: {fmt(data.window_start)} – {fmt(data.window_end)}
      </p>
      <p className="text-stone-600">Núcleo ótimo até {fmt(data.optimal_end)}</p>
      {Number(data.penalty_sc_ha) > 0 && (
        <p className="text-orange-700">
          Penalidade estimada: −{Number(data.penalty_sc_ha).toFixed(1)} sc/ha
        </p>
      )}
    </div>
  );
}
