"""Knowledge Engine — endpoints do loop de aprendizado por talhão.

- `/calibration/compute` é **stateless** (a UI envia o histórico previsto-vs-real e
  recebe a correção) — útil antes mesmo de existir banco/cockpit.
- Os demais persistem safras no talhão (PostGIS) e calculam a calibração a partir do
  histórico real, alimentando o Nível 2 (ML) no futuro.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from agro_engine import (
    FieldSeason,
    Observation as EvidenceObs,
    SeasonRecord,
    calibrate,
    confidence_for,
    data_quality,
    personality,
    season_features,
    simulate,
)

from ..db import get_session
from ..models import Field, Observation, Season
from ..schemas import (
    CalibrationComputeIn,
    CalibrationOut,
    ObservationIn,
    ObservationOut,
    SeasonRecordIn,
)
from .simulation import _to_scenario

router = APIRouter(tags=["aprendizado"])


def _calibration_out(records: list[SeasonRecord]) -> CalibrationOut:
    cal = calibrate(records)
    return CalibrationOut(**cal.__dict__)


@router.post("/calibration/compute", response_model=CalibrationOut)
def compute_calibration(payload: CalibrationComputeIn) -> CalibrationOut:
    """Stateless: calcula a correção aprendida a partir do histórico previsto-vs-real."""
    records = [
        SeasonRecord(r.crop_year, r.predicted_sc_ha, r.actual_sc_ha) for r in payload.records
    ]
    return _calibration_out(records)


@router.post("/fields/{field_id}/seasons")
def record_season(field_id: str, payload: SeasonRecordIn, db: Session = Depends(get_session)) -> dict:
    """Registra uma safra do talhão: roda o motor (previsto + atributos) e persiste."""
    field = db.get(Field, field_id)
    if not field:
        raise HTTPException(404, "talhão não encontrado")

    scenario = _to_scenario(payload.scenario)
    # O previsto registrado deve ser a saída do modelo BRUTO (sem a calibração do
    # talhão), senão o loop de aprendizado se realimentaria: a correção é aprendida do
    # resíduo (colhido − previsto-bruto).
    scenario.calibration_bias_sc_ha = 0.0
    scenario.calibration_confidence = 0.0
    scenario.calibration_seasons = 0
    sim = simulate(scenario)
    feats = season_features(scenario, sim)

    season = Season(
        field_id=field.id,
        crop_year=payload.crop_year,
        cultivar_name=scenario.cultivar.name,
        sowing_date=scenario.sowing_date,
        population_k_per_ha=scenario.population_k_per_ha,
        soybean_price_per_sc=scenario.soybean_price_per_sc,
        predicted_yield_sc_ha=sim.yield_result.expected_sc_ha,
        actual_yield_sc_ha=payload.actual_yield_sc_ha,
        scenario_snapshot=payload.scenario.model_dump(mode="json"),
        features=feats,
    )
    db.add(season)
    db.commit()
    return {
        "id": str(season.id),
        "crop_year": season.crop_year,
        "predicted_yield_sc_ha": season.predicted_yield_sc_ha,
        "actual_yield_sc_ha": season.actual_yield_sc_ha,
    }


@router.post("/seasons/{season_id}/harvest")
def record_harvest(season_id: str, actual_yield_sc_ha: float, db: Session = Depends(get_session)) -> dict:
    """Fecha o loop: registra a produtividade realmente colhida."""
    season = db.get(Season, season_id)
    if not season:
        raise HTTPException(404, "safra não encontrada")
    season.actual_yield_sc_ha = actual_yield_sc_ha
    db.commit()
    return {"id": str(season.id), "actual_yield_sc_ha": actual_yield_sc_ha}


def _obs_out(o: Observation) -> ObservationOut:
    return ObservationOut(
        id=str(o.id), field_id=str(o.field_id), observed_at=o.observed_at, kind=o.kind,
        source=o.source, value=o.value, unit=o.unit, confidence=o.confidence,
        latitude=o.latitude, longitude=o.longitude, consequence=o.consequence,
    )


@router.post("/fields/{field_id}/observations", response_model=ObservationOut)
def add_observation(field_id: str, payload: ObservationIn, db: Session = Depends(get_session)) -> ObservationOut:
    """Registra uma EVIDÊNCIA no talhão. Se a confiança não for informada, o Reality
    Engine a deriva da fonte (drone/satélite/agrônomo/API > relato manual)."""
    field = db.get(Field, field_id)
    if not field:
        raise HTTPException(404, "talhão não encontrado")
    # corroboração: nº de fontes independentes já registradas para o mesmo fato (kind+dia)
    same_fact = db.scalars(
        select(Observation).where(
            Observation.field_id == field_id,
            Observation.kind == payload.kind,
            Observation.observed_at == payload.observed_at,
        )
    ).all()
    indep_sources = {o.source for o in same_fact}
    conf = payload.confidence
    if conf is None:
        conf = confidence_for(payload.source, corroborations=len(indep_sources))
    obs = Observation(
        field_id=field_id, season_id=payload.season_id, observed_at=payload.observed_at,
        kind=payload.kind, source=payload.source, value=payload.value, unit=payload.unit,
        confidence=conf, latitude=payload.latitude, longitude=payload.longitude,
        consequence=payload.consequence,
    )
    db.add(obs)
    db.commit()
    return _obs_out(obs)


@router.get("/fields/{field_id}/observations", response_model=list[ObservationOut])
def list_observations(field_id: str, db: Session = Depends(get_session)) -> list[ObservationOut]:
    obs = db.scalars(
        select(Observation).where(Observation.field_id == field_id).order_by(Observation.observed_at.desc())
    ).all()
    return [_obs_out(o) for o in obs]


@router.get("/fields/{field_id}/personality")
def field_personality(field_id: str, db: Session = Depends(get_session)) -> dict:
    """Genética do talhão: traços APRENDIDOS (responde a P, risco de ferrugem, estável,
    sensível a atraso...) com % de conhecimento, derivados das safras e evidências."""
    if not db.get(Field, field_id):
        raise HTTPException(404, "talhão não encontrado")
    seasons = db.scalars(
        select(Season).where(
            Season.field_id == field_id,
            Season.predicted_yield_sc_ha.is_not(None),
            Season.actual_yield_sc_ha.is_not(None),
        )
    ).all()
    fseasons = [
        FieldSeason(s.crop_year, s.predicted_yield_sc_ha, s.actual_yield_sc_ha, s.features or {})
        for s in seasons
    ]
    obs_rows = db.scalars(select(Observation).where(Observation.field_id == field_id)).all()
    evid = [
        EvidenceObs(kind=o.kind, source=o.source, observed_at=o.observed_at.isoformat(),
                    value=o.value or {}, confidence=o.confidence)
        for o in obs_rows
    ]
    result = personality(fseasons, evid)
    result["data_quality"] = data_quality(evid)
    return result


@router.get("/fields/{field_id}/calibration", response_model=CalibrationOut)
def field_calibration(field_id: str, db: Session = Depends(get_session)) -> CalibrationOut:
    """Modelo de correção aprendido para o talhão (a partir das safras encerradas)."""
    seasons = db.scalars(
        select(Season).where(
            Season.field_id == field_id,
            Season.predicted_yield_sc_ha.is_not(None),
            Season.actual_yield_sc_ha.is_not(None),
        )
    ).all()
    records = [
        SeasonRecord(s.crop_year, s.predicted_yield_sc_ha, s.actual_yield_sc_ha) for s in seasons
    ]
    return _calibration_out(records)
