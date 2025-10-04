import newrelic.agent
newrelic.agent.initialize("newrelic.ini")

from app.core.newrelic_logger import logger

from contextlib import asynccontextmanager
from fastapi import FastAPI
# from loguru import logger

from app.core.config import settings
from app.api.websocket import router as websocket_router
from app.core.mongodb_init import init_mongodb
from app.core.mongodb_client import close_mongodb_connection

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up the app")
    try:
        await init_mongodb()
        yield
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB: {e}")
        raise

    logger.info("Shutting down the app")
    await close_mongodb_connection()


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.include_router(websocket_router)

@app.get('/health')
async def health_check():
    logger.info("Health check called")
    return {
        "status": "ok",
        "project": settings.PROJECT_NAME
    }
