import uuid
from datetime import datetime
from pydantic import BaseModel, field_serializer, Field


class UserClaims(BaseModel):
    user_id: uuid.UUID
    access_level: str

class SiteResponse(BaseModel):
    public_id: uuid.UUID = Field(alias='id')
    name: str

    @field_serializer('public_id')
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)[:8]

    model_config = {"from_attributes": True}


class DeviceRequest(BaseModel):
    id: uuid.UUID | None = None
    name: str
    site_id: uuid.UUID | None = None
    type: str | None = None


class DeviceFullResponse(BaseModel):
    public_device_id: uuid.UUID = Field(alias="id")
    name: str
    public_site_id: uuid.UUID = Field(alias="site_id")
    type: str

    @field_serializer('public_id')
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)[:8]

    @field_serializer('public_site_id')
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)[:8]

    model_config = {"from_attributes": True}


class DeviceResponse(BaseModel):
    status: int
    msg: str

    model_config = {"from_attributes": True}


class MetricStatusCodeResponse(BaseModel):
    status: int
    msg: str

class MetricResponse(BaseModel):
    time: datetime
    metric_type: str
    value: float
    unit: str = "unknown"

class SubscriptionCreate(BaseModel):
    metric_types: list[str]
    device_ids: list[uuid.UUID]

class SubscriptionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    metric_type: str
    device_id: uuid.UUID

class TimeSeriesResponse(BaseModel):
    time: datetime
    value: float


class CreateSubscriptionRequest(BaseModel):
    device_ids: list[uuid.UUID]
    metric_types: list[str]


class SubscriptionResponse(BaseModel):
    id: uuid.UUID
    device_id: uuid.UUID
    metric_type: str
    created_at: datetime


class TimeSeriesResponse(BaseModel):
    device_id: uuid.UUID
    metric_type: str
    data: list
    start_time: datetime
    end_time: datetime
    count: int