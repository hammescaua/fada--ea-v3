"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { PersonalityTrait } from "@/lib/types";

function TraitRow({ t }: { t: PersonalityTrait }) {
  const pct = Math.round(t.value * 100);
  return (
    <div className="rounded-lg border border-stone-200 p-2.5">
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm font-medium text-stone-800">{t.label}</span>
        <span className="flex items-center gap-1.5 text-xs">
          <span className="font-semibold text-leafdark">{t.level}</span>
          {t.learning && (
            <span className="rounded bg-amber-100 px-1 py-0.5 text-[10px] font-medium text-amber-700">
              aprendendo
            </span>
          )}
        </span>
      </div>
      <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-stone-100">
        <div className="h-1.5 rounded-full bg-leaf/70" style={{ width: `${pct}%` }} />
      </div>
      <div className="mt-1 flex items-center justify-between text-[11px] text-stone-400">
        <span>{t.basis}</span>
        <span className="shrink-0">confiança {Math.round(t.confidence * 100)}%</span>
      </div>
    </div>
  );
}

const DQ_LABEL: Record<string, string> = {
  solo: "Solo",
  clima: "Clima",
  fitossanidade: "Fitossanidade",
  produtividade: "Produtividade",
  mercado: "Mercado",
};

export function PersonalityPanel({ fieldId }: { fieldId: string | null }) {
  const { data } = useQuery({
    queryKey: ["personality", fieldId],
    queryFn: () => api.personality(fieldId!),
    enabled: !!fieldId,
    retry: false,
  });

  if (!fieldId) {
    return (
      <div>
        <h3 className="mb-1 text-sm font-semibold text-stone-600">🧬 Personalidade do talhão</h3>
        <p className="text-xs text-stone-500">
          Selecione um talhão salvo para ver os traços que o gêmeo aprendeu dele. Cada safra e
          observação registrada ensina a lavoura ao modelo.
        </p>
      </div>
    );
  }
  if (!data) return null;
  const pct = Math.round(data.knowledge_pct * 100);

  return (
    <div>
      <div className="mb-1 flex items-baseline justify-between">
        <h3 className="text-sm font-semibold text-stone-600">🧬 Personalidade do talhão</h3>
        <span className="text-sm font-bold text-leafdark">conhecimento {pct}%</span>
      </div>
      <p className="mb-3 text-xs text-stone-500">{data.resumo}</p>

      {data.traits.length === 0 ? (
        <p className="rounded-lg bg-stone-50 p-3 text-xs text-stone-500">
          Sem histórico suficiente. Registre safras (com a colheita) e observações para o gêmeo
          aprender a genética desta lavoura.
        </p>
      ) : (
        <div className="space-y-2">
          {data.traits.map((t) => (
            <TraitRow key={t.key} t={t} />
          ))}
        </div>
      )}

      {data.interactions && data.interactions.n_interactions > 0 && (
        <div className="mt-3">
          <div className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-stone-400">
            🧠 Aprendizados da linha do tempo (evento → consequência)
          </div>
          <ul className="space-y-1.5">
            {data.interactions.interactions.map((i, idx) => (
              <li
                key={idx}
                className={`rounded-lg border p-2 text-xs ${
                  i.positive ? "border-leaf/30 bg-green-50/40" : "border-amber-300 bg-amber-50/50"
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium text-stone-800">
                    {i.positive ? "✓" : "⚠"} {i.label}
                  </span>
                  <span className="shrink-0 text-[10px] text-stone-400">
                    {new Date(i.when).toLocaleDateString("pt-BR")} · conf {Math.round(i.confidence * 100)}%
                  </span>
                </div>
                <p className="mt-0.5 text-stone-600">{i.description}</p>
                <p className="mt-0.5 text-stone-500">→ {i.recomendacao}</p>
                <p className="mt-0.5 text-[10px] text-stone-400">fonte: {i.source}</p>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-3">
        <div className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-stone-400">
          Qualidade dos dados (0–100) — quando confiar
        </div>
        <div className="flex flex-wrap gap-1.5">
          {Object.entries(data.data_quality).map(([g, v]) => (
            <span
              key={g}
              className={`rounded-md px-2 py-1 text-[11px] ${
                v >= 70 ? "bg-green-100 text-leafdark" : v >= 40 ? "bg-amber-100 text-amber-700" : "bg-stone-100 text-stone-400"
              }`}
            >
              {DQ_LABEL[g] ?? g}: {Math.round(v)}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
