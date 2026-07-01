"use client";

import type { ScenarioIn } from "@/lib/types";
import { WhyBadge } from "@/components/WhyBadge";

/** Nível de digitalização: quanto da propriedade o FADA já conhece, contado só
 *  a partir de dados reais que o produtor forneceu. Não obriga nada — mostra o
 *  próximo passo que mais aumenta a precisão. Fica calmo (uma linha + accordion). */
export function DigitalizationLevel({
  scenario,
  soilReal,
  onGoToTalhao,
}: {
  scenario: ScenarioIn;
  soilReal: boolean;
  onGoToTalhao?: () => void;
}) {
  const items = [
    { key: "local", label: "Localização do talhão", done: !!scenario.municipality, weight: 0.15,
      why: "Define a janela ZARC e busca o clima real daquele ponto." },
    { key: "plano", label: "Cultivar e data de plantio", done: !!scenario.cultivar?.name && !!scenario.sowing_date, weight: 0.1,
      why: "Base da fenologia e da janela de semeadura." },
    { key: "solo", label: "Análise de solo do talhão", done: soilReal, weight: 0.3,
      why: "O dado que mais personaliza calagem e adubação." },
    { key: "rotacao", label: "Rotação (cultura anterior)", done: !!scenario.previous_crop, weight: 0.15,
      why: "Entra no risco de nematoides e na resposta a nitrogênio." },
    { key: "nema", label: "Pressão de nematoides", done: !!scenario.nematode_pressure, weight: 0.1,
      why: "Ajusta a quebra esperada por reboleiras." },
    { key: "manejos", label: "Manejos registrados no plano", done: scenario.operations.length > 0, weight: 0.2,
      why: "Cada aplicação registrada afina a sanidade e o custo." },
  ];

  const pct = Math.round(items.reduce((s, i) => s + (i.done ? i.weight : 0), 0) * 100);
  const missing = items.filter((i) => !i.done).sort((a, b) => b.weight - a.weight);
  const next = missing[0];

  return (
    <details className="group rounded-2xl border border-stone-200 bg-white">
      <summary className="flex cursor-pointer list-none items-center gap-3 p-4">
        <div className="flex-1">
          <div className="flex items-center text-sm font-medium text-stone-700">
            Sua propriedade está {pct}% digitalizada
            <WhyBadge id="digitalizacao" />
          </div>
          <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-stone-100">
            <div className="h-full rounded-full bg-leaf transition-all" style={{ width: `${pct}%` }} />
          </div>
          {next ? (
            <div className="mt-1.5 text-xs text-stone-500">
              Próximo passo: <span className="font-medium text-stone-700">{next.label}</span> — deixa a previsão mais sua.
            </div>
          ) : (
            <div className="mt-1.5 text-xs text-leafdark">Tudo informado — a previsão está no seu máximo de precisão ✓</div>
          )}
        </div>
        <span className="text-stone-400 transition group-open:rotate-180">▾</span>
      </summary>
      <ul className="space-y-2 border-t border-stone-100 p-4">
        {items.map((i) => (
          <li key={i.key} className="flex items-start gap-2 text-sm">
            <span className={i.done ? "text-leaf" : "text-stone-300"}>{i.done ? "✓" : "○"}</span>
            <div>
              <div className={i.done ? "text-stone-700" : "font-medium text-stone-800"}>{i.label}</div>
              {!i.done && <div className="text-xs text-stone-500">{i.why}</div>}
            </div>
          </li>
        ))}
        {onGoToTalhao && missing.length > 0 && (
          <li>
            <button onClick={onGoToTalhao} className="mt-1 text-xs font-medium text-leafdark underline">
              Informar no Talhão →
            </button>
          </li>
        )}
      </ul>
    </details>
  );
}
