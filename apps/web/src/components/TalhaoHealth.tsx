"use client";

import type { RadarOut } from "@/lib/types";

/** "Saúde do Talhão": em vez de um painel técnico, um número de saúde e seis
 *  dimensões que se abrem ao toque. Tudo vem do radar (dados reais); as
 *  explicações são orientações gerais, não números inventados. */

const DIMS: Record<string, { desc: string; melhora: string }> = {
  solo: {
    desc: "Fertilidade e estrutura do solo — pH, saturação de bases, fósforo, potássio e compactação.",
    melhora: "Análise de solo real do talhão, calagem/gessagem e correção de P e K.",
  },
  clima: {
    desc: "Água e temperatura em cada estádio, do plantio à colheita.",
    melhora: "Ajustar a janela de semeadura (ZARC) e o ciclo da cultivar ao clima do seu talhão.",
  },
  sanidade: {
    desc: "Pressão de doenças, pragas e nematoides sobre a lavoura.",
    melhora: "Fungicida no momento certo, rotação de culturas e cultivar tolerante.",
  },
  nutricao: {
    desc: "Suprimento de nutrientes para sustentar o potencial da cultivar.",
    melhora: "Adubação de base e de cobertura conforme a análise e a produtividade esperada.",
  },
  mercado: {
    desc: "Relação entre o preço da soja e o custo da sua safra.",
    melhora: "Travar preço em boas janelas e manter o custo por hectare sob controle.",
  },
  execucao: {
    desc: "Qualidade e pontualidade das operações — população, espaçamento e manejos.",
    melhora: "População no alvo, aplicações na hora certa e boa distribuição de plantas.",
  },
};

function status(score: number) {
  if (score >= 80) return { txt: "boa", cls: "text-leafdark", bar: "bg-leaf" };
  if (score >= 60) return { txt: "atenção", cls: "text-amber-700", bar: "bg-amber-400" };
  return { txt: "crítica", cls: "text-orange-700", bar: "bg-orange-500" };
}

export function TalhaoHealth({ radar, loading }: { radar: RadarOut | undefined; loading: boolean }) {
  if (!radar) {
    return (
      <div className="animate-pulse rounded-2xl border border-stone-200 bg-white p-6">
        <div className="mb-3 h-5 w-40 rounded bg-stone-200" />
        <div className="h-24 rounded bg-stone-100" />
      </div>
    );
  }
  const overall = status(radar.score);

  return (
    <div className="rounded-2xl border border-stone-200 bg-white p-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-stone-800">Saúde do talhão hoje</h2>
          <p className="text-xs text-stone-500">
            toque em cada item para entender e ver como melhorar {loading && "· atualizando…"}
          </p>
        </div>
        <div className="text-right">
          <div className={`text-4xl font-bold leading-none ${overall.cls}`}>{Math.round(radar.score)}</div>
          <div className={`text-xs font-medium ${overall.cls}`}>saúde {overall.txt}</div>
        </div>
      </div>

      <div className="mt-4 space-y-1.5">
        {radar.dimensions.map((d) => {
          const st = status(d.score);
          const info = DIMS[d.key];
          return (
            <details key={d.key} className="group rounded-xl border border-stone-100 bg-stone-50/60">
              <summary className="flex cursor-pointer list-none items-center gap-3 p-3">
                <div className="w-24 shrink-0 text-sm font-medium text-stone-700">
                  {d.label}
                  {d.foco && <span className="ml-1 text-leaf" title="foco da fase atual">●</span>}
                </div>
                <div className="h-2 flex-1 overflow-hidden rounded-full bg-stone-200">
                  <div className={`h-full rounded-full ${st.bar}`} style={{ width: `${d.score}%` }} />
                </div>
                <div className={`w-16 shrink-0 text-right text-sm font-semibold ${st.cls}`}>{Math.round(d.score)}</div>
                <span className="shrink-0 text-stone-400 transition group-open:rotate-180">▾</span>
              </summary>
              {info && (
                <div className="space-y-2 border-t border-stone-100 px-3 py-3 text-xs">
                  <p className="text-stone-600">{info.desc}</p>
                  <p className="text-stone-500">
                    <span className="font-semibold uppercase tracking-wide text-stone-400">Como melhorar</span>
                    <br />
                    {info.melhora}
                  </p>
                </div>
              )}
            </details>
          );
        })}
      </div>

      {radar.estado?.foco_texto && (
        <p className="mt-4 rounded-lg bg-green-50 p-3 text-xs text-stone-600">
          <span className="font-medium text-leafdark">Agora importa:</span> {radar.estado.foco_texto}
        </p>
      )}
    </div>
  );
}
