from datetime import datetime, timezone
from app.core.redis_client import redis_client
from app.core.newrelic_logger import logger

class CompanyKBManager:
    """Manage Company wide KB stored in MongoDB and optionally Redis for session use"""
    COLLECTION = "company_kb"
    REDIS_PREFIX = "kb:company:"

    @property
    def collection(self):
        from app.core.mongodb_client import db
        if db is None:
            raise RuntimeError("MongoDB collection not initialized yet")
        return db[self.COLLECTION]

    async def upload_kb(self, company_id: str, kb_entries: str) -> None:
        """Save or update company KB in mongoDB"""
        now = datetime.now(timezone.utc)
        kb_text = "\n".join(kb_entries)

        await self.collection.update_one(
            {"_id": company_id},
            {"$set": {"kb_text": kb_text, "updated_at": now}},
            upsert = True
        )
        logger.bind(company_id=company_id).info("Company KB uploaded succesfully")

        # Redis cache
        redis_key = f"{self.REDIS_PREFIX}{company_id}"
        await redis_client.delete(redis_key)
        if kb_entries:
            await redis_client.rpush(redis_key, *kb_entries)
        logger.bind(company_id=company_id).info("Company KB uploaded to Redis for session use.")

    async def get_kb(self, company_id: str) -> str|None:
        """Fetch KB text for a company from MongoDB
        Priority: Redis cache -> MongoDB fallback"""

        redis_key = f"{self.REDIS_PREFIX}{company_id}"
        entries = await redis_client.lrange(redis_key, 0, -1)
        if entries:
            kb_text = "\n".join([e.decode("utf-8") if isinstance(e, bytes) else e for e in entries])
            logger.bind(company_id=company_id).info("Fetched company KB from Redis")
            return kb_text
        
        # Fallback to MongoDB
        doc = await self.collection.find_one({"_id": company_id})
        if doc:
            kb_text = doc.get("kb_text")
            logger.bind(company_id=company_id).info("Fetched company KB")
            return kb_text
        
        return None