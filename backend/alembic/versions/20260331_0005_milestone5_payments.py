"""Upgrade payments for milestone 5 MVP billing.

Revision ID: 20260331_0005
Revises: 20260330_0004
Create Date: 2026-03-31
"""

from __future__ import annotations

from datetime import date, datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


revision = "20260331_0005"
down_revision = "20260330_0004"
branch_labels = None
depends_on = None


payment_status_enum = sa.Enum("pending", "paid", "overdue", name="payment_status", native_enum=False)
payment_method_enum = sa.Enum("cash", "click", "payme", "bank_transfer", name="payment_method", native_enum=False)


def _has_table(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_index(inspector, table_name: str, index_name: str) -> bool:
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def _has_unique(inspector, table_name: str, constraint_name: str) -> bool:
    return any(item["name"] == constraint_name for item in inspector.get_unique_constraints(table_name))


def _create_payments_table() -> None:
    op.create_table(
        "payments",
        sa.Column("payment_id", sa.String(), nullable=False),
        sa.Column("kindergarten_id", sa.String(), nullable=False),
        sa.Column("child_id", sa.String(), nullable=False),
        sa.Column("parent_id", sa.String(), nullable=True),
        sa.Column("billing_period", sa.String(length=7), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("status", payment_status_enum, nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("payment_method", payment_method_enum, nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("amount > 0", name="ck_payments_amount_positive"),
        sa.ForeignKeyConstraint(["child_id"], ["children.child_id"]),
        sa.ForeignKeyConstraint(["kindergarten_id"], ["kindergartens.kindergarten_id"]),
        sa.ForeignKeyConstraint(["parent_id"], ["parents.parent_id"]),
        sa.PrimaryKeyConstraint("payment_id"),
        sa.UniqueConstraint(
            "kindergarten_id",
            "child_id",
            "billing_period",
            name="uq_payments_kindergarten_child_billing_period",
        ),
    )
    op.create_index("ix_payments_kindergarten_id", "payments", ["kindergarten_id"], unique=False)
    op.create_index("ix_payments_child_id", "payments", ["child_id"], unique=False)
    op.create_index("ix_payments_due_date", "payments", ["due_date"], unique=False)
    op.create_index("ix_payments_status", "payments", ["status"], unique=False)
    op.create_index("ix_payments_billing_period", "payments", ["billing_period"], unique=False)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "payments"):
        _create_payments_table()
        return

    existing_columns = {column["name"] for column in inspector.get_columns("payments")}
    if {"kindergarten_id", "billing_period", "due_date", "payment_method", "updated_at"}.issubset(existing_columns):
        return

    op.rename_table("payments", "payments_legacy")
    _create_payments_table()

    legacy_table = sa.table(
        "payments_legacy",
        sa.column("payment_id", sa.String()),
        sa.column("parent_id", sa.String()),
        sa.column("child_id", sa.String()),
        sa.column("payment_date", sa.Date()),
        sa.column("amount", sa.Numeric(10, 2)),
        sa.column("provider", sa.String()),
        sa.column("status", sa.String()),
        sa.column("recipient_info", sa.Text()),
        sa.column("created_at", sa.DateTime()),
    )
    children_table = sa.table(
        "children",
        sa.column("child_id", sa.String()),
        sa.column("kindergarten_id", sa.String()),
    )

    child_rows = {
        row.child_id: row.kindergarten_id
        for row in bind.execute(sa.select(children_table.c.child_id, children_table.c.kindergarten_id))
    }
    legacy_rows = bind.execute(sa.select(legacy_table)).fetchall()

    for row in legacy_rows:
        due_date = row.payment_date or date.today()
        billing_period = due_date.strftime("%Y-%m")
        raw_status = (row.status or "pending").lower()
        if raw_status == "completed":
            status_value = "paid"
            paid_at = row.created_at or datetime.utcnow()
        elif due_date < date.today():
            status_value = "overdue"
            paid_at = None
        else:
            status_value = "pending"
            paid_at = None

        bind.execute(
            sa.text(
                """
                INSERT INTO payments (
                    payment_id, kindergarten_id, child_id, parent_id, billing_period, amount,
                    due_date, status, notes, paid_at, payment_method, created_at, updated_at
                ) VALUES (
                    :payment_id, :kindergarten_id, :child_id, :parent_id, :billing_period, :amount,
                    :due_date, :status, :notes, :paid_at, :payment_method, :created_at, :updated_at
                )
                """
            ),
            {
                "payment_id": row.payment_id,
                "kindergarten_id": child_rows.get(row.child_id),
                "child_id": row.child_id,
                "parent_id": row.parent_id,
                "billing_period": billing_period,
                "amount": row.amount,
                "due_date": due_date,
                "status": status_value,
                "notes": row.recipient_info,
                "paid_at": paid_at,
                "payment_method": row.provider if row.provider in {"cash", "bank_transfer"} else None,
                "created_at": row.created_at or datetime.utcnow(),
                "updated_at": row.created_at or datetime.utcnow(),
            },
        )

    op.drop_table("payments_legacy")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not _has_table(inspector, "payments"):
        return

    for index_name in [
        "ix_payments_billing_period",
        "ix_payments_status",
        "ix_payments_due_date",
        "ix_payments_child_id",
        "ix_payments_kindergarten_id",
    ]:
        if _has_index(inspector, "payments", index_name):
            op.drop_index(index_name, table_name="payments")

    with op.batch_alter_table("payments") as batch_op:
        if _has_unique(inspector, "payments", "uq_payments_kindergarten_child_billing_period"):
            batch_op.drop_constraint("uq_payments_kindergarten_child_billing_period", type_="unique")

    op.drop_table("payments")
