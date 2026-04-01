"""Add parent submissions inbox model.

Revision ID: 20260401_0007
Revises: 20260401_0006
Create Date: 2026-04-01
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260401_0007"
down_revision = "20260401_0006"
branch_labels = None
depends_on = None


submission_source_enum = sa.Enum("telegram_bot", name="parent_submission_source", native_enum=False)
submission_type_enum = sa.Enum("payment_proof", "message", "other", name="parent_submission_type", native_enum=False)
attachment_type_enum = sa.Enum("image", "screenshot", "document", name="parent_submission_attachment_type", native_enum=False)
submission_status_enum = sa.Enum("pending", "reviewed", "approved", "rejected", name="parent_submission_status", native_enum=False)


def _has_table(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_index(inspector, table_name: str, index_name: str) -> bool:
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_table(inspector, "parent_submissions"):
        return

    op.create_table(
        "parent_submissions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("kindergarten_id", sa.String(), nullable=False),
        sa.Column("parent_id", sa.String(), nullable=False),
        sa.Column("child_id", sa.String(), nullable=True),
        sa.Column("payment_id", sa.String(), nullable=True),
        sa.Column("source", submission_source_enum, nullable=False),
        sa.Column("submission_type", submission_type_enum, nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("attachment_url", sa.Text(), nullable=True),
        sa.Column("attachment_type", attachment_type_enum, nullable=True),
        sa.Column("status", submission_status_enum, nullable=False),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["child_id"], ["children.child_id"]),
        sa.ForeignKeyConstraint(["kindergarten_id"], ["kindergartens.kindergarten_id"]),
        sa.ForeignKeyConstraint(["parent_id"], ["parents.parent_id"]),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.payment_id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_parent_submissions_kindergarten_id", "parent_submissions", ["kindergarten_id"], unique=False)
    op.create_index("ix_parent_submissions_parent_id", "parent_submissions", ["parent_id"], unique=False)
    op.create_index("ix_parent_submissions_child_id", "parent_submissions", ["child_id"], unique=False)
    op.create_index("ix_parent_submissions_payment_id", "parent_submissions", ["payment_id"], unique=False)
    op.create_index("ix_parent_submissions_status", "parent_submissions", ["status"], unique=False)
    op.create_index("ix_parent_submissions_submission_type", "parent_submissions", ["submission_type"], unique=False)
    op.create_index("ix_parent_submissions_created_at", "parent_submissions", ["created_at"], unique=False)
    op.create_index(
        "ix_parent_submissions_kindergarten_status_created",
        "parent_submissions",
        ["kindergarten_id", "status", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "parent_submissions"):
        return

    for index_name in [
        "ix_parent_submissions_kindergarten_status_created",
        "ix_parent_submissions_created_at",
        "ix_parent_submissions_submission_type",
        "ix_parent_submissions_status",
        "ix_parent_submissions_payment_id",
        "ix_parent_submissions_child_id",
        "ix_parent_submissions_parent_id",
        "ix_parent_submissions_kindergarten_id",
    ]:
        if _has_index(inspector, "parent_submissions", index_name):
            op.drop_index(index_name, table_name="parent_submissions")

    op.drop_table("parent_submissions")
