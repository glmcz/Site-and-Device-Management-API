import uuid
from dataclasses import asdict
from datetime import datetime
from unittest.mock import Mock
from uuid import UUID
import jwt
import pytest
from asyncmock import AsyncMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.database import get_db
from src.main import app
from src.models import Sites, Devices
from src.dependencies import UserClaims, decode_jwt_token


site_id = UUID(int=3)
device_id = UUID(int=4)
subscription_id = UUID(int=5)
metric_time = datetime.now()
technical_user = UserClaims(str(uuid.uuid4()), "technical", None)
normal_user = UserClaims(str(uuid.uuid4()), "viewer", None)


def override_decode_jwt_token_technical():
    return technical_user

def override_decode_jwt_token():
    return normal_user


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session


# !!!!!!!!!
# If you make the fixture itself async (async def override_get_db()), pytest returns a coroutine object instead of executing the fixture,
@pytest.fixture
def override_get_db(mock_db_session):
    """Override the get_db dependency with mock session."""

    async def _get_db():
        yield mock_db_session

    app.dependency_overrides[get_db] = _get_db
    yield mock_db_session
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_site(override_get_db, mock_db_session):
    """Test listing sites endpoint."""
    mock_site = Sites(id=site_id, name="Test Site", user_id=technical_user.id)
    mock_db_session.execute = AsyncMock()
    mock_result = AsyncMock()
    mock_db_session.execute.return_value = mock_result
    mock_result.first.return_value = [mock_site]

    app.dependency_overrides[decode_jwt_token] = override_decode_jwt_token
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        response = await async_client.get(f"/sites/{site_id}")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_sites(override_get_db, mock_db_session):
    """Test listing sites endpoint."""
    mock_site = Sites(id=site_id, name="Test Site", user_id=technical_user.id)

    # scalar needs to be sync !!!!!!!!!!!!!!
    mock_scalars = Mock()
    mock_scalars.fetchall.return_value = [mock_site]

    mock_result = Mock()
    mock_result.scalars = Mock(return_value=mock_scalars)

    # Only the execute method should be async
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    app.dependency_overrides[decode_jwt_token] = override_decode_jwt_token
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        response = await async_client.get("/sites")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_device_technical(override_get_db, mock_db_session):
    mock_site = Sites(id=site_id, name="Test Site", user_id=technical_user.id)

    # Configure the mock to return the site when first() is called
    mock_scalars_result = AsyncMock()
    mock_scalars_result.first.return_value = mock_site
    mock_db_session.scalars.return_value = mock_scalars_result
    app.dependency_overrides[decode_jwt_token] = override_decode_jwt_token_technical


    payload = {"name": "Test Device", "site_id": str(site_id), "type": "pv_panel"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        response = await async_client.post("/devices", json=payload)
        assert response.status_code == 200
        mock_db_session.scalars.assert_called()
        mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_device_success(override_get_db):
    existing_device = Devices(
        id=device_id,
        name="Old Device Name",
        site_id=site_id,
        type="pv_panel"
    )

    # Mock the database responses
    override_get_db.get.return_value = existing_device
    payload = {
        "id": str(site_id), # TODO remove from model
        "name": "Updated Device Name",
        "site_id": str(site_id),
        "type" : "pv_panel",
    }
    app.dependency_overrides[decode_jwt_token] = override_decode_jwt_token_technical


    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        response = await async_client.put(
            f"/devices/{device_id}",
            json=payload
        )

        assert response.status_code == 200
        # response_data = response.json()
        # assert response_data["message"] == "Device updated successfully"
        # assert response_data["device"]["name"] == "Updated Device Name"
        # assert response_data["device"]["site_id"] == str(site_id)
        # assert response_data["device"]["type"] == "pv_panel"  # Unchanged

        # Verify database calls
        override_get_db.get.assert_called_once_with(Devices, device_id)
        override_get_db.commit.assert_called_once()
        override_get_db.refresh.assert_called_once_with(existing_device)



@pytest.mark.asyncio
async def test_delete_device_technical(override_get_db, mock_db_session):
    # Mock the site lookup to return a site (so it exists)
    existing_device = Devices(
        id=device_id,
        name="Old Device Name",
        site_id=site_id,
        type="pv_panel"
    )
    override_get_db.get.return_value = existing_device
    app.dependency_overrides[decode_jwt_token] = override_decode_jwt_token_technical

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        response = await async_client.delete(f"/devices/{device_id}")

        assert response.status_code == 200, f"Response: {response.text}"
        mock_db_session.commit.assert_called_once()
