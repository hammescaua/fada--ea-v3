"use client";

import { useState } from "react";
import type { DecisionOut } from "@/lib/types";

const brl0 = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });

function ProbBadge({ p }: { p: number }) {
  const color = p >= 0.7 ? "bg-green-100 text-leafdark" : p >= 0.5 ? "bg-amber-100 text-amber-800" : "bg-stone-200 text-stone-600";
  return <span className={`rounded px-1.5 py-0.5 text-[11px] font-semibold ${color}`}>{(p * 100).toFixed(0)}% +</span>;
}

function DecisionRow({ d }: { d: DecisionOut }) {
  const [open, setOpen] = useState(false);
  const gain = d.delta_profit_per_ha >= 0;
  return (
    <li className="rounded-lg border border-stone-200">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-3 px-3 py-2 text-left"
      >
        <span
          className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
            gain ? "bg-leaf text-white" : "bg-orange-200 text-orange-800"
          }`}
        >
          {gain ? "↑" : "↓"}
        </span>
        <span className="min-w-0 flex-1">
          <span className="block truncate text-sm font-medium text-stone-800">{d.label}</span>
          <span className="block text-[11px] text-stone-500">
            {d.delta_yield_sc_ha >= 0 ? "+" : ""}
            {d.delta_yield_sc_ha.toFixed(1)} sc/ha
            {d.action_roi !== null && ` · ROI ${d.action_roi.toFixed(1)}x`}
          </span>
        </span>
        <span className="text-right">
          <span className={`block text-sm font-semibold ${gain ? "text-leafdark" : "text-orange-700"}`}>
            {gain ? "+" : ""}
            {brl0(d.delta_profit_per_ha)}
          </span>
          <span className="block">
            <ProbBadge p={d.probability_positive} />
          </span>
        </span>
      </button>
      {open && (
        <p className="border-t border-stone-100 px-3 py-2 text-xs text-stone-600">
          {d.justification}
          {d.added_cost_per_ha !== 0 && (
            <span className="mt-1 block text-stone-400">
              Custo da ação: {brl0(Math.abs(d.added_cost_per_ha))}/ha
              {d.added_cost_per_ha < 0 ? " (economia)" : ""}
            </span>
          )}
        </p>
      )}
    </li>
  );
}

export function DecisionPanel({ decisions, loading }: { decisions?: DecisionOut[]; loading: boolean }) {
  return (
    <div>
      <div className="mb-2 flex items-baseline justify-between">
        <h3 className="text-sm font-semibold text-stone-600">
          Recomendações de manejo — priorizadas por retorno
        </h3>
        {loading && <span className="text-xs text-stone-400">avaliando…</span>}
      </div>
      <p className="mb-3 text-xs text-stone-500">
        O motor de decisão simula cada intervenção possível neste talhão e mede o
        impacto no lucro. Clique para ver a justificativa técnica.
      </p>
      {!decisions || decisions.length === 0 ? (
        <p className="text-sm text-stone-400">
          {loading ? "Calculando o melhor conjunto de decisões…" : "Sem ações relevantes — o talhão já está bem manejado neste cenário."}
        </p>
      ) : (
        <ul className="space-y-2">
          {decisions.map((d) => (
            <DecisionRow key={d.key} d={d} />
          ))}
        </ul>
      )}
    </div>
  );
}
