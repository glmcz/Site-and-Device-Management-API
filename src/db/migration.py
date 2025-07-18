import random
import uuid
from venv import logger

from sqlalchemy.ext.asyncio import AsyncSession

import faker

from src.db.database import get_db
from src.models import Sites, Devices, DeviceMetrics, DeviceType, Users
from datetime import datetime, timedelta

fake = faker.Faker()
METRIC_TYPES = ["power_output", "voltage", "current", "charge_level", "temperature"]

async def generate_random_users(session: AsyncSession, numb_of_users:int):
    users = []
    access_level = ["normal", "technic"]
    for _ in range(1, numb_of_users +1):
        user_id = uuid.uuid4()
        name = fake.name()
        access_level = random.choice(access_level)
        users.append(Users(id=user_id, name=name, access_level=access_level))
        session.add(Users(id=user_id, name=name, access_level=access_level))
    await session.commit()
    return users

async def generate_random_sites(session: AsyncSession, users:list):
    sites = []
    for user in users:
        site_id = uuid.uuid4()
        name = fake.address()
        sites.append(Sites(id=site_id, name=name, user_id=user.id))
        session.add(Sites(id=site_id, name=name, user_id=user.id))

    await session.commit()
    return sites

async def generate_random_devices(session: AsyncSession, sites:list):
    devices = []
    device_types = list(DeviceType)  #
    for site in sites:
        device_id = uuid.uuid4()
        name = fake.address()
        device_type = random.choice(list(device_types))
        devices.append(Devices(id=device_id, name=name, site_id=site.id, type=device_type.value))
        session.add(Devices(id=device_id, name=name, site_id=site.id, type=device_type.value))

    await session.commit()
    return devices

async def generate_random_metrics(session: AsyncSession, devices:list):
    metrics = []
    now = datetime.now()
    for device in devices:
        metric_type = random.choice(METRIC_TYPES)
        value = random.uniform(0.0, 100.0)
        random_datetime = now - timedelta(minutes=random.randint(0, 10800))
        metrics.append(DeviceMetrics(time=random_datetime, device_id=device.id, metric_type=metric_type, value=value))
        session.add(DeviceMetrics(time=random_datetime, device_id=device.id, metric_type=metric_type, value=value))

    await session.commit()


async def seed_database():
    async for session in get_db():
        try:
            users = await generate_random_users(session, numb_of_users=50)

            sites = await generate_random_sites(session, users=users)

            devices = await generate_random_devices(session, sites=sites)

            await generate_random_metrics(session, devices=devices)

        except Exception as e:
            logger.error(e)
            await session.rollback()



if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_database())