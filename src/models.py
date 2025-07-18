from enum import Enum
from sqlalchemy import Column, String, UUID, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from datetime import datetime
import uuid

# DB models
Base = declarative_base()

class METRIC_TYPE_TO_UNIT(Enum):
    POWER_OUTPUT = "W"
    VOLTAGE = "V"
    CURRENT = "A"
    CHARGE_LEVEL = "%"
    TEMPERATURE = "C"

class DeviceType(Enum):
    SOLAR_PANEL = "pv_panel"
    WIND_TURBINES = "wind_turbines"
    BATTERY = "battery"
    INVERTER = "inverter"

class Users(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100))
    access_level = Column(String(50))

class Sites(Base):
    __tablename__ = "sites"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # References Users.user_id

class Devices(Base):
    __tablename__ = "devices"
    id = Column(UUID, primary_key=True)
    name = Column(String(100), nullable=False)
    site_id = Column(UUID, ForeignKey("sites.id"), nullable=False)
    type = Column(String(100), nullable=False)

# hyper table
class DeviceMetrics(Base):
    __tablename__ = "device_metrics"
    time = Column(DateTime(timezone=True), primary_key=True)
    device_id = Column(UUID(as_uuid=True), primary_key=True)
    metric_type = Column(String(100), primary_key=True)
    value = Column(Float)

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(UUID, primary_key=True)
    device_id = Column(UUID, ForeignKey("devices.id"), nullable=False)
    metric_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# Response models
# Pydantic Models
class UserClaims(BaseModel):
    user_id: uuid.UUID
    access_level: str

class SiteResponse(BaseModel):
    name: list[str]


class CreateDevice(BaseModel):
    name: str
    site_id: uuid.UUID
    type: str

class DeviceRequest(BaseModel):
    id: uuid.UUID
    name: str
    site_id: uuid.UUID
    type: str


class DeviceResponse(BaseModel):
    id: uuid.UUID
    name: str
    site_id: uuid.UUID
    type: str

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


# Pydantic models for request/response
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
