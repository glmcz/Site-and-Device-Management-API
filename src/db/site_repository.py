import uuid
from select import select

from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Sites


class SQLAlchemySites:

    def __init__(self, session: AsyncSession):
        self._session = session


    async def get_user_site(self, site_id: uuid.UUID) -> [Sites | None]:
        result = await self._session.execute(select(Sites).where(Sites.id == site_id))
        site = result.first()
        return site


    async def get_all_user_sites(self, user_id: uuid.UUID, offset: int, limit: int) -> list[Sites] | None:
        result = await self._session.execute(select(Sites).where(Sites.user_id == user_id)).offset(offset).limit(limit)
        sites = result.scalars().all()
        return sites
