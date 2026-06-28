"""CRUD de fazendas e talhões (fundação do Gêmeo Digital).

Exige banco PostGIS. Geometria do talhão é recebida como GeoJSON Polygon
(desenhado no mapa) e armazenada em coluna PostGIS 4326.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from geoalchemy2.shape import from_shape
from shapely.geometry import shape
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import Farm, Field
from ..schemas import FarmIn, FarmOut, FieldIn, FieldOut

router = APIRouter(tags=["fazendas"])


@router.post("/farms", response_model=FarmOut)
def create_farm(payload: FarmIn, db: Session = Depends(get_session)) -> FarmOut:
    farm = Farm(name=payload.name, municipality=payload.municipality)
    db.add(farm)
    db.commit()
    return FarmOut(id=str(farm.id), name=farm.name, municipality=farm.municipality)


@router.get("/farms", response_model=list[FarmOut])
def list_farms(db: Session = Depends(get_session)) -> list[FarmOut]:
    farms = db.scalars(select(Farm)).all()
    return [FarmOut(id=str(f.id), name=f.name, municipality=f.municipality) for f in farms]


@router.post("/farms/{farm_id}/fields", response_model=FieldOut)
def create_field(farm_id: str, payload: FieldIn, db: Session = Depends(get_session)) -> FieldOut:
    farm = db.get(Farm, farm_id)
    if not farm:
        raise HTTPException(404, "fazenda não encontrada")

    area_ha = payload.area_ha
    lat, lon = payload.centroid_lat, payload.centroid_lon
    geom = None
    if payload.geojson:
        poly = shape(payload.geojson)
        geom = from_shape(poly, srid=4326)
        if lat is None or lon is None:
            lat, lon = poly.centroid.y, poly.centroid.x
        if area_ha is None:
            # área aproximada via graus²→ha no centroide (suficiente para v0)
            area_ha = round(poly.area * (111_000 ** 2) / 10_000, 2)

    field = Field(
        farm_id=farm.id, name=payload.name, municipality=payload.municipality,
        area_ha=area_ha, centroid_lat=lat, centroid_lon=lon, geom=geom,
    )
    db.add(field)
    db.commit()
    return FieldOut(
        id=str(field.id), farm_id=str(farm.id), name=field.name,
        municipality=field.municipality, area_ha=field.area_ha,
        centroid_lat=field.centroid_lat, centroid_lon=field.centroid_lon,
    )


@router.get("/farms/{farm_id}/fields", response_model=list[FieldOut])
def list_fields(farm_id: str, db: Session = Depends(get_session)) -> list[FieldOut]:
    fields = db.scalars(select(Field).where(Field.farm_id == farm_id)).all()
    return [
        FieldOut(
            id=str(f.id), farm_id=str(f.farm_id), name=f.name,
            municipality=f.municipality, area_ha=f.area_ha,
            centroid_lat=f.centroid_lat, centroid_lon=f.centroid_lon,
        )
        for f in fields
    ]
