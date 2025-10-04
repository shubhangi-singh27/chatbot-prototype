# Chatbot — Support Bot Prototype

**Short description**
A modular FastAPI + WebSocket chatbot with Redis session store and MongoDB persistence. Streamlit UI for demoing sessions and uploading session-specific Knowledge Base (KB).

## Features
- Phone-number based session start
- Session TTL with Redis
- Session-based KB upload (text)
- LLM (OpenAI) integration for responses
- Conversation persistence in MongoDB
- Streamlit frontend (demo & POC)
- New Relic logging integration

## Quickstart (local development)

### Prereqs
- Python 3.10+ 
- Redis & MongoDB running locally (or set MONGODB_URI / REDIS_URL to remote)
- Virtualenv

### Setup
```bash
# create & activate venv
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# install dependencies
pip install -r requirements.txt

# copy .env.example to .env and fill secrets
cp .env.example .env

### Run Backend
uvicorn main:app --reload

### Run Streamlit demo
streamlit run streamlit_app.py