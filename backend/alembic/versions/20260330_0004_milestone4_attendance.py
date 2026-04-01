"""Upgrade attendance for milestone 4.

Revision ID: 20260330_0004
Revises: 20260326_0003
Create Date: 2026-03-30
"""

from alembic import op
import sqlalchemy as sa


revision = "20260330_0004"
down_revision = "20260326_0003"
branch_labels = None
depends_on = None


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

    if not _has_table(inspector, "attendance"):
        op.create_table(
            "attendance",
            sa.Column("attendance_id", sa.String(), nullable=False),
            sa.Column("kindergarten_id", sa.String(), nullable=False),
            sa.Column("child_id", sa.String(), nullable=False),
            sa.Column("group_id", sa.String(), nullable=False),
            sa.Column("attend_date", sa.Date(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("marked_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("enrol_id", sa.String(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(["child_id"], ["children.child_id"]),
            sa.ForeignKeyConstraint(["enrol_id"], ["enrollments.enrol_id"]),
            sa.ForeignKeyConstraint(["group_id"], ["groups.group_id"]),
            sa.ForeignKeyConstraint(["kindergarten_id"], ["kindergartens.kindergarten_id"]),
            sa.PrimaryKeyConstraint("attendance_id"),
            sa.UniqueConstraint("child_id", "attend_date", name="uq_attendance_child_date"),
        )
        op.create_index("ix_attendance_kindergarten_id", "attendance", ["kindergarten_id"], unique=False)
        op.create_index("ix_attendance_group_id", "attendance", ["group_id"], unique=False)
        op.create_index("ix_attendance_attend_date", "attendance", ["attend_date"], unique=False)
        return

    with op.batch_alter_table("attendance") as batch_op:
        if not _has_column(inspector, "attendance", "kindergarten_id"):
            batch_op.add_column(sa.Column("kindergarten_id", sa.String(), nullable=True))
        if not _has_column(inspector, "attendance", "group_id"):
            batch_op.add_column(sa.Column("group_id", sa.String(), nullable=True))
        if not _has_column(inspector, "attendance", "marked_at"):
            batch_op.add_column(sa.Column("marked_at", sa.DateTime(), nullable=True))
        if not _has_column(inspector, "attendance", "updated_at"):
            batch_op.add_column(sa.Column("updated_at", sa.DateTime(), nullable=True))
        if not _has_column(inspector, "attendance", "notes"):
            batch_op.add_column(sa.Column("notes", sa.Text(), nullable=True))
        if not _has_column(inspector, "attendance", "enrol_id"):
            batch_op.add_column(sa.Column("enrol_id", sa.String(), nullable=True))

    if _has_column(inspector, "attendance", "kindergarten_id"):
        op.execute(
            """
            UPDATE attendance
            SET kindergarten_id = (
                SELECT children.kindergarten_id
                FROM children
                WHERE children.child_id = attendance.child_id
            )
            WHERE kindergarten_id IS NULL
            """
        )
    if _has_column(inspector, "attendance", "group_id"):
        op.execute(
            """
            UPDATE attendance
            SET group_id = COALESCE(
                (
                    SELECT children.group_id
                    FROM children
                    WHERE children.child_id = attendance.child_id
                ),
                (
                    SELECT enrollments.group_id
                    FROM enrollments
                    WHERE enrollments.enrol_id = attendance.enrol_id
                )
            )
            WHERE group_id IS NULL
            """
        )
    if _has_column(inspector, "attendance", "marked_at"):
        op.execute("UPDATE attendance SET marked_at = COALESCE(marked_at, created_at)")
    if _has_column(inspector, "attendance", "updated_at"):
        op.execute("UPDATE attendance SET updated_at = COALESCE(updated_at, created_at)")

    with op.batch_alter_table("attendance") as batch_op:
        if _has_column(inspector, "attendance", "kindergarten_id"):
            batch_op.alter_column("kindergarten_id", existing_type=sa.String(), nullable=False)
        if _has_column(inspector, "attendance", "group_id"):
            batch_op.alter_column("group_id", existing_type=sa.String(), nullable=False)
        if _has_column(inspector, "attendance", "marked_at"):
            batch_op.alter_column("marked_at", existing_type=sa.DateTime(), nullable=False)
        if _has_column(inspector, "attendance", "updated_at"):
            batch_op.alter_column("updated_at", existing_type=sa.DateTime(), nullable=False)

        existing_columns = {column["name"] for column in inspector.get_columns("attendance")}
        if "status" in existing_columns:
            batch_op.alter_column("status", existing_type=sa.String(length=50), type_=sa.String(length=20), nullable=False)

        if not _has_unique(inspector, "attendance", "uq_attendance_child_date"):
            batch_op.create_unique_constraint("uq_attendance_child_date", ["child_id", "attend_date"])

    inspector = sa.inspect(bind)
    if not _has_index(inspector, "attendance", "ix_attendance_kindergarten_id"):
        op.create_index("ix_attendance_kindergarten_id", "attendance", ["kindergarten_id"], unique=False)
    if not _has_index(inspector, "attendance", "ix_attendance_group_id"):
        op.create_index("ix_attendance_group_id", "attendance", ["group_id"], unique=False)
    if not _has_index(inspector, "attendance", "ix_attendance_attend_date"):
        op.create_index("ix_attendance_attend_date", "attendance", ["attend_date"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not _has_table(inspector, "attendance"):
        return

    if _has_index(inspector, "attendance", "ix_attendance_attend_date"):
        op.drop_index("ix_attendance_attend_date", table_name="attendance")
    if _has_index(inspector, "attendance", "ix_attendance_group_id"):
        op.drop_index("ix_attendance_group_id", table_name="attendance")
    if _has_index(inspector, "attendance", "ix_attendance_kindergarten_id"):
        op.drop_index("ix_attendance_kindergarten_id", table_name="attendance")

    with op.batch_alter_table("attendance") as batch_op:
        if _has_unique(inspector, "attendance", "uq_attendance_child_date"):
            batch_op.drop_constraint("uq_attendance_child_date", type_="unique")
