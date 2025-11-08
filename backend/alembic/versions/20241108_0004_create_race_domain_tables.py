"""レース関連ドメインテーブルを追加するマイグレーション。"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20241108_0004"
down_revision = "20241108_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "weathers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("condition", sa.String(length=64), nullable=False),
        sa.Column("track_condition", sa.String(length=64), nullable=True),
        sa.Column("temperature_c", sa.Float(), nullable=True),
        sa.Column("humidity", sa.Float(), nullable=True),
        sa.Column("wind_speed_ms", sa.Float(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=True),
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
    )

    op.create_table(
        "horses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("sex", sa.String(length=16), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("sire", sa.String(length=255), nullable=True),
        sa.Column("dam", sa.String(length=255), nullable=True),
        sa.Column("color", sa.String(length=32), nullable=True),
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
        sa.UniqueConstraint("name", name="uq_horses_name"),
    )
    op.create_index("ix_horses_name", "horses", ["name"], unique=False)

    op.create_table(
        "jockeys",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("license_area", sa.String(length=64), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("debut_year", sa.Integer(), nullable=True),
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
        sa.UniqueConstraint("name", name="uq_jockeys_name"),
    )
    op.create_index("ix_jockeys_name", "jockeys", ["name"], unique=False)

    op.create_table(
        "trainers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("stable_location", sa.String(length=255), nullable=True),
        sa.Column("license_area", sa.String(length=64), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
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
        sa.UniqueConstraint("name", name="uq_trainers_name"),
    )
    op.create_index("ix_trainers_name", "trainers", ["name"], unique=False)

    op.create_table(
        "races",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("race_date", sa.Date(), nullable=False),
        sa.Column("venue", sa.String(length=64), nullable=False),
        sa.Column("course_type", sa.String(length=32), nullable=False),
        sa.Column("distance", sa.Integer(), nullable=False),
        sa.Column("grade", sa.String(length=32), nullable=True),
        sa.Column("weather_id", sa.Integer(), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
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
            ("weather_id",),
            ("weathers.id",),
            name="fk_races_weather_id_weathers",
            ondelete="SET NULL",
        ),
    )
    op.create_index("ix_races_race_date", "races", ["race_date"], unique=False)
    op.create_index("ix_races_venue", "races", ["venue"], unique=False)

    op.create_table(
        "race_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("race_id", sa.Integer(), nullable=False),
        sa.Column("horse_id", sa.Integer(), nullable=False),
        sa.Column("jockey_id", sa.Integer(), nullable=True),
        sa.Column("trainer_id", sa.Integer(), nullable=True),
        sa.Column("horse_number", sa.Integer(), nullable=True),
        sa.Column("post_position", sa.Integer(), nullable=True),
        sa.Column("final_position", sa.Integer(), nullable=True),
        sa.Column("odds", sa.Numeric(10, 2), nullable=True),
        sa.Column("carried_weight", sa.Numeric(5, 1), nullable=True),
        sa.Column("comment", sa.String(length=255), nullable=True),
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
            ("race_id",),
            ("races.id",),
            name="fk_race_entries_race_id_races",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ("horse_id",),
            ("horses.id",),
            name="fk_race_entries_horse_id_horses",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ("jockey_id",),
            ("jockeys.id",),
            name="fk_race_entries_jockey_id_jockeys",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ("trainer_id",),
            ("trainers.id",),
            name="fk_race_entries_trainer_id_trainers",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("race_id", "horse_id", name="uq_race_entries_race_horse"),
    )
    op.create_index("ix_race_entries_race_id", "race_entries", ["race_id"], unique=False)
    op.create_index("ix_race_entries_horse_id", "race_entries", ["horse_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_race_entries_horse_id", table_name="race_entries")
    op.drop_index("ix_race_entries_race_id", table_name="race_entries")
    op.drop_table("race_entries")

    op.drop_index("ix_races_venue", table_name="races")
    op.drop_index("ix_races_race_date", table_name="races")
    op.drop_table("races")

    op.drop_index("ix_trainers_name", table_name="trainers")
    op.drop_table("trainers")

    op.drop_index("ix_jockeys_name", table_name="jockeys")
    op.drop_table("jockeys")

    op.drop_index("ix_horses_name", table_name="horses")
    op.drop_table("horses")

    op.drop_table("weathers")


