from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

import src.main
from src.db.database import get_db
from loguru import logger

@src.main.app.get("/metrics")
def stream_metrics(db : AsyncSession = Depends(get_db)):
    try:
        pass
    except Exception as e:
        logger.error(e)
    # directly stream metrics from device to subscribed users and also save result in db
    pass