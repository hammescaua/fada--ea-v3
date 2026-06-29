"""Endpoints do motor: simulação, janela de semeadura, catálogos de apoio."""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter

from agro_engine import (
    accuracy_report,
    assess_data_quality,
    crop_plan,
    operations_impact,
    optimize_season,
    recommend_amendments,
    recommend_decisions,
    recommend_sowing_window,
    run_montecarlo,
    season_briefing,
    season_budget,
    simulate,
)
from agro_engine.models import (
    CostItem,
    Cultivar,
    Operation,
    Scenario,
    SoilProfile,
    SoilTexture,
)
from agro_engine.reference import NO_RS_MUNICIPALITIES

from .. import weather
from .. import assistant
from ..schemas import (
    AccuracyIn,
    AssistantIn,
    BriefingIn,
    CropPlanIn,
    DataQualityIn,
    MonteCarloIn,
    ScenarioIn,
    SimulationOut,
)
from agro_engine import kb

router = APIRouter(tags=["motor"])


def _to_scenario(payload: ScenarioIn) -> Scenario:
    soil = SoilProfile(
        texture=SoilTexture(payload.soil.texture),
        clay_pct=payload.soil.clay_pct,
        organic_matter_pct=payload.soil.organic_matter_pct,
        ph=payload.soil.ph,
        cec=payload.soil.cec,
        base_saturation_pct=payload.soil.base_saturation_pct,
        phosphorus_ppm=payload.soil.phosphorus_ppm,
        potassium_ppm=payload.soil.potassium_ppm,
        compaction=payload.soil.compaction,
        rooting_depth_m=payload.soil.rooting_depth_m,
    )
    cultivar = Cultivar(
        name=payload.cultivar.name,
        maturity_group=payload.cultivar.maturity_group,
        base_potential_sc_ha=payload.cultivar.base_potential_sc_ha,
        cycle_days=payload.cultivar.cycle_days,
        disease_tolerance=payload.cultivar.disease_tolerance,
    )
    scenario = Scenario(
        soil=soil,
        cultivar=cultivar,
        sowing_date=payload.sowing_date,
        municipality=payload.municipality,
        latitude=payload.latitude,
        longitude=payload.longitude,
        population_k_per_ha=payload.population_k_per_ha,
        row_spacing_cm=payload.row_spacing_cm,
        operations=[
            Operation(
                kind=o.kind, op_date=o.op_date, product=o.product,
                dose=o.dose, cost_per_ha=o.cost_per_ha, quality=o.quality,
            )
            for o in payload.operations
        ],
        costs=[
            CostItem(category=c.category, description=c.description, cost_per_ha=c.cost_per_ha)
            for c in payload.costs
        ],
        soybean_price_per_sc=payload.soybean_price_per_sc,
    )

    scenario._weather_source = "sintetico"  # type: ignore[attr-defined]
    scenario._weather_meta = {}  # type: ignore[attr-defined]
    if payload.use_live_weather:
        end = payload.sowing_date + timedelta(days=cultivar.cycle_days + 20)
        try:
            series, meta = weather.get_season_weather(
                payload.latitude, payload.longitude, payload.sowing_date, end
            )
            scenario.weather = series
            scenario._weather_source = meta.get("source", "climatologia_real")  # type: ignore[attr-defined]
            scenario._weather_meta = meta  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001 — degrada para clima sintético
            scenario.weather = None
    return scenario


@router.post("/simulate", response_model=SimulationOut)
def post_simulate(payload: ScenarioIn) -> SimulationOut:
    """Roda o pipeline completo (fenologia→água→ZARC→IPPD→econômico)."""
    scenario = _to_scenario(payload)
    result = simulate(scenario)
    water = {**result.water, "source": getattr(scenario, "_weather_source", "sintetico")}
    return SimulationOut(
        yield_result={
            "base_potential_sc_ha": result.yield_result.base_potential_sc_ha,
            "contributions": [c.__dict__ for c in result.yield_result.contributions],
            "expected_sc_ha": result.yield_result.expected_sc_ha,
            "uncertainty_sc_ha": result.yield_result.uncertainty_sc_ha,
            "confidence": result.yield_result.confidence,
        },
        economics=result.economics.__dict__,
        phenology=result.phenology,
        water=water,
        sowing_window=result.sowing_window,
    )


@router.post("/briefing")
def post_briefing(payload: BriefingIn) -> dict:
    """Resumo da Safra: a resposta única do gêmeo. Compõe simulação, risco, melhor
    ação e veracidade dos dados num veredito priorizado com status de saúde — o que o
    agricultor lê em segundos para decidir. Auto-detecta a fonte do clima."""
    scenario = _to_scenario(payload.scenario)
    return season_briefing(scenario, _with_climate_prov(scenario, payload.provenance))


_CLIMATE_PROV = {
    "safra_realizada": "safra_realizada",
    "safra_corrente": "safra_corrente",
    "climatologia_real": "climatologia_real",
    "sintetico": "estimado",
}


def _with_climate_prov(scenario, provenance: dict) -> dict:
    """Preenche a fonte do clima detectada pelo backend (realizado/corrente/histórico)."""
    prov = dict(provenance)
    src = getattr(scenario, "_weather_source", "sintetico")
    prov.setdefault("clima", _CLIMATE_PROV.get(src, "estimado"))
    return prov


def _climate_known_fraction(scenario) -> float | None:
    """Fração do ciclo já conhecida (observada + prevista) — encolhe a incerteza do clima."""
    meta = getattr(scenario, "_weather_meta", {}) or {}
    obs = meta.get("observed_days", 0)
    fc = meta.get("forecast_days", 0)
    clim = meta.get("climatology_days", 0)
    total = obs + fc + clim
    return (obs + fc) / total if total else None


