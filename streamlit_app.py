import streamlit as st
import asyncio
import websockets
import json
from app.core.config import settings 

WS_URL = settings.WS_URL


# ----------------- Async Setup -----------------
if "loop" not in st.session_state:
    st.session_state.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(st.session_state.loop)

async def connect_ws():
    ws = await websockets.connect(WS_URL, ping_interval=300, ping_timeout=60)
    return ws

async def send_and_receive(ws, message: str):
    """Send message to backend and wait for reply"""
    await ws.send(message)
    reply = await ws.recv()
    return reply

#async def send_json(ws, payload: dict):
#    await ws.send(json.dumps(payload))
#    reply = await ws.recv()
#    return reply

def run_async(coro):
    """Run async coroutines safely inside Streamlit"""
    return st.session_state.loop.run_until_complete(coro)

# ----------------- App Title -----------------
st.title("Chatbot with phone session + Company KB")

# ----------------- Session State Initialization -----------------
if "ws" not in st.session_state:
    st.session_state.ws = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_active" not in st.session_state:
    st.session_state.session_active = False
if "company_selected" not in st.session_state:
    st.session_state.company_selected = False


# ----------------- Step 1: Phone Number -----------------
if not st.session_state.session_active:
    company_options = ["Company A", "Company B", "Company C"]
    company_selected = st.selectbox("Select company", company_options)
    phone = st.text_input("Enter you phone number to start: ", key="phone_input")

    if st.button("Start Chat"):
        if not phone.strip():
            st.warning("Enter a valid phone number")
            st.stop()
        try:
            ws = run_async(connect_ws())
            st.session_state.ws = ws
            
            # Step 1: Read greeting from backend
            greeting = run_async(ws.recv())
            st.write(greeting)

            # Step 2: Send Company
            run_async(ws.send(company_selected))
            st.session_state.company_selected = company_selected

            # Step 3: Wait for phone prompt
            prompt = run_async(ws.recv())
            st.write(prompt)

            # Step 4: Send phone number
            run_async(ws.send(phone))   

            # Step 5: Wait for confirmation
            confirmation = run_async(ws.recv())

            st.session_state.session_active = True
            st.success(confirmation)

        except Exception as e:
            st.error(f"Connection failed: {e}")
            st.stop()
    
# ----------------- Step 2: KB Upload -----------------
#if st.session_state.session_active and not st.session_state.kb_uploaded:
#    # st.subheader("Step 2: Upload or paste knowledge base for this session")
#    kb_input = st.text_area("Paste KB content here: ", height=200, key="kb_input")
#    if st.button("Upload KB"):
#        if kb_input.strip():
#            _ = run_async(st.session_state.ws.recv())
#            st.session_state.kb_content = kb_input
#
#            # Send KB to backend
#            try:
#                payload = {"type": "kb_upload", "content": kb_input}
#                
#                kb_confirmation = run_async(send_json(st.session_state.ws, kb_input))
#                # kb_reply = run_async(send_json(st.session_state.ws, kb_input))
#                # st.write(f"KB uploaded successfully. Backend response: {kb_reply}")
#                st.session_state.kb_uploaded = True
#                st.success("Knowledge Base uploaded successfully! You can now chat with the bot.")
#            except Exception as e:
#                st.error(f"Error: {e}")"""

# ----------------- Step 2: Chat -----------------
if st.session_state.session_active:
    user_input = st.text_input("Your message: ", key="msg_input")
    if st.button("Send"):
        if user_input.strip():
            st.session_state.messages.append(("User", user_input))

            try:
                reply = run_async(send_and_receive(st.session_state.ws, user_input))
                st.session_state.messages.append(("Bot", reply))
            except Exception as e:
                st.error(f"Error: {e}")


    # Display Chat History
    st.subheader("Conversation")
    for role, msg in st.session_state.messages:
        if role=="User":
            st.markdown(f"**You:** {msg}")
        else:
            st.markdown(f"**Bot:** {msg}")