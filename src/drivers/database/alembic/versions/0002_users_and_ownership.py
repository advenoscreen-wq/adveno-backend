"""Add unified users and explicit resource ownership.

Revision ID: 0002_users_and_ownership
Revises: 0001_initial
"""

from uuid import UUID

import sqlalchemy as sa
from alembic import op

revision = "0002_users_and_ownership"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Preserve existing data while introducing user ownership."""
    op.rename_table("admin_profiles", "users")
    op.add_column(
        "users",
        sa.Column("role", sa.String(20), nullable=False, server_default="ADMIN"),
    )
    op.create_check_constraint("ck_users_role", "users", "role IN ('ADMIN', 'USER')")
    op.create_index("ix_users_role", "users", ["role"])
    op.execute(
        sa.text(
            "DO $$ BEGIN "
            "IF to_regclass('auth.users') IS NOT NULL THEN "
            "ALTER TABLE users ADD CONSTRAINT fk_users_auth_user "
            "FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE; "
            "END IF; END $$;"
        )
    )

    for table in ("screens", "media_assets", "playlists"):
        op.add_column(table, sa.Column("user_id", sa.UUID(), nullable=True))

    connection = op.get_bind()
    has_owned_rows = connection.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM screens) "
            "OR EXISTS (SELECT 1 FROM media_assets) "
            "OR EXISTS (SELECT 1 FROM playlists)"
        )
    ).scalar()
    user_count: int = connection.execute(sa.text("SELECT count(*) FROM users")).scalar_one()
    if has_owned_rows and user_count != 1:
        raise RuntimeError(
            "Cannot safely backfill ownership: existing resources require exactly one user"
        )
    if user_count == 1:
        user_id: UUID = connection.execute(sa.text("SELECT id FROM users LIMIT 1")).scalar_one()
        for table in ("screens", "media_assets", "playlists"):
            connection.execute(
                sa.text(f"UPDATE {table} SET user_id = :user_id"),
                {"user_id": user_id},
            )

    for table in ("screens", "media_assets", "playlists"):
        op.alter_column(table, "user_id", nullable=False)
        op.create_foreign_key(
            f"fk_{table}_user_id",
            table,
            "users",
            ["user_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        op.create_index(f"ix_{table}_user_id", table, ["user_id"])


def downgrade() -> None:
    """Remove ownership fields and restore the admin profile table name."""
    op.execute(
        sa.text(
            "DO $$ BEGIN "
            "IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_users_auth_user') THEN "
            "ALTER TABLE users DROP CONSTRAINT fk_users_auth_user; "
            "END IF; END $$;"
        )
    )
    for table in ("screens", "media_assets", "playlists"):
        op.drop_index(f"ix_{table}_user_id", table_name=table)
        op.drop_constraint(f"fk_{table}_user_id", table, type_="foreignkey")
        op.drop_column(table, "user_id")
    op.drop_index("ix_users_role", table_name="users")
    op.drop_constraint("ck_users_role", "users", type_="check")
    op.drop_column("users", "role")
    op.rename_table("users", "admin_profiles")
