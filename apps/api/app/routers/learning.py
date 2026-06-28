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
    SeasonRecord,
    calibrate,
    season_features,
    simulate,
)

from ..db import get_session
from ..models import Field, Season
from ..schemas import (
    CalibrationComputeIn,
    CalibrationOut,
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
