"use client";

import type { ScenarioIn } from "@/lib/types";

/** "Como o FADA chegou nesse número." Assume a incerteza explicitamente e mostra
 *  a pirâmide de conhecimento — da ciência ao talhão. A mensagem: o FADA não
 *  adivinha; começa com ciência e troca médias pelo que é específico da sua
 *  lavoura. Tudo derivado de dados reais informados — nada inventado. */
export function KnowledgeBasis({
  expected,
  precision,
  scenario,
  soilReal,
}: {
  expected: number;
  precision: number; // 0..1
  scenario: ScenarioIn;
  soilReal: boolean;
}) {
  const pct = Math.round(precision * 100);
  const temManejos = scenario.operations.length > 0;
  const temHistorico = (scenario.calibration_seasons ?? 0) > 0;

  const levels = [
    { n: 1, label: "Conhecimento científico", detail: "Embrapa, universidades, literatura", active: true },
    { n: 2, label: "Conhecimento regional", detail: "Noroeste do RS: clima, solos e calendário ZARC", active: true },
    { n: 3, label: "Conhecimento da propriedade", detail: "Localização e cultivar informadas", active: true },
    { n: 4, label: "Conhecimento do talhão", detail: "Análise de solo do seu talhão", active: soilReal },
    { n: 5, label: "Conhecimento desta safra", detail: "Plantio, manejos e observações", active: temManejos },
    { n: 6, label: "Aprendizado contínuo", detail: "Resultados de safras anteriores", active: temHistorico },
  ];

  const used = [
    "Histórico climático do seu talhão",
    "Cultivar e grupo de maturação",
    "Data de plantio e população",
    soilReal ? "Análise de solo do talhão" : "Perfil de solo regional (NO-RS)",
    "Rotação de culturas",
    "Literatura científica e modelos agronômicos",
    ...(temManejos ? ["Manejos registrados nesta safra"] : []),
    ...(temHistorico ? ["Resultados de safras anteriores"] : []),
  ];
  const notUsed = [
    ...(soilReal ? [] : ["Análise de solo real do seu talhão"]),
    ...(temManejos ? [] : ["Monitoramento de campo desta safra"]),
    ...(temHistorico ? [] : ["Colheita das safras anteriores"]),
    "Imagens de satélite (NDVI)",
    "Imagens de drone",
  ];

  return (
    <div className="rounded-2xl border border-stone-200 bg-white p-6">
      <h3 className="text-sm font-bold text-stone-800">Como o FADA chegou nesse número</h3>

      {/* Assumir a incerteza gera mais confiança que um número "mágico". Isto
          fica sempre visível; o detalhe (pirâmide e fontes) abre sob demanda. */}
      <p className="mt-2 text-sm leading-relaxed text-stone-600">
        Nossa estimativa é <span className="font-semibold text-stone-800">{expected.toFixed(1)} sc/ha</span>, com{" "}
        <span className="font-semibold text-stone-800">{pct}% de confiança</span> nos dados — porque já conhecemos{" "}
        {used.slice(0, 3).join(", ").toLowerCase()}.{" "}
        {notUsed.length > 0 && (
          <>
            Ainda não temos {notUsed.slice(0, 2).join(" nem ").toLowerCase()}, então essa previsão pode mudar conforme
            novos dados chegam.
          </>
        )}
      </p>

      <details className="group mt-3">
        <summary className="flex cursor-pointer list-none items-center gap-1 text-xs font-medium text-leafdark">
          <span className="transition group-open:rotate-180">▾</span> Ver a base do cálculo (pirâmide de conhecimento e fontes)
        </summary>
        <div className="mt-4">
      {/* Pirâmide de conhecimento: da ciência ao talhão. */}
      <div>
        <div className="mb-2 text-[11px] uppercase tracking-wide text-stone-400">
          O FADA começa com ciência e vai ficando específico da sua lavoura
        </div>
        <ol className="space-y-1">
          {levels.map((l) => (
            <li
              key={l.n}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 ${
                l.active ? "bg-green-50" : "bg-stone-50"
              }`}
            >
              <span
                className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                  l.active ? "bg-leaf text-white" : "bg-stone-200 text-stone-400"
                }`}
              >
                {l.n}
              </span>
              <span className="min-w-0 flex-1">
                <span className={`block text-sm font-medium ${l.active ? "text-stone-800" : "text-stone-400"}`}>
                  {l.label}
                </span>
                <span className="block text-xs text-stone-500">{l.detail}</span>
              </span>
              <span className={`shrink-0 text-xs ${l.active ? "text-leafdark" : "text-stone-300"}`}>
                {l.active ? "ativo" : "aguardando dados"}
              </span>
            </li>
          ))}
        </ol>
      </div>

      {/* Transparência total: o que entra e o que ainda não entra. */}
      <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <div className="mb-1 text-[11px] uppercase tracking-wide text-stone-400">Já usamos</div>
          <ul className="space-y-0.5">
            {used.map((u) => (
              <li key={u} className="flex items-start gap-1.5 text-xs text-stone-600">
                <span className="text-leaf">✓</span> {u}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <div className="mb-1 text-[11px] uppercase tracking-wide text-stone-400">Ainda não usamos</div>
          <ul className="space-y-0.5">
            {notUsed.map((u) => (
              <li key={u} className="flex items-start gap-1.5 text-xs text-stone-400">
                <span>✗</span> {u}
              </li>
            ))}
          </ul>
        </div>
      </div>

          <p className="mt-4 border-t border-stone-100 pt-3 text-xs text-stone-500">
            Nenhum sistema prevê uma safra com exatidão. O que o FADA faz é construir um modelo da{" "}
            <span className="font-medium text-stone-700">sua</span> lavoura e, a cada safra, trocar médias pelo
            conhecimento real do seu talhão.
          </p>
        </div>
      </details>
    </div>
  );
}
