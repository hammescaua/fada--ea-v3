"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ScenarioIn } from "@/lib/types";

const SUGGESTIONS = [
  "Quanto devo colher e qual o risco de prejuízo?",
  "Vale a pena antecipar a semeadura?",
  "O que mais compensa investir neste talhão?",
  "E se eu reduzir o fungicida para 1 aplicação?",
];

export function AssistantPanel({ scenario }: { scenario: ScenarioIn }) {
  const [question, setQuestion] = useState("");
  const ask = useMutation({ mutationFn: (q: string) => api.assistant(q, scenario) });

  const submit = (q: string) => {
    if (!q.trim()) return;
    setQuestion(q);
    ask.mutate(q);
  };

  const data = ask.data;
  return (
    <div>
      <div className="mb-1 flex items-baseline justify-between">
        <h3 className="text-sm font-semibold text-stone-600">
          🤖 Assistente de decisão
        </h3>
        <span className="text-xs text-stone-500">Nível 3 · consulta os motores</span>
      </div>
      <p className="mb-3 text-xs text-stone-500">
        Pergunte em linguagem natural. O assistente consulta os modelos agronômicos e
        responde com números reais — nunca inventa.
      </p>

      <div className="flex gap-2">
        <input
          className="flex-1 rounded-md border border-stone-300 px-3 py-2 text-sm focus:border-leaf focus:outline-none"
          placeholder="Ex.: vale a pena antecipar a semeadura?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit(question)}
        />
        <button
          onClick={() => submit(question)}
          disabled={ask.isPending}
          className="rounded-md bg-leaf px-3 py-2 text-sm font-medium text-white hover:bg-leafdark disabled:opacity-60"
        >
          {ask.isPending ? "Analisando…" : "Perguntar"}
        </button>
      </div>

      <div className="mt-2 flex flex-wrap gap-1.5">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => submit(s)}
            className="rounded-full border border-stone-200 bg-stone-50 px-2.5 py-1 text-[11px] text-stone-600 hover:border-leaf"
          >
            {s}
          </button>
        ))}
      </div>

      {data && (
        <div className="mt-3 rounded-lg bg-stone-50 p-3">
          <div className="whitespace-pre-wrap text-sm text-stone-800">{data.answer}</div>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-[11px] text-stone-400">
            <span>
              {data.used_llm ? "Resposta do assistente (Claude Opus 4.8)" : "Narrador determinístico (sem chave de IA)"}
            </span>
            {data.tool_calls?.length > 0 && (
              <span>· motores: {data.tool_calls.map((t) => t.tool).join(", ")}</span>
            )}
          </div>
          {data.note && <p className="mt-1 text-[11px] text-amber-700">{data.note}</p>}
        </div>
      )}
    </div>
  );
}
