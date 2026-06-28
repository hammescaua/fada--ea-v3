"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { SeasonOutcome } from "@/lib/types";

interface Props {
  currentExpected: number; // produtividade prevista no cenário atual (pré-preenche linhas)
}

export function LearningPanel({ currentExpected }: Props) {
  const [rows, setRows] = useState<SeasonOutcome[]>([
    { crop_year: "2022/23", predicted_sc_ha: 58, actual_sc_ha: 62 },
    { crop_year: "2023/24", predicted_sc_ha: 61, actual_sc_ha: 66 },
  ]);
  const cal = useMutation({ mutationFn: () => api.calibration(rows) });

  const update = (i: number, patch: Partial<SeasonOutcome>) =>
    setRows((rs) => rs.map((r, j) => (j === i ? { ...r, ...patch } : r)));
  const addRow = () =>
    setRows((rs) => [
      ...rs,
      { crop_year: "", predicted_sc_ha: Math.round(currentExpected), actual_sc_ha: Math.round(currentExpected) },
    ]);
  const removeRow = (i: number) => setRows((rs) => rs.filter((_, j) => j !== i));

  const c = cal.data;
  const correctedNow = c ? currentExpected + c.bias_sc_ha : null;

  return (
    <div>
      <div className="mb-1 flex items-baseline justify-between">
        <h3 className="text-sm font-semibold text-stone-600">
          Aprendizado do talhão (Knowledge Engine)
        </h3>
        <span className="text-xs text-stone-500">Nível 2 · correção por safra</span>
      </div>
      <p className="mb-3 text-xs text-stone-500">
        Registre o que o modelo previu e o que o talhão realmente colheu. A cada safra o
        modelo daquele talhão aprende a corrigir o erro — e a incerteza diminui.
      </p>

      <div className="space-y-1">
        <div className="grid grid-cols-[1fr_1fr_1fr_auto] gap-2 text-[11px] font-medium text-stone-400">
          <span>Safra</span>
          <span>Previsto (sc/ha)</span>
          <span>Colhido (sc/ha)</span>
          <span />
        </div>
        {rows.map((r, i) => (
          <div key={i} className="grid grid-cols-[1fr_1fr_1fr_auto] items-center gap-2">
            <input
              className="rounded border border-stone-300 px-2 py-1 text-sm"
              value={r.crop_year}
              placeholder="2024/25"
              onChange={(e) => update(i, { crop_year: e.target.value })}
            />
            <input
              type="number"
              className="rounded border border-stone-300 px-2 py-1 text-sm"
              value={r.predicted_sc_ha}
              onChange={(e) => update(i, { predicted_sc_ha: Number(e.target.value) })}
            />
            <input
              type="number"
              className="rounded border border-stone-300 px-2 py-1 text-sm"
              value={r.actual_sc_ha}
              onChange={(e) => update(i, { actual_sc_ha: Number(e.target.value) })}
            />
            <button
              onClick={() => removeRow(i)}
              className="px-1 text-stone-400 hover:text-orange-700"
              aria-label="remover"
            >
              ×
            </button>
          </div>
        ))}
      </div>

      <div className="mt-2 flex gap-2">
        <button onClick={addRow} className="rounded-md border border-stone-300 px-2 py-1 text-xs text-stone-600">
          + safra
        </button>
        <button
          onClick={() => cal.mutate()}
          disabled={cal.isPending || rows.length === 0}
          className="rounded-md bg-leaf px-3 py-1 text-xs font-medium text-white hover:bg-leafdark disabled:opacity-60"
        >
          Treinar modelo do talhão
        </button>
      </div>

      {c && (
        <div className="mt-3 rounded-lg bg-stone-100 p-3">
          <div className="grid grid-cols-3 gap-2 text-center text-xs">
            <div>
              <div className="text-lg font-bold text-leafdark">
                {c.bias_sc_ha >= 0 ? "+" : ""}
                {c.bias_sc_ha} sc/ha
              </div>
              <div className="text-stone-500">correção aprendida</div>
            </div>
            <div>
              <div className="text-lg font-bold text-stone-700">{(c.confidence * 100).toFixed(0)}%</div>
              <div className="text-stone-500">confiança ({c.n_seasons} safras)</div>
            </div>
            <div>
              <div className="text-lg font-bold text-stone-700">
                {c.mae_before} → {c.mae_after}
              </div>
              <div className="text-stone-500">erro médio (sc/ha)</div>
            </div>
          </div>
          {correctedNow !== null && (
            <p className="mt-2 text-center text-sm text-stone-700">
              Projeção do cenário atual <b>calibrada para este talhão</b>:{" "}
              <span className="font-bold text-leafdark">{correctedNow.toFixed(1)} sc/ha</span>
              <span className="text-stone-500"> (era {currentExpected.toFixed(1)})</span>
            </p>
          )}
          <div className="mt-2 h-1.5 w-full overflow-hidden rounded bg-stone-200">
            <div className="h-full bg-leaf" style={{ width: `${c.confidence * 100}%` }} />
          </div>
        </div>
      )}
    </div>
  );
}
