"use client";

import {
  Bar,
  BarChart,
  Cell,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { YieldOut } from "@/lib/types";

interface Row {
  label: string;
  base: number; // parte invisível (offset)
  value: number; // magnitude visível
  kind: "potential" | "gain" | "loss" | "result";
  display: number; // valor mostrado (delta ou total)
}

function buildRows(y: YieldOut): Row[] {
  const rows: Row[] = [];
  let running = y.base_potential_sc_ha;
  rows.push({
    label: "Potencial",
    base: 0,
    value: running,
    kind: "potential",
    display: running,
  });
  for (const c of y.contributions) {
    const delta = c.delta_sc_ha;
    if (delta >= 0) {
      rows.push({ label: c.label, base: running, value: delta, kind: "gain", display: delta });
      running += delta;
    } else {
      running += delta;
      rows.push({ label: c.label, base: running, value: -delta, kind: "loss", display: delta });
    }
  }
  rows.push({
    label: "Esperado",
    base: 0,
    value: y.expected_sc_ha,
    kind: "result",
    display: y.expected_sc_ha,
  });
  return rows;
}

const COLORS: Record<Row["kind"], string> = {
  potential: "#64748b",
  gain: "#2f7d32",
  loss: "#c2410c",
  result: "#1b5e20",
};

export function YieldWaterfall({ y }: { y: YieldOut }) {
  const rows = buildRows(y);
  return (
    <div className="w-full">
      <div className="mb-2 flex items-baseline justify-between">
        <h3 className="text-sm font-semibold text-stone-600">
          Decomposição do potencial produtivo (IPPD)
        </h3>
        <span className="text-xs text-stone-500">sc/ha de 60 kg</span>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={rows} margin={{ top: 20, right: 10, left: -10, bottom: 30 }}>
          <XAxis
            dataKey="label"
            angle={-30}
            textAnchor="end"
            interval={0}
            tick={{ fontSize: 11 }}
            height={60}
          />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip
            formatter={(_v, _n, p) => {
              const r = p.payload as Row;
              return [`${r.display > 0 && r.kind !== "potential" && r.kind !== "result" ? "+" : ""}${r.display.toFixed(1)} sc/ha`, r.label];
            }}
          />
          <Bar dataKey="base" stackId="a" fill="transparent" />
          <Bar dataKey="value" stackId="a" radius={[3, 3, 0, 0]}>
            {rows.map((r, i) => (
              <Cell key={i} fill={COLORS[r.kind]} />
            ))}
            <LabelList
              dataKey="display"
              position="top"
              formatter={(v: number) => (v > 0 ? `+${v.toFixed(1)}` : v.toFixed(1))}
              style={{ fontSize: 10, fill: "#44403c" }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <p className="mt-1 text-center text-sm text-stone-700">
        Produtividade esperada:{" "}
        <span className="font-bold text-leafdark">
          {y.expected_sc_ha.toFixed(1)} ± {y.uncertainty_sc_ha.toFixed(1)} sc/ha
        </span>{" "}
        <span className="text-stone-500">
          (confiança {(y.confidence * 100).toFixed(0)}%)
        </span>
      </p>
    </div>
  );
}
