// Tipos espelhando o contrato da API (apps/api/app/schemas.py).

export interface SoilIn {
  texture: string;
  clay_pct: number;
  organic_matter_pct: number;
  ph: number;
  cec: number;
  base_saturation_pct: number;
  phosphorus_ppm: number;
  potassium_ppm: number;
  compaction: string;
  rooting_depth_m: number;
}

export interface CultivarIn {
  name: string;
  maturity_group: number;
  base_potential_sc_ha: number;
  cycle_days: number;
  disease_tolerance: number;
}

export interface OperationIn {
  kind: string;
  op_date: string;
  product?: string;
  dose?: number;
  cost_per_ha: number;
  quality: number;
}

export interface CostItemIn {
  category: string;
  description: string;
  cost_per_ha: number;
}

export interface ScenarioIn {
  soil: SoilIn;
  cultivar: CultivarIn;
  sowing_date: string;
  municipality: string;
  latitude: number;
  longitude: number;
  population_k_per_ha: number;
  row_spacing_cm: number;
  operations: OperationIn[];
  costs: CostItemIn[];
  soybean_price_per_sc: number;
  use_live_weather: boolean;
}

export interface FactorOut {
  label: string;
  delta_sc_ha: number;
  confidence: number;
  detail: string;
}

export interface YieldOut {
  base_potential_sc_ha: number;
  contributions: FactorOut[];
  expected_sc_ha: number;
  uncertainty_sc_ha: number;
  confidence: number;
}

export interface EconomicsOut {
  total_cost_per_ha: number;
  revenue_per_ha: number;
  profit_per_ha: number;
  margin_pct: number;
  roi: number;
  breakeven_yield_sc_ha: number;
  breakeven_price_per_sc: number;
}

export interface SimulationOut {
  yield_result: YieldOut;
  economics: EconomicsOut;
  phenology: Record<string, string>;
  water: Record<string, unknown>;
  sowing_window: Record<string, unknown>;
}

export interface HistBin {
  start: number;
  end: number;
  count: number;
}

export interface DistributionOut {
  mean: number;
  p10: number;
  p50: number;
  p90: number;
  histogram: HistBin[];
}

export interface MonteCarloOut {
  iterations: number;
  yield: DistributionOut;
  profit: DistributionOut;
  probabilities: {
    yield_above_target: number;
    yield_target: number;
    profit_above_target: number;
    profit_target: number;
    loss: number;
  };
}

export interface OptimizeOut {
  combinacoes_avaliadas: number;
  atual: { expected_sc_ha: number; profit_per_ha: number };
  melhor_plano: {
    sowing_date: string;
    population_k_per_ha: number;
    num_fungicidas: number;
    expected_sc_ha: number;
    profit_per_ha: number;
    delta_profit_vs_atual: number;
    delta_yield_vs_atual: number;
  };
  ranking: {
    sowing_date: string;
    population_k_per_ha: number;
    num_fungicidas: number;
    expected_sc_ha: number;
    profit_per_ha: number;
  }[];
  decomposicao: { fator: string; delta_sc_ha: number; detalhe: string }[];
  porques: string[];
  fertilidade: { acao: string; investimento_por_ha: number; liquido_por_ano: number; roi: number | null }[];
}

export interface FertilityRec {
  key: string;
  label: string;
  product: string;
  dose: number;
  dose_unit: string;
  investment_per_ha: number;
  residual_years: number;
  annual_cost_per_ha: number;
  delta_yield_sc_ha: number;
  value_per_ha: number;
  net_per_ha: number;
  roi: number | null;
  rationale: string;
}

export interface SeasonPlanOut {
  budget: {
    cost_by_category: Record<string, number>;
    total_cost_per_ha: number;
    revenue_per_ha: number;
    profit_per_ha: number;
    working_capital_per_ha: number;
    harvest_date: string;
    cashflow: { day: string; label: string; amount: number; balance: number }[];
  };
  operations_impact: {
    kind: string;
    op_date: string;
    cost_per_ha: number;
    delta_yield_sc_ha: number;
    value_per_ha: number;
    net_per_ha: number;
    roi: number | null;
  }[];
}

export interface FarmOut {
  id: string;
  name: string;
  municipality: string;
}

export interface FieldOut {
  id: string;
  farm_id: string;
  name: string;
  municipality: string;
  area_ha: number | null;
  centroid_lat: number | null;
  centroid_lon: number | null;
}

export interface SoilTestOut {
  id: string;
  field_id: string;
  sampled_at: string | null;
  clay_pct: number | null;
  organic_matter_pct: number | null;
  ph: number | null;
  cec: number | null;
  base_saturation_pct: number | null;
  phosphorus_ppm: number | null;
  potassium_ppm: number | null;
}

export interface SeasonSummaryOut {
  id: string;
  crop_year: string;
  cultivar_name: string | null;
  sowing_date: string | null;
  predicted_yield_sc_ha: number | null;
  actual_yield_sc_ha: number | null;
}

export interface AssistantOut {
  answer: string;
  used_llm: boolean;
  tool_calls: { tool: string }[];
  note?: string;
}

export interface SeasonOutcome {
  crop_year: string;
  predicted_sc_ha: number;
  actual_sc_ha: number;
}

export interface CalibrationOut {
  n_seasons: number;
  bias_sc_ha: number;
  confidence: number;
  mae_before: number;
  mae_after: number;
  raw_bias_sc_ha: number;
}

export interface DecisionOut {
  key: string;
  label: string;
  description: string;
  category: string;
  added_cost_per_ha: number;
  delta_yield_sc_ha: number;
  delta_profit_per_ha: number;
  action_roi: number | null;
  probability_positive: number;
  justification: string;
}

export interface MonteCarloIn extends ScenarioIn {
  iterations: number;
  seed: number | null;
  price_sd_pct: number;
  profit_target_per_ha: number;
  yield_target_sc_ha: number | null;
}
