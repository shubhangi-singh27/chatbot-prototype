from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from loguru import logger

client: AsyncIOMotorClient | None = None
db = None

async def connect_to_mongo():
    """
    Create a MongoDB client and assign database reference.
    """
    global client, db
    client = AsyncIOMotorClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
    db = client[settings.MONGODB_DB]
    logger.info(f"Connected to MongoDB at {settings.MONGODB_URI}, using DB: {settings.MONGODB_DB}")

async def close_mongodb_connection():
    global client
    if client:
        client.close()
        logger.info(f"Mongo DB connection closed")