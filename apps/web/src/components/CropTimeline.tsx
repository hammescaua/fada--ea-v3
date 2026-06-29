"use client";

import type { CropPlanOut, CropPlanPhase } from "@/lib/types";

const brl = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });
const ddmm = (iso: string) =>
  new Date(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });

const STATUS_BADGE: Record<CropPlanPhase["status"], { txt: string; cls: string; dot: string }> = {
  concluida: { txt: "concluída", cls: "text-stone-500", dot: "bg-stone-300" },
  em_andamento: { txt: "em andamento", cls: "text-leafdark font-semibold", dot: "bg-leaf animate-pulse" },
  futura: { txt: "a fazer", cls: "text-stone-400", dot: "bg-white border border-stone-300" },
};

function ProgressBar({ pct, current }: { pct: number; current: string | null }) {
  return (
    <div>
      <div className="relative h-2.5 w-full rounded-full bg-stone-200">
        <div
          className="absolute left-0 top-0 h-2.5 rounded-full bg-leaf transition-all"
          style={{ width: `${pct}%` }}
        />
        <div
          className="absolute top-1/2 h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-leaf bg-white shadow"
          style={{ left: `${Math.min(98, Math.max(2, pct))}%` }}
        />
      </div>
      <div className="mt-1 flex justify-between text-[11px] text-stone-400">
        <span>semeadura</span>
        <span className="font-medium text-stone-500">
          {pct >= 100 ? "safra concluída" : current ? `hoje: ${labelOf(current)}` : `${pct}%`}
        </span>
        <span>colheita</span>
      </div>
    </div>
  );
}

function labelOf(key: string): string {
  return (
    {
      preparo_solo: "preparo do solo",
      semeadura: "semeadura",
      vegetativo: "vegetativo",
      reprodutivo: "reprodutivo",
      colheita: "colheita",
    }[key] ?? key
  );
}

function Manejo({ m }: { m: CropPlanPhase["manejos"][number] }) {
  if (m.planned) {
    return (
      <div className="flex items-start justify-between gap-3 rounded-md bg-green-50/60 px-2.5 py-1.5">
        <div className="min-w-0">
          <span className="text-sm font-medium text-stone-800">{m.label}</span>
          {m.op_date && <span className="ml-2 text-xs text-stone-400">{ddmm(m.op_date)}</span>}
          {m.funcao && <div className="text-xs text-stone-500">{m.funcao}</div>}
        </div>
        <div className="shrink-0 text-right">
          {m.impact_sc_ha != null && (
            <div className="text-sm font-semibold text-leafdark">
              +{m.impact_sc_ha.toFixed(1)} sc/ha
            </div>
          )}
          {m.impact_rs != null && (
            <div className={`text-xs ${m.impact_rs >= 0 ? "text-leaf" : "text-orange-700"}`}>
              {m.impact_rs >= 0 ? "+" : ""}
              {brl(m.impact_rs)}/ha líq.
            </div>
          )}
        </div>
      </div>
    );
  }
  return (
    <div className="flex items-start justify-between gap-3 rounded-md border border-dashed border-amber-300 bg-amber-50/50 px-2.5 py-1.5">
      <div className="min-w-0">
        <span className="text-sm text-amber-900">
          <span className="mr-1">＋</span>
          {m.label}
        </span>
        <span className="ml-1 rounded bg-amber-100 px-1 py-0.5 text-[10px] font-medium uppercase text-amber-700">
          sugerido
        </span>
        {m.funcao && <div className="text-xs text-stone-500">{m.funcao}</div>}
        {m.cost_reference && <div className="text-[11px] text-stone-400">ref.: {m.cost_reference}</div>}
      </div>
      {m.janela && <div className="shrink-0 text-[11px] text-stone-400">{m.janela}</div>}
    </div>
  );
}

