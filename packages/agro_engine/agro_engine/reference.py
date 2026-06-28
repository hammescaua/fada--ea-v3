"""Parâmetros de referência agronômica (soja, Noroeste do RS).

Valores derivados de literatura consolidada (Embrapa Soja, ZARC/MAPA, FAO-56) e
calibráveis. São conservadores e servem ao motor **v0 determinístico**; a IA
personalizada (fases futuras) ajustará estes números por talhão com dados reais.

Cada constante é documentada com sua origem conceitual para auditabilidade.
"""

from __future__ import annotations

from .models import SoilTexture

# --- Fenologia (graus-dia, Tbase = 10 °C) -----------------------------------
# Estádios da soja em fração do total de GDD acumulado da EMERGÊNCIA até R8.
# Referência de ciclo: cultivar GMR 5.5 ~ 1450 GDD (emergência→R8).
TBASE_C: float = 10.0
TUPPER_C: float = 30.0  # acima disso o ganho de GDD satura (cap fisiológico)
GDD_PLANTING_TO_EMERGENCE: float = 110.0
GDD_EMERGENCE_TO_R8_REF: float = 1450.0
MATURITY_GROUP_REF: float = 5.5
# Cada ponto de grupo de maturação altera ~8% o total de GDD do ciclo.
GDD_PER_MATURITY_POINT: float = 0.08

STAGE_GDD_FRACTION: dict[str, float] = {
    "VE": 0.00,   # emergência
    "V1": 0.05,
    "V4": 0.18,
    "R1": 0.35,   # início do florescimento
    "R2": 0.42,   # pleno florescimento
    "R3": 0.50,   # início de formação de vagens
    "R4": 0.58,   # pleno desenvolvimento de vagens
    "R5": 0.66,   # início de enchimento de grãos
    "R5.5": 0.73,
    "R6": 0.80,   # pleno enchimento de grãos
    "R7": 0.92,   # início da maturação
    "R8": 1.00,   # maturação plena (colheita)
}

# --- Coeficiente de cultura Kc (FAO-56) por estádio --------------------------
KC_BY_STAGE: dict[str, float] = {
    "VE": 0.40,
    "V1": 0.55,
    "V4": 0.80,
    "R1": 1.05,
    "R2": 1.15,
    "R3": 1.15,
    "R4": 1.15,
    "R5": 1.10,
    "R5.5": 1.00,
    "R6": 0.90,
    "R7": 0.65,
    "R8": 0.45,
}

# Sensibilidade ao déficit hídrico por estádio (peso 0..1 do impacto na produtividade).
# R3–R5 (formação de vagens e enchimento) são os mais críticos.
WATER_SENSITIVITY_BY_STAGE: dict[str, float] = {
    "VE": 0.10,
    "V1": 0.15,
    "V4": 0.30,
    "R1": 0.60,
    "R2": 0.75,
    "R3": 0.95,
    "R4": 1.00,
    "R5": 1.00,
    "R5.5": 0.90,
    "R6": 0.70,
    "R7": 0.30,
    "R8": 0.05,
}

# --- Solo: água disponível (AWC, mm de água por m de solo) -------------------
AWC_MM_PER_M: dict[SoilTexture, float] = {
    SoilTexture.ARENOSO: 90.0,
    SoilTexture.MEDIO: 140.0,
    SoilTexture.ARGILOSO: 160.0,
}
DEPLETION_FRACTION_P: float = 0.50  # fração de água facilmente disponível (RAW = p·TAW)

# --- ZARC: janela de semeadura por município (Noroeste do RS) ----------------
# Período de menor risco climático (dia/mês). Fonte conceitual: Portarias ZARC/MAPA
# para soja no RS. Datas representativas para ciclo médio; refináveis por portaria.
# (start, end) no formato (mês, dia).
ZARC_SOWING_WINDOW: dict[str, tuple[tuple[int, int], tuple[int, int]]] = {
    "Santo Ângelo": ((10, 11), (12, 20)),
    "Ijuí": ((10, 11), (12, 20)),
    "Cruz Alta": ((10, 21), (12, 31)),
    "Santa Rosa": ((10, 1), (12, 10)),
    "Três de Maio": ((10, 1), (12, 10)),
    "Panambi": ((10, 11), (12, 20)),
    "Carazinho": ((10, 21), (12, 31)),
    "Palmeira das Missões": ((10, 11), (12, 20)),
    "_default_no_rs": ((10, 11), (12, 20)),
}
# Janela "ótima" (núcleo de maior potencial) costuma estar no terço inicial.
# Penalidade de produtividade por dia fora da janela ótima (sc/ha por dia).
SOWING_PENALTY_SC_PER_DAY: float = 0.18

