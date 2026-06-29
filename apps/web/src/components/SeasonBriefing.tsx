"use client";

import type { BriefingOut } from "@/lib/types";
import { InfoTip } from "@/components/InfoTip";

const brl = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });

const STATUS: Record<BriefingOut["status"], { ring: string; bg: string; dot: string; text: string }> = {
  saudavel: { ring: "border-leaf/40", bg: "bg-green-50", dot: "bg-leaf", text: "text-leafdark" },
  atencao: { ring: "border-amber-300", bg: "bg-amber-50", dot: "bg-amber-500", text: "text-amber-800" },
  critico: { ring: "border-red-300", bg: "bg-red-50", dot: "bg-red-500", text: "text-red-800" },
};

const POSITION: Record<string, { txt: string; cls: string }> = {
  otimo: { txt: "Janela ótima ✓", cls: "text-leaf" },
  dentro_da_janela: { txt: "Dentro da janela", cls: "text-stone-700" },
  antes_da_janela: { txt: "Antes da janela ⚠", cls: "text-orange-700" },
  depois_da_janela: { txt: "Depois da janela ⚠", cls: "text-orange-700" },
};

function Metric({ label, value, hint, tone, info }: { label: string; value: string; hint?: string; tone?: string; info?: string }) {
  return (
    <div className="min-w-0">
      <div className="flex items-center text-[11px] font-medium uppercase tracking-wide text-stone-400">
        {label}
        {info && <InfoTip text={info} />}
      </div>
      <div className={`text-lg font-bold leading-tight ${tone ?? "text-stone-800"}`}>{value}</div>
      {hint && <div className="truncate text-[11px] text-stone-500">{hint}</div>}
    </div>
  );
}

export function SeasonBriefing({ b, loading }: { b: BriefingOut | undefined; loading: boolean }) {
  if (!b) {
    return (
      <div className="animate-pulse rounded-xl border border-stone-200 bg-white p-5">
        <div className="mb-3 h-5 w-48 rounded bg-stone-200" />
        <div className="h-16 rounded bg-stone-100" />
      </div>
    );
  }

  const s = STATUS[b.status];
  const pos = POSITION[b.sowing_position] ?? { txt: b.sowing_position, cls: "text-stone-700" };
  const profitTone = b.profit_per_ha > 0 ? "text-leafdark" : "text-red-700";
  const riskTone = b.prob_loss >= 0.4 ? "text-red-700" : b.prob_loss > 0.2 ? "text-amber-700" : "text-leaf";

  return (
    <div className={`rounded-xl border ${s.ring} ${s.bg} p-5 shadow-sm`}>
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className={`h-2.5 w-2.5 rounded-full ${s.dot}`} />
          <h2 className={`text-base font-bold ${s.text}`}>Resumo da safra — {b.status_label}</h2>
        </div>
        <span className="text-xs text-stone-500">
          confiança dos dados {Math.round(b.data_confidence * 100)}%
          {loading && " · atualizando…"}
        </span>
      </div>

      {/* Os 4 números que o agricultor quer de cara */}
      <div className="grid grid-cols-2 gap-4 rounded-lg bg-white/70 p-3 sm:grid-cols-4">
        <Metric
          label="Deve colher"
          value={`${b.expected_sc_ha.toFixed(0)} sc/ha`}
          hint={`entre ${b.p10_sc_ha.toFixed(0)} e ${b.p90_sc_ha.toFixed(0)}`}
          info="Sacas de 60 kg por hectare. A faixa mostra onde o resultado deve cair na maioria das safras parecidas, conforme o clima."
        />
        <Metric
          label={b.profit_per_ha > 0 ? "Lucro" : "Prejuízo"}
          value={`${brl(b.profit_per_ha)}/ha`}
          hint={`ROI ${b.roi.toFixed(1)}x · empata em ${b.breakeven_yield_sc_ha.toFixed(0)} sc/ha`}
          tone={profitTone}
          info="Lucro por hectare ao preço informado. ROI = quantas vezes o lucro cobre o custo. 'Empata em' = produtividade mínima para não ter prejuízo."
        />
        <Metric
          label="Risco de prejuízo"
          value={`${Math.round(b.prob_loss * 100)}%`}
          hint="das safras simuladas"
          tone={riskTone}
          info="De cada 100 safras possíveis (variando clima e preço), em quantas o resultado seria negativo."
        />
        <Metric
          label="Semeadura"
          value={pos.txt}
          hint={b.sowing_penalty_sc_ha > 0 ? `−${b.sowing_penalty_sc_ha.toFixed(1)} sc/ha por desvio` : "no período recomendado"}
          tone={pos.cls}
          info="Se a data está dentro da janela recomendada pelo ZARC para o município — fora dela, sobe o risco e cai o potencial."
        />
      </div>

      {/* Veredito em linguagem do agricultor */}
      <p className="mt-3 text-sm leading-relaxed text-stone-700">{b.veredito}</p>

      {/* Alertas (só quando há) */}
      {b.alertas.length > 0 && (
        <ul className="mt-3 space-y-1">
          {b.alertas.map((a, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-red-700">
              <span aria-hidden>⚠</span>
              <span>{a}</span>
            </li>
          ))}
        </ul>
      )}

      {/* Ações priorizadas por retorno */}
      {b.actions.length > 0 && (
        <div className="mt-4">
          <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-stone-500">
            O que fazer primeiro (ordenado por retorno)
          </div>
          <ol className="space-y-2">
            {b.actions.map((a) => (
              <li key={a.key} className="flex items-start gap-3 rounded-lg border border-stone-200 bg-white p-2.5">
                <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-leaf text-xs font-bold text-white">
                  {a.rank}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-baseline justify-between gap-x-3">
                    <span className="text-sm font-medium text-stone-800">{a.label}</span>
                    <span className="text-sm font-semibold text-leafdark">
                      +{a.delta_yield_sc_ha.toFixed(1)} sc/ha · +{brl(a.delta_profit_per_ha)}/ha
                    </span>
                  </div>
                  <div className="mt-0.5 text-xs text-stone-500">
                    {Math.round(a.probability_positive * 100)}% de chance de melhorar o lucro
                    {a.action_roi != null && ` · ROI da ação ${a.action_roi.toFixed(1)}x`}
                  </div>
                  <p className="mt-1 text-xs text-stone-600">{a.justification}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
