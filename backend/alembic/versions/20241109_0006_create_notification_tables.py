"""通知テーブルおよび設定テーブルを追加するマイグレーション。"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20241109_0006"
down_revision = "20241108_0005"
branch_labels = None
depends_on = None

notification_category_enum = sa.Enum(
    "prediction",
    "result",
    "system",
    name="notification_category",
)

notification_status_enum = sa.Enum(
    "pending",
    "sent",
    "failed",
    "suppressed",
    name="notification_status",
)


def upgrade() -> None:
    bind = op.get_bind()
    notification_category_enum.create(bind, checkfirst=True)
    notification_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "notification_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "enable_app",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("TRUE"),
        ),
        sa.Column(
            "enable_push",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
        ),
        sa.Column(
            "allow_prediction",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("TRUE"),
        ),
        sa.Column(
            "allow_race_result",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("TRUE"),
        ),
        sa.Column(
            "allow_system",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("TRUE"),
        ),
        sa.Column("quiet_hours_start", sa.Time(), nullable=True),
        sa.Column("quiet_hours_end", sa.Time(), nullable=True),
        sa.Column("push_endpoint", sa.String(length=512), nullable=True),
        sa.Column("push_p256dh", sa.String(length=255), nullable=True),
        sa.Column("push_auth", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ("user_id",),
            ("users.id",),
            name="fk_notification_settings_user_id_users",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("user_id", name="uq_notification_settings_user_id"),
    )
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("race_id", sa.Integer(), nullable=True),
        sa.Column("category", notification_category_enum, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("action_url", sa.String(length=512), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column(
            "is_read",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
        ),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            notification_status_enum,
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "retry_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "max_retries",
            sa.SmallInteger(),
            nullable=False,
            server_default=sa.text("3"),
        ),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ("user_id",),
            ("users.id",),
            name="fk_notifications_user_id_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ("race_id",),
            ("races.id",),
            name="fk_notifications_race_id_races",
            ondelete="SET NULL",
        ),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"], unique=False)
    op.create_index("ix_notifications_race_id", "notifications", ["race_id"], unique=False)
    op.create_index(
        "ix_notifications_status",
        "notifications",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_notifications_is_read",
        "notifications",
        ["is_read"],
        unique=False,
    )
    op.create_index(
        "ix_notifications_created_at",
        "notifications",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_notifications_created_at", table_name="notifications")
    op.drop_index("ix_notifications_is_read", table_name="notifications")
    op.drop_index("ix_notifications_status", table_name="notifications")
    op.drop_index("ix_notifications_race_id", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")

    op.drop_table("notification_settings")

    bind = op.get_bind()
    notification_status_enum.drop(bind, checkfirst=True)
    notification_category_enum.drop(bind, checkfirst=True)


