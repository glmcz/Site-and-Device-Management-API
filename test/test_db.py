import uuid
from datetime import datetime
from uuid import UUID

import pytest
from asyncmock import AsyncMock
from httpx import AsyncClient, ASGITransport
from src.db.database import get_db
from src.main import app
from src.models import Sites, Devices, DeviceMetrics, METRIC_TYPE_TO_UNIT
from src.dependencies import UserClaims, decode_jwt_token
from src.routers.router_model import DeviceRequest

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
def test_client_with_repos():

    """Create a mock database session."""
    mocked_devices = AsyncMock()
    mocked_metrics = AsyncMock()
    mocked_sites = AsyncMock()

    mock_session = AsyncMock()
    mock_session.sites = mocked_sites
    mock_session.devices = mocked_devices
    mock_session.metrics = mocked_metrics

    async def _get_db():
        yield mock_session

    def override_auth():
        return technical_user

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[decode_jwt_token] = override_auth
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    yield client, mock_session

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_site(test_client_with_repos):
    """Test listing sites endpoint."""
    client, mock_repos = test_client_with_repos
    mock_site = Sites(id=site_id, name="Test Site", user_id=technical_user.id)
    mock_repos.sites.get_user_site.return_value = mock_site

    async with client as c:
        response = await c.get(f"/sites/{site_id}")
        assert response.status_code == 200
        site = Sites(**response.json())
        assert site.name == mock_site.name


@pytest.mark.asyncio
async def test_list_sites(test_client_with_repos):
    client, mock_db_session = test_client_with_repos
    """Test listing sites endpoint."""
    mock_site = Sites(id=site_id, name="Test Site", user_id=technical_user.id)

    # Only the execute method should be async
    mock_db_session.sites.get_all_user_sites.return_value = [mock_site]

    app.dependency_overrides[decode_jwt_token] = override_decode_jwt_token
    async with client as c:
        response = await c.get("/sites")
        assert response.status_code == 200
        response_data = response.json()
        sites = [Sites(**site_dict) for site_dict in response_data]
        assert sites[0].name == mock_site.name


@pytest.mark.asyncio
async def test_create_device_technical(test_client_with_repos):
    client, mock_db_session = test_client_with_repos

    mock_device = {"name": "Test Device", "site_id": str(site_id), "type": "pv_panel"}
    mock_db_session.devices.create_device.return_value = mock_device
    app.dependency_overrides[decode_jwt_token] = override_decode_jwt_token_technical

    async with client as c:
        response = await c.post("/devices", json=mock_device)
        assert response.status_code == 200
        value = response.json()
        assert value["msg"] == "Device was created"



@pytest.mark.asyncio
async def test_update_device_success(test_client_with_repos):
    client, mock_db_session = test_client_with_repos
    existing_device = {
        "id": str(device_id),
        "name": "Old Device Name",
        "site_id": str(site_id),
        "type": "pv_panel"
    }

    # Mock the database responses
    mock_db_session.devices.update_device.return_value = existing_device
    app.dependency_overrides[decode_jwt_token] = override_decode_jwt_token_technical
    async with client as c:
        response = await c.put(
            f"/devices/{device_id}",
            json=existing_device
        )

        assert response.status_code == 200
        value = response.json()
        assert value["msg"] == "Device was updated"



@pytest.mark.asyncio
async def test_delete_device_technical(test_client_with_repos):
    client, mock_db_session = test_client_with_repos

    mock_db_session.devices.delete_device.return_value = True
    app.dependency_overrides[decode_jwt_token] = override_decode_jwt_token_technical

    async with client as c:
        response = await c.delete(f"/devices/{device_id}")
        assert response.status_code == 200
        value = response.json()
        assert value["msg"] == "Device was deleted"


# test R3 metrics

@pytest.mark.asyncio
async def test_metric_last_value(test_client_with_repos):
    client, mock_db_session = test_client_with_repos
    existing_metrics = DeviceMetrics(
        time=datetime.now(),
        device_id = device_id,
        metric_type = str(METRIC_TYPE_TO_UNIT.CURRENT),
        value = 47.47
    )
    mock_db_session.metrics.get_metric_last_values.return_value = existing_metrics


    app.dependency_overrides[decode_jwt_token] = override_decode_jwt_token_technical
    payload = { "metric_type": "current"}
    async with client as c:
        response = await c.get(f"/devices/{device_id}/metrics/latest", params=payload)
        assert response.status_code == 200