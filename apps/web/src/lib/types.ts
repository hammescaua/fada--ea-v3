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
  nematode_tolerance?: number;
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
  enso?: "el_nino" | "neutro" | "la_nina";
  nematode_pressure?: "nenhuma" | "baixa" | "media" | "alta";
  previous_crop?: "soja" | "milho" | "trigo" | "cobertura" | "pousio";
  // Calibração aprendida do talhão (injetada ao carregar um talhão com histórico).
  calibration_bias_sc_ha?: number;
  calibration_confidence?: number;
  calibration_seasons?: number;
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

export interface DataQualityOut {
  data_confidence: number;
  sources: Record<string, string>;
  gaps: { group: string; current_source: string; leverage_sc_ha: number; como_obter: string }[];
  resumo: string;
}

export interface BriefingAction {
  rank: number;
  key: string;
  label: string;
  delta_yield_sc_ha: number;
  delta_profit_per_ha: number;
  action_roi: number | null;
  probability_positive: number;
  justification: string;
}

export interface BriefingOut {
  status: "saudavel" | "atencao" | "critico";
  status_label: string;
  municipality: string;
  sowing_date: string;
  expected_sc_ha: number;
  uncertainty_sc_ha: number;
  p10_sc_ha: number;
  p90_sc_ha: number;
  profit_per_ha: number;
  roi: number;
  breakeven_yield_sc_ha: number;
  prob_loss: number;
  sowing_position: string;
  sowing_penalty_sc_ha: number;
  data_confidence: number;
  top_data_gap: { group: string; leverage_sc_ha: number; como_obter: string } | null;
  actions: BriefingAction[];
  veredito: string;
  alertas: string[];
}

export interface AccuracyVariable {
  group: string;
  label: string;
  drives: string[];
  current_tier: string;
  current_label: string;
  current_note: string;
  quality: number;
  is_local: boolean;
  locality: string;
  leverage_sc_ha: number;
  how_to_improve: string;
  source: string;
  tiers: { id: string; label: string; quality: number; note: string }[];
}

export interface AccuracyOut {
  precision_index: number;
  precision_label: string;
  variables: AccuracyVariable[];
  top_improvements: AccuracyVariable[];
  resumo: string;
}

export interface ManejoEvidence {
  kind: string;
  alvo: string;
  mecanismo: string;
  coeficiente: { key: string; value: unknown; source: string | null } | null;
  coeficiente_secundario: { key: string; value: unknown; source: string | null } | null;
  personaliza_por: string[];
  leitura_talhao: string;
  fonte: string;
}

export interface CropPlanManejo {
  kind: string;
  label: string;
  planned: boolean;
  op_date: string | null;
  cost_per_ha: number | null;
  dose: number | null;
  product?: string | null;
  funcao: string;
  janela?: string;
  cost_reference?: string | null;
  impact_sc_ha: number | null;
  impact_rs: number | null;
  evidencia: ManejoEvidence | null;
}

export interface CropPlanPhase {
  key: string;
  label: string;
  factor: string;
  orientacao: string;
  start: string;
  end: string;
  status: "concluida" | "em_andamento" | "futura";
  manejos: CropPlanManejo[];
  impact_sc_ha: number;
  impact_rs: number;
  water_stress: number | null;
  data_basis: {
    group: string;
    label: string;
    current_label: string;
    is_local: boolean;
    leverage_sc_ha: number;
    how_to_improve: string;
  }[];
}

export interface CropPlanOut {
  today: string;
  sowing_date: string;
  harvest_date: string;
  cycle_days: number;
  progress_pct: number;
  current_phase: string | null;
  expected_sc_ha: number;
  profit_per_ha: number;
  precision_index: number;
  weather_source: string;
  weather_meta: {
    observed_days?: number;
    forecast_days?: number;
    climatology_days?: number;
    source?: string;
  };
  phases: CropPlanPhase[];
  stages: { stage: string; date: string; status: string }[];
}

