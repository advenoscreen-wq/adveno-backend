"""Add PIN-protected screen administration sessions."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "ca0d95147b3a"
down_revision: str | None = "a1840ef32bd9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "screen_admin_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("screen_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code_hash", sa.String(length=255), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_activity_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "expires_at > created_at",
            name="ck_screen_admin_sessions_expiration",
        ),
        sa.ForeignKeyConstraint(["screen_id"], ["screens.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_screen_admin_sessions_token_hash"),
    )
    op.create_index(
        "ix_screen_admin_sessions_screen_created",
        "screen_admin_sessions",
        ["screen_id", "created_at"],
    )
    op.create_index(
        "uq_screen_admin_sessions_pending_pin_per_screen",
        "screen_admin_sessions",
        ["screen_id"],
        unique=True,
        postgresql_where=sa.text("token_hash IS NULL AND revoked_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_screen_admin_sessions_pending_pin_per_screen",
        table_name="screen_admin_sessions",
    )
    op.drop_index(
        "ix_screen_admin_sessions_screen_created",
        table_name="screen_admin_sessions",
    )
    op.drop_table("screen_admin_sessions")
