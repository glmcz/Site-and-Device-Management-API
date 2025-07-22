import uuid
from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, TypeVar, Any

T = TypeVar('T')

@dataclass
class TimeSeriesQuery:
    """Query parameters for time-series data"""
    start_time: datetime | None = None
    end_time: datetime | None = None
    interval: str | None = None  # '1h', '1d', etc.
    aggregation: str | None = None  # 'avg', 'sum', 'max', 'min'

class SitesRepository(Protocol[T]):
    """ Base device interface"""

    @abstractmethod
    async def get_user_site(self, site_id: uuid.UUID) -> T:
        ...

    @abstractmethod
    async def get_all_user_sites(self, user_id: uuid.UUID, offset: int, limit: int) -> T:
        ...



class DevicesRepository(Protocol[T]):
    """ Base device interface"""

    @abstractmethod
    async def create_device(self, site_id: uuid.UUID, device: dict[str, Any]) -> bool:
        ...

    @abstractmethod
    async def get_device(self, device_id: uuid.UUID) -> T:
        ...

    @abstractmethod
    async def update_device(self, device_id: uuid.UUID, updated_device: dict[str, Any]) -> bool:
        ...

    @abstractmethod
    async def delete_device(self, device_id: uuid.UUID) -> bool:
        ...

    @abstractmethod
    async def check_exist_user_devices(self, user_id: uuid.UUID, device_ids: [uuid.UUID]) -> T:
        ...

class MetricsRepository(Protocol[T]):
    """ Base metrics interface"""


    @abstractmethod
    async def get_device_metric_last_values(self, device_id, metric_type: str | list[str], num_of_last_values: int) -> T:
        ...

    @abstractmethod
    async def create_device_subscriptions(self, device_id: uuid.UUID, metric_type: list[str] | str) -> T:
        ...

    @abstractmethod
    async def create_devices_subscriptions(self, device_ids: list[uuid.UUID], metric_types: list[str], existing_pairs:set[tuple[Any, Any]]) -> bool:
        ...

    @abstractmethod
    async def get_user_subscription(self, subscription_id: uuid.UUID) -> T:
        ...

    @abstractmethod
    async def check_existing_subscription(self, device_ids: list[uuid.UUID], metric_types: [str]) -> bool:
        ...

    @abstractmethod
    async def check_existing_subscription_by_id(self, subscription_id: uuid.UUID) -> bool:
        ...

    @abstractmethod
    async def get_subscription_timeseries_data(self, subscription_id: uuid.UUID, query: TimeSeriesQuery) -> T:
        ...

    @abstractmethod
    async def get_subscriptions_timeseries_data(self, subscription_ids: list[uuid.UUID], query: TimeSeriesQuery) -> [T]:
        ...




