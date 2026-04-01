"""Create admins table and rewire admin-owned references.

Revision ID: 20260319_0001
Revises:
Create Date: 2026-03-19
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260319_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admins",
        sa.Column("admin_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False, server_default="super_admin"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("phone", name="uq_admins_phone"),
        sa.UniqueConstraint("email", name="uq_admins_email"),
    )
    op.create_index("ix_admins_admin_id", "admins", ["admin_id"])
    op.create_index("ix_admins_email", "admins", ["email"])

    with op.batch_alter_table("posts") as batch_op:
        batch_op.add_column(sa.Column("created_by_admin_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_posts_created_by_admin_id_admins",
            "admins",
            ["created_by_admin_id"],
            ["admin_id"],
        )

    with op.batch_alter_table("feedback") as batch_op:
        batch_op.add_column(sa.Column("handled_by_admin_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_feedback_handled_by_admin_id_admins",
            "admins",
            ["handled_by_admin_id"],
            ["admin_id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("feedback") as batch_op:
        batch_op.drop_constraint("fk_feedback_handled_by_admin_id_admins", type_="foreignkey")
        batch_op.drop_column("handled_by_admin_id")

    with op.batch_alter_table("posts") as batch_op:
        batch_op.drop_constraint("fk_posts_created_by_admin_id_admins", type_="foreignkey")
        batch_op.drop_column("created_by_admin_id")

    op.drop_index("ix_admins_email", table_name="admins")
    op.drop_index("ix_admins_admin_id", table_name="admins")
    op.drop_table("admins")
