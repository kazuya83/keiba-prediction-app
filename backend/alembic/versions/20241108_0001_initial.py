"""初期マイグレーション。"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20241108_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass


