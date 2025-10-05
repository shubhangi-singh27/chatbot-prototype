import streamlit as st
import asyncio
from app.core.redis_client import redis_client
from app.utils.company_kb_manager import CompanyKBManager
from app.core.mongodb_init import init_mongodb

kb_manager = CompanyKBManager()

# -------------------------Async Setup-----------------------
if "loop" not in st.session_state:
    st.session_state.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(st.session_state.loop)

# Initialize MongoDB (must be awaited)
async def setup_mongo():
    await init_mongodb()

def run_async(coro):
    return st.session_state.loop.run_until_complete(coro)

async def upload_to_redis(company_id: str, kb_entries: list[str]):
    """
    Save KB entries to Redis for quick session access.
    """
    key = f"kb:company:{company_id}"
    for entry in kb_entries:
        await redis_client.rpush(key, entry)
    return True

st.session_state.loop.run_until_complete(setup_mongo())

# -------------------------Admin KB Upload-----------------------
st.title("Admin: Upload Company KB")

company_id = st.text_input("Enter Company ID/Name:")
kb_input = st.text_area("Paste KB entries (one per line):", height=300)

if st.button("Upload KB"):
    if not company_id.strip() or not kb_input.strip():
        st.warning("Provide both Company ID and KB content")
    else:
        kb_entries = [line.strip() for line in kb_input.split("\n") if line.strip()]
        kb_text = "\n".join(kb_entries)
        try:
            # Upload to MongoDB
            run_async(kb_manager.upload_kb(company_id, kb_text))
            # Upload to Redis
            run_async(upload_to_redis(company_id, kb_entries))

            st.success(f"Upload {len(kb_entries)} KB entries for company {company_id}")
        except Exception as e:
            st.error(f"Error uploading KB: {e}")