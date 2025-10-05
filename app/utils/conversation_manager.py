"""
ConversationManager - handle storing and retrieving conversation transcripts.

This module is the single place where conversation documents are created/queried.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Optional

from app.core.mongodb_client import db
from app.models.conversation import Conversation, MessageItem
from app.core.newrelic_logger import logger

class ConversationManager:
    COLLECTION = "conversations"

    @property
    def collection(self):
        from app.core.mongodb_client import db
        if db is None:
            raise RuntimeError("MongoDB not initialized yet")
        return db[self.COLLECTION]

    async def save_conversation(
            self,
            customer_id: str,
            session_id: str,
            company_id: str,
            phone_number: Optional[str],
            messages: List[Dict],
            start_time: datetime,
            end_time: datetime,
    ) -> str:
        """
        Save a conversation transcript into MongoDB.
        Returns conversation_id.
        """
        conversation_id = str(uuid.uuid4())
        msg_items = [MessageItem(**m) for m in messages]

        conv = Conversation(
            conversation_id=conversation_id,
            customer_id=customer_id,
            session_id=session_id,
            company_id=company_id,
            phone_number=phone_number,
            messages=msg_items,
            start_time=start_time,
            end_time=end_time,
            # created_at will be set by model default
        )

        doc = conv.model_dump()
        await self.collection.insert_one(doc)

        logger.bind(
            company_id=company_id,
            customer_id=customer_id, 
            session_id=session_id, 
            conversation_id=conversation_id
        ).info("Saved conversation transcript.")
        
        return conversation_id
    
async def get_conversation_for_customer(self, customer_id: str, limit: int=50) -> List[Dict]:
    """Return most recent conversation for a customer."""
    cursor = self.collection.find({"customer_id": customer_id}).sort("created_at", -1).limit(limit)
    results = []
    async for doc in cursor:
        results.append(doc)
    return results