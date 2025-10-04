from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Support Bot"
    OPENAI_KEY: str = os.getenv("OPENAI_API_KEY")
    REDIS_URL: str = os.getenv("REDIS_URL")
    MONGODB_URI: str = os.getenv("MONGODB_URI")
    MONGODB_DB: str = os.getenv("MONGODB_DB")
    NEW_RELIC_INGEST_LICENSE_KEY = os.getenv("NEW_RELIC_INGEST_LICENSE_KEY")
    NEW_RELIC_LOG_API_URL = os.getenv("NEW_RELIC_LOG_API_URL")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL")
    SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT")
    WS_URL = os.getenv("WS_URL")

settings = Settings()