import uuid
from datetime import datetime
import faker
from fastapi import APIRouter, Depends
from fastapi import status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import decode_jwt_token, UserClaims
from src.db.database import get_db
from src.models import Sites, Devices, DeviceRequest, DeviceMetrics, MetricResponse, METRIC_TYPE_TO_UNIT, Users, \
    CreateDevice, Subscription, CreateSubscriptionRequest, TimeSeriesResponse


router = APIRouter()


@router.post("/users/")
async def insert_user(
    user: UserClaims = Depends(decode_jwt_token),
    db: AsyncSession = Depends(get_db)
):
    db.add(user)
    await db.commit()
    await db.refresh(Users)
    return status.HTTP_200_OK

#
# @router.put("/users/{id}")
# async def update_user(
#     current_user: UserClaims = Depends(decode_jwt_token),
#     db: AsyncSession = Depends(get_db)
# ):
#     #update device info
#     return status.HTTP_200_OK
#
# #

@router.get("/sites")
async def get_sites(
    user: UserClaims = Depends(decode_jwt_token),
    db: AsyncSession = Depends(get_db)
):
    # get all sites attached to user
    result = await db.execute(select(Sites).where(Sites.user_id == uuid.UUID(user.id)))
    sites = result.scalars().fetchall() # returns site as tuple[0]
    if not sites:
        return status.HTTP_404_NOT_FOUND
    return sites

@router.get("/sites/{site_id}")
async def get_site(
    site_id: uuid.UUID,
    user: UserClaims = Depends(decode_jwt_token),
    db: AsyncSession = Depends(get_db)
):
    # more detailed data about requested site
    result = await db.execute(select(Sites).where(Sites.id == site_id, Sites.user_id == uuid.UUID(user.id)))
    site = await result.first()
    if not site:
        return status.HTTP_404_NOT_FOUND
    return site


# DEVICES ***************
@router.post("/devices",)
async def create_device(payload: CreateDevice, user: UserClaims = Depends(decode_jwt_token), db: AsyncSession = Depends(get_db)):
    if user.access_level != "technical":
        return status.HTTP_401_UNAUTHORIZED

    # first() has to be called after await...
    site = (await db.scalars(select(Sites).filter_by(id=payload.site_id))).first()
    if not site:
        return status.HTTP_400_BAD_REQUEST # site not found
    # Create device
    device = Devices(name=payload.name, site_id=payload.site_id, type=payload.type)
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return status.HTTP_200_OK



@router.put("/devices/{device_id}")
async def update_device(device_id: uuid.UUID, payload: DeviceRequest, user: UserClaims = Depends(decode_jwt_token), db: AsyncSession = Depends(get_db)):
    if user.access_level != "technical":
        return status.HTTP_401_UNAUTHORIZED

    device = await db.get(Devices, device_id)
    if not device:
        return status.HTTP_404_NOT_FOUND # device not found

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(device, key, value)

    await db.commit()
    await db.refresh(device)

    return status.HTTP_200_OK


@router.delete("/devices/{device_id}")
async def delete_device(
        device_id: uuid.UUID,
        user: UserClaims = Depends(decode_jwt_token),
        db: AsyncSession = Depends(get_db)
):
    if user.access_level != "technical":
        return status.HTTP_401_UNAUTHORIZED

    device = await db.get(Devices, device_id)
    if not device:
        return status.HTTP_404_NOT_FOUND

    await db.delete(device)
    await db.commit()
    await db.refresh(device)

    return status.HTTP_200_OK



# Metric feed – Every Device exposes at least
# one metric; the API must return the latest
# value together with metadata (timestamp,
# unit).
# R3: Latest Metric
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
        return status.HTTP_404_NOT_FOUND

    unit = METRIC_TYPE_TO_UNIT[metric_type.upper()].value
    return MetricResponse(time=metric.time,
                          metric_type=metric.metric_type,
                          value=metric.value,
                          unit=unit)


# R4: Metric Subscription (Streaming)
@router.post("/subscriptions")
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
        return status.HTTP_404_NOT_FOUND

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
        return status.HTTP_409_CONFLICT

    await db.commit()

    # Refresh to get created_at values
    for subscription in new_subscriptions:
        await db.refresh(subscription)

    return status.HTTP_200_OK


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
        return status.HTTP_404_NOT_FOUND


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
