"use client";

import { useEffect, useRef, useState } from "react";
import { EXPLANATIONS } from "@/lib/explanations";

/** "Por que estou vendo isso?" — um "?" ao lado de qualquer indicador que, ao
 *  toque (funciona no tablet, não só no hover), explica o que é, de onde vem,
 *  por que importa e o que fazer. Fecha ao clicar fora ou com Esc. */
export function WhyBadge({ id, label = "Por quê?" }: { id: keyof typeof EXPLANATIONS | string; label?: string }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLSpanElement>(null);
  const e = EXPLANATIONS[id];

  useEffect(() => {
    if (!open) return;
    const onDoc = (ev: MouseEvent) => {
      if (ref.current && !ref.current.contains(ev.target as Node)) setOpen(false);
    };
    const onKey = (ev: KeyboardEvent) => ev.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  if (!e) return null;

  return (
    <span ref={ref} className="relative inline-flex print:hidden">
      <button
        type="button"
        aria-label={`${label}: ${e.titulo}`}
        onClick={(ev) => {
          ev.stopPropagation();
          setOpen((v) => !v);
        }}
        className={`ml-1 flex h-4 w-4 items-center justify-center rounded-full text-[10px] font-bold transition ${
          open ? "bg-leaf text-white" : "bg-stone-200 text-stone-500 hover:bg-stone-300"
        }`}
      >
        ?
      </button>
      {open && (
        <span
          role="dialog"
          className="absolute left-1/2 top-6 z-30 w-72 -translate-x-1/2 space-y-2 rounded-xl border border-stone-200 bg-white p-3.5 text-left shadow-xl"
        >
          <span className="block text-sm font-bold text-leafdark">{e.titulo}</span>
          <Line rot="O que é" txt={e.o_que_e} />
          <Line rot="De onde vem" txt={e.de_onde_vem} />
          <Line rot="Por que importa" txt={e.por_que_importa} />
          <Line rot="O que fazer" txt={e.o_que_fazer} accent />
        </span>
      )}
    </span>
  );
}

function Line({ rot, txt, accent }: { rot: string; txt: string; accent?: boolean }) {
  return (
    <span className="block">
      <span className="block text-[10px] font-semibold uppercase tracking-wide text-stone-400">{rot}</span>
      <span className={`block text-xs leading-snug ${accent ? "text-leafdark" : "text-stone-600"}`}>{txt}</span>
    </span>
  );
}
