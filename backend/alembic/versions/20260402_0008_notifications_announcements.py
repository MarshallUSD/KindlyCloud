"""Add structured notifications and announcements.

Revision ID: 20260402_0008
Revises: 20260401_0007
Create Date: 2026-04-02
"""

from __future__ import annotations

import uuid

from alembic import op
import sqlalchemy as sa


revision = "20260402_0008"
down_revision = "20260401_0007"
branch_labels = None
depends_on = None


notification_type_enum = sa.Enum("system", "announcement", name="notification_type", native_enum=False)
notification_event_type_enum = sa.Enum(
    "attendance_late",
    "attendance_absent",
    "payment_created",
    "payment_overdue",
    "payment_paid",
    name="notification_event_type",
    native_enum=False,
)
telegram_delivery_status_enum = sa.Enum(
    "pending",
    "sent",
    "failed",
    "skipped",
    name="telegram_delivery_status",
    native_enum=False,
)
announcement_target_type_enum = sa.Enum("all", "group", "child", name="announcement_target_type", native_enum=False)


def _has_table(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _has_index(inspector, table_name: str, index_name: str) -> bool:
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def _drop_table_if_exists(inspector, table_name: str, *, indexes: list[str] | None = None) -> None:
    if not _has_table(inspector, table_name):
        return
    indexes = indexes or []
    for index_name in indexes:
        if _has_index(inspector, table_name, index_name):
            op.drop_index(index_name, table_name=table_name)
    op.drop_table(table_name)


def _schema_is_current(inspector) -> bool:
    return (
        _has_table(inspector, "notifications")
        and _has_column(inspector, "notifications", "source_announcement_id")
        and _has_column(inspector, "notifications", "telegram_delivery_status")
        and _has_column(inspector, "notifications", "updated_at")
        and _has_table(inspector, "announcements")
        and _has_column(inspector, "announcements", "target_group_id")
        and _has_column(inspector, "announcements", "target_child_id")
        and _has_column(inspector, "announcements", "created_by_user_id")
        and _has_table(inspector, "parent_notification_settings")
        and _has_column(inspector, "parent_notification_settings", "telegram_enabled")
        and _has_column(inspector, "parent_notification_settings", "id")
        and _has_table(inspector, "notification_delivery_stats")
        and _has_column(inspector, "notification_delivery_stats", "announcement_id")
    )


def _create_schema() -> None:
    op.create_table(
        "announcements",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("kindergarten_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("target_type", announcement_target_type_enum, nullable=False),
        sa.Column("target_group_id", sa.String(), nullable=True),
        sa.Column("target_child_id", sa.String(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["kindergarten_id"], ["kindergartens.kindergarten_id"]),
        sa.ForeignKeyConstraint(["target_group_id"], ["groups.group_id"]),
        sa.ForeignKeyConstraint(["target_child_id"], ["children.child_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_announcements_kindergarten_id", "announcements", ["kindergarten_id"], unique=False)
    op.create_index("ix_announcements_target_group_id", "announcements", ["target_group_id"], unique=False)
    op.create_index("ix_announcements_target_child_id", "announcements", ["target_child_id"], unique=False)
    op.create_index("ix_announcements_scheduled_at", "announcements", ["scheduled_at"], unique=False)
    op.create_index("ix_announcements_sent_at", "announcements", ["sent_at"], unique=False)

    op.create_table(
        "notifications",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("kindergarten_id", sa.String(), nullable=False),
        sa.Column("parent_id", sa.String(), nullable=False),
        sa.Column("child_id", sa.String(), nullable=True),
        sa.Column("type", notification_type_enum, nullable=False),
        sa.Column("event_type", notification_event_type_enum, nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("source_announcement_id", sa.String(), nullable=True),
        sa.Column("telegram_delivery_status", telegram_delivery_status_enum, nullable=True),
        sa.Column("telegram_delivered_at", sa.DateTime(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("dedup_key", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["child_id"], ["children.child_id"]),
        sa.ForeignKeyConstraint(["kindergarten_id"], ["kindergartens.kindergarten_id"]),
        sa.ForeignKeyConstraint(["parent_id"], ["parents.parent_id"]),
        sa.ForeignKeyConstraint(["source_announcement_id"], ["announcements.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dedup_key", name="uq_notifications_dedup_key"),
    )
    op.create_index("ix_notifications_kindergarten_id", "notifications", ["kindergarten_id"], unique=False)
    op.create_index("ix_notifications_parent_id", "notifications", ["parent_id"], unique=False)
    op.create_index("ix_notifications_child_id", "notifications", ["child_id"], unique=False)
    op.create_index("ix_notifications_event_type", "notifications", ["event_type"], unique=False)
    op.create_index("ix_notifications_source_announcement_id", "notifications", ["source_announcement_id"], unique=False)
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"], unique=False)
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"], unique=False)
    op.create_index("ix_notifications_dedup_key", "notifications", ["dedup_key"], unique=True)

    op.create_table(
        "parent_notification_settings",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("parent_id", sa.String(), nullable=False),
        sa.Column("attendance_enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("payments_enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("announcements_enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("telegram_enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["parent_id"], ["parents.parent_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("parent_id", name="uq_parent_notification_settings_parent_id"),
    )
    op.create_index("ix_parent_notification_settings_parent_id", "parent_notification_settings", ["parent_id"], unique=True)

    op.create_table(
        "notification_delivery_stats",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("announcement_id", sa.String(), nullable=True),
        sa.Column("sent_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("delivered_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("read_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["announcement_id"], ["announcements.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("announcement_id", name="uq_notification_delivery_stats_announcement_id"),
    )
    op.create_index(
        "ix_notification_delivery_stats_announcement_id",
        "notification_delivery_stats",
        ["announcement_id"],
        unique=True,
    )


def _migrate_legacy_notifications(bind) -> None:
    legacy_notifications = sa.table(
        "notifications_legacy",
        sa.column("notification_id", sa.String()),
        sa.column("user_id", sa.String()),
        sa.column("notif_type", sa.String()),
        sa.column("payload", sa.JSON()),
        sa.column("read_at", sa.DateTime()),
        sa.column("created_at", sa.DateTime()),
    )
    parent_users = sa.table(
        "parent_users",
        sa.column("user_id", sa.Integer()),
        sa.column("parent_id", sa.String()),
    )
    parent_child_links = sa.table(
        "parent_child_links",
        sa.column("parent_id", sa.String()),
        sa.column("child_id", sa.String()),
        sa.column("status", sa.String()),
    )
    children = sa.table(
        "children",
        sa.column("child_id", sa.String()),
        sa.column("kindergarten_id", sa.String()),
    )

    parent_map = {
        str(row.user_id): row.parent_id
        for row in bind.execute(sa.select(parent_users.c.user_id, parent_users.c.parent_id)).fetchall()
    }
    child_rows = bind.execute(
        sa.select(parent_child_links.c.parent_id, parent_child_links.c.child_id, children.c.kindergarten_id)
        .select_from(parent_child_links.join(children, children.c.child_id == parent_child_links.c.child_id))
        .where(parent_child_links.c.status == "active")
    ).fetchall()

    tenant_by_parent: dict[str, tuple[str | None, str | None]] = {}
    for row in child_rows:
        tenant_by_parent.setdefault(row.parent_id, (row.kindergarten_id, row.child_id))

    supported_events = {
        "attendance_late",
        "attendance_absent",
        "payment_created",
        "payment_overdue",
        "payment_paid",
    }
    rows = bind.execute(sa.select(legacy_notifications)).fetchall()
    for row in rows:
        parent_id = parent_map.get(str(row.user_id))
        if not parent_id:
            continue
        kindergarten_id, fallback_child_id = tenant_by_parent.get(parent_id, (None, None))
        if not kindergarten_id:
            continue

        payload = row.payload or {}
        title = payload.get("title") or str(row.notif_type or "Notification").replace("_", " ").title()
        message = payload.get("message") or title
        event_type = row.notif_type if row.notif_type in supported_events else None
        notification_id = row.notification_id or str(uuid.uuid4())
        created_at = row.created_at
        bind.execute(
            sa.text(
                """
                INSERT INTO notifications (
                    id, kindergarten_id, parent_id, child_id, type, event_type,
                    title, message, source_announcement_id, telegram_delivery_status,
                    telegram_delivered_at, is_read, read_at, dedup_key, created_at, updated_at
                ) VALUES (
                    :id, :kindergarten_id, :parent_id, :child_id, :type, :event_type,
                    :title, :message, NULL, :telegram_delivery_status,
                    NULL, :is_read, :read_at, NULL, :created_at, :updated_at
                )
                """
            ),
            {
                "id": notification_id,
                "kindergarten_id": kindergarten_id,
                "parent_id": parent_id,
                "child_id": payload.get("child_id") or fallback_child_id,
                "type": "system",
                "event_type": event_type,
                "title": title,
                "message": message,
                "telegram_delivery_status": "skipped",
                "is_read": 1 if row.read_at is not None else 0,
                "read_at": row.read_at,
                "created_at": created_at,
                "updated_at": created_at,
            },
        )


def _seed_default_settings(bind) -> None:
    parents = sa.table("parents", sa.column("parent_id", sa.String()))
    rows = bind.execute(sa.select(parents.c.parent_id)).fetchall()
    for row in rows:
        bind.execute(
            sa.text(
                """
                INSERT INTO parent_notification_settings (
                    id, parent_id, attendance_enabled, payments_enabled,
                    announcements_enabled, telegram_enabled, created_at, updated_at
                ) VALUES (
                    :id, :parent_id, 1, 1, 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                """
            ),
            {"id": str(uuid.uuid4()), "parent_id": row.parent_id},
        )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _schema_is_current(inspector):
        return

    if _has_table(inspector, "notifications"):
        op.rename_table("notifications", "notifications_legacy")
        inspector = sa.inspect(bind)

    _drop_table_if_exists(
        inspector,
        "notification_delivery_stats",
        indexes=["ix_notification_delivery_stats_notification_id", "ix_notification_delivery_stats_announcement_id"],
    )
    inspector = sa.inspect(bind)
    _drop_table_if_exists(inspector, "parent_notification_settings", indexes=["ix_parent_notification_settings_parent_id"])
    inspector = sa.inspect(bind)
    _drop_table_if_exists(
        inspector,
        "announcements",
        indexes=[
            "ix_announcements_kindergarten_id",
            "ix_announcements_target_id",
            "ix_announcements_target_group_id",
            "ix_announcements_target_child_id",
            "ix_announcements_scheduled_at",
            "ix_announcements_sent_at",
        ],
    )

    _create_schema()
    inspector = sa.inspect(bind)
    if _has_table(inspector, "notifications_legacy"):
        _migrate_legacy_notifications(bind)
        op.drop_table("notifications_legacy")
    _seed_default_settings(bind)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    _drop_table_if_exists(inspector, "notification_delivery_stats", indexes=["ix_notification_delivery_stats_announcement_id"])
    inspector = sa.inspect(bind)
    _drop_table_if_exists(inspector, "parent_notification_settings", indexes=["ix_parent_notification_settings_parent_id"])
    inspector = sa.inspect(bind)
    _drop_table_if_exists(
        inspector,
        "notifications",
        indexes=[
            "ix_notifications_dedup_key",
            "ix_notifications_created_at",
            "ix_notifications_is_read",
            "ix_notifications_source_announcement_id",
            "ix_notifications_event_type",
            "ix_notifications_child_id",
            "ix_notifications_parent_id",
            "ix_notifications_kindergarten_id",
        ],
    )
    inspector = sa.inspect(bind)
    _drop_table_if_exists(
        inspector,
        "announcements",
        indexes=[
            "ix_announcements_sent_at",
            "ix_announcements_scheduled_at",
            "ix_announcements_target_child_id",
            "ix_announcements_target_group_id",
            "ix_announcements_kindergarten_id",
        ],
    )
