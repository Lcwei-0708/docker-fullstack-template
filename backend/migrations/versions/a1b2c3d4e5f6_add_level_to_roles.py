"""Add level to roles

Revision ID: a1b2c3d4e5f6
Revises: 2023d62e40eb
Create Date: 2026-08-26 20:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "2023d62e40eb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "roles",
        sa.Column("level", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index(op.f("ix_roles_level"), "roles", ["level"], unique=False)
    op.execute("UPDATE roles SET level = 100 WHERE name = 'super-admin'")
    op.execute("UPDATE roles SET level = 1 WHERE name = 'user'")


def downgrade() -> None:
    op.drop_index(op.f("ix_roles_level"), table_name="roles")
    op.drop_column("roles", "level")
