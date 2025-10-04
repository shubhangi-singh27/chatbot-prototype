import os
import json
import asyncio
from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError
from app.core.config import settings
from app.core.newrelic_logger import logger

client = AsyncOpenAI(api_key=settings.OPENAI_KEY)

class OpenAIClient:
    def __init__(self):
        self.client = client
        self.model = settings.OPENAI_MODEL or "gpt-4.1-mini"
        self.max_tries = 3

    def _format_message(self, history: str) -> list[dict]:
        """
        history: [{ "role": "user"/"bot", "message": "..." }]
        Converts history to OpenAI format and gets response.
        """

        messages =[
            {"role": "system", "content": settings.SYSTEM_PROMPT or "You are a friendly support bot. Answer clearly and politely."}
        ]
        for raw_item in history:
            if isinstance(raw_item, str):
                item = json.loads(raw_item)

            role = "assistant" if item["role"]=="bot" else "user"
            messages.append({"role": role, "content": item["message"]})
        return messages

    async def generate_response(self, history: str):
        messages = self._format_message(history)
        attempt = 0
        while attempt < self.max_tries:
            try:
                """full_reply = ""
                async with self.client.chat.completions.stream(
                    model = "gpt-4.1-mini",
                    messages = messages
                ) as stream:
                    async for event in stream:
                        if event.type == "content.delta":
                            yield event.delta
                            full_reply+=event.delta
                        elif event.type == "content.done":
                            return"""
                            
                response = await self.client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages = messages,
                    max_tokens = 300,
                    temperature = 0.7
                )
                return response.choices[0].message.content
            except (RateLimitError, APITimeoutError) as e:
                wait = 2 ** attempt
                logger.warning(f"OpenAIrate/timeout error: {e}, retrying in {wait}s")
                await asyncio.sleep(wait)
                attempt+=1
            except APIError as e:
                logger.error(f"OpenAI API error: {e}")
                raise

        raise RuntimeError("OpenAI request failed after retries")
