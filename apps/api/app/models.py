"""Modelo de dados do Gêmeo Digital (SQLAlchemy + PostGIS).

Núcleo desenhado para acumular a história de cada talhão ao longo das safras —
o ativo que cresce com o tempo e habilita a IA personalizada nas fases futuras.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from geoalchemy2 import Geometry
from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class Farm(Base):
    __tablename__ = "farms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(160))
    municipality: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    fields: Mapped[list["Field"]] = relationship(back_populates="farm", cascade="all, delete-orphan")


class Field(Base):
    """Talhão — unidade central do gêmeo digital."""

    __tablename__ = "fields"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    farm_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("farms.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(120))
    municipality: Mapped[str] = mapped_column(String(120))
    area_ha: Mapped[float | None] = mapped_column(Float, nullable=True)
    centroid_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    centroid_lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    geom: Mapped[object | None] = mapped_column(
        Geometry(geometry_type="POLYGON", srid=4326), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    farm: Mapped[Farm] = relationship(back_populates="fields")
    soil_tests: Mapped[list["SoilTest"]] = relationship(back_populates="field", cascade="all, delete-orphan")
    seasons: Mapped[list["Season"]] = relationship(back_populates="field", cascade="all, delete-orphan")


class SoilTest(Base):
    __tablename__ = "soil_tests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    field_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("fields.id", ondelete="CASCADE"))
    sampled_at: Mapped[date] = mapped_column(Date)
    clay_pct: Mapped[float | None] = mapped_column(Float)
    organic_matter_pct: Mapped[float | None] = mapped_column(Float)
    ph: Mapped[float | None] = mapped_column(Float)
    cec: Mapped[float | None] = mapped_column(Float)
    base_saturation_pct: Mapped[float | None] = mapped_column(Float)
    phosphorus_ppm: Mapped[float | None] = mapped_column(Float)
    potassium_ppm: Mapped[float | None] = mapped_column(Float)

    field: Mapped[Field] = relationship(back_populates="soil_tests")


class Cultivar(Base):
    __tablename__ = "cultivars"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(120))
    maturity_group: Mapped[float] = mapped_column(Float)
    base_potential_sc_ha: Mapped[float] = mapped_column(Float, default=95.0)
    cycle_days: Mapped[int] = mapped_column(Integer, default=130)
    disease_tolerance: Mapped[float] = mapped_column(Float, default=0.5)


class Season(Base):
    """Safra de um talhão (talhão × cultivar × ano-safra)."""

    __tablename__ = "seasons"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    field_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("fields.id", ondelete="CASCADE"))
    crop_year: Mapped[str] = mapped_column(String(12))  # ex.: "2025/26"
    cultivar_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    sowing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    population_k_per_ha: Mapped[float | None] = mapped_column(Float, nullable=True)
    row_spacing_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    soybean_price_per_sc: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Loop de aprendizado (Knowledge Engine): previsto vs. realizado + atributos da safra.
    predicted_yield_sc_ha: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_yield_sc_ha: Mapped[float | None] = mapped_column(Float, nullable=True)
    scenario_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    features: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    field: Mapped[Field] = relationship(back_populates="seasons")
    operations: Mapped[list["Operation"]] = relationship(back_populates="season", cascade="all, delete-orphan")
    cost_items: Mapped[list["CostItem"]] = relationship(back_populates="season", cascade="all, delete-orphan")


class Operation(Base):
    __tablename__ = "operations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    season_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("seasons.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(60))
    op_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    product: Mapped[str | None] = mapped_column(String(160), nullable=True)
    dose: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost_per_ha: Mapped[float] = mapped_column(Float, default=0.0)
    quality: Mapped[float] = mapped_column(Float, default=1.0)

    season: Mapped[Season] = relationship(back_populates="operations")


class CostItem(Base):
    __tablename__ = "cost_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    season_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("seasons.id", ondelete="CASCADE"))
    category: Mapped[str] = mapped_column(String(60))
    description: Mapped[str] = mapped_column(String(200))
    cost_per_ha: Mapped[float] = mapped_column(Float)

    season: Mapped[Season] = relationship(back_populates="cost_items")


class WeatherCache(Base):
    """Cache de séries climáticas por célula de grade (evita reconsultar APIs)."""

    __tablename__ = "weather_cache"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    grid_key: Mapped[str] = mapped_column(String(40), index=True)  # ex.: "-28.30_-54.26"
    source: Mapped[str] = mapped_column(String(40))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    series: Mapped[dict] = mapped_column(JSONB)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Simulation(Base):
    """Histórico de cenários simulados (entrada + saída) para comparação."""

    __tablename__ = "simulations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    field_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("fields.id", ondelete="SET NULL"), nullable=True)
    label: Mapped[str | None] = mapped_column(String(160), nullable=True)
    scenario_in: Mapped[dict] = mapped_column(JSONB)
    result_out: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
