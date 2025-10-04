from loguru import logger as _logger
import requests
import socket
import time
from app.core.config import settings

HEADERS = {
    "Content-Type": "application/json",
    "Api-Key": settings.NEW_RELIC_INGEST_LICENSE_KEY,  
}


class NewRelicSink:
    """Custom Loguru sink to send logs to New Relic."""

    def write(self, message):
        record = message.record
        level = record["level"].name
        log_message = record["message"]

        # Extract context if provided
        session_id = record["extra"].get("session_id", None)
        customer_id = record["extra"].get("customer_id", None)

        payload = [
            {
                "common": {
                    "attributes": {
                        "service.name": "chatbot",
                        "host": socket.gethostname(),
                        "environment": "test"
                    }
                },
                "logs": [
                    {
                        "timestamp": int(time.time() * 1000),
                        "message": log_message,
                        "level": level,
                        "attributes": {
                            "module": record["module"],
                            "function": record["function"],
                            "line": record["line"],
                            "session_id": session_id,
                            "customer_id": customer_id,
                        },
                    }
                ],
            }
        ]

        try:
            resp = requests.post(settings.NEW_RELIC_LOG_API_URL, headers=HEADERS, json=payload, timeout=5)
            if resp.status_code != 202:
                print(f"New Relic log send failed: {resp.status_code}, body: {resp.text}")
        except Exception as e:
            print(f"Failed to send log to New Relic: {e}")


_logger.remove()

_logger.add(lambda msg: print(msg, end=""), level="DEBUG")

_logger.add(NewRelicSink(), level="ERROR", backtrace=True, diagnose=True)

class DepthLogger:
    """Wrapper to enforce logger.opt(depth=1) automatically."""

    def __getattr__(self, name):
        return getattr(_logger.opt(depth=1, exception=True), name)
    
logger = DepthLogger()