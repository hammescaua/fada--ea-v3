"""Ingestão de dados da lavoura (miniestação WiFi / pluviômetro / sonda de umidade).

A fonte mais verídica é a medição no próprio talhão. Aqui a estação do agricultor envia
leituras (chuva, umidade do solo, temperatura) que passam a alimentar o balanço hídrico —
sobrepondo a reanálise. Autenticação simples por token do talhão (cada talhão tem o seu).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from agro_engine.observations import daily_mean, daily_sum

from ..db import get_session
from ..models import Field as FieldModel
from ..models import SensorReading

router = APIRouter(tags=["sensores"])


class ReadingIn(BaseModel):
    measured_at: datetime
    variable: str = Field(description="rain_mm | soil_moisture | temp_c | rh_pct")
    value: float
    unit: str | None = None
    depth_cm: float | None = None
    station_id: str | None = None


class ReadingsBatch(BaseModel):
    readings: list[ReadingIn]


@router.get("/fields/{field_id}/station")
def get_station(field_id: str, db: Session = Depends(get_session)) -> dict:
    """Configuração da estação do talhão: para onde enviar e com qual token."""
    field = db.get(FieldModel, field_id)
    if not field:
        raise HTTPException(404, "talhão não encontrado")
    return {
        "field_id": str(field.id),
        "ingest_token": str(field.ingest_token),
        "endpoint": f"/api/fields/{field.id}/readings",
        "header": "X-Ingest-Token",
        "variaveis": ["rain_mm", "soil_moisture", "temp_c", "rh_pct"],
        "exemplo": {
            "readings": [
                {"measured_at": "2025-12-01T12:00:00Z", "variable": "rain_mm", "value": 12.4, "station_id": "esp32-01"},
                {"measured_at": "2025-12-01T12:00:00Z", "variable": "soil_moisture", "value": 0.62, "unit": "frac", "depth_cm": 20},
            ]
        },
    }


@router.post("/fields/{field_id}/readings")
def ingest_readings(
    field_id: str,
    batch: ReadingsBatch,
    db: Session = Depends(get_session),
    x_ingest_token: str = Header(default=""),
) -> dict:
    """Recebe leituras da estação (autenticado pelo token do talhão)."""
    field = db.get(FieldModel, field_id)
    if not field:
        raise HTTPException(404, "talhão não encontrado")
    if x_ingest_token != str(field.ingest_token):
        raise HTTPException(401, "token de ingestão inválido")

    rows = [
        SensorReading(
            field_id=field.id, measured_at=r.measured_at, variable=r.variable,
            value=r.value, unit=r.unit, depth_cm=r.depth_cm, station_id=r.station_id,
        )
        for r in batch.readings
    ]
    db.add_all(rows)
    db.commit()
    return {"ingeridas": len(rows)}


@router.get("/fields/{field_id}/observations")
def get_observations(field_id: str, db: Session = Depends(get_session)) -> dict:
    """Resumo das observações da lavoura: chuva diária e umidade do solo medidas."""
    obs = _field_observations(field_id, db)
    return {
        "tem_dados": bool(obs["rain"] or obs["soil_moisture"]),
        "dias_com_chuva_medida": len(obs["rain"]),
        "dias_com_umidade_medida": len(obs["soil_moisture"]),
        "chuva_total_medida_mm": round(sum(obs["rain"].values()), 1),
    }


def _field_observations(field_id: str, db: Session) -> dict:
    """Constrói os dicionários de chuva (soma diária) e umidade do solo (média diária)."""
    rows = db.scalars(
        select(SensorReading).where(SensorReading.field_id == field_id)
    ).all()
    rain_rows = [(r.measured_at.date(), r.value) for r in rows if r.variable == "rain_mm"]
    sm_rows = [
        (r.measured_at.date(), r.value / 100.0 if (r.unit or "").lower() in ("%", "pct") else r.value)
        for r in rows
        if r.variable == "soil_moisture"
    ]
    return {"rain": daily_sum(rain_rows), "soil_moisture": daily_mean(sm_rows)}
