"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { defaultScenario } from "@/lib/api";
import type { ScenarioIn } from "@/lib/types";

/** Estado compartilhado por todas as páginas (o cenário do talhão vive aqui,
 *  não numa página gigante). Persiste no navegador para o produtor voltar e
 *  encontrar tudo como deixou. */

interface Store {
  scenario: ScenarioIn;
  debounced: ScenarioIn;
  setScenario: (u: ScenarioIn | ((s: ScenarioIn) => ScenarioIn)) => void;
  patchScenario: (p: Partial<ScenarioIn>) => void;
  soilReal: boolean;
  setSoilReal: (b: boolean) => void;
  provenance: Record<string, string>;
  configured: boolean;
  setConfigured: (b: boolean) => void;
  hydrated: boolean;
  selectedFieldId: string | null;
  setSelectedFieldId: (id: string | null) => void;
}

const Ctx = createContext<Store | null>(null);

function useDebounced<T>(value: T, ms = 350): T {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return v;
}

export function ScenarioProvider({ children }: { children: React.ReactNode }) {
  const [scenario, setScenario] = useState<ScenarioIn>(defaultScenario);
  const [soilReal, setSoilReal] = useState(false);
  const [configured, setConfigured] = useState(false);
  const [hydrated, setHydrated] = useState(false);
  const [selectedFieldId, setSelectedFieldId] = useState<string | null>(null);
  const debounced = useDebounced(scenario, 350);

  // Hidratar do navegador na primeira montagem.
  useEffect(() => {
    try {
      const raw = window.localStorage.getItem("fada_state");
      if (raw) {
        const p = JSON.parse(raw);
        if (p.scenario) setScenario(p.scenario);
        if (typeof p.soilReal === "boolean") setSoilReal(p.soilReal);
      }
      setConfigured(!!window.localStorage.getItem("fada_setup"));
    } catch {
      /* ignora */
    }
    setHydrated(true);
  }, []);

  // Persistir mudanças.
  useEffect(() => {
    if (!hydrated) return;
    try {
      window.localStorage.setItem("fada_state", JSON.stringify({ scenario, soilReal }));
    } catch {
      /* ignora */
    }
  }, [scenario, soilReal, hydrated]);

  const value = useMemo<Store>(
    () => ({
      scenario,
      debounced,
      setScenario,
      patchScenario: (p) => setScenario((s) => ({ ...s, ...p })),
      soilReal,
      setSoilReal,
      provenance: { solo: soilReal ? "real" : "estimado" },
      configured,
      setConfigured,
      hydrated,
      selectedFieldId,
      setSelectedFieldId,
    }),
    [scenario, debounced, soilReal, configured, hydrated, selectedFieldId],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useScenario(): Store {
  const v = useContext(Ctx);
  if (!v) throw new Error("useScenario precisa do ScenarioProvider");
  return v;
}