export interface Hypothesis {
  causa: string;
  fator: string;
  perda_sc_ha: number;
  perda_rs_ha: number;
  probabilidade: number;
  forca_cientifica: number;
  confianca_cientifica: number;
  nivel_evidencia: string;
  controlabilidade: "sim" | "parcial" | "nao";
  certeza_do_dado: number;
  a_confirmar: boolean;
  cadeia: string[];
  confirma_se: string;
  acao: string;
  fonte: string;
}

export interface DiagnoseOut {
  potencial_sc_ha: number;
  esperado_sc_ha: number;
  incerteza_sc_ha: number;
  gap_sc_ha: number;
  hipoteses: Hypothesis[];
  niveis_confianca: { dados: number; modelo: number; recomendacao: number; resultado: number };
  principal_incerteza: { variavel: string; amplitude_sc_ha: number; como_reduzir: string } | null;
  resumo: string;
}

export interface PriorityAction {
  rank: number;
  key: string;
  acao: string;
  categoria: string;
  impacto_sc_ha: number;
  impacto_rs: number;
  custo_per_ha: number;
  roi: number | null;
  probabilidade: number;
  veredito?: "recomendar" | "avaliar";
  urgencia?: number;
  prazo: string;
  porque: string;
  janela_status?: "agora" | "em breve" | "passou";
}

export interface MemoryOut {
  similares: {
    crop_year: string;
    semelhanca: number;
    principal_diferenca: string;
    resultado: { colhido_sc_ha: number; vs_previsto: string } | null;
  }[];
  resumo: string;
}

export interface RadarOut {
  score: number;
  score_label: "saudável" | "atenção" | "crítico";
  estado?: { fase: string; fase_label: string; foco: string[]; foco_texto: string };
  dimensions: { key: string; label: string; score: number; foco?: boolean }[];
  maior_risco: { dimensao: string; fator: string; perda_sc_ha: number; perda_rs_ha: number; detalhe: string } | null;
  maior_oportunidade: PriorityAction | null;
  maior_investimento: PriorityAction | null;
  actions: PriorityAction[];
  respostas: { maior_risco: string; melhor_decisao: string; quanto_vale: string; por_que: string };
  expected_sc_ha: number;
  profit_per_ha: number;
}

export interface RealityAdjustment {
  factor: string;
  manejo: string;
  before: number;
  after: number;
  reason: string;
  source: string;
  confidence: number;
}

export interface SeasonReviewOut {
  plano: { expected_sc_ha: number; profit_per_ha: number };
  realidade: { expected_sc_ha: number; profit_per_ha: number };
  delta_sc_ha: number;
  delta_profit_per_ha: number;
  adjustments: RealityAdjustment[];
  n_observations: number;
}

export interface PersonalityTrait {
  key: string;
  label: string;
  level: string;
  value: number;
  confidence: number;
  basis: string;
  learning: boolean;
}

export interface Interaction {
  rule: string;
  label: string;
  when: string;
  positive: boolean;
  description: string;
  recomendacao: string;
  confidence: number;
  efficacy_loss: number | null;
  source: string;
}

export interface InteractionsReport {
  n_interactions: number;
  interactions: Interaction[];
  resumo: string;
}

export interface PersonalityOut {
  knowledge_pct: number;
  n_seasons: number;
  n_observations: number;
  traits: PersonalityTrait[];
  resumo: string;
  data_quality: Record<string, number>;
  interactions?: InteractionsReport;
}

export interface CounterfactualItem {
  key: string;
  label: string;
  delta_yield_sc_ha: number;
  delta_profit_per_ha: number;
  expected_sc_ha: number;
  profit_per_ha: number;
  narrative: string;
}

export interface CounterfactualOut {
  base_expected_sc_ha: number;
  base_profit_per_ha: number;
  counterfactuals: CounterfactualItem[];
}

export interface ObservationOut {
  id: string;
  field_id: string;
  observed_at: string;
  kind: string;
  source: string;
  value: Record<string, unknown>;
  unit: string | null;
  confidence: number;
  latitude: number | null;
  longitude: number | null;
  consequence: string | null;
}

export interface ObservationIn {
  kind: string;
  source: string;
  observed_at: string;
  value: Record<string, unknown>;
  unit?: string | null;
  consequence?: string | null;
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
