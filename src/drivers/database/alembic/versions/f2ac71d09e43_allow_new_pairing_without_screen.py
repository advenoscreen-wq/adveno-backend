"""Allow NEW_SCREEN approvals without creating a screen row.

Revision ID: f2ac71d09e43
Revises: e4b617a93c20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f2ac71d09e43"
down_revision: str | None = "e4b617a93c20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _reference_constraint(*, allow_new_screen_without_screen: bool) -> str:
    new_screen_paired = (
        "(paired_at IS NOT NULL AND status = 'PAIRED')"
        if allow_new_screen_without_screen
        else "(paired_at IS NOT NULL AND screen_id IS NOT NULL AND status = 'PAIRED')"
    )
    return (
        "(pairing_type IS NULL AND screen_id IS NULL AND paired_at IS NULL "
        "AND status IN ('PENDING', 'EXPIRED')) OR "
        "(pairing_type = 'NEW_SCREEN' AND "
        "((paired_at IS NULL AND screen_id IS NULL AND status IN ('PENDING', 'EXPIRED')) OR "
        f"{new_screen_paired})) OR "
        "(pairing_type = 'RECONNECT_EXISTING' AND "
        "((paired_at IS NULL AND status IN ('PENDING', 'EXPIRED')) OR "
        "(paired_at IS NOT NULL AND screen_id IS NOT NULL AND status = 'PAIRED')))"
    )


def upgrade() -> None:
    op.drop_constraint(
        "ck_pairing_sessions_screen_reference",
        "screen_pairing_sessions",
        type_="check",
    )
    op.create_check_constraint(
        "ck_pairing_sessions_screen_reference",
        "screen_pairing_sessions",
        _reference_constraint(allow_new_screen_without_screen=True),
    )


def downgrade() -> None:
    has_paired_new_without_screen = op.get_bind().execute(
        sa.text(
            "SELECT id FROM screen_pairing_sessions "
            "WHERE pairing_type = 'NEW_SCREEN' AND status = 'PAIRED' "
            "AND screen_id IS NULL LIMIT 1"
        )
    ).scalar_one_or_none()
    if has_paired_new_without_screen is not None:
        raise RuntimeError(
            "Cannot downgrade while NEW_SCREEN pairing sessions are paired without a screen."
        )

    op.drop_constraint(
        "ck_pairing_sessions_screen_reference",
        "screen_pairing_sessions",
        type_="check",
    )
    op.create_check_constraint(
        "ck_pairing_sessions_screen_reference",
        "screen_pairing_sessions",
        _reference_constraint(allow_new_screen_without_screen=False),
    )
