# Metric feed – Every Device exposes at least
# one metric; the API must return the latest
# value together with metadata (timestamp,
# unit).
# R3: Latest Metric
import uuid
from datetime import datetime

import faker
from fastapi import Depends, status, HTTPException, APIRouter
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db, RepositoryContainer
from src.dependencies import UserClaims, decode_jwt_token
from src.models import DeviceMetrics, Devices, Sites, METRIC_TYPE_TO_UNIT, Subscription
from src.routers.router_model import MetricResponse, CreateSubscriptionRequest, TimeSeriesResponse, MetricStatusCodeResponse


metrics_router = APIRouter()

@metrics_router.get("/devices/{device_id}/metrics/latest",
                    response_model=MetricResponse)
async def get_latest_metric(device_id: uuid.UUID, metric_type: str, user: UserClaims = Depends(decode_jwt_token),
                            db: RepositoryContainer = Depends(get_db)):
    if user.access_level != "technical":
        return status.HTTP_401_UNAUTHORIZED

    metric = await db.metrics.get_metric_last_values(device_id, metric_type)
    if not metric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"given metrics for device {device_id} was not found")

    unit = METRIC_TYPE_TO_UNIT[metric_type.upper()].value
    return MetricResponse(time=metric.time,
                          metric_type=metric.metric_type,
                          value=metric.value,
                          unit=unit)


# R4: Metric Subscription (Streaming)
@metrics_router.post("/subscriptions",
                   response_model=MetricResponse)
async def create_subscriptions(
        request: CreateSubscriptionRequest,
        user: UserClaims = Depends(decode_jwt_token),
        db: RepositoryContainer = Depends(get_db)
):

    valid_devices = await db.devices.check_exist_user_devices(user_id=uuid.UUID(user.id), device_ids=request.device_ids)
    valid_device_ids = {device.id for device in valid_devices}

    if len(valid_device_ids) != len(request.device_ids):
        invalid_device_ids = set(request.device_ids) - valid_device_ids
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Didn't find valid device_id: {list[invalid_device_ids]} for subscription")


    # Check for existing subscriptions to avoid duplicates
    existing_subscriptions = await db.metrics.check_existing_subscription(device_ids=request.device_ids, metric_types=request.metric_types)
    existing_pairs = {(sub.device_id, sub.metric_type) for sub in existing_subscriptions}

    # Create only new subscriptions
    new_subscriptions = []

    if not new_subscriptions:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Subscription already exist")

    await db.metrics.create_devices_subscriptions(device_ids=request.device_ids, metric_types=request.metric_types, existing_pairs=existing_pairs)
    return MetricStatusCodeResponse(status_code=status.HTTP_200_OK, details="Subscription was created")


# # R5: Time-Series Endpoint
@metrics_router.get("/subscriptions/{subscription_id}/time-series")
async def get_time_series(
        subscription_id: uuid.UUID,
        start_time: datetime,
        end_time: datetime,
        user: UserClaims = Depends(decode_jwt_token),
        db: RepositoryContainer = Depends(get_db)
):

    subscription = await db.metrics.check_existing_subscription_by_id(subscription_id=subscription_id)
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription was not created so far. Do it first")


    fake = faker.Faker()
    time_diff = end_time - start_time
    hours = max(1, int(time_diff.total_seconds() / 3600))
    limit = min(100, hours)

    metric_ranges = {
        "temperature": (15.0, 35.0),
        "humidity": (30.0, 80.0),
        "pressure": (980.0, 1040.0),
        "voltage": (220.0, 240.0),
        "current": (1.0, 10.0),
        "power_output": (0.0, 100.0),
        "charge_level": (0.0, 100.0)
    }

    min_val, max_val = metric_ranges.get(subscription.metric_type, (0.0, 100.0))

    data = []
    for _ in range(limit):
        value = fake.pyfloat(min_value=min_val, max_value=max_val, right_digits=2)
        data.append(value)

    return TimeSeriesResponse(
        device_id=subscription.device_id,
        metric_type=subscription.metric_type,
        data= data,
        start_time= start_time,
        end_time= end_time,
        count= limit,
    )
