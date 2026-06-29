"""Sensores da lavoura: leituras + token de ingestão por talhão.

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-29
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "fields",
        sa.Column("ingest_token", UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
    )
    op.create_index("ix_fields_ingest_token", "fields", ["ingest_token"])
    op.create_table(
        "sensor_readings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("field_id", UUID(as_uuid=True), sa.ForeignKey("fields.id", ondelete="CASCADE"), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("variable", sa.String(length=40), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=True),
        sa.Column("depth_cm", sa.Float(), nullable=True),
        sa.Column("station_id", sa.String(length=60), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_sensor_readings_field_id", "sensor_readings", ["field_id"])
    op.create_index("ix_sensor_readings_measured_at", "sensor_readings", ["measured_at"])
    op.create_index("ix_sensor_readings_variable", "sensor_readings", ["variable"])


def downgrade() -> None:
    op.drop_table("sensor_readings")
    op.drop_index("ix_fields_ingest_token", table_name="fields")
    op.drop_column("fields", "ingest_token")
