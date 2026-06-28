import type { MonteCarloIn, MonteCarloOut, ScenarioIn, SimulationOut } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

async function jget<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`GET ${path} falhou: ${res.status}`);
  return res.json();
}

async function jpost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path} falhou: ${res.status}`);
  return res.json();
}

export const api = {
  simulate: (scenario: ScenarioIn) => jpost<SimulationOut>("/api/simulate", scenario),
  montecarlo: (input: MonteCarloIn) =>
    jpost<MonteCarloOut>("/api/simulate/montecarlo", input),
  municipalities: () => jget<string[]>("/api/municipalities"),
  sampleCultivars: () =>
    jget<
      { name: string; maturity_group: number; base_potential_sc_ha: number; cycle_days: number; disease_tolerance: number }[]
    >("/api/cultivars/sample"),
  sowingWindow: (municipality: string, year: number) =>
    jget<Record<string, string>>(
      `/api/sowing-window?municipality=${encodeURIComponent(municipality)}&year=${year}`,
    ),
};

// Cenário padrão (talhão argiloso típico do Noroeste do RS).
export function defaultScenario(): ScenarioIn {
  return {
    soil: {
      texture: "argiloso",
      clay_pct: 62,
      organic_matter_pct: 3.8,
      ph: 5.8,
      cec: 15,
      base_saturation_pct: 62,
      phosphorus_ppm: 12,
      potassium_ppm: 140,
      compaction: "leve",
      rooting_depth_m: 0.6,
    },
    cultivar: {
      name: "GMR 5.5 média",
      maturity_group: 5.5,
      base_potential_sc_ha: 95,
      cycle_days: 130,
      disease_tolerance: 0.6,
    },
    sowing_date: "2025-11-05",
    municipality: "Santo Ângelo",
    latitude: -28.3,
    longitude: -54.26,
    population_k_per_ha: 300,
    row_spacing_cm: 45,
    operations: [
      { kind: "fungicida", op_date: "2026-01-10", cost_per_ha: 180, quality: 0.9 },
      { kind: "fungicida", op_date: "2026-01-24", cost_per_ha: 180, quality: 0.9 },
    ],
    costs: [
      { category: "semente", description: "Semente RR", cost_per_ha: 520 },
      { category: "fertilizante", description: "MAP + KCl", cost_per_ha: 1450 },
      { category: "defensivo", description: "Herbicidas + inseticidas", cost_per_ha: 650 },
      { category: "diesel", description: "Operações mecanizadas", cost_per_ha: 380 },
      { category: "outros", description: "Frete + secagem + admin", cost_per_ha: 620 },
    ],
    soybean_price_per_sc: 120,
    use_live_weather: false,
  };
}
