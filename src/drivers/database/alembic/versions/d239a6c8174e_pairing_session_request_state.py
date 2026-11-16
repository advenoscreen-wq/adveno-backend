"""Allow unselected pending pairing sessions and persist lifecycle status.

Revision ID: d239a6c8174e
Revises: b81c4a2f9d60
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d239a6c8174e"
down_revision: str | None = "b81c4a2f9d60"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _reference_constraint() -> str:
    return (
        "(pairing_type IS NULL AND screen_id IS NULL AND paired_at IS NULL "
        "AND status IN ('PENDING', 'EXPIRED')) OR "
        "(pairing_type = 'NEW_SCREEN' AND "
        "((paired_at IS NULL AND screen_id IS NULL AND status IN ('PENDING', 'EXPIRED')) OR "
        "(paired_at IS NOT NULL AND screen_id IS NOT NULL AND status = 'PAIRED'))) OR "
        "(pairing_type = 'RECONNECT_EXISTING' AND screen_id IS NOT NULL AND "
        "((paired_at IS NULL AND status IN ('PENDING', 'EXPIRED')) OR "
        "(paired_at IS NOT NULL AND status = 'PAIRED')))"
    )


def upgrade() -> None:
    op.drop_constraint(
        "ck_pairing_sessions_screen_reference",
        "screen_pairing_sessions",
        type_="check",
    )
    op.drop_constraint(
        "ck_pairing_sessions_pairing_type",
        "screen_pairing_sessions",
        type_="check",
    )
    op.alter_column(
        "screen_pairing_sessions",
        "pairing_type",
        existing_type=sa.String(length=32),
        nullable=True,
    )
    op.add_column(
        "screen_pairing_sessions",
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="PENDING",
            nullable=False,
        ),
    )
    op.execute(
        sa.text(
            "UPDATE screen_pairing_sessions SET status = "
            "CASE WHEN paired_at IS NULL THEN 'PENDING' ELSE 'PAIRED' END"
        )
    )
    op.create_check_constraint(
        "ck_pairing_sessions_pairing_type",
        "screen_pairing_sessions",
        "pairing_type IS NULL OR pairing_type IN ('NEW_SCREEN', 'RECONNECT_EXISTING')",
    )
    op.create_check_constraint(
        "ck_pairing_sessions_screen_reference",
        "screen_pairing_sessions",
        _reference_constraint(),
    )
    op.create_check_constraint(
        "ck_pairing_sessions_status",
        "screen_pairing_sessions",
        "status IN ('PENDING', 'PAIRED', 'EXPIRED')",
    )


def downgrade() -> None:
    pending_without_screen = (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT id FROM screen_pairing_sessions "
                "WHERE pairing_type IS NULL OR screen_id IS NULL LIMIT 1"
            )
        )
        .scalar_one_or_none()
    )
    if pending_without_screen is not None:
        raise RuntimeError(
            "Cannot downgrade while unselected pairing sessions or sessions without a "
            "screen exist; the previous schema requires a pairing type and screen ID."
        )

    op.drop_constraint("ck_pairing_sessions_status", "screen_pairing_sessions", type_="check")
    op.drop_constraint(
        "ck_pairing_sessions_screen_reference",
        "screen_pairing_sessions",
        type_="check",
    )
    op.drop_constraint(
        "ck_pairing_sessions_pairing_type",
        "screen_pairing_sessions",
        type_="check",
    )
    op.drop_column("screen_pairing_sessions", "status")
    op.alter_column(
        "screen_pairing_sessions",
        "pairing_type",
        existing_type=sa.String(length=32),
        nullable=False,
    )
    op.create_check_constraint(
        "ck_pairing_sessions_pairing_type",
        "screen_pairing_sessions",
        "pairing_type IN ('NEW_SCREEN', 'RECONNECT_EXISTING')",
    )
    op.create_check_constraint(
        "ck_pairing_sessions_screen_reference",
        "screen_pairing_sessions",
        "(pairing_type = 'NEW_SCREEN' AND "
        "((paired_at IS NULL AND screen_id IS NULL) OR "
        "(paired_at IS NOT NULL AND screen_id IS NOT NULL))) OR "
        "(pairing_type = 'RECONNECT_EXISTING' AND screen_id IS NOT NULL)",
    )
