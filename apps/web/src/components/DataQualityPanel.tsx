"use client";

import type { DataQualityOut } from "@/lib/types";

const GROUP_LABEL: Record<string, string> = {
  clima: "Clima",
  solo: "Análise de solo",
  cultivar: "Cultivar",
  manejo: "Manejo",
  populacao: "População",
  preco: "Preços",
  data_semeadura: "Data de semeadura",
};

function confColor(c: number) {
  return c >= 0.75 ? "text-leafdark" : c >= 0.5 ? "text-amber-700" : "text-orange-700";
}

export function DataQualityPanel({ dq }: { dq?: DataQualityOut }) {
  if (!dq) return null;
  const pct = Math.round(dq.data_confidence * 100);
  const gaps = dq.gaps.filter((g) => g.current_source !== "real");

  return (
    <div>
      <div className="mb-1 flex items-baseline justify-between">
        <h3 className="text-sm font-semibold text-stone-600">✅ Confiança dos dados deste talhão</h3>
        <span className={`text-sm font-bold ${confColor(dq.data_confidence)}`}>{pct}%</span>
      </div>
      <div className="mb-2 h-2 w-full overflow-hidden rounded bg-stone-200">
        <div
          className={`h-full ${pct >= 75 ? "bg-leaf" : pct >= 50 ? "bg-amber-400" : "bg-orange-400"}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="mb-3 text-xs text-stone-500">
        A estimativa é tão boa quanto os dados. Quanto mais dado real do seu talhão, mais
        verídica a recomendação. Veja o que mais aumentaria a precisão:
      </p>

      <ul className="space-y-1">
        {gaps.map((g) => (
          <li key={g.group} className="flex items-start gap-2 text-xs">
            <span className="mt-0.5 inline-block w-4 shrink-0 text-stone-400">•</span>
            <span className="flex-1">
              <span className="font-medium text-stone-700">{GROUP_LABEL[g.group] ?? g.group}</span>
              {g.leverage_sc_ha > 0 && (
                <span className="ml-1 rounded bg-orange-100 px-1 text-[10px] font-semibold text-orange-700">
                  ±{g.leverage_sc_ha.toFixed(0)} sc/ha
                </span>
              )}
              <span className="block text-stone-500">{g.como_obter}</span>
            </span>
          </li>
        ))}
      </ul>
      {gaps.length === 0 && (
        <p className="text-sm text-leafdark">Dados completos — recomendação no maior nível de confiança. ✓</p>
      )}
    </div>
  );
}
