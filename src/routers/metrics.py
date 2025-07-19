# Metric feed – Every Device exposes at least
# one metric; the API must return the latest
# value together with metadata (timestamp,
# unit).
# R3: Latest Metric
import uuid
from datetime import datetime

import faker
from fastapi import Depends, status, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.dependencies import UserClaims, decode_jwt_token
from src.models import DeviceMetrics, Devices, Sites, METRIC_TYPE_TO_UNIT, Subscription
from src.routers.router_model import MetricResponse, CreateSubscriptionRequest, TimeSeriesResponse, MetricStatusCodeResponse
from src.routers.users import router


@router.get("/devices/{device_id}/metrics/latest")
async def get_latest_metric(device_id: uuid.UUID, metric_type: str, user: UserClaims = Depends(decode_jwt_token),
                            db: AsyncSession = Depends(get_db)):
    if user.access_level != "technical":
        return status.HTTP_401_UNAUTHORIZED

    result = await db.execute(
        select(DeviceMetrics).where(
            DeviceMetrics.device_id == device_id,
            func.lower(DeviceMetrics.metric_type) == metric_type.lower(),
            DeviceMetrics.device_id.in_(
                select(Devices.id).where(Devices.site_id.in_(select(Sites.id).where(Sites.user_id == uuid.UUID(user.id))))
            )
        ).order_by(DeviceMetrics.time.desc()).limit(1)
    )
    metric = result.scalars().first()
    if not metric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"given metrics for device {device_id} was not found")

    unit = METRIC_TYPE_TO_UNIT[metric_type.upper()].value
    return MetricResponse(time=metric.time,
                          metric_type=metric.metric_type,
                          value=metric.value,
                          unit=unit)


# R4: Metric Subscription (Streaming)
@router.post("/subscriptions",
             response_model=MetricResponse)
async def create_subscriptions(
        request: CreateSubscriptionRequest,
        user: UserClaims = Depends(decode_jwt_token),
        db: AsyncSession = Depends(get_db)
):

    device_query = select(Devices).join(Sites).where(
        Devices.id.in_(request.device_ids),
        Sites.user_id == uuid.UUID(user.id)
    )
    result = await db.execute(device_query)
    valid_devices = result.scalars().all()
    valid_device_ids = {device.id for device in valid_devices}

    if len(valid_device_ids) != len(request.device_ids):
        invalid_device_ids = set(request.device_ids) - valid_device_ids
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Didn't find valid device_id: {list[invalid_device_ids]} for subscription")

    # Check for existing subscriptions to avoid duplicates
    existing_query = select(Subscription).where(
        Subscription.device_id.in_(request.device_ids),
        Subscription.metric_type.in_(request.metric_types)
    )
    existing_result = await db.execute(existing_query)
    existing_subscriptions = existing_result.scalars().all()
    existing_pairs = {(sub.device_id, sub.metric_type) for sub in existing_subscriptions}

    # Create only new subscriptions
    new_subscriptions = []
    for device_id in request.device_ids:
        for metric_type in request.metric_types:
            if (device_id, metric_type) not in existing_pairs:
                subscription = Subscription(
                    id=uuid.uuid4(),
                    device_id=device_id,
                    metric_type=metric_type,
                    created_at=datetime.utcnow()
                )
                new_subscriptions.append(subscription)
                db.add(subscription)

    if not new_subscriptions:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Subscription already exist")

    await db.commit()

    # Refresh to get created_at values
    for subscription in new_subscriptions:
        await db.refresh(subscription)

    return MetricStatusCodeResponse(status_code=status.HTTP_200_OK, details="Subscription was created")


# # R5: Time-Series Endpoint
@router.get("/subscriptions/{subscription_id}/time-series")
async def get_time_series(
        subscription_id: uuid.UUID,
        start_time: datetime,
        end_time: datetime,
        user: UserClaims = Depends(decode_jwt_token),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Subscription).where(
            Subscription.id == subscription_id,
                        Subscription.user_id == user.user_id)
    )
    subscription = result.scalars().first()
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
