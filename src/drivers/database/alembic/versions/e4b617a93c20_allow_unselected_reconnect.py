"""Allow selecting the reconnect screen after session creation.

Revision ID: e4b617a93c20
Revises: d239a6c8174e
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e4b617a93c20"
down_revision: str | None = "d239a6c8174e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_pairing_sessions_screen_reference",
        "screen_pairing_sessions",
        type_="check",
    )
    op.create_check_constraint(
        "ck_pairing_sessions_screen_reference",
        "screen_pairing_sessions",
        "(pairing_type IS NULL AND screen_id IS NULL AND paired_at IS NULL "
        "AND status IN ('PENDING', 'EXPIRED')) OR "
        "(pairing_type = 'NEW_SCREEN' AND "
        "((paired_at IS NULL AND screen_id IS NULL AND status IN ('PENDING', 'EXPIRED')) OR "
        "(paired_at IS NOT NULL AND screen_id IS NOT NULL AND status = 'PAIRED'))) OR "
        "(pairing_type = 'RECONNECT_EXISTING' AND "
        "((paired_at IS NULL AND status IN ('PENDING', 'EXPIRED')) OR "
        "(paired_at IS NOT NULL AND screen_id IS NOT NULL AND status = 'PAIRED')))",
    )


def downgrade() -> None:
    has_unselected_reconnect = op.get_bind().execute(
        sa.text(
            "SELECT id FROM screen_pairing_sessions "
            "WHERE pairing_type = 'RECONNECT_EXISTING' AND screen_id IS NULL LIMIT 1"
        )
    ).scalar_one_or_none()
    if has_unselected_reconnect is not None:
        raise RuntimeError(
            "Cannot downgrade while reconnect sessions have no selected screen."
        )

    op.drop_constraint(
        "ck_pairing_sessions_screen_reference",
        "screen_pairing_sessions",
        type_="check",
    )
    op.create_check_constraint(
        "ck_pairing_sessions_screen_reference",
        "screen_pairing_sessions",
        "(pairing_type IS NULL AND screen_id IS NULL AND paired_at IS NULL "
        "AND status IN ('PENDING', 'EXPIRED')) OR "
        "(pairing_type = 'NEW_SCREEN' AND "
        "((paired_at IS NULL AND screen_id IS NULL AND status IN ('PENDING', 'EXPIRED')) OR "
        "(paired_at IS NOT NULL AND screen_id IS NOT NULL AND status = 'PAIRED'))) OR "
        "(pairing_type = 'RECONNECT_EXISTING' AND screen_id IS NOT NULL AND "
        "((paired_at IS NULL AND status IN ('PENDING', 'EXPIRED')) OR "
        "(paired_at IS NOT NULL AND status = 'PAIRED')))",
    )
