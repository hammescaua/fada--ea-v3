"""Schema inicial do Gêmeo Digital (PostGIS + tabelas do núcleo).

Cria a extensão PostGIS e todas as tabelas a partir da metadata do SQLAlchemy,
garantindo que o schema acompanhe exatamente os modelos em app/models.py.

Revision ID: 0001
Revises:
Create Date: 2026-06-28
"""

from __future__ import annotations

from alembic import op

from app.db import Base
from app import models  # noqa: F401 — registra as tabelas

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
