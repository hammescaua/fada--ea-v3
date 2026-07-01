"use client";

import type { RadarOut, ScenarioIn } from "@/lib/types";
import { WhyBadge } from "@/components/WhyBadge";
import { DigitalizationLevel } from "@/components/DigitalizationLevel";

const brl = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });

function greeting(): string {
  const h = new Date().getHours();
  return h < 12 ? "Bom dia" : h < 18 ? "Boa tarde" : "Boa noite";
}

function cropYear(sowing: string): string {
  const d = new Date(sowing);
  const y = d.getFullYear();
  return d.getMonth() >= 6 ? `${y}/${String(y + 1).slice(2)}` : `${y - 1}/${String(y).slice(2)}`;
}

const SIT: Record<RadarOut["score_label"], { dot: string; txt: string; cls: string }> = {
  "saudável": { dot: "🟢", txt: "Situação boa", cls: "text-leafdark" },
  "atenção": { dot: "🟡", txt: "Requer atenção", cls: "text-amber-700" },
  "crítico": { dot: "🔴", txt: "Problema grave", cls: "text-red-700" },
};

/** A Home-copiloto: em 20 segundos — como está a safra, o que decidir e por quê. */
export function HomeOverview({
  radar,
  scenario,
  soilReal,
  loading,
  onSeeDetails,
}: {
  radar: RadarOut | undefined;
  scenario: ScenarioIn;
  soilReal: boolean;
  loading: boolean;
  onSeeDetails: () => void;
}) {
  if (!radar) {
    return (
      <div className="animate-pulse rounded-2xl border border-stone-200 bg-white p-8">
        <div className="mb-4 h-6 w-56 rounded bg-stone-200" />
        <div className="h-24 rounded bg-stone-100" />
      </div>
    );
  }
  const sit = SIT[radar.score_label];
  // Decisões que dá para tomar AGORA, ordenadas por urgência.
  const decisoes = [...radar.actions]
    .filter((a) => a.janela_status !== "passou")
    .sort((a, b) => (b.urgencia ?? 0) - (a.urgencia ?? 0))
    .slice(0, 2);

  return (
    <div className="space-y-5">
      {/* Q1 — Como está minha safra? */}
      <div className="rounded-2xl border border-stone-200 bg-white p-6">
        <p className="text-sm text-stone-500">
          {greeting()}. Safra {scenario.municipality} {cropYear(scenario.sowing_date)}.
          {loading && <span className="ml-2 text-xs text-stone-400">analisando…</span>}
        </p>
        <div className="mt-1 text-[11px] font-semibold uppercase tracking-wide text-leaf">Como está minha safra</div>
        <div className="mt-2 flex flex-wrap items-end gap-x-6 gap-y-2">
          <div>
            <div className="flex items-center text-[11px] uppercase tracking-wide text-stone-400">
              Potencial atual <WhyBadge id="potencial" />
            </div>
            <div className="text-4xl font-bold text-stone-800">{radar.expected_sc_ha.toFixed(0)} <span className="text-xl font-medium text-stone-400">sc/ha</span></div>
          </div>
          <div className={`flex items-center gap-2 pb-1 text-lg font-semibold ${sit.cls}`}>
            <span>{sit.dot}</span>
            <span>{sit.txt}</span>
            <WhyBadge id="situacao" />
          </div>
          <div className="flex items-center pb-1.5 text-sm text-stone-500">
            lucro estimado <span className="ml-1 font-semibold text-stone-700">{brl(radar.profit_per_ha)}/ha</span>
            <WhyBadge id="lucro" />
          </div>
        </div>
      </div>

      {/* Q2 — O que preciso fazer? */}
      <div className="rounded-2xl border border-stone-200 bg-white p-6">
        <div className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-leaf">O que preciso fazer</div>
        {decisoes.length === 0 ? (
          <div className="flex items-center gap-2 text-leafdark">
            <span className="text-lg">✓</span>
            <span className="font-medium">Nenhuma ação urgente hoje — o plano está bem ajustado.</span>
          </div>
        ) : (
          <>
            <h2 className="mb-3 flex items-center text-base font-bold text-stone-800">
              Hoje {decisoes.length === 1 ? "existe 1 decisão importante" : `existem ${decisoes.length} decisões importantes`}
              <WhyBadge id="decisao" />
            </h2>
            <ol className="space-y-3">
              {decisoes.map((a, i) => (
                <li key={a.key} className="flex items-start gap-3 rounded-xl bg-stone-50 p-3">
                  <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-leaf text-sm font-bold text-white">
                    {i + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="font-medium text-stone-800">{a.acao}</div>
                    <div className="mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-sm">
                      <span className="font-semibold text-leafdark">+{brl(a.impacto_rs)}/ha</span>
                      <span className="text-stone-500">{Math.round(a.probabilidade * 100)}% de confiança</span>
                      <span className="text-stone-400">prazo: {a.prazo}</span>
                    </div>
                  </div>
                  <button onClick={onSeeDetails} className="shrink-0 self-center rounded-md border border-stone-300 px-2.5 py-1 text-xs text-stone-600 hover:bg-white">
                    Entender recomendação
                  </button>
                </li>
              ))}
            </ol>
          </>
        )}
      </div>

      {/* Q3 — O que ainda falta? Calmo, recolhido por padrão; o topo segue limpo. */}
      <div>
        <div className="mb-2 px-1 text-[11px] font-semibold uppercase tracking-wide text-leaf">O que ainda falta</div>
        <DigitalizationLevel scenario={scenario} soilReal={soilReal} onGoToTalhao={onSeeDetails} />
      </div>

      <p className="text-center text-xs text-stone-400">
        Quer entender o porquê? Abra <button onClick={onSeeDetails} className="underline hover:text-stone-600">o talhão</button> para o diagnóstico completo.
      </p>
    </div>
  );
}
