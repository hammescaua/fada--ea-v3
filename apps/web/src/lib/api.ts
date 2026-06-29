import type {
  AccuracyOut,
  AssistantOut,
  BriefingOut,
  CalibrationOut,
  CounterfactualOut,
  CropPlanOut,
  DataQualityOut,
  ObservationIn,
  ObservationOut,
  PersonalityOut,
  RadarOut,
  SeasonReviewOut,
  DecisionOut,
  FarmOut,
  FertilityRec,
  FieldOut,
  MonteCarloIn,
  MonteCarloOut,
  OptimizeOut,
  ScenarioIn,
  SeasonOutcome,
  SeasonPlanOut,
  SeasonSummaryOut,
  SimulationOut,
  SoilTestOut,
} from "./types";

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
  decisions: (scenario: ScenarioIn) => jpost<DecisionOut[]>("/api/decisions", scenario),
  seasonPlan: (scenario: ScenarioIn) => jpost<SeasonPlanOut>("/api/season-plan", scenario),
  fertility: (scenario: ScenarioIn) => jpost<FertilityRec[]>("/api/fertility", scenario),
  optimizeSeason: (scenario: ScenarioIn) => jpost<OptimizeOut>("/api/optimize-season", scenario),
  radar: (scenario: ScenarioIn) => jpost<RadarOut>("/api/radar", scenario),
  briefing: (scenario: ScenarioIn, provenance: Record<string, string>) =>
    jpost<BriefingOut>("/api/briefing", { scenario, provenance }),
  cropPlan: (scenario: ScenarioIn, provenance: Record<string, string>, today?: string) =>
    jpost<CropPlanOut>("/api/crop-plan", { scenario, provenance, today: today ?? null }),
  accuracy: (scenario: ScenarioIn, provenance: Record<string, string>) =>
    jpost<AccuracyOut>("/api/accuracy", { scenario, provenance }),
  counterfactual: (scenario: ScenarioIn) =>
    jpost<CounterfactualOut>("/api/counterfactual", { scenario }),
  personality: (fieldId: string) => jget<PersonalityOut>(`/api/fields/${fieldId}/personality`),
  observations: (fieldId: string) => jget<ObservationOut[]>(`/api/fields/${fieldId}/observations`),
  seasonReview: (fieldId: string, scenario: ScenarioIn) =>
    jpost<SeasonReviewOut>(`/api/fields/${fieldId}/season-review`, { scenario }),
  addObservation: (fieldId: string, obs: ObservationIn) =>
    jpost<ObservationOut>(`/api/fields/${fieldId}/observations`, obs),
  dataQuality: (scenario: ScenarioIn, provenance: Record<string, string>) =>
    jpost<DataQualityOut>("/api/data-quality", { scenario, provenance }),
  calibration: (records: SeasonOutcome[]) =>
    jpost<CalibrationOut>("/api/calibration/compute", { records }),
  assistant: (question: string, scenario: ScenarioIn) =>
    jpost<AssistantOut>("/api/assistant", { question, scenario }),
  municipalities: () => jget<string[]>("/api/municipalities"),
  sampleCultivars: () =>
    jget<
      { name: string; maturity_group: number; base_potential_sc_ha: number; cycle_days: number; disease_tolerance: number }[]
    >("/api/cultivars/sample"),
  sowingWindow: (municipality: string, year: number) =>
    jget<Record<string, string>>(
      `/api/sowing-window?municipality=${encodeURIComponent(municipality)}&year=${year}`,
    ),

  // --- Gêmeo Digital persistido (cockpit) ---
  farms: () => jget<FarmOut[]>("/api/farms"),
  createFarm: (name: string, municipality: string) =>
    jpost<FarmOut>("/api/farms", { name, municipality }),
  fields: (farmId: string) => jget<FieldOut[]>(`/api/farms/${farmId}/fields`),
  createField: (farmId: string, body: Partial<FieldOut>) =>
    jpost<FieldOut>(`/api/farms/${farmId}/fields`, body),
  soilTests: (fieldId: string) => jget<SoilTestOut[]>(`/api/fields/${fieldId}/soil-tests`),
  createSoilTest: (fieldId: string, soil: Partial<SoilTestOut>) =>
    jpost<SoilTestOut>(`/api/fields/${fieldId}/soil-tests`, soil),
  fieldSeasons: (fieldId: string) => jget<SeasonSummaryOut[]>(`/api/fields/${fieldId}/seasons`),
  recordSeason: (fieldId: string, crop_year: string, scenario: ScenarioIn) =>
    jpost<{ id: string }>(`/api/fields/${fieldId}/seasons`, { crop_year, scenario }),
  fieldCalibration: (fieldId: string) =>
    jget<CalibrationOut>(`/api/fields/${fieldId}/calibration`),
  recordHarvest: (seasonId: string, actual_yield_sc_ha: number) =>
    jpost<{ id: string }>(
      `/api/seasons/${seasonId}/harvest?actual_yield_sc_ha=${actual_yield_sc_ha}`,
      {},
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
      nematode_tolerance: 0.5,
    },
    sowing_date: "2025-11-05",
    municipality: "Santo Ângelo",
    latitude: -28.3,
    longitude: -54.26,
    population_k_per_ha: 300,
    row_spacing_cm: 45,
    operations: [
      { kind: "herbicida", op_date: "2025-11-20", cost_per_ha: 160, quality: 0.9 },
      { kind: "inseticida", op_date: "2026-01-05", cost_per_ha: 120, quality: 0.9 },
      { kind: "fungicida", op_date: "2026-01-10", cost_per_ha: 180, quality: 0.9 },
      { kind: "fungicida", op_date: "2026-01-24", cost_per_ha: 180, quality: 0.9 },
    ],
    // Custos de referência (mercado BR/RS 2025 — ver /reference/inputs); o agricultor ajusta ao real.
    costs: [
      { category: "semente", description: "Semente RR (≈2,4 sc/ha)", cost_per_ha: 520 },
      { category: "fertilizante", description: "MAP + KCl (base, ref. catálogo)", cost_per_ha: 1450 },
      { category: "diesel", description: "Operações mecanizadas", cost_per_ha: 380 },
      { category: "outros", description: "Frete + secagem + admin", cost_per_ha: 620 },
    ],
    soybean_price_per_sc: 120,
    use_live_weather: true, // clima histórico REAL da localização (climatologia por talhão)
    enso: "neutro",
    nematode_pressure: "nenhuma",
    previous_crop: "soja",
    calibration_bias_sc_ha: 0,
    calibration_confidence: 0,
    calibration_seasons: 0,
  };
}
