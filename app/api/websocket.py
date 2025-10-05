import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
#from loguru import logger

# Import your New Relic logger setup
from app.core.newrelic_logger import logger

from app.utils.session_manager import SessionManager
from app.utils.customer_manager import CustomerManager
from app.utils.context_manager import ContextManager
from app.utils.openai_client import OpenAIClient
from app.utils.conversation_manager import ConversationManager
from app.utils.company_kb_manager import CompanyKBManager
from app.models.customer import Customer
from pydantic import ValidationError
from datetime import datetime, timezone
from typing import Optional
import uuid
import json


router = APIRouter()
session_manager = SessionManager()
customer_manager = CustomerManager()
context_manager = ContextManager()
openai_client = OpenAIClient()
conversation_manager = ConversationManager()
company_kb_manager = CompanyKBManager()


# Helper function to wait for a message with a timeout
async def wait_for_message_with_timeout(websocket: WebSocket, timeout: int = session_manager.EXPIRY_SECONDS) -> str:
    return await asyncio.wait_for(websocket.receive_text(), timeout=timeout)

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()

    # Step 0: Company selection before phone number
    await websocket.send_text("Select company for this session:")

    company_id = await wait_for_message_with_timeout(websocket)

    # Step 1: Phone number input
    await websocket.send_text("Welcome! Please provide your phone number: ")
    
    try:
        # Wait max 5 minutes (session TTL) for phone number
        phone_number_raw = await wait_for_message_with_timeout(websocket, timeout=session_manager.EXPIRY_SECONDS)
    except asyncio.TimeoutError:
        await websocket.send_text("Session timed out due to inactivity.")
        await websocket.close()
        return
    except Exception:
        return

    # Validate phone number
    try:
        temp_id = str(uuid.uuid4())
        validated = Customer(_id=temp_id, phone_number=phone_number_raw)
        normalized_phone = validated.phone_number
    except ValidationError as e:
        await websocket.send_text("Invalid phone number format. Please try again")
        await websocket.close()
        return
    
    # Get or create customer
    try:
        customer_id = await customer_manager.get_or_create_customer(normalized_phone)
    except Exception as e:
        logger.bind(phone_number = normalized_phone).error(f"Failed to get or create customer: {e}")
        await websocket.send_text("Internal server error. Please try again later.")
        await websocket.close()
        return

    # Step 2: Create new session
    try:
        session = await session_manager.create_session(customer_id)
        session_id = session["session_id"]
        start_time = datetime.now(timezone.utc)
    except Exception as e:
        logger.error(f"Failed to create session for customer {customer_id}: {e}")
        await websocket.send_text("Internal server error. Please try again later.")
        await websocket.close()
        return
    
    log = logger.bind(session_id = session_id, customer_id = customer_id)
    log.info(f"New session created started for customer.")

    await websocket.send_text(
        f"Hello Customer {customer_id[:8]}! Your session ID is {session_id[:8]}"
    )

    """# Step 3: Wait for KB upload
    await websocket.send_text("Please upload your Knowledge Base for this session: ")
    try:
        kb_raw = await wait_for_message_with_timeout(websocket, timeout=session_manager.EXPIRY_SECONDS)
        await context_manager.add_message(session_id, "kb", kb_raw)
        log.info(f"KB uploaded and stored for session {session_id}")
        await websocket.send_text("Knowledge Base uploaded successfully")
    except asyncio.TimeoutError:
        await websocket.send_text("KB upload timed out due to inactivity")
        await websocket.close()
        return
    except Exception as e:
        log.error(f"Failed Kb upload: {e}")
        await websocket.send_text("Error uploading KB. Please try again.")
        await websocket.close()
        return"""

    # Step 3: Fetch company KB directly
    try:
        company_kb = await company_kb_manager.get_kb(company_id)
        if company_kb:
            await context_manager.add_message(session_id, "system", company_kb)
            log.info(f"Loaded company KB into session for {company_id}")
    except Exception as e:
        log.error(f"Failed to load company KB: {e}")

    # Step 4: Conversation Loop
    try:
        while True:
            try:
                data = await wait_for_message_with_timeout(websocket)

                # log = logger.bind(customer_id=customer_id, session_id=session_id)
                log.info(f"Received msg: {data}")
            except asyncio.TimeoutError:
                await websocket.send_text("Session timed out due to inactivity.")
                log.info("Session timeout.")
                break
            
            # log.info(f"Customer {customer_id} | Session {session_id} | Msg: {data}")

            # Save user msg
            await context_manager.add_message(session_id, "user", data)

            # Get conversation history + session KB
            history = await context_manager.get_history(session_id, company_id=company_id)

            # Await OpenAI client
            try:
                reply = await openai_client.generate_response(history)
            except Exception as e:
                log.error(f"OpenAI generation failed: {e}")
                await websocket.send_text("Sorry, something went wrong generating a response.")
                continue
            """try:
                async for token in openai_client.generate_streaming_response(history):
                    
                    if token in ("[END]", "\n[Error: Could not generate response]"):
                        continue
                    await websocket.send_text(token)
                    reply_text += token
            except Exception as e:
                log.error(f"OpenAI streaming failed: {e}")
                await websocket.send_text("Sorry, something went wrong generating a response.")
                continue"""

            # Save bot reply
            await context_manager.add_message(session_id, "bot", reply)

            # Refresh session TTL
            try:
                await session_manager.refresh_session(session_id)
            except Exception as e:
                log.error(f"Error refreshing the session. {e}")

            await websocket.send_text(reply)
            log.info(f"Sent reply: {reply}")

    except WebSocketDisconnect:
        # await session_manager.end_session(session_id)
        # await context_manager.clear_history(session_id)
        log.info(f"Session {session_id} disconnected for customer {customer_id}")

    except Exception as e:
        log.error(f"Unexpected error in session {session_id}: {e}")
        try:
            await websocket.send_text("Sorry, something went wrong. Please try again later.")
        except Exception:
            pass
    finally:
        try:
            end_time = datetime.now(timezone.utc)
            raw_history = await context_manager.get_history(session_id, company_id=company_id)

            messages_for_save =[]
            for raw in raw_history:
                item = json.loads(raw)
                ts = item.get("timestamp")
                try:
                    dt = datetime.fromisoformat(ts) if ts else datetime.now(timezone.utc)
                except Exception:
                    dt = datetime.now(timezone.utc)
                messages_for_save.append({
                    "role": item.get("role", "user"),
                    "message": item.get("message", ""),
                    "timestamp": dt
                })
            
            customer_doc = await customer_manager.get_customer(normalized_phone)
            phone_for_record = customer_doc.get("phone_number") if customer_doc else normalized_phone

            conversation_id = await conversation_manager.save_conversation(
                company_id=company_id,
                customer_id=customer_id,
                session_id=session_id,
                phone_number=phone_for_record,
                messages=messages_for_save,
                start_time=start_time,
                end_time=end_time,
            )
            log.bind(conversation_id=conversation_id).info("Conversation persisted")
        except Exception as e:
            log.error(f"Failed to persist conversation: {e}")

        await session_manager.end_session(session_id)
        await context_manager.clear_history(session_id)
        try:
            await websocket.close()
        except Exception:
            pass
        log.info("Session cleanup complete.")