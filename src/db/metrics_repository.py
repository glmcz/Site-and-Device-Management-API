import uuid
from datetime import datetime

from sqlalchemy import select, func
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import exc, Result

from src.db.repository import TimeSeriesQuery
from src.models import DeviceMetrics, Devices, Subscription


class SQLAlchemyMetrics:
    """ Specific impl of MetricsRepository interface"""

    def __init__(self, session: AsyncSession):
        self._session = session


    async def get_device_metric_last_values(self, device_id: uuid.UUID, metric_type: str | list[str], num_of_last_values: int=1) -> list[DeviceMetrics]:
        stmt = (
            select(DeviceMetrics)
            .where(
                DeviceMetrics.device_id == device_id,
                func.lower(DeviceMetrics.metric_type) == metric_type.lower()
            )
            .order_by(DeviceMetrics.time.desc())
            .limit(num_of_last_values)
        )

        result = await self._session.execute(stmt)
        scalars = result.scalars()
        return scalars.all()


    async def create_devices_subscriptions(self, device_ids: list[uuid.UUID], metric_types: list[str], existing_pairs:set[tuple[Any, Any]]) -> bool:
        for device_id in device_ids:
            for metric_type in metric_types:
                if (device_id, metric_type) not in existing_pairs:
                    subscription = Subscription(
                        id=uuid.uuid4(),
                        device_id=device_id,
                        metric_type=metric_type,
                        created_at=datetime.utcnow()
                    )
                    self._session.add(subscription)

        try:
            await self._session.commit()
        except exc.IntegrityError:
            await self._session.rollback()
            return False
        return True


    async def create_device_subscriptions(self, device_id: int, metric_type: str) -> bool:
        sub = Subscription(device_id=device_id, metric_type=metric_type, created_at=datetime.utcnow())
        self._session.add(sub)

        try:
            await self._session.commit()
            return True
        except exc.IntegrityError:
            await self._session.rollback()
            return False


    # return a list of subscription devices with metrics_types
    async def get_user_subscription(self, subscription_id: uuid.UUID) -> list[dict]:
        result = await self._session.execute(
            select(
                Devices.id,
                Devices.name,
                func.array_agg(func.distinct(DeviceMetrics.metric_type)).label('metric_types')
            )
            .join(Subscription, Devices.id == Subscription.device_id)
            .join(DeviceMetrics, Devices.id == DeviceMetrics.device_id)
            .where(Subscription.id == subscription_id)
            .group_by(Devices.id, Devices.name)
        )

        return [
            {
                'device_id': row.device_id,
                'device_name': row.device_name,
                'metric_types': row.metric_types
            }
            for row in result
        ]

    async def check_existing_subscription(self, device_ids: list[uuid.UUID], metric_types: [str]) -> list:
        stmt = select(Subscription).where(
            Subscription.device_id.in_(device_ids),
            Subscription.metric_type.in_(metric_types)
        )

        result: Result = await self._session.execute(stmt)
        return result.scalars().all()



    async def check_existing_subscription_by_id(self, subscription_id: uuid.UUID) -> bool:
        stmt = select(Subscription).where(Subscription.id == subscription_id)
        result: Result = await self._session.execute(stmt)
        if result.scalars().first():
            return True
        return False

    async def get_subscriptions_timeseries_data(self, subscription_ids: list[uuid.UUID], query: TimeSeriesQuery) -> list[dict]:
        ...


