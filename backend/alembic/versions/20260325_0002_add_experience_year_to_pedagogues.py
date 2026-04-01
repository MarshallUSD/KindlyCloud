"""Add experience_year to pedagogues.

Revision ID: 20260325_0002
Revises: 20260319_0001
Create Date: 2026-03-25
"""

from alembic import op
import sqlalchemy as sa


revision = "20260325_0002"
down_revision = "20260319_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("pedagogues") as batch_op:
        batch_op.add_column(sa.Column("experience_year", sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("pedagogues") as batch_op:
        batch_op.drop_column("experience_year")
