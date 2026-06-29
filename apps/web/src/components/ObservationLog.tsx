"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ObservationIn } from "@/lib/types";

const KINDS = [
  ["chuva", "Chuva (mm)"],
  ["ndvi", "NDVI (satélite/drone)"],
  ["ferrugem", "Ferrugem (severidade)"],
  ["praga", "Praga (nível)"],
  ["plantio", "Plantio (data)"],
  ["emergencia", "Estande (mil plantas/ha)"],
  ["aplicacao", "Aplicação (fungicida/herbicida/inseticida)"],
  ["colheita", "Colheita (sc/ha)"],
] as const;

const SOURCES = [
  "api_clima", "estacao_inmet", "satelite", "drone", "agronomo",
  "nota_fiscal", "gps", "monitor_colheita", "produtor", "manual",
] as const;

const input = "rounded-md border border-stone-300 px-2 py-1 text-xs";

function buildValue(kind: string, raw: string): Record<string, unknown> {
  const n = Number(raw);
  if (kind === "chuva") return { mm: isNaN(n) ? raw : n };
  if (kind === "ndvi") return { ndvi: isNaN(n) ? raw : n };
  if (kind === "colheita") return { sc_ha: isNaN(n) ? raw : n };
  if (kind === "emergencia") return { plantas_mil: isNaN(n) ? raw : n };
  if (kind === "plantio") return { marco: "plantio" };
  if (kind === "aplicacao") return { tipo: raw || "fungicida" };
  if (kind === "ferrugem" || kind === "praga") return { severidade: raw };
  return { valor: isNaN(n) ? raw : n };
}

// dica do que digitar no campo "valor", por tipo de evidência
const HINT: Record<string, string> = {
  chuva: "mm",
  ndvi: "0-1",
  ferrugem: "baixa/media/alta",
  praga: "baixa/media/alta",
  emergencia: "mil/ha",
  aplicacao: "fungicida/herbicida/inseticida",
  colheita: "sc/ha",
};

export function ObservationLog({ fieldId }: { fieldId: string | null }) {
  const qc = useQueryClient();
  const [kind, setKind] = useState("chuva");
  const [source, setSource] = useState("api_clima");
  const [obsDate, setObsDate] = useState(new Date().toISOString().slice(0, 10));
  const [raw, setRaw] = useState("");

  const { data: obs } = useQuery({
    queryKey: ["observations", fieldId],
    queryFn: () => api.observations(fieldId!),
    enabled: !!fieldId,
    retry: false,
  });

  const add = useMutation({
    mutationFn: () => {
      const payload: ObservationIn = { kind, source, observed_at: obsDate, value: buildValue(kind, raw) };
      return api.addObservation(fieldId!, payload);
    },
    onSuccess: () => {
      setRaw("");
      qc.invalidateQueries({ queryKey: ["observations", fieldId] });
      qc.invalidateQueries({ queryKey: ["personality", fieldId] });
    },
  });

  if (!fieldId) {
    return (
      <div>
        <h3 className="mb-1 text-sm font-semibold text-stone-600">📒 Evidências do talhão</h3>
        <p className="text-xs text-stone-500">
          Selecione um talhão para registrar evidências. Tudo vira observação com fonte e confiança —
          chuva, NDVI, ferrugem, aplicação, colheita — e o gêmeo aprende com a sequência de eventos.
        </p>
      </div>
    );
  }

  return (
    <div>
      <h3 className="mb-1 text-sm font-semibold text-stone-600">📒 Evidências do talhão</h3>
      <p className="mb-2 text-xs text-stone-500">
        Cada dado é uma evidência: <em>o quê · onde · com que confiança</em>. A confiança é
        atribuída pela fonte (drone/satélite/agrônomo &gt; relato manual) e sobe quando fontes
        independentes confirmam o mesmo fato.
      </p>

      <div className="flex flex-wrap items-end gap-1.5 rounded-lg bg-stone-50 p-2">
        <select className={input} value={kind} onChange={(e) => setKind(e.target.value)}>
          {KINDS.map(([k, l]) => (
            <option key={k} value={k}>{l}</option>
          ))}
        </select>
        <input
          className={`${input} w-28`}
          placeholder={HINT[kind] ?? "valor"}
          value={raw}
          onChange={(e) => setRaw(e.target.value)}
        />
        <select className={input} value={source} onChange={(e) => setSource(e.target.value)}>
          {SOURCES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <input type="date" className={input} value={obsDate} onChange={(e) => setObsDate(e.target.value)} />
        <button
          onClick={() => add.mutate()}
          disabled={(!raw && kind !== "plantio" && kind !== "aplicacao") || add.isPending}
          className="rounded-md bg-leaf px-2.5 py-1 text-xs font-medium text-white hover:bg-leafdark disabled:opacity-50"
        >
          registrar
        </button>
      </div>

      {obs && obs.length > 0 && (
        <ul className="mt-2 space-y-1 text-[11px]">
          {obs.slice(0, 8).map((o) => (
            <li key={o.id} className="flex items-center justify-between gap-2 border-b border-stone-100 pb-1">
              <span className="text-stone-600">
                {new Date(o.observed_at).toLocaleDateString("pt-BR")} · <span className="font-medium">{o.kind}</span>{" "}
                {Object.values(o.value)[0] as string} · {o.source}
              </span>
              <span
                className={`shrink-0 rounded px-1 py-0.5 ${
                  o.confidence >= 0.85 ? "bg-green-100 text-leafdark" : o.confidence >= 0.6 ? "bg-amber-100 text-amber-700" : "bg-stone-100 text-stone-500"
                }`}
              >
                {Math.round(o.confidence * 100)}%
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
