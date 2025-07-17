from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI
import uvicorn
from loguru import logger

from .config import app_config
from .routers.users import router
app = FastAPI()

app.include_router(router)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        _app.postgres_pool = await asyncpg.create_pool(
            dsn=app_config.dns,
            min_size=5,
            max_size=20,
        )
        yield
    except Exception as e:
        logger.error(e)
    finally:
        await _app.postgres_pool.close()


if __name__ == "__main__":
    uvicorn.run(app)