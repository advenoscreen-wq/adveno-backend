"""Allow playback reports for ads interrupted before completion."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1840ef32bd9"
down_revision: str | None = "7b4e2ac91f63"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "screen_playback_events",
        "played_complete_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
    )


def downgrade() -> None:
    incomplete_event_exists = (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT id FROM screen_playback_events WHERE played_complete_at IS NULL LIMIT 1"
            )
        )
        .scalar_one_or_none()
    )
    if incomplete_event_exists is not None:
        raise RuntimeError(
            "Cannot make played_complete_at required while incomplete playback events exist."
        )
    op.alter_column(
        "screen_playback_events",
        "played_complete_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
