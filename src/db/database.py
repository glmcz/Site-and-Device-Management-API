from collections.abc import AsyncGenerator

from loguru import logger
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.config import app_config
from src.db.devices_repository import SQLAlchemyDevices
from src.db.metrics_repository import SQLAlchemyMetrics
from src.db.repository import DevicesRepository, MetricsRepository, SitesRepository
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.site_repository import SQLAlchemySites

engine = create_async_engine(
    app_config.dns,
    future=True,
    echo=True,
)

AsyncSessionFactory = async_sessionmaker(
    engine,
    autoflush=False,
    expire_on_commit=False,
)


class RepositoryContainer:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._devices_repo: DevicesRepository | None = None
        self._metrics_repo: MetricsRepository | None = None
        self._sites_repo: SitesRepository | None = None

    @property
    def devices(self) -> DevicesRepository:
        if self._devices_repo is None:
            self._devices_repo = SQLAlchemyDevices(self._session)
        return self._devices_repo


    @property
    def metrics(self) -> MetricsRepository:
        if self._metrics_repo is None:
            self._metrics_repo = SQLAlchemyMetrics(self._session)
        return self._metrics_repo


    @property
    def sites(self) -> SitesRepository:
        if self._sites_repo is None:
            self._sites_repo = SQLAlchemySites(self._session)
        return self._sites_repo


async def get_db() -> AsyncGenerator[RepositoryContainer| None]:
    async with AsyncSessionFactory() as session:
        logger.debug(f"ASYNC Pool: {engine.pool.status()}")
        try:
            yield RepositoryContainer(session)
        except Exception as e:
            logger.error(f"Error getting database session: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

