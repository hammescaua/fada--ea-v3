"use client";

import { useScenario } from "@/lib/store";
import { useSim } from "@/lib/queries";
import { PageHeader } from "@/components/PageHeader";
import { LearningPanel } from "@/components/LearningPanel";
import { SeasonReviewPanel } from "@/components/SeasonReviewPanel";

export default function ResultadosPage() {
  const { debounced, selectedFieldId } = useScenario();
  const { data: sim } = useSim(debounced);

  return (
    <div className="space-y-8">
      <PageHeader title="Resultados e aprendizado" subtitle="o previsto × o realizado, safra após safra" />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        <div className="rounded-2xl border border-stone-200 bg-white p-6">
          <LearningPanel currentExpected={sim?.yield_result.expected_sc_ha ?? 0} />
        </div>
        <div className="rounded-2xl border border-leaf/30 bg-white p-6 shadow-sm">
          <SeasonReviewPanel fieldId={selectedFieldId} scenario={debounced} />
        </div>
      </div>
    </div>
  );
}
