"""Create the Adveno domain schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-11-12
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the ten domain tables and their integrity constraints."""
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "admin_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_table(
        "screens",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("screen_code", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("device_model", sa.String(255)),
        sa.Column("app_version", sa.String(100)),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
        sa.Column("last_successful_sync_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("screen_code", name="uq_screens_screen_code"),
        sa.CheckConstraint("length(trim(screen_code)) > 0", name="ck_screens_screen_code"),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_screens_name"),
    )
    op.create_index("ix_screens_status", "screens", ["status"])
    op.create_table(
        "screen_pairing_sessions",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column(
            "screen_id",
            UUID(as_uuid=True),
            sa.ForeignKey("screens.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("paired_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("token_hash", name="uq_pairing_sessions_token_hash"),
    )
    op.create_index(
        "ix_pairing_sessions_valid",
        "screen_pairing_sessions",
        ["token_hash", "expires_at", "paired_at"],
    )
    op.create_table(
        "screen_credentials",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column(
            "screen_id",
            UUID(as_uuid=True),
            sa.ForeignKey("screens.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("credential_hash", sa.String(255), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_screen_credentials_screen_id", "screen_credentials", ["screen_id"])
    op.create_index(
        "ix_screen_credentials_active", "screen_credentials", ["screen_id", "revoked_at"]
    )
    op.create_table(
        "media_assets",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("media_type", sa.String(20), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("storage_path", sa.String(1024), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("checksum", sa.String(255), nullable=False),
        sa.Column("width", sa.Integer()),
        sa.Column("height", sa.Integer()),
        sa.Column("duration_seconds", sa.Integer()),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("storage_path", name="uq_media_assets_storage_path"),
        sa.CheckConstraint("file_size >= 0", name="ck_media_assets_file_size"),
        sa.CheckConstraint("width IS NULL OR width > 0", name="ck_media_assets_width"),
        sa.CheckConstraint("height IS NULL OR height > 0", name="ck_media_assets_height"),
        sa.CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds > 0",
            name="ck_media_assets_duration",
        ),
    )
    op.create_index("ix_media_assets_status", "media_assets", ["status"])
    op.create_table(
        "playlists",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_playlists_name"),
        sa.CheckConstraint("version > 0", name="ck_playlists_version"),
    )
    op.create_table(
        "playlist_items",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column(
            "playlist_id",
            UUID(as_uuid=True),
            sa.ForeignKey("playlists.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "media_asset_id",
            UUID(as_uuid=True),
            sa.ForeignKey("media_assets.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("duration_seconds", sa.Integer()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("playlist_id", "position", name="uq_playlist_items_position"),
        sa.CheckConstraint("position > 0", name="ck_playlist_items_position"),
        sa.CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds > 0",
            name="ck_playlist_items_duration",
        ),
    )
    op.create_index("ix_playlist_items_playlist_id", "playlist_items", ["playlist_id"])
    op.create_table(
        "screen_playlist_assignments",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column(
            "screen_id",
            UUID(as_uuid=True),
            sa.ForeignKey("screens.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "playlist_id",
            UUID(as_uuid=True),
            sa.ForeignKey("playlists.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("unassigned_at", sa.DateTime(timezone=True)),
    )
    op.create_index(
        "uq_active_assignment_per_screen",
        "screen_playlist_assignments",
        ["screen_id"],
        unique=True,
        postgresql_where=sa.text("unassigned_at IS NULL"),
    )
    op.create_index("ix_assignments_screen_id", "screen_playlist_assignments", ["screen_id"])
    op.create_index("ix_assignments_playlist_id", "screen_playlist_assignments", ["playlist_id"])
    op.create_table(
        "screen_sync_states",
        sa.Column(
            "screen_id",
            UUID(as_uuid=True),
            sa.ForeignKey("screens.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("desired_revision", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("applied_revision", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("sync_status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("last_sync_started_at", sa.DateTime(timezone=True)),
        sa.Column("last_successful_sync_at", sa.DateTime(timezone=True)),
        sa.Column("last_error", sa.Text()),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("desired_revision >= 0", name="ck_sync_states_desired_revision"),
        sa.CheckConstraint("applied_revision >= 0", name="ck_sync_states_applied_revision"),
        sa.CheckConstraint(
            "applied_revision <= desired_revision", name="ck_sync_states_revision_order"
        ),
    )
    op.create_index("ix_sync_states_status", "screen_sync_states", ["sync_status"])
    op.create_table(
        "audit_logs",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column(
            "admin_id", UUID(as_uuid=True), sa.ForeignKey("admin_profiles.id", ondelete="SET NULL")
        ),
        sa.Column(
            "screen_id", UUID(as_uuid=True), sa.ForeignKey("screens.id", ondelete="SET NULL")
        ),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("details", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_audit_logs_screen_id_created_at", "audit_logs", ["screen_id", "created_at"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    """Drop the Adveno domain schema."""
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_screen_id_created_at", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_sync_states_status", table_name="screen_sync_states")
    op.drop_table("screen_sync_states")
    op.drop_index("ix_assignments_playlist_id", table_name="screen_playlist_assignments")
    op.drop_index("ix_assignments_screen_id", table_name="screen_playlist_assignments")
    op.drop_index("uq_active_assignment_per_screen", table_name="screen_playlist_assignments")
    op.drop_table("screen_playlist_assignments")
    op.drop_index("ix_playlist_items_playlist_id", table_name="playlist_items")
    op.drop_table("playlist_items")
    op.drop_table("playlists")
    op.drop_index("ix_media_assets_status", table_name="media_assets")
    op.drop_table("media_assets")
    op.drop_index("ix_screen_credentials_active", table_name="screen_credentials")
    op.drop_index("ix_screen_credentials_screen_id", table_name="screen_credentials")
    op.drop_table("screen_credentials")
    op.drop_index("ix_pairing_sessions_valid", table_name="screen_pairing_sessions")
    op.drop_table("screen_pairing_sessions")
    op.drop_index("ix_screens_status", table_name="screens")
    op.drop_table("screens")
    op.drop_table("admin_profiles")
