"""Add CONNECTING as the intermediate pairing state.

Revision ID: c6310c5d7e24
Revises: f2ac71d09e43
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c6310c5d7e24"
down_revision: str | None = "f2ac71d09e43"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _reference_constraint() -> str:
    return (
        "(pairing_type IS NULL AND screen_id IS NULL AND paired_at IS NULL "
        "AND status IN ('PENDING', 'EXPIRED')) OR "
        "(pairing_type = 'NEW_SCREEN' AND "
        "((paired_at IS NULL AND screen_id IS NULL "
        "AND status IN ('PENDING', 'CONNECTING', 'EXPIRED')) OR "
        "(paired_at IS NOT NULL AND screen_id IS NOT NULL AND status = 'PAIRED'))) OR "
        "(pairing_type = 'RECONNECT_EXISTING' AND "
        "((paired_at IS NULL AND screen_id IS NULL AND status IN ('PENDING', 'EXPIRED')) OR "
        "(paired_at IS NULL AND screen_id IS NOT NULL AND status = 'CONNECTING') OR "
        "(paired_at IS NOT NULL AND screen_id IS NOT NULL AND status = 'PAIRED')))"
    )


def upgrade() -> None:
    op.drop_constraint(
        "ck_pairing_sessions_screen_reference",
        "screen_pairing_sessions",
        type_="check",
    )
    op.drop_constraint(
        "ck_pairing_sessions_status",
        "screen_pairing_sessions",
        type_="check",
    )

    # Existing PAIRED rows without an active credential have completed the
    # old approval step only; keep them resumable under the new lifecycle.
    op.execute(
        sa.text(
            "UPDATE screen_pairing_sessions AS pairing "
            "SET status = 'CONNECTING', paired_at = NULL "
            "WHERE pairing.status = 'PAIRED' AND ("
            "(pairing.pairing_type = 'NEW_SCREEN' AND pairing.screen_id IS NULL) OR "
            "(pairing.pairing_type = 'RECONNECT_EXISTING' AND NOT EXISTS ("
            "SELECT 1 FROM screen_credentials AS credential "
            "WHERE credential.screen_id = pairing.screen_id "
            "AND credential.revoked_at IS NULL)))"
        )
    )

    op.create_check_constraint(
        "ck_pairing_sessions_screen_reference",
        "screen_pairing_sessions",
        _reference_constraint(),
    )
    op.create_check_constraint(
        "ck_pairing_sessions_status",
        "screen_pairing_sessions",
        "status IN ('PENDING', 'CONNECTING', 'PAIRED', 'EXPIRED')",
    )


def downgrade() -> None:
    has_connecting_sessions = (
        op.get_bind()
        .execute(
            sa.text("SELECT id FROM screen_pairing_sessions WHERE status = 'CONNECTING' LIMIT 1")
        )
        .scalar_one_or_none()
    )
    if has_connecting_sessions is not None:
        raise RuntimeError("Cannot downgrade while pairing sessions are CONNECTING.")

    op.drop_constraint(
        "ck_pairing_sessions_screen_reference",
        "screen_pairing_sessions",
        type_="check",
    )
    op.drop_constraint(
        "ck_pairing_sessions_status",
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
        "(paired_at IS NOT NULL AND status = 'PAIRED'))) OR "
        "(pairing_type = 'RECONNECT_EXISTING' AND "
        "((paired_at IS NULL AND status IN ('PENDING', 'EXPIRED')) OR "
        "(paired_at IS NOT NULL AND screen_id IS NOT NULL AND status = 'PAIRED')))",
    )
    op.create_check_constraint(
        "ck_pairing_sessions_status",
        "screen_pairing_sessions",
        "status IN ('PENDING', 'PAIRED', 'EXPIRED')",
    )
