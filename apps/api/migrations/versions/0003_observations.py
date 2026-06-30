"""Camada de evidências: tabela observations (gêmeo orientado a eventos).

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-29
"""

from __future__ import annotations

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Idempotente: 0001 (create_all) já cria a tabela num banco novo. Só cria se faltar.
    if "observations" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        "observations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("field_id", UUID(as_uuid=True), sa.ForeignKey("fields.id", ondelete="CASCADE"), nullable=False),
        sa.Column("season_id", UUID(as_uuid=True), sa.ForeignKey("seasons.id", ondelete="SET NULL"), nullable=True),
        sa.Column("observed_at", sa.Date(), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("value", JSONB(), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("geom", geoalchemy2.types.Geometry(geometry_type="POINT", srid=4326), nullable=True),
        sa.Column("consequence", sa.String(length=240), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_observations_field_id", "observations", ["field_id"])
    op.create_index("ix_observations_observed_at", "observations", ["observed_at"])
    op.create_index("ix_observations_kind", "observations", ["kind"])


def downgrade() -> None:
    op.drop_index("ix_observations_kind", table_name="observations")
    op.drop_index("ix_observations_observed_at", table_name="observations")
    op.drop_index("ix_observations_field_id", table_name="observations")
    op.drop_table("observations")
