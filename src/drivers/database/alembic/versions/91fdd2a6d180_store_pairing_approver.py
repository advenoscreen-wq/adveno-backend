"""Store the user who approved screen pairing."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "91fdd2a6d180"
down_revision: str | None = "c6310c5d7e24"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "screen_pairing_sessions",
        sa.Column("approved_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE screen_pairing_sessions AS pairing "
            "SET approved_by_user_id = screens.user_id "
            "FROM screens "
            "WHERE pairing.pairing_type = 'RECONNECT_EXISTING' "
            "AND pairing.screen_id = screens.id"
        )
    )


def downgrade() -> None:
    op.drop_column("screen_pairing_sessions", "approved_by_user_id")
