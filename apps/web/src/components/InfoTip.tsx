"use client";

/** Dica em linguagem do agricultor: um "?" que mostra a explicação ao passar o mouse.
 *  CSS puro (group-hover), sem estado — leve e sem custo de render. */
export function InfoTip({ text }: { text: string }) {
  return (
    <span className="group relative ml-1 inline-flex print:hidden">
      <span className="flex h-3.5 w-3.5 cursor-help items-center justify-center rounded-full bg-stone-200 text-[9px] font-bold text-stone-500">
        ?
      </span>
      <span className="pointer-events-none absolute bottom-full left-1/2 z-20 mb-1 w-52 -translate-x-1/2 rounded-md bg-stone-800 px-2 py-1.5 text-[11px] font-normal leading-snug text-white opacity-0 shadow-lg transition-opacity group-hover:opacity-100">
        {text}
      </span>
    </span>
  );
}
