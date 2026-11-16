"""Support delayed screen registration and reconnect pairing.

Revision ID: b81c4a2f9d60
Revises: 65a4d712416f
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b81c4a2f9d60"
down_revision: str | None = "65a4d712416f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    duplicates = (
        bind.execute(
            sa.text(
                "SELECT screen_id FROM screen_credentials "
                "WHERE revoked_at IS NULL GROUP BY screen_id HAVING count(*) > 1"
            )
        )
        .scalars()
        .all()
    )
    if duplicates:
        raise RuntimeError(
            "Cannot enforce one active screen credential per screen because duplicate "
            f"active credentials exist for: {', '.join(map(str, duplicates))}. "
            "Resolve these records explicitly, then rerun the migration."
        )

    op.add_column(
        "screen_pairing_sessions",
        sa.Column("pairing_type", sa.String(length=32), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE screen_pairing_sessions "
            "SET pairing_type = 'RECONNECT_EXISTING' WHERE pairing_type IS NULL"
        )
    )
    op.alter_column(
        "screen_pairing_sessions",
        "pairing_type",
        existing_type=sa.String(length=32),
        nullable=False,
    )
    op.alter_column(
        "screen_pairing_sessions",
        "screen_id",
        existing_type=sa.UUID(),
        nullable=True,
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

    op.drop_index("ix_screen_credentials_active", table_name="screen_credentials")
    op.create_index(
        "uq_screen_credentials_one_active_per_screen",
        "screen_credentials",
        ["screen_id"],
        unique=True,
        postgresql_where=sa.text("revoked_at IS NULL"),
    )


def downgrade() -> None:
    bind = op.get_bind()
    pending_new_screens = bind.execute(
        sa.text(
            "SELECT id FROM screen_pairing_sessions "
            "WHERE pairing_type = 'NEW_SCREEN' AND screen_id IS NULL LIMIT 1"
        )
    ).scalar_one_or_none()
    if pending_new_screens is not None:
        raise RuntimeError(
            "Cannot downgrade while unpaired NEW_SCREEN sessions exist because the "
            "previous schema requires every pairing session to reference a screen."
        )

    op.drop_index(
        "uq_screen_credentials_one_active_per_screen",
        table_name="screen_credentials",
        postgresql_where=sa.text("revoked_at IS NULL"),
    )
    op.create_index(
        "ix_screen_credentials_active",
        "screen_credentials",
        ["screen_id", "revoked_at"],
        unique=False,
    )
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
        "screen_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
    op.drop_column("screen_pairing_sessions", "pairing_type")
