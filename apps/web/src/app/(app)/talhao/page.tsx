"use client";

import { useScenario } from "@/lib/store";
import { useRadar, useSim, useAccuracy, useBriefing } from "@/lib/queries";
import { PageHeader } from "@/components/PageHeader";
import { TalhaoHealth } from "@/components/TalhaoHealth";
import { FarmManager } from "@/components/FarmManager";
import { PersonalityPanel } from "@/components/PersonalityPanel";
import { KnowledgeBasis } from "@/components/KnowledgeBasis";
import { SeasonBriefing } from "@/components/SeasonBriefing";
import { DiagnosisPanel } from "@/components/DiagnosisPanel";
import { SeasonRadar } from "@/components/SeasonRadar";
import { CounterfactualPanel } from "@/components/CounterfactualPanel";
import { ObservationLog } from "@/components/ObservationLog";
import { AccuracyPanel } from "@/components/AccuracyPanel";

export default function TalhaoPage() {
  const { scenario, debounced, provenance, soilReal, patchScenario, setSoilReal, selectedFieldId, setSelectedFieldId } =
    useScenario();
  const { data: radar, isFetching: radarLoading } = useRadar(debounced);
  const { data: sim } = useSim(debounced);
  const { data: accuracy } = useAccuracy(debounced, provenance);
  const { data: briefing, isFetching: briefingLoading } = useBriefing(debounced, provenance);

  const loadField = (patch: Parameters<typeof patchScenario>[0]) => {
    patchScenario(patch);
    if (patch.soil) setSoilReal(true);
  };

  return (
    <div className="space-y-8">
      <PageHeader title="Meu talhão" subtitle="como está hoje e por que o FADA chegou nesses números" />

      <TalhaoHealth radar={radar} loading={radarLoading} />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-stone-200 bg-white p-6">
          <FarmManager scenario={scenario} onFieldChange={setSelectedFieldId} onLoadField={loadField} />
        </div>
        <div className="rounded-2xl border border-leaf/30 bg-white p-6 shadow-sm">
          <PersonalityPanel fieldId={selectedFieldId} scenario={debounced} />
        </div>
      </div>

      {sim && (
        <KnowledgeBasis
          expected={sim.yield_result.expected_sc_ha}
          precision={accuracy?.precision_index ?? sim.yield_result.confidence}
          scenario={scenario}
          soilReal={soilReal}
        />
      )}

      {/* Profundidade para quem quiser — recolhida por padrão. */}
      <details className="group rounded-2xl border border-stone-200 bg-white">
        <summary className="flex cursor-pointer list-none items-center justify-between p-6 text-sm font-medium text-stone-600 hover:text-leafdark">
          <span>Ver análise detalhada (briefing, diagnóstico técnico, prioridades e precisão)</span>
          <span className="text-stone-400 transition group-open:rotate-180">▾</span>
        </summary>
        <div className="space-y-8 border-t border-stone-100 p-6">
          {(briefing || sim) && <SeasonBriefing b={briefing} loading={briefingLoading} />}
          <DiagnosisPanel scenario={debounced} />
          {(radar || sim) && <SeasonRadar r={radar} loading={radarLoading} />}
          <CounterfactualPanel scenario={debounced} />
          <ObservationLog fieldId={selectedFieldId} />
          <AccuracyPanel acc={accuracy} />
        </div>
      </details>
    </div>
  );
}
