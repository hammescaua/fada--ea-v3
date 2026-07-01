"use client";

import { useMemo } from "react";
import { useScenario } from "@/lib/store";
import { useCropPlan, useSeasonPlan, useFertility, useSim } from "@/lib/queries";
import { PageHeader } from "@/components/PageHeader";
import { CropTimeline } from "@/components/CropTimeline";
import { SeasonPlanPanel } from "@/components/SeasonPlanPanel";
import { EconomicsCard } from "@/components/EconomicsCard";
import { FertilityPanel } from "@/components/FertilityPanel";

const PHENO_ORDER = ["VE", "V1", "V4", "R1", "R2", "R3", "R4", "R5", "R5.5", "R6", "R7", "R8"];
const MANEJO_COST: Record<string, number> = {
  fungicida: 180, inseticida: 120, herbicida: 160, herbicida_pre: 140, dessecacao: 90,
  cobertura: 220, adubacao_foliar: 80, calagem: 180, gessagem: 160,
  adubacao_p: 240, adubacao_k: 200, adubacao_base: 260, inoculacao: 40,
  tratamento_sementes: 60, regulador: 70,
};
const midDate = (start: string, end: string) =>
  new Date((new Date(start).getTime() + new Date(end).getTime()) / 2).toISOString().slice(0, 10);

export default function CalendarioPage() {
  const { scenario, debounced, provenance, setScenario } = useScenario();
  const { data: cropPlan, isFetching: cropPlanLoading } = useCropPlan(debounced, provenance);
  const { data: plan } = useSeasonPlan(debounced);
  const { data: fertility, isFetching: fertilityLoading } = useFertility(debounced);
  const { data: sim } = useSim(debounced);

  const phenoRows = useMemo(
    () => (sim ? PHENO_ORDER.filter((k) => sim.phenology[k]).map((k) => ({ stage: k, date: sim.phenology[k] })) : []),
    [sim],
  );

  const handlers = {
    onAdd: (kind: string, phase: { start: string; end: string }) =>
      setScenario((s) => ({
        ...s,
        operations: [
          ...s.operations,
          { kind, op_date: midDate(phase.start, phase.end), cost_per_ha: MANEJO_COST[kind] ?? 150, quality: 0.9 },
        ],
      })),
    onRemove: (kind: string, opDate: string | null) =>
      setScenario((s) => {
        const i = s.operations.findIndex((o) => o.kind === kind && (!opDate || o.op_date === opDate));
        if (i < 0) return s;
        const ops = [...s.operations];
        ops.splice(i, 1);
        return { ...s, operations: ops };
      }),
  };

  return (
    <div className="space-y-8">
      <PageHeader title="Calendário da safra" subtitle="o que já aconteceu e o que vem pela frente" />

      <CropTimeline plan={cropPlan} loading={cropPlanLoading} handlers={handlers} />

      {plan && (
        <details className="group rounded-2xl border border-stone-200 bg-white">
          <summary className="flex cursor-pointer list-none items-center justify-between p-6 text-sm font-medium text-stone-600 hover:text-leafdark">
            <span>Custos, retorno e janelas da safra</span>
            <span className="text-stone-400 transition group-open:rotate-180">▾</span>
          </summary>
          <div className="space-y-8 border-t border-stone-100 p-6">
            <SeasonPlanPanel plan={plan} />
            {sim && <EconomicsCard e={sim.economics} />}
            <FertilityPanel recs={fertility} loading={fertilityLoading} />
            {sim && (
              <div className="grid grid-cols-1 gap-8 sm:grid-cols-2">
                <div>
                  <h3 className="mb-2 text-sm font-semibold text-stone-600">Janela de semeadura (ZARC)</h3>
                  <SowingWindow data={sim.sowing_window} />
                </div>
                <div>
                  <h3 className="mb-2 text-sm font-semibold text-stone-600">Calendário fenológico</h3>
                  <ul className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                    {phenoRows.map((r) => (
                      <li key={r.stage} className="flex justify-between">
                        <span className="font-medium text-stone-500">{r.stage}</span>
                        <span className="text-stone-700">{new Date(r.date).toLocaleDateString("pt-BR")}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        </details>
      )}
    </div>
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
      <p className="text-stone-600">Recomendado: {fmt(data.window_start)} – {fmt(data.window_end)}</p>
      <p className="text-stone-600">Núcleo ótimo até {fmt(data.optimal_end)}</p>
      {Number(data.penalty_sc_ha) > 0 && (
        <p className="text-orange-700">Penalidade estimada: −{Number(data.penalty_sc_ha).toFixed(1)} sc/ha</p>
      )}
    </div>
  );
}
