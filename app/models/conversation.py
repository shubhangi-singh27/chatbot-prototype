# app/models/conversation.py
"""
Pydantic model for conversation documents stored in MongoDB.

We keep this model small and strict to validate conversation documents
before inserting into the DB. Uses ISO 8601 timestamps for portability.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

class MessageItem(BaseModel):
    role: str
    message: str
    timestamp: datetime

class Conversation(BaseModel):
    conversation_id: str = Field(..., description="UUID for the conversation")
    customer_id: str = Field(..., description="Customer UUID")
    session_id: str = Field(..., description="Session UUID")
    phone_number: Optional[str] = Field(None, description="Normalized phone number (E.164)")
    messages: List[MessageItem] = Field(..., description="Ordered list of messages in the conversation")
    start_time: datetime = Field(..., description="Session start time (UTC)")
    end_time: datetime = Field(..., description="Session end time (UTC)")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Record insertion time (UTC)")