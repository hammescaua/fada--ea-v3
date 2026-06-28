"use client";

import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { MonteCarloOut } from "@/lib/types";

const brl0 = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });

function ProbCard({
  label,
  pct,
  good,
}: {
  label: string;
  pct: number;
  good: boolean;
}) {
  const color = good ? "text-leafdark" : "text-orange-700";
  return (
    <div className="rounded-lg bg-stone-100 px-3 py-2 text-center">
      <div className={`text-2xl font-bold ${color}`}>{(pct * 100).toFixed(0)}%</div>
      <div className="text-[11px] leading-tight text-stone-500">{label}</div>
    </div>
  );
}

export function RiskDistribution({ mc }: { mc: MonteCarloOut }) {
  const bins = mc.profit.histogram.map((b) => ({
    mid: (b.start + b.end) / 2,
    count: b.count,
    loss: b.end <= 0,
  }));
  const p = mc.probabilities;
  return (
    <div>
      <div className="mb-2 flex items-baseline justify-between">
        <h3 className="text-sm font-semibold text-stone-600">
          Distribuição de lucro — {mc.iterations.toLocaleString("pt-BR")} safras simuladas
        </h3>
        <span className="text-xs text-stone-500">Monte Carlo (clima + preço)</span>
      </div>

      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={bins} margin={{ top: 8, right: 8, left: 4, bottom: 4 }}>
          <XAxis
            dataKey="mid"
            tickFormatter={(v) => `${(v / 1000).toFixed(1)}k`}
            tick={{ fontSize: 10 }}
            interval={3}
          />
          <YAxis tick={{ fontSize: 10 }} width={28} />
          <Tooltip
            formatter={(v) => [`${v} safras`, "freq."]}
            labelFormatter={(v) => `≈ ${brl0(Number(v))}/ha`}
          />
          <Bar dataKey="count">
            {bins.map((b, i) => (
              <Cell key={i} fill={b.loss ? "#c2410c" : "#2f7d32"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="mt-3 grid grid-cols-3 gap-2">
        <ProbCard
          label={`lucro ≥ ${brl0(p.profit_target)}/ha`}
          pct={p.profit_above_target}
          good
        />
        <ProbCard label={`produtividade ≥ ${p.yield_target} sc/ha`} pct={p.yield_above_target} good />
        <ProbCard label="prejuízo" pct={p.loss} good={false} />
      </div>

      <div className="mt-3 grid grid-cols-3 gap-2 text-center text-xs">
        <div className="rounded bg-orange-50 px-2 py-1">
          <div className="font-semibold text-orange-800">{brl0(mc.profit.p10)}</div>
          <div className="text-stone-500">pessimista (p10)</div>
        </div>
        <div className="rounded bg-stone-50 px-2 py-1">
          <div className="font-semibold text-stone-700">{brl0(mc.profit.p50)}</div>
          <div className="text-stone-500">provável (p50)</div>
        </div>
        <div className="rounded bg-green-50 px-2 py-1">
          <div className="font-semibold text-leafdark">{brl0(mc.profit.p90)}</div>
          <div className="text-stone-500">otimista (p90)</div>
        </div>
      </div>
    </div>
  );
}
