"""予測関連テーブルを追加するマイグレーション。"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20241108_0005"
down_revision = "20241108_0004"
branch_labels = None
depends_on = None

prediction_result_enum = sa.Enum("pending", "hit", "miss", name="prediction_result")


def upgrade() -> None:
    bind = op.get_bind()
    prediction_result_enum.create(bind, checkfirst=True)

    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("race_id", sa.Integer(), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=True),
        sa.Column(
            "stake_amount",
            sa.Numeric(12, 2),
            nullable=False,
            server_default=sa.text("100.00"),
        ),
        sa.Column("odds", sa.Numeric(10, 2), nullable=True),
        sa.Column(
            "payout",
            sa.Numeric(12, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "result",
            prediction_result_enum,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("memo", sa.Text(), nullable=True),
        sa.Column(
            "prediction_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
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
            name="fk_predictions_user_id_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ("race_id",),
            ("races.id",),
            name="fk_predictions_race_id_races",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_predictions_user_id", "predictions", ["user_id"], unique=False)
    op.create_index("ix_predictions_race_id", "predictions", ["race_id"], unique=False)
    op.create_index(
        "ix_predictions_prediction_at",
        "predictions",
        ["prediction_at"],
        unique=False,
    )

    op.create_table(
        "prediction_histories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("prediction_id", sa.Integer(), nullable=False),
        sa.Column("race_entry_id", sa.Integer(), nullable=True),
        sa.Column("rank", sa.SmallInteger(), nullable=False),
        sa.Column("probability", sa.Numeric(5, 4), nullable=True),
        sa.Column("odds", sa.Numeric(10, 2), nullable=True),
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
            ("prediction_id",),
            ("predictions.id",),
            name="fk_prediction_histories_prediction_id_predictions",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ("race_entry_id",),
            ("race_entries.id",),
            name="fk_prediction_histories_race_entry_id_race_entries",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint(
            "prediction_id",
            "rank",
            name="uq_prediction_histories_prediction_rank",
        ),
    )
    op.create_index(
        "ix_prediction_histories_prediction_id",
        "prediction_histories",
        ["prediction_id"],
        unique=False,
    )
    op.create_index(
        "ix_prediction_histories_race_entry_id",
        "prediction_histories",
        ["race_entry_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_prediction_histories_race_entry_id",
        table_name="prediction_histories",
    )
    op.drop_index(
        "ix_prediction_histories_prediction_id",
        table_name="prediction_histories",
    )
    op.drop_table("prediction_histories")

    op.drop_index("ix_predictions_prediction_at", table_name="predictions")
    op.drop_index("ix_predictions_race_id", table_name="predictions")
    op.drop_index("ix_predictions_user_id", table_name="predictions")
    op.drop_table("predictions")

    bind = op.get_bind()
    prediction_result_enum.drop(bind, checkfirst=True)


