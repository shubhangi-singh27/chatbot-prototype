import uuid
#from loguru import logger
from app.core.newrelic_logger import logger
from typing import Optional
from app.core.redis_client import redis_client

class SessionManager:
    """Manages customer chat sessions stored in Redis."""

    SESSION_PREFIX = "session:"
    EXPIRY_SECONDS = 300    # 5 minutes
    
    async def create_session(self, customer_id: str|None = None) -> dict:
        """
        Create a new session for the given customer_id.
        Returns session metadata as a dict.
        """

        try:
            session_id = str(uuid.uuid4())
            key = f"{self.SESSION_PREFIX}{session_id}"

            await redis_client.hset(key, mapping={"customer_id": customer_id})
            await redis_client.expire(key, self.EXPIRY_SECONDS)

            log = logger.bind(session_id=session_id, customer_id=customer_id)
            log.info("Created new session")

            return {"session_id": session_id, "customer_id": customer_id}
        except Exception as e:
            logger.bind(customer_id=customer_id).error(f"Failed to create session: {e}")
            raise

        
    async def get_customer_id(self, session_id: str) -> str|None:
        """Retrieve the customer_id for a given session_id."""
        
        key = f"{self.SESSION_PREFIX}{session_id}"
        try:
            customer_id = await redis_client.hget(key, "customer_id")
            if customer_id:
                customer_id = customer_id.decode("utf-8") if isinstance(customer_id, bytes) else customer_id
                logger.bind(session_id=session_id, customer_id=customer_id).info("Fetched customer_id from session")
                return customer_id
            return None
        except Exception as e:
            logger.bind(session_id=session_id).error(f"Failed to get customer id: {e}")
            return None
    
    async def end_session(self, session_id: str) -> bool:
        """End a session and remove it from Redis."""

        key = f"{self.SESSION_PREFIX}{session_id}"

        try:
            result = await redis_client.delete(key)
            log = logger.bind(session_id=session_id)

            if result:
                log.info(f"Ended session")
            else:
                log.warning(f"Tried to end non-existing session")
            return bool(result)
        except Exception as e:
            logger.bind(session_id=session_id).error(f"Failed to end session: {e}")    
            return False

    async def refresh_session(self, session_id: str) -> bool:
        """Refresh TTL of an active session."""

        key = f"{self.SESSION_PREFIX}{session_id}"

        try:
            result = await redis_client.expire(key, self.EXPIRY_SECONDS)
            log = logger.bind(session_id=session_id)

            if result:
                log.info(f"Refreshed session")
            else:
                log.warning(f"Tried to refreshing a non-existing session")
            return bool(result)
        except Exception as e:
            logger.bind(session_id=session_id).error(f"Failed to refresh session: {e}")
            return False