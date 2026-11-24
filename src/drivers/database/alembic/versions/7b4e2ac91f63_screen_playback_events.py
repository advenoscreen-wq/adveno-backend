"""Store immutable screen-reported playback events."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "7b4e2ac91f63"
down_revision: str | None = "91fdd2a6d180"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "screen_playback_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("screen_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("playlist_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("playlist_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("media_asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("playlist_version", sa.Integer(), nullable=False),
        sa.Column("media_checksum", sa.String(length=255), nullable=False),
        sa.Column("played_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("played_complete_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("playlist_version > 0", name="ck_playback_events_playlist_version"),
        sa.CheckConstraint(
            "played_complete_at >= played_at",
            name="ck_playback_events_completion_after_start",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("screen_id", "event_id", name="uq_playback_events_screen_event_id"),
    )
    op.create_index(
        "ix_playback_events_screen_played_at",
        "screen_playback_events",
        ["screen_id", "played_at"],
    )
    op.create_index(
        "ix_playback_events_playlist_played_at",
        "screen_playback_events",
        ["playlist_id", "played_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_playback_events_playlist_played_at",
        table_name="screen_playback_events",
    )
    op.drop_index(
        "ix_playback_events_screen_played_at",
        table_name="screen_playback_events",
    )
    op.drop_table("screen_playback_events")
