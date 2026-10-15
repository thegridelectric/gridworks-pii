"""baseline: the pii schema

Revision ID: 0001
Revises:
Create Date: 2026-10-15 20:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMA = "pii"


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
    op.create_table(
        "installers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("contact_name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=False),
        sa.Column(
            "created",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        schema=SCHEMA,
    )
    op.create_table(
        "customers",
        sa.Column("ta_g_node_id", sa.String(36), primary_key=True),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=False),
        sa.Column("street", sa.String(), nullable=False),
        sa.Column("city", sa.String(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("zip", sa.String(), nullable=False),
        sa.Column("country", sa.String(), nullable=False),
        sa.Column("second_contact_name", sa.String(), nullable=True),
        sa.Column("second_contact_email", sa.String(), nullable=True),
        sa.Column("second_contact_phone", sa.String(), nullable=True),
        sa.Column(
            "installer_id",
            sa.String(36),
            sa.ForeignKey(f"{SCHEMA}.installers.id"),
            nullable=True,
        ),
        sa.Column(
            "created",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        schema=SCHEMA,
    )
    op.create_table(
        "partner_labels",
        sa.Column("ta_g_node_id", sa.String(36), primary_key=True),
        sa.Column("partner", sa.String(), primary_key=True),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("issued", sa.Date(), nullable=False),
        sa.UniqueConstraint("partner", "label"),
        schema=SCHEMA,
    )
    op.create_table(
        "partner_label_schemes",
        sa.Column("partner", sa.String(), primary_key=True),
        sa.Column("prefix", sa.String(), nullable=False),
        sa.Column("digits", sa.Integer(), nullable=False),
        sa.Column("unissued", JSONB, nullable=False),
        schema=SCHEMA,
    )
    op.create_table(
        "changes",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("who", sa.String(), nullable=False),
        sa.Column("table_name", sa.String(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("before", JSONB, nullable=True),
        sa.Column("after", JSONB, nullable=True),
        schema=SCHEMA,
    )


def downgrade() -> None:
    for table in (
        "changes",
        "partner_label_schemes",
        "partner_labels",
        "customers",
        "installers",
    ):
        op.drop_table(table, schema=SCHEMA)
    op.execute(f"DROP SCHEMA {SCHEMA}")
