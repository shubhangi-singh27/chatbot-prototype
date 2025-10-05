# Chatbot — Support Bot Prototype

**Short description**
A modular **FastAPI + WebSocket chatbot** with **Redis-based session management** and **MongoDB persistence**.  
Includes a **Streamlit UI** for demoing chat sessions and uploading session-specific or company-level Knowledge Bases (KBs).

## ✨ Features

- **Phone-number-based session start** (unique user identification)
- **Session TTL with Redis** (automatic expiry handling)
- **Company Knowledge Base (KB)** — load and use company-specific data
- **LLM (OpenAI)** integration for context-aware responses
- **Conversation persistence** in MongoDB (with timestamps)
- **Streamlit frontend** for demo and KB upload
- **New Relic logging integration** for monitoring and observability

---

## 🧰 Tech Stack

| Component | Technology |
|------------|-------------|
| Backend | FastAPI (WebSocket-based) |
| Frontend | Streamlit |
| Session Store | Redis |
| Database | MongoDB |
| LLM | OpenAI API |
| Logging | New Relic |

---

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
# Update .env with your API keys and DB URLs

### Run Backend
uvicorn main:app --reload

### Run Streamlit demo (Backend)
streamlit run streamlit_backend.py
# Upload company based KBs

### Run Streamlit demo (Frontend)
# Edit the company names in selectbox to the companies for which you have uploaded KBs
streamlit run streamlit_app.py

### How It Works

# Backend:
Company connects via Streamlit and uploads their Knowledge Base to Mongo DB

# Frontend:
User connects via WebSocket → selects company → enters phone number.
Customer & session created → session context initialized in Redis.
Company KB auto-loaded from MongoDB.
Chat messages stored & sent to OpenAI LLM for response.
Full conversation history persisted in MongoDB.
