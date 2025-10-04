import json
from typing import Dict, List
#from loguru import logger
from datetime import datetime, timezone
from app.core.newrelic_logger import logger
from app.core.redis_client import redis_client

class ContextManager:
    """Manages conversation context (chat history) for each session."""

    CONTEXT_PREFIX = "context:"
    KB_PREFIX = "kb:"   
    EXPIRY_SECONDS = 300

    async def add_message(self, session_id: str, role: str, message: str) -> None:
        """
        Add a message to the session context.
        Role can be 'user' or 'bot'.
        """

        key = f"{self.CONTEXT_PREFIX}{session_id}"
        msg_payload = json.dumps({
            "role": role, 
            "message": message, 
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        await redis_client.rpush(key, json.dumps(msg_payload))
        await redis_client.expire(key, self.EXPIRY_SECONDS)

        log = logger.bind(session_id=session_id, role=role)
        log.info(f"Added message to context.")
    
    async def add_kb_entry(self, session_id: str, entry: str) -> None:
        """Add a KB snippet to the session"""
        key = f"{self.KB_PREFIX}{session_id}"
        await redis_client.rpush(key, entry)
        await redis_client.expire(key, self.EXPIRY_SECONDS)

        log = logger.bind(session_id=session_id)
        log.info(f"Added KB entry to session")

    async def get_history(self, session_id: str) -> List[Dict]:
        """
        Retrieve full conversation history for a session.
        Returns a list of dicts like: [{"role": "user", "message": "..."}].
        """

        key = f"{self.CONTEXT_PREFIX}{session_id}"
        msgs = await redis_client.lrange(key, 0, -1)
        history = []

        for m in msgs:
            if isinstance(m, bytes):
                m = m.decode("utf-8")
            try:
                history.append(json.loads(m))
            except Exception:
                logger.bind(session_id=session_id).warning("Malformed message in context, skipping")

        kb_key = f"{self.KB_PREFIX}{session_id}"
        kb_entries = await redis_client.lrange(kb_key, 0, -1)
        for kb in kb_entries:
            if isinstance(kb, bytes):
                kb = kb.decode("utf-8")

            history.insert(0, {"role": "system", "message": kb})

        logger.bind(session_id=session_id).info(f"Fetched {len(history)} messages for session.")
        return history
    
    async def clear_history(self, session_id: str) -> bool:
        """
        Delete all messages for a given session.
        Returns True if deleted, False otherwise.
        """

        keys = [f"{self.CONTEXT_PREFIX}{session_id}", f"{self.KB_PREFIX}{session_id}"]
        result = 0
        for key in keys:
            result += await redis_client.delete(key)

        log = logger.bind(session_id=session_id)
        if result:
            log.info(f"Cleared context and KB history for session.")
        else:
            log.warning(f"Tried to clear non-existing history for session.")
        
        return bool(result)