import uuid
from sqlalchemy import select, delete, Result
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Devices, Sites
from src.routers.router_model import DeviceResponse, DeviceFullResponse


class SQLAlchemyDevices:
    """ Specific impl of DevicesRepository interface"""


    def __init__(self, session: AsyncSession):
        self._session = session


    async def create_device(self, site_id: uuid.UUID, device: dict[str, Any]) -> bool:
        result = await self._session.execute(select(Sites).where(Sites.id == site_id))
        site = result.first()

        if not site:
            return False

        device['site_id'] = site.id
        new_device = Devices(**device)

        self._session.add(new_device)
        await self._session.commit()
        await self._session.refresh(new_device)
        return True

    async def get_device(self, device_id: uuid.UUID) -> Devices | None:
        result = await self._session.execute(select(Devices).where(Devices.id==device_id))
        device_model = result.scalar_one_or_none()
        return self._to_domain(device_model) if device_model else None

    async def update_device(self, device_id: uuid.UUID, updated_device: dict[str, Any]) -> bool:
        result = await self._session.execute(select(Devices).where(Devices.id == device_id))
        device_model = result.scalar_one_or_none()
        if not device_model:
            return False

        for k, v in updated_device.items():
            setattr(device_model, k, v)

        await self._session.commit()
        await self._session.refresh(Devices)
        return True


    async def delete_device(self, device_id: uuid.UUID) -> bool:
        result = await self._session.execute(delete(Devices).where(Devices.id == device_id))
        await self._session.commit()
        return result.rowcount() > 0


    async def exist_device(self, user_id: uuid.UUID, device_ids: [uuid.UUID]) -> list:
        stmt = select(Devices).join(Sites).where(
            Devices.id.in_(device_ids),
            Sites.user_id == uuid.UUID(user_id)
        )

        result: Result = await self._session.execute(stmt)
        return result.scalars().all()

    def _to_domain(self, device_model) -> DeviceFullResponse:
        """Convert SQLAlchemy model to domain object"""
        return DeviceFullResponse(
            id=device_model.id,
            name=device_model.name,
            site_id=device_model.site_id,
            type=device_model.device_type
        )