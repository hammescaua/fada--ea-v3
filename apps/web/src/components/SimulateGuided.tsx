"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ScenarioIn, SimulationOut } from "@/lib/types";

/** Simular de forma guiada: o produtor escolhe UMA coisa para testar e vê, na
 *  hora, o efeito na produtividade e no lucro — sem preencher vinte campos.
 *  Cada teste é uma mudança real no cenário, simulada pelo motor. */

const brl = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });

const shift = (iso: string, days: number) => {
  const d = new Date(iso);
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
};
const midSeason = (s: ScenarioIn) => shift(s.sowing_date, 68); // ~R1–R3

const CULTIVARS = [
  { name: "GMR 5.2 precoce", maturity_group: 5.2, base_potential_sc_ha: 92, cycle_days: 120, disease_tolerance: 0.5, nematode_tolerance: 0.5 },
  { name: "GMR 6.2 tardia", maturity_group: 6.2, base_potential_sc_ha: 98, cycle_days: 140, disease_tolerance: 0.4, nematode_tolerance: 0.5 },
];

type Test = { key: string; icon: string; label: string; patch: (s: ScenarioIn) => Partial<ScenarioIn> };

const TESTS: Test[] = [
  { key: "antes", icon: "📅", label: "Plantar 7 dias antes", patch: (s) => ({ sowing_date: shift(s.sowing_date, -7) }) },
  { key: "depois", icon: "📅", label: "Plantar 7 dias depois", patch: (s) => ({ sowing_date: shift(s.sowing_date, 7) }) },
  { key: "pop_mais", icon: "🌱", label: "Aumentar população (+25 mil/ha)", patch: (s) => ({ population_k_per_ha: s.population_k_per_ha + 25 }) },
  { key: "pop_menos", icon: "🌱", label: "Reduzir população (−25 mil/ha)", patch: (s) => ({ population_k_per_ha: Math.max(180, s.population_k_per_ha - 25) }) },
  { key: "fungi_mais", icon: "🛡️", label: "Aplicar um fungicida a mais", patch: (s) => ({ operations: [...s.operations, { kind: "fungicida", op_date: midSeason(s), cost_per_ha: 180, quality: 0.9 }] }) },
  { key: "invest_menos", icon: "✂️", label: "Cortar um fungicida (menos custo)", patch: (s) => {
    const i = s.operations.findIndex((o) => o.kind.includes("fungicida"));
    if (i < 0) return {};
    const ops = [...s.operations]; ops.splice(i, 1); return { operations: ops };
  } },
  { key: "cult_precoce", icon: "🧬", label: "Trocar por cultivar precoce", patch: () => ({ cultivar: CULTIVARS[0] }) },
  { key: "cult_tardia", icon: "🧬", label: "Trocar por cultivar tardia", patch: () => ({ cultivar: CULTIVARS[1] }) },
];

export function SimulateGuided({
  scenario,
  baseSim,
  onApply,
}: {
  scenario: ScenarioIn;
  baseSim: SimulationOut | undefined;
  onApply: (patch: Partial<ScenarioIn>) => void;
}) {
  const [selected, setSelected] = useState<Test | null>(null);
  const patch = selected ? selected.patch(scenario) : null;
  const variant: ScenarioIn | null = patch ? { ...scenario, ...patch } : null;
  const empty = patch && Object.keys(patch).length === 0;

  const { data: vsim, isFetching } = useQuery({
    queryKey: ["sim-guided", variant],
    queryFn: () => api.simulate(variant as ScenarioIn),
    enabled: !!variant && !empty,
    placeholderData: (p) => p,
  });

  const baseY = baseSim?.yield_result.expected_sc_ha ?? 0;
  const baseP = baseSim?.economics.profit_per_ha ?? 0;
  const dY = vsim ? vsim.yield_result.expected_sc_ha - baseY : 0;
  const dP = vsim ? vsim.economics.profit_per_ha - baseP : 0;
  const vale = dP > 5;

  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-stone-200 bg-white p-6">
        <h2 className="text-base font-bold text-stone-800">O que você deseja testar?</h2>
        <p className="mb-4 text-xs text-stone-500">
          Escolha uma mudança e veja na hora o efeito no seu talhão — sem mexer em nada de verdade.
        </p>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {TESTS.map((t) => (
            <button
              key={t.key}
              onClick={() => setSelected(t)}
              className={`flex items-center gap-2 rounded-xl border px-3 py-3 text-left text-sm transition ${
                selected?.key === t.key ? "border-leaf bg-green-50 text-leafdark" : "border-stone-200 text-stone-700 hover:border-leaf hover:bg-green-50"
              }`}
            >
              <span className="text-lg">{t.icon}</span> {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Resultado do teste escolhido */}
      {selected && (
        <div className="rounded-2xl border border-leaf/30 bg-white p-6 shadow-sm">
          <div className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-leaf">Resultado do teste</div>
          <h3 className="text-base font-bold text-stone-800">{selected.icon} {selected.label}</h3>

          {empty ? (
            <p className="mt-3 text-sm text-stone-500">Não há esse item no seu plano para alterar.</p>
          ) : !baseSim || (isFetching && !vsim) ? (
            <p className="mt-3 text-sm text-stone-400">Simulando…</p>
          ) : vsim ? (
            <>
              <div className="mt-4 grid grid-cols-2 gap-4">
                <Delta label="Produtividade" base={`${baseY.toFixed(1)} sc/ha`} novo={`${vsim.yield_result.expected_sc_ha.toFixed(1)} sc/ha`} delta={dY} unit=" sc/ha" fmt={(v) => v.toFixed(1)} />
                <Delta label="Lucro" base={`${brl(baseP)}/ha`} novo={`${brl(vsim.economics.profit_per_ha)}/ha`} delta={dP} unit="/ha" fmt={(v) => brl(v)} />
              </div>

              <div className={`mt-4 rounded-xl p-3 text-sm font-medium ${vale ? "bg-green-50 text-leafdark" : dP < -5 ? "bg-orange-50 text-orange-800" : "bg-stone-50 text-stone-600"}`}>
                {vale
                  ? `Vale a pena: some cerca de ${brl(dP)}/ha ao seu resultado.`
                  : dP < -5
                  ? `Não compensa: reduz cerca de ${brl(Math.abs(dP))}/ha do seu resultado.`
                  : "Efeito pequeno no resultado — pouca diferença prática."}
              </div>

              {!empty && (
                <button
                  onClick={() => { onApply(selected.patch(scenario)); setSelected(null); }}
                  className="mt-4 rounded-md bg-leaf px-4 py-2 text-sm font-semibold text-white hover:bg-leafdark"
                >
                  Aplicar no meu plano
                </button>
              )}
            </>
          ) : null}
        </div>
      )}
    </div>
  );
}

function Delta({ label, base, novo, delta, unit, fmt }: { label: string; base: string; novo: string; delta: number; unit: string; fmt: (v: number) => string }) {
  const pos = delta >= 0;
  return (
    <div className="rounded-xl bg-stone-50 p-3">
      <div className="text-[11px] uppercase tracking-wide text-stone-400">{label}</div>
      <div className="mt-1 text-lg font-bold text-stone-800">{novo}</div>
      <div className="text-xs text-stone-400">antes: {base}</div>
      <div className={`mt-1 text-sm font-semibold ${pos ? "text-leaf" : "text-orange-700"}`}>
        {pos ? "+" : ""}{fmt(delta)}{unit === "/ha" ? "/ha" : unit}
      </div>
    </div>
  );
}
