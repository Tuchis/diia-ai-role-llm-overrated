import asyncio
import os
import logging
from typing import Any
from openai import AsyncAzureOpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AIRUN_API_KEY = os.getenv("AIRUN_API_KEY")
AIRUN_ENDPOINT = "https://codemie.lab.epam.com/llms"
API_VERSION = "2024-02-01"
DEFAULT_MODEL = "gemini-2.5-flash"

class TranslationEngine:
    def __init__(self):
        if not AIRUN_API_KEY:
            logger.warning("AIRUN_API_KEY not set. Calls will fail unless set in environment.")

        self.client = AsyncAzureOpenAI(
            api_key=AIRUN_API_KEY,
            azure_endpoint=AIRUN_ENDPOINT,
            api_version=API_VERSION
        )

    async def translate_text(self, text: str, source: str, target: str, model: str) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system", 
                        "content": (
                            f"You are a professional translator. "
                            f"Translate the following text from {source} to {target}. "
                            f"Return ONLY the translated text without quotes or explanations."
                        )
                    },
                    {"role": "user", "content": text}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"LLM Translation Error: {str(e)}")
            return f"[Translation Error: {str(e)}]"

    async def process_document(self, data: Any, source: str, target: str, model: str, ignore_keys: list[str]) -> Any:
        """
        Recursively traverses a JSON object (dict or list) and translates string values.
        """
        if isinstance(data, dict):
            return {
                k: (await self.process_document(v, source, target, model, ignore_keys) if k not in ignore_keys else v)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [await self.process_document(item, source, target, model, ignore_keys) for item in data]
        elif isinstance(data, str):
            if not data.strip() or data.isnumeric():
                return data
            return await self.translate_text(data, source, target, model)
        else:
            return data
