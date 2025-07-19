import uuid
from fastapi import APIRouter, Depends
from fastapi import status
from fastapi.params import Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.dependencies import decode_jwt_token, UserClaims
from src.db.database import get_db
from src.models import Sites, Devices, Users

from src.routers.router_model import DeviceRequest, SiteResponse, DeviceResponse

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

@router.get(
    "/sites",
    response_model=list[SiteResponse],
    description="Return list of all site for given user",
    responses={
           "200": {"description":"List of all sites", "model": list[SiteResponse] },
           "401": {"description": "Invalid of missing JSON" },
        }
    )
async def get_sites(
    user: UserClaims = Depends(decode_jwt_token),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of sites to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of sites to return")
):
    # get all sites attached to user
    result = await db.execute(
        select(Sites).where(Sites.user_id == uuid.UUID(user.id)).offset(skip).limit(limit)
    )
    sites = result.scalars().all()
    return sites

@router.get("/sites/{site_id}",
            response_model=SiteResponse)
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
async def create_device(payload: DeviceRequest, user: UserClaims = Depends(decode_jwt_token), db: AsyncSession = Depends(get_db)):
    if user.access_level != "technical":
        return status.HTTP_401_UNAUTHORIZED

    # first() has to be called after await...
    site = (await db.scalars(select(Sites).filter_by(id=payload.site_id))).first()
    if not site:
        return status.HTTP_400_BAD_REQUEST, "site not found"
    # Create device
    device = Devices(name=payload.name, site_id=payload.site_id, type=payload.type)
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return DeviceResponse(status=status.HTTP_200_OK, msg="Device was created")



@router.put("/devices/{device_id}",
            response_model=DeviceResponse)
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

    return DeviceResponse(status=status.HTTP_200_OK, msg="Device was updated")


@router.delete("/devices/{device_id}",
               response_model=DeviceResponse)
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

    return DeviceResponse(status=status.HTTP_200_OK, msg="Device was deleted")
