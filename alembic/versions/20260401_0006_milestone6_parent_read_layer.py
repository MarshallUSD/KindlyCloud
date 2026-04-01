"""Add parent read layer schema support for milestone 6.

Revision ID: 20260401_0006
Revises: 20260331_0005
Create Date: 2026-04-01
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260401_0006"
down_revision = "20260331_0005"
branch_labels = None
depends_on = None


menu_status_enum = sa.Enum("draft", "published", name="menu_status", native_enum=False)


def _has_table(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _has_index(inspector, table_name: str, index_name: str) -> bool:
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def _has_unique(inspector, table_name: str, constraint_name: str) -> bool:
    return any(item["name"] == constraint_name for item in inspector.get_unique_constraints(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_table(inspector, "parents"):
        with op.batch_alter_table("parents") as batch_op:
            if not _has_column(inspector, "parents", "telegram_id"):
                batch_op.add_column(sa.Column("telegram_id", sa.String(length=64), nullable=True))
        inspector = sa.inspect(bind)
        if not _has_index(inspector, "parents", "ix_parents_telegram_id"):
            op.create_index("ix_parents_telegram_id", "parents", ["telegram_id"], unique=True)

    if _has_table(inspector, "menus"):
        with op.batch_alter_table("menus") as batch_op:
            if not _has_column(inspector, "menus", "status"):
                batch_op.add_column(
                    sa.Column(
                        "status",
                        menu_status_enum,
                        nullable=False,
                        server_default="published",
                    )
                )
            if not _has_column(inspector, "menus", "published_at"):
                batch_op.add_column(sa.Column("published_at", sa.DateTime(), nullable=True))
            if not _has_column(inspector, "menus", "notes"):
                batch_op.add_column(sa.Column("notes", sa.Text(), nullable=True))
            if not _has_column(inspector, "menus", "updated_at"):
                batch_op.add_column(
                    sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"))
                )

        op.execute(
            sa.text(
                """
                UPDATE menus
                SET
                    status = COALESCE(status, 'published'),
                    published_at = COALESCE(published_at, created_at),
                    updated_at = COALESCE(updated_at, created_at)
                """
            )
        )

    inspector = sa.inspect(bind)
    if _has_table(inspector, "group_menus") and not _has_unique(inspector, "group_menus", "uq_group_menus_group_menu"):
        with op.batch_alter_table("group_menus") as batch_op:
            batch_op.create_unique_constraint("uq_group_menus_group_menu", ["group_id", "menu_id"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_table(inspector, "group_menus") and _has_unique(inspector, "group_menus", "uq_group_menus_group_menu"):
        with op.batch_alter_table("group_menus") as batch_op:
            batch_op.drop_constraint("uq_group_menus_group_menu", type_="unique")

    if _has_table(inspector, "menus"):
        with op.batch_alter_table("menus") as batch_op:
            if _has_column(inspector, "menus", "updated_at"):
                batch_op.drop_column("updated_at")
            if _has_column(inspector, "menus", "notes"):
                batch_op.drop_column("notes")
            if _has_column(inspector, "menus", "published_at"):
                batch_op.drop_column("published_at")
            if _has_column(inspector, "menus", "status"):
                batch_op.drop_column("status")

    inspector = sa.inspect(bind)
    if _has_table(inspector, "parents"):
        if _has_index(inspector, "parents", "ix_parents_telegram_id"):
            op.drop_index("ix_parents_telegram_id", table_name="parents")
        with op.batch_alter_table("parents") as batch_op:
            if _has_column(inspector, "parents", "telegram_id"):
                batch_op.drop_column("telegram_id")
