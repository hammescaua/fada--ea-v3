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
