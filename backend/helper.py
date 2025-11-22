import httpx
import logging
import os
import uuid
from typing import ANy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TRANSLATION_SERVICE_URL = os.getenv("TRANSLATION_SERVICE_URL")

async def translate_batch(texts_map: dict[str, str], source: str = "uk", target: str = "en") -> dict[str, str]:
    if not texts_map:
        return {}

    payload = {
        "source_lang": source,
        "target_lang": target,
        "content": texts_map,
        "ignore_keys": []
    }

    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"Sending batch translation request ({len(texts_map)} items) to {TRANSLATION_SERVICE_URL}")
            response = await client.post(TRANSLATION_SERVICE_URL, json=payload, timeout=60.0)
            response.raise_for_status()
            result = response.json()
            return result.get("translated_content", {})
        except httpx.RequestError as e:
            logger.error(f"Translation service connection failed: {e}")
            return {} # Fail gracefully, return empty translations
        except httpx.HTTPStatusError as e:
            logger.error(f"Translation service returned error: {e.response.text}")
            return {}

def extract_text_nodes(data: Any, collector: dict[str, str], node_map: dict[str, dict]):
    """
    Recursively finds dictionaries with a 'text' key.
    - collector: Maps 'temp_id' -> 'original_text' (payload for translation service)
    - node_map: Maps 'temp_id' -> reference to the dictionary object (so we can update it later)
    """
    if isinstance(data, dict):
        # If this node has a 'text' field that is a string, capture it
        if "text" in data and isinstance(data["text"], str) and data["text"].strip():
            # Generate a temporary unique ID for this node to track it across the batch call
            temp_id = str(uuid.uuid4())
            collector[temp_id] = data["text"]
            node_map[temp_id] = data
        
        # Recurse into children
        for key, value in data.items():
            extract_text_nodes(value, collector, node_map)
            
    elif isinstance(data, list):
        for item in data:
            extract_text_nodes(item, collector, node_map)
