"""Unit tests for persistence-to-domain mapping."""

from datetime import UTC, datetime
from uuid import uuid4

from adapters.repositories.mappers import to_screen
from domain.value_object.enums import ScreenStatus
from drivers.database.models.entities import ScreenModel

USER_ID = uuid4()


def test_screen_mapper_returns_domain_entity() -> None:
    now = datetime.now(UTC)
    model = ScreenModel(
        id=uuid4(),
        user_id=USER_ID,
        screen_code="SCR-1",
        name="Lobby",
        status="ACTIVE",
        created_at=now,
        updated_at=now,
    )

    screen = to_screen(model)

    assert screen.status is ScreenStatus.ACTIVE
    assert screen.screen_code == "SCR-1"
    assert screen.user_id == USER_ID