# --- Nutrição: faixas de suficiência (interpretação de análise de solo) ------
PH_OPTIMAL: tuple[float, float] = (5.8, 6.5)
P_SUFFICIENT_PPM: float = 12.0   # P (mehlich) suficiente p/ solos argilosos
K_SUFFICIENT_PPM: float = 120.0
V_SUFFICIENT_PCT: float = 60.0

# --- População ---------------------------------------------------------------
POPULATION_OPTIMAL_K: tuple[float, float] = (260.0, 340.0)  # mil plantas/ha

# --- Fitossanidade: pressões e eficiência de controle (NO do RS) -------------
# Perda potencial se NÃO houver controle algum; cada aplicação de boa qualidade
# remove uma fração da perda remanescente. Valores conservadores de literatura.
DISEASE_PRESSURE: float = 0.18   # ferrugem-asiática: pressão alta
DISEASE_CONTROL_EFF: float = 0.55
PEST_PRESSURE: float = 0.12      # percevejo / lagartas
PEST_CONTROL_EFF: float = 0.60
WEED_PRESSURE: float = 0.16      # competição de plantas daninhas
WEED_CONTROL_EFF: float = 0.70   # herbicida bem manejado controla bem
# Estresse térmico: calor acima deste limiar nos estádios reprodutivos derruba vagens.
HEAT_THRESHOLD_C: float = 34.0
HEAT_MAX_LOSS: float = 0.18      # perda máxima por calor extremo persistente

# --- Defaults regionais Noroeste do RS ---------------------------------------
DEFAULT_PRICE_PER_SC: float = 120.0
NO_RS_MUNICIPALITIES: list[str] = [
    "Santo Ângelo", "Ijuí", "Cruz Alta", "Santa Rosa", "Três de Maio",
    "Panambi", "Carazinho", "Palmeira das Missões",
]


def gdd_total_for(maturity_group: float) -> float:
    """GDD total (emergência→R8) ajustado ao grupo de maturação da cultivar."""
    delta = (maturity_group - MATURITY_GROUP_REF) * GDD_PER_MATURITY_POINT
    return GDD_EMERGENCE_TO_R8_REF * (1.0 + delta)


def zarc_window(municipality: str) -> tuple[tuple[int, int], tuple[int, int]]:
    return ZARC_SOWING_WINDOW.get(municipality, ZARC_SOWING_WINDOW["_default_no_rs"])


# --- Sincroniza os coeficientes com a Base de Conhecimento (data/knowledge) ---
# Os valores no JSON são idênticos aos literais acima (que servem de fallback): o
# objetivo é tornar a fonte auditável e atualizável sem mexer no código.
def _sync_from_kb() -> None:
    try:
        from . import kb
    except Exception:  # noqa: BLE001
        return
    g = globals()
    mapping = {
        "DISEASE_PRESSURE": "fitossanidade.disease_pressure",
        "DISEASE_CONTROL_EFF": "fitossanidade.disease_control_eff",
        "PEST_PRESSURE": "fitossanidade.pest_pressure",
        "PEST_CONTROL_EFF": "fitossanidade.pest_control_eff",
        "WEED_PRESSURE": "fitossanidade.weed_pressure",
        "WEED_CONTROL_EFF": "fitossanidade.weed_control_eff",
        "HEAT_THRESHOLD_C": "clima.heat_threshold_c",
        "HEAT_MAX_LOSS": "clima.heat_max_loss",
        "P_SUFFICIENT_PPM": "nutricao.p_suficiente_ppm",
        "K_SUFFICIENT_PPM": "nutricao.k_suficiente_ppm",
        "V_SUFFICIENT_PCT": "nutricao.v_suficiente_pct",
        "SOWING_PENALTY_SC_PER_DAY": "semeadura.penalidade_sc_por_dia_fora_otimo",
    }
    for const, path in mapping.items():
        val = kb.param(path)
        if isinstance(val, (int, float)):
            g[const] = float(val)


_sync_from_kb()
