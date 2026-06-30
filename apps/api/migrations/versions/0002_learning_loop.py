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
    # 0001 cria o schema via Base.metadata.create_all (sempre o modelo atual), então num
    # banco novo estas colunas já existem. Idempotente: adiciona só o que faltar.
    bind = op.get_bind()
    existing = {c["name"] for c in sa.inspect(bind).get_columns("seasons")}
    cols = {
        "predicted_yield_sc_ha": sa.Column("predicted_yield_sc_ha", sa.Float(), nullable=True),
        "actual_yield_sc_ha": sa.Column("actual_yield_sc_ha", sa.Float(), nullable=True),
        "scenario_snapshot": sa.Column("scenario_snapshot", JSONB(), nullable=True),
        "features": sa.Column("features", JSONB(), nullable=True),
    }
    for name, col in cols.items():
        if name not in existing:
            op.add_column("seasons", col)


def downgrade() -> None:
    bind = op.get_bind()
    existing = {c["name"] for c in sa.inspect(bind).get_columns("seasons")}
    for name in ("features", "scenario_snapshot", "actual_yield_sc_ha", "predicted_yield_sc_ha"):
        if name in existing:
            op.drop_column("seasons", name)