@router.post("/accuracy")
def post_accuracy(payload: AccuracyIn) -> dict:
    """Acurácia por talhão: para cada variável, a fonte em uso, quão local ela é, quanto
    a estimativa pode mudar (sc/ha) e COMO torná-la mais precisa para este talhão/local."""
    scenario = _to_scenario(payload.scenario)
    return accuracy_report(
        scenario,
        _with_climate_prov(scenario, payload.provenance),
        _climate_known_fraction(scenario),
    )


@router.post("/crop-plan")
def post_crop_plan(payload: CropPlanIn) -> dict:
    """Plano de Safra ao Vivo: passo-a-passo por fase (preparo → semeadura → vegetativo →
    reprodutivo → colheita), com manejos, impacto em sc/ha e R$, status vs. hoje e a
    proveniência dos dados de cada etapa (de onde vêm e como melhorar)."""
    scenario = _to_scenario(payload.scenario)
    return crop_plan(
        scenario,
        today=payload.today,
        provenance=_with_climate_prov(scenario, payload.provenance),
        climate_known_fraction=_climate_known_fraction(scenario),
    )


@router.get("/reference/inputs")
def get_reference_inputs() -> dict:
    """Catálogo de insumos com PREÇO DE REFERÊNCIA e fonte citada — a fidelidade dos
    custos vem daqui (mercado BR/RS), não de números mágicos; o agricultor ajusta ao real."""
    raw = kb._load("inputs_catalog.json")  # type: ignore[attr-defined]
    return {"meta": raw.get("_meta", {}), "inputs": raw.get("inputs", {})}


@router.post("/simulate/montecarlo")
def post_montecarlo(payload: MonteCarloIn) -> dict:
    """Roda N safras possíveis (clima + preço estocásticos) e devolve a distribuição
    de produtividade e lucro, com probabilidades de atingir metas e de prejuízo."""
    payload.use_live_weather = False  # Monte Carlo sintetiza o próprio clima
    scenario = _to_scenario(payload)
    return run_montecarlo(
        scenario,
        n=payload.iterations,
        seed=payload.seed,
        price_sd_pct=payload.price_sd_pct,
        profit_target_per_ha=payload.profit_target_per_ha,
        yield_target_sc_ha=payload.yield_target_sc_ha,
    )


@router.post("/assistant")
def post_assistant(payload: AssistantIn) -> dict:
    """Assistente de decisão (LLM): interpreta a pergunta, consulta os motores via
    tool use e narra os números — nunca calcula. Cai para narrador determinístico
    quando não há ANTHROPIC_API_KEY."""
    scenario = _to_scenario(payload.scenario)
    return assistant.ask(payload.question, scenario)


@router.post("/data-quality")
def post_data_quality(payload: DataQualityIn) -> dict:
    """Veracidade dos dados do talhão: índice de confiança + lacunas ranqueadas por
    valor-da-informação (o que medir primeiro). Auto-detecta a fonte do clima."""
    scenario = _to_scenario(payload.scenario)
    return assess_data_quality(scenario, _with_climate_prov(scenario, payload.provenance))


@router.post("/optimize-season")
def post_optimize_season(payload: ScenarioIn) -> dict:
    """Motor de cenários: varre combinações de data × população × programa de fungicida,
    ranqueia por lucro e devolve o melhor plano para o talhão + a explicação do porquê."""
    scenario = _to_scenario(payload)
    return optimize_season(scenario)


@router.post("/fertility")
def post_fertility(payload: ScenarioIn) -> list[dict]:
    """Recomendação de corretivos/adubação para o solo do talhão: dose (método CQFS),
    investimento (preço do catálogo), impacto na produtividade e ROI — ranqueado por
    rentabilidade. Responde 'vale a pena para o meu solo e qual é mais rentável'."""
    scenario = _to_scenario(payload)
    return [r.__dict__ for r in recommend_amendments(scenario)]


@router.post("/season-plan")
def post_season_plan(payload: ScenarioIn) -> dict:
    """Plano da safra: orçamento por categoria, fluxo de caixa (capital de giro) e o
    impacto de cada manejo (quanto cada ação representa em produtividade e R$)."""
    scenario = _to_scenario(payload)
    result = simulate(scenario)
    budget = season_budget(scenario, result.yield_result.expected_sc_ha)
    impacts = [i.__dict__ for i in operations_impact(scenario)]
    return {"budget": budget, "operations_impact": impacts}


@router.post("/decisions")
def post_decisions(payload: ScenarioIn) -> list[dict]:
    """Motor de Decisão: avalia intervenções possíveis no talhão e as ordena por
    Δlucro esperado, com Δprodutividade, ROI da ação e probabilidade de retorno."""
    scenario = _to_scenario(payload)
    return [r.__dict__ for r in recommend_decisions(scenario)]


@router.get("/sowing-window")
def get_sowing_window(municipality: str, year: int | None = None) -> dict:
    year = year or date.today().year
    return recommend_sowing_window(municipality, year)


@router.get("/municipalities")
def get_municipalities() -> list[str]:
    return NO_RS_MUNICIPALITIES


@router.get("/cultivars/sample")
def get_sample_cultivars() -> list[dict]:
    """Catálogo de exemplo (grupos de maturação típicos do NO do RS)."""
    return [
        {"name": "GMR 5.2 precoce", "maturity_group": 5.2, "base_potential_sc_ha": 92, "cycle_days": 120, "disease_tolerance": 0.5},
        {"name": "GMR 5.5 média", "maturity_group": 5.5, "base_potential_sc_ha": 95, "cycle_days": 130, "disease_tolerance": 0.6},
        {"name": "GMR 6.2 tardia", "maturity_group": 6.2, "base_potential_sc_ha": 98, "cycle_days": 140, "disease_tolerance": 0.4},
    ]