function PhaseCard({ p }: { p: CropPlanPhase }) {
  const b = STATUS_BADGE[p.status];
  const ring =
    p.status === "em_andamento" ? "border-leaf/50 bg-white shadow-sm" : "border-stone-200 bg-white";
  return (
    <div className={`relative rounded-xl border ${ring} p-4`}>
      <div className="mb-1 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className={`h-2.5 w-2.5 rounded-full ${b.dot}`} />
          <h4 className="text-sm font-bold text-stone-800">{p.label}</h4>
        </div>
        <span className={`text-xs ${b.cls}`}>{b.txt}</span>
      </div>
      <div className="mb-2 flex flex-wrap items-center gap-x-3 text-[11px] text-stone-400">
        <span>
          {ddmm(p.start)} – {ddmm(p.end)}
        </span>
        <span>·</span>
        <span>governa: {p.factor}</span>
        {p.water_stress != null && (
          <>
            <span>·</span>
            <span className={p.water_stress > 0.3 ? "text-orange-600" : "text-leaf"}>
              estresse hídrico {Math.round(p.water_stress * 100)}%
            </span>
          </>
        )}
      </div>
      <p className="mb-3 text-xs text-stone-600">{p.orientacao}</p>

      {p.manejos.length > 0 && (
        <div className="space-y-1.5">
          {p.manejos.map((m, i) => (
            <Manejo key={`${m.kind}-${i}`} m={m} />
          ))}
        </div>
      )}

      {p.impact_sc_ha > 0 && (
        <div className="mt-2 text-right text-xs text-stone-500">
          Manejos desta fase somam{" "}
          <span className="font-semibold text-leafdark">+{p.impact_sc_ha.toFixed(1)} sc/ha</span>
        </div>
      )}

      {/* De onde vêm os dados desta etapa + como deixar mais preciso */}
      {p.data_basis.length > 0 && (
        <details className="mt-3 rounded-lg bg-stone-50 p-2.5">
          <summary className="cursor-pointer text-[11px] font-semibold uppercase tracking-wide text-stone-500">
            🔎 De onde vêm os dados desta etapa
          </summary>
          <ul className="mt-2 space-y-2">
            {p.data_basis.map((d) => (
              <li key={d.group} className="text-xs">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-stone-700">{d.label}:</span>
                  <span className="text-stone-600">{d.current_label}</span>
                  <span
                    className={`rounded px-1 py-0.5 text-[10px] font-medium ${
                      d.is_local ? "bg-green-100 text-leafdark" : "bg-amber-100 text-amber-700"
                    }`}
                  >
                    {d.is_local ? "específico do talhão" : "default regional"}
                  </span>
                </div>
                {!d.is_local && (
                  <div className="mt-0.5 text-stone-500">
                    → {d.how_to_improve}
                    {d.leverage_sc_ha > 0 && (
                      <span className="text-stone-400"> (±{d.leverage_sc_ha.toFixed(0)} sc/ha)</span>
                    )}
                  </div>
                )}
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}

export function CropTimeline({ plan, loading }: { plan: CropPlanOut | undefined; loading: boolean }) {
  if (!plan) {
    return (
      <div className="animate-pulse rounded-xl border border-stone-200 bg-white p-5">
        <div className="mb-3 h-4 w-40 rounded bg-stone-200" />
        <div className="h-24 rounded bg-stone-100" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-stone-200 bg-white p-5">
        <div className="mb-3 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h3 className="text-base font-bold text-leafdark">📅 Acompanhamento da safra</h3>
            <p className="text-xs text-stone-500">
              Passo a passo do talhão — do preparo do solo à colheita. {loading && "atualizando…"}
            </p>
          </div>
          <div className="flex gap-5 text-right">
            <div>
              <div className="text-[11px] uppercase text-stone-400">Projeção</div>
              <div className="text-lg font-bold text-stone-800">{plan.expected_sc_ha.toFixed(0)} sc/ha</div>
            </div>
            <div>
              <div className="text-[11px] uppercase text-stone-400">Lucro</div>
              <div className={`text-lg font-bold ${plan.profit_per_ha > 0 ? "text-leafdark" : "text-red-700"}`}>
                {brl(plan.profit_per_ha)}/ha
              </div>
            </div>
          </div>
        </div>
        <ProgressBar pct={plan.progress_pct} current={plan.current_phase} />
        <div className="mt-2 text-center text-[11px] text-stone-400">
          semeadura {ddmm(plan.sowing_date)} · colheita prevista {ddmm(plan.harvest_date)} · ciclo {plan.cycle_days} dias
        </div>
      </div>

      <div className="space-y-3">
        {plan.phases.map((p) => (
          <PhaseCard key={p.key} p={p} />
        ))}
      </div>
    </div>
  );
}
