"""Reusable HTTP workflows shared by end-to-end tests."""

import httpx

from domain.value_object import PairingSessionStatus, PairingType


async def create_paired_screen(
    client: httpx.AsyncClient,
    *,
    name: str = "End-to-end TV",
) -> dict[str, object]:
    pairing_sessions_url = "/api/v1/pairing/sessions"
    created = await client.post(
        pairing_sessions_url,
        json={"pairing_type": PairingType.NEW_SCREEN.value},
    )
    assert created.status_code == 201
    session_id = str(created.json()["session_id"])
    token = str(created.json()["pairing_token"])
    headers = {"Authorization": "Bearer valid-access-token", "X-Pairing-Token": token}

    approved = await client.post(
        f"{pairing_sessions_url}/approve",
        headers=headers,
        json={},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == PairingSessionStatus.CONNECTING.value

    response = await client.post(
        f"{pairing_sessions_url}/{session_id}/screen",
        headers=headers,
        json={"name": name, "device_model": "E2E model", "app_version": "1.0.0"},
    )
    assert response.status_code == 201
    return response.json()
