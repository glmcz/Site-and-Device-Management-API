from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient, ASGITransport

from src.main import app
from src.dependencies import UserClaims, decode_jwt_token
from src.models import Sites
from test.test_db import technical_user, site_id, mock_db_session, override_get_db, override_decode_jwt_token_technical



@pytest.mark.asyncio
async def test_standart_user_access(override_get_db, mock_db_session):
    mock_site = Sites(id=site_id, name="Test Site", user_id=technical_user.id)
    mock_db_session.scalars.return_value.all.return_value = [mock_site]

    user_claims = UserClaims("user_name", "normal", {"msg":"nothing so"})
    token = generate_token(user_claims)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        res = await async_client.get("/sites", headers={"Authorization": f"Bearer {token}"})
        res_payload = res.json()
        assert res.status_code == 200
        assert res_payload["payload"]["msg"] == "nothing so"


def test_invalid_jwt_token():
    headers = {"Authorization": f"Bearer InvalidToken"}
    res = client.get("/users", headers=headers)
    assert res.status_code == 401

def test_technical_user_access():
    user_claims = UserClaims("user_name", "technical",  {"msg":"it works"})
    token = generate_token(payload=user_claims)
    headers = { "Authorization": f"Bearer {token}"}
    res = client.get("/users", headers=headers)
    assert res.status_code == 200
    res_payload = res.json()
    assert res_payload["payload"]["msg"] == "it works"


def test_technical_requests():
    user_claims_create = UserClaims("user_name", "technical", {"create": "device_name"})
    token_create_device = generate_token(payload=user_claims_create)
    user_claims_update = UserClaims("user_name", "technical", {"update": "{device_name: updated_name}"})
    token_update_device = generate_token(payload=user_claims_update)
    user_claims_delete = UserClaims("user_name", "technical", {"delete": "device_name"})
    token_delete_device = generate_token(payload=user_claims_delete)

    headers = {"Authorization": f"Bearer {token_create_device}"}
    res = client.get("/users", headers=headers)
    res_payload = res.json().get("payload")
    assert res.status_code == 200
    assert res_payload.get("res") == "device_name was created"

    headers = {"Authorization": f"Bearer {token_update_device}"}
    res = client.get("/users", headers=headers)
    res_payload = res.json().get("payload")
    assert res.status_code == 200
    assert res_payload.get("res") == "device_name was updated"

    headers = {"Authorization": f"Bearer {token_delete_device}"}
    res = client.get("/users", headers=headers)
    res_payload = res.json().get("payload")
    assert res.status_code == 200
    assert res_payload.get("res") == "device_name was deleted"

