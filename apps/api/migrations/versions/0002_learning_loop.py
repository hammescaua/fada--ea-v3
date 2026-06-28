"""Loop de aprendizado: colunas previsto/realizado + atributos na tabela seasons.

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-28
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("seasons", sa.Column("predicted_yield_sc_ha", sa.Float(), nullable=True))
    op.add_column("seasons", sa.Column("actual_yield_sc_ha", sa.Float(), nullable=True))
    op.add_column("seasons", sa.Column("scenario_snapshot", JSONB(), nullable=True))
    op.add_column("seasons", sa.Column("features", JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("seasons", "features")
    op.drop_column("seasons", "scenario_snapshot")
    op.drop_column("seasons", "actual_yield_sc_ha")
    op.drop_column("seasons", "predicted_yield_sc_ha")
