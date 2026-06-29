"use client";

import type { RadarOut } from "@/lib/types";

const brl = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });

const RING: Record<RadarOut["score_label"], { ring: string; text: string; bg: string }> = {
  "saudável": { ring: "border-leaf/40", text: "text-leafdark", bg: "bg-green-50" },
  "atenção": { ring: "border-amber-300", text: "text-amber-800", bg: "bg-amber-50" },
  "crítico": { ring: "border-red-300", text: "text-red-800", bg: "bg-red-50" },
};

function dimColor(s: number) {
  return s >= 80 ? "bg-leaf" : s >= 60 ? "bg-amber-400" : "bg-orange-500";
}

function Answer({ q, a, accent }: { q: string; a: string; accent?: string }) {
  return (
    <div className="rounded-lg bg-white/70 p-2.5">
      <div className="text-[11px] font-medium uppercase tracking-wide text-stone-400">{q}</div>
      <div className={`text-sm font-medium ${accent ?? "text-stone-800"}`}>{a}</div>
    </div>
  );
}

export function SeasonRadar({ r, loading }: { r: RadarOut | undefined; loading: boolean }) {
  if (!r) {
    return (
      <div className="animate-pulse rounded-xl border border-stone-200 bg-white p-5">
        <div className="mb-3 h-5 w-40 rounded bg-stone-200" />
        <div className="h-20 rounded bg-stone-100" />
      </div>
    );
  }
  const s = RING[r.score_label];

  return (
    <div className={`rounded-xl border ${s.ring} ${s.bg} p-5 shadow-sm`}>
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <h2 className={`text-base font-bold ${s.text}`}>🛰️ Radar da safra</h2>
          <p className="text-xs text-stone-500">o que decidir hoje — em 20 segundos {loading && "· atualizando…"}</p>
        </div>
        <div className="text-right">
          <div className={`text-3xl font-bold leading-none ${s.text}`}>{Math.round(r.score)}</div>
          <div className="text-[11px] uppercase text-stone-400">{r.score_label}</div>
        </div>
      </div>

      {/* As 4 respostas — o coração do copiloto */}
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        <Answer q="① Maior risco da safra hoje" a={r.respostas.maior_risco} accent="text-orange-800" />
        <Answer q="② Melhor decisão agora" a={r.respostas.melhor_decisao} accent="text-leafdark" />
        <Answer q="③ Quanto isso vale" a={r.respostas.quanto_vale} accent="text-leaf" />
        <Answer q="④ Por quê (e confiança)" a={r.respostas.por_que} />
      </div>

      {/* 6 dimensões da saúde da safra */}
      <div className="mt-4 grid grid-cols-3 gap-2 sm:grid-cols-6">
        {r.dimensions.map((d) => (
          <div key={d.key} className="rounded-lg bg-white/70 p-2 text-center">
            <div className="text-[10px] uppercase text-stone-400">{d.label}</div>
            <div className="text-base font-bold text-stone-800">{Math.round(d.score)}</div>
            <div className="mt-1 h-1 w-full overflow-hidden rounded-full bg-stone-200">
              <div className={`h-1 rounded-full ${dimColor(d.score)}`} style={{ width: `${d.score}%` }} />
            </div>
          </div>
        ))}
      </div>

      {/* Tabela de prioridades — onde colocar o dinheiro primeiro */}
      {r.actions.length > 0 && (
        <div className="mt-4">
          <div className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-stone-500">
            Onde investir primeiro (ordenado por retorno)
          </div>
          <div className="overflow-x-auto rounded-lg border border-stone-200 bg-white">
            <table className="w-full text-xs">
              <thead className="bg-stone-50 text-stone-400">
                <tr>
                  <th className="px-2 py-1.5 text-left font-medium">#</th>
                  <th className="px-2 py-1.5 text-left font-medium">Ação</th>
                  <th className="px-2 py-1.5 text-right font-medium">Impacto</th>
                  <th className="px-2 py-1.5 text-right font-medium">Custo</th>
                  <th className="px-2 py-1.5 text-right font-medium">ROI</th>
                  <th className="px-2 py-1.5 text-right font-medium">Chance</th>
                  <th className="px-2 py-1.5 text-left font-medium">Prazo</th>
                </tr>
              </thead>
              <tbody>
                {r.actions.map((a) => (
                  <tr key={a.key} className="border-t border-stone-100">
                    <td className="px-2 py-1.5 font-bold text-leaf">{a.rank}</td>
                    <td className="px-2 py-1.5 text-stone-800">{a.acao}</td>
                    <td className="px-2 py-1.5 text-right">
                      <div className="font-medium text-leafdark">+{a.impacto_sc_ha.toFixed(1)} sc/ha</div>
                      <div className="text-stone-500">+{brl(a.impacto_rs)}/ha</div>
                    </td>
                    <td className="px-2 py-1.5 text-right text-stone-600">
                      {a.custo_per_ha > 0 ? `${brl(a.custo_per_ha)}` : "—"}
                    </td>
                    <td className="px-2 py-1.5 text-right text-stone-600">{a.roi ? `${a.roi.toFixed(1)}x` : "—"}</td>
                    <td className="px-2 py-1.5 text-right text-stone-600">{Math.round(a.probabilidade * 100)}%</td>
                    <td className="px-2 py-1.5 text-stone-500">{a.prazo}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
