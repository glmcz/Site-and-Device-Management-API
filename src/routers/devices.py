import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi import status
from src.dependencies import decode_jwt_token, UserClaims
from src.db.database import get_db, RepositoryContainer

from src.routers.router_model import DeviceRequest, DeviceResponse

devices_router = APIRouter()


# @router.post("/users/")
# async def insert_user(
#     user: UserClaims = Depends(decode_jwt_token),
#     db: AsyncSession = Depends(get_db)
# ):
#     db.add(user)
#     await db.commit()
#     await db.refresh(Users)
#     return status.HTTP_200_OK

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


# DEVICES ***************
@devices_router.post("/devices",
                     response_model=DeviceResponse)
async def create_device(payload: DeviceRequest, user: UserClaims = Depends(decode_jwt_token), db: RepositoryContainer = Depends(get_db)):
    if user.access_level != "technical":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Don't have technical status")

    dict_payload = payload.model_dump(exclude_unset=True)
    result = await db.devices.create_device(site_id=payload.site_id, device=dict_payload)
    if not result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="site not found")

    return DeviceResponse(status=status.HTTP_200_OK, msg="Device was created")


@devices_router.put("/devices/{device_id}",
                    response_model=DeviceResponse)
async def update_device(device_id: uuid.UUID, payload: DeviceRequest, user: UserClaims = Depends(decode_jwt_token), db: RepositoryContainer = Depends(get_db)):
    if user.access_level != "technical":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Don't have technical status")

    dict_payload = payload.model_dump(exclude_unset=True, exclude={'id'})
    device = await db.devices.update_device(device_id=device_id, updated_device=dict_payload)

    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="device was not found")
    return DeviceResponse(status=status.HTTP_200_OK, msg="Device was updated")


@devices_router.delete("/devices/{device_id}",
                       response_model=DeviceResponse)
async def delete_device(
        device_id: uuid.UUID,
        user: UserClaims = Depends(decode_jwt_token),
        db: RepositoryContainer = Depends(get_db)
):
    if user.access_level != "technical":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Don't have technical status")

    device = await db.devices.delete_device(device_id=device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="device was not found")

    return DeviceResponse(status=status.HTTP_200_OK, msg="Device was deleted")
