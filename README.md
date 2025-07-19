# Site and Device Management API

## Overview
A FastAPI-based API for managing sites, devices, metrics, and subscriptions, using TimescaleDB for persistence. Supports JWT-based authentication with role-based access (technical users for CRUD, all users for read-only).

## Setup
1. Download uv and make venv
    ```bash
    curl -Ls https://astral.sh/uv/install.sh | bash
    uv venv
    source .venv/bin/activate
    uv sync
    uv sync --dev  
    ```
2. Start TimescaleDB and app: `./run_postgresql_timescaledb.sh`
3. Run tests: `pytest tests/test_api.py -v`

## Design Decisions
- **RESTful Endpoints**: Separate endpoints for sites, devices, metrics, and subscriptions for clarity and maintainability.
- **JWT Authentication**: Tokens encode `user_id` and `access_level` to enforce permissions.
- **Async SQLAlchemy**: For non-blocking database operations with TimescaleDB.
- **Pydantic Models**: For strict validation and OpenAPI documentation.
- **Mocked Tests**: Unit tests mock database interactions to ensure isolation.

## API Endpoints
- `GET /sites`: List sites for the authenticated user.
- `GET /sites/{site_id}`: Get site details.
- `POST /devices`: Create a device (technical only).
- `PUT /devices/{device_id}`: Update a device (technical only).
- `DELETE /devices/{device_id}`: Delete a device (technical only).
- `GET /devices/{device_id}`: Get device details.
- `GET /devices/{device_id}/metrics/latest`: Get latest metric.
- `POST /subscriptions`: Create a subscription.
- `GET /subscriptions/{subscription_id}/time-series`: Get mocked time-series data.

## Testing
Run `uv run pytest` to execute unit tests, which mock database interactions using `AsyncMock`.