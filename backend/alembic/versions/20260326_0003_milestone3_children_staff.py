"""Add Milestone 3 children and staff fields.

Revision ID: 20260326_0003
Revises: 20260325_0002
Create Date: 2026-03-26
"""

from alembic import op
import sqlalchemy as sa


revision = "20260326_0003"
down_revision = "20260325_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("children") as batch_op:
        batch_op.add_column(sa.Column("notes", sa.Text(), nullable=True))

    with op.batch_alter_table("pedagogues") as batch_op:
        batch_op.add_column(sa.Column("role", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("salary", sa.Numeric(12, 2), nullable=True))
        batch_op.add_column(sa.Column("hired_at", sa.Date(), nullable=True))

    op.execute("UPDATE pedagogues SET role = 'teacher' WHERE role IS NULL")

    with op.batch_alter_table("pedagogues") as batch_op:
        batch_op.alter_column("role", existing_type=sa.String(length=50), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("pedagogues") as batch_op:
        batch_op.drop_column("hired_at")
        batch_op.drop_column("salary")
        batch_op.drop_column("role")

    with op.batch_alter_table("children") as batch_op:
        batch_op.drop_column("notes")
