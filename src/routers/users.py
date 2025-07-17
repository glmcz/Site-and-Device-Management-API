import uuid
from fastapi import APIRouter, Depends
from fastapi import status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import decode_jwt_token, UserClaims
from src.db.database import get_db
from src.models import Sites, Devices, DeviceRequest, DeviceMetrics, MetricResponse, METRIC_UNITS, Users, SiteResponse, \
    CreateDevice

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
    return site


# DEVICES ***************
@router.post("/devices",)
async def create_device(payload: CreateDevice, user: UserClaims = Depends(decode_jwt_token), db: AsyncSession = Depends(get_db)):
    if user.access_level != "technical":
        return status.HTTP_401_UNAUTHORIZED

    # first() has to be called after await...
    site = (await db.scalars(select(Sites).filter_by(id=payload.site_id))).first()
    if not site:
        raise status.HTTP_400_BAD_REQUEST # site not found
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
        raise status.HTTP_400_BAD_REQUEST # device not found

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
        raise status.HTTP_400_BAD_REQUEST

    await db.delete(device)
    await db.commit()
    await db.refresh(device)

    return status.HTTP_200_OK



# Metric feed – Every Device exposes at least
# one metric; the API must return the latest
# value together with metadata (timestamp,
# unit).
# R4 Metric sub
# R3: Latest Metric
@router.get("/devices/{device_id}/metrics/latest")
async def get_latest_metric(device_id: uuid.UUID, metric_type: str, user: UserClaims = Depends(decode_jwt_token),
                            db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DeviceMetrics).where(
            DeviceMetrics.device_id == uuid.UUID(device_id),
            func.lower(DeviceMetrics.metric_type) == metric_type.lower(),
            DeviceMetrics.device_id.in_(
                select(Devices.id).where(Devices.site_id.in_(select(Sites.id).where(Sites.user_id == uuid.UUID(ser.id))))
            )
        ).order_by(DeviceMetrics.time.desc()).limit(1)
    )
    metric = result.scalars().first()
    if not metric:
        raise status.HTTP_400_BAD_REQUEST

    unit = METRIC_UNITS(metric_type)
    return MetricResponse(time=metric.time,
                          metric_type=metric.metric_type,
                          value=metric.value,
                          unit=unit)


# R4: Metric Subscription (Streaming)
# @app.websocket("/subscriptions/stream")
# async def metric_subscription_stream(websocket: WebSocket, token: str, db: AsyncSession = Depends(get_db)):
#     user = await get_current_user(token)
#     await stream_metrics(websocket, user.user_id, db)
#
#
# @app.post("/subscriptions", status_code=201, response_model=None)
# async def create_subscription(
#         subscription: SubscriptionCreate,
#         user: UserClaims = Depends(get_current_user),
#         db: AsyncSession = Depends(get_db)
# ):
#     for device_id in subscription.device_ids:
#         result = await db.execute(
#             select(Device).where(Device.id == device_id, Device.site_id.in_(
#                 select(Site.id).where(Site.user_id == user.user_id)
#             ))
#         )
#         if not result.scalars().first():
#             raise HTTPException(status_code=404, detail=f"Device {device_id} not found or unauthorized")
#         for metric_type in subscription.metric_types:
#             await db.execute(
#                 insert(Subscription).values(
#                     id=uuid4(),
#                     user_id=user.user_id,
#                     metric_type=metric_type,
#                     device_id=device_id
#                 )
#             )
#     await db.commit()
#     return None
#
#
# # R5: Time-Series Endpoint
# @app.get("/subscriptions/{subscription_id}/time-series", response_model=List[TimeSeriesResponse])
# async def get_time_series(
#         subscription_id: UUID,
#         start_time: datetime,
#         end_time: datetime,
#         user: UserClaims = Depends(get_current_user),
#         db: AsyncSession = Depends(get_db)
# ):
#     result = await db.execute(
#         select(Subscription).where(Subscription.id == subscription_id, Subscription.user_id == user.user_id)
#     )
#     subscription = result.scalars().first()
#     if not subscription:
#         raise HTTPException(status_code=404, detail="Subscription not found or unauthorized")
#
#     # Fetch real time-series data from device_metrics
#     result = await db.execute(
#         select(DeviceMetric.time, DeviceMetric.value).where(
#             DeviceMetric.device_id == subscription.device_id,
#             DeviceMetric.metric_type == subscription.metric_type,
#             DeviceMetric.time >= start_time,
#             DeviceMetric.time <= end_time
#         ).order_by(DeviceMetric.time)
#     )
#     metrics = result.all()
#     return [TimeSeriesResponse(time=m.time, value=m.value) for m in metrics]
