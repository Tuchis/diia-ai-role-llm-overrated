from fnmatch import translate
import os
import logging
import re
import json
from typing import Any
from openai import AsyncAzureOpenAI, AsyncOpenAI
from transliteration import transliteration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AIRUN_API_KEY = os.getenv("AIRUN_API_KEY")
AIRUN_ENDPOINT = "https://codemie.lab.epam.com/llms"
API_VERSION = "2024-02-01"
DEFAULT_MODEL = "gemini-2.5-flash"

LAPA_ENDPOINT = ""

class TranslationEngine:
    def __init__(self):
        if not AIRUN_API_KEY:
            logger.warning("AIRUN_API_KEY not set. Calls will fail unless set in environment.")

        self.clients = {
                "common": AsyncAzureOpenAI(
                    api_key=AIRUN_API_KEY,
                    azure_endpoint=AIRUN_ENDPOINT,
                    api_version=API_VERSION
                ),
                "lapa": AsyncOpenAI(
                    base_url=LAPA_ENDPOINT,
                    api_key=""
                ),
        }

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

    def _transliterate_entity(self, text: str) -> str:
        try:
            return transliteration(text)
        except Exception as e:
            logger.error(f"Transliteration error: {e}")
            return text

    async def _extract_entities_llm(self, text: str, model: str) -> list[str]:
        try:
            system_prompt = (
                "You are an expert Named Entity Recognition system. "
                "Analyze the provided text and extract all entities that refer to a PERSON (names of people). "
                "Return the response strictly as a JSON object with a single key 'entities' containing a list of strings found exactly as they appear in the text. "
                "If no entities are found, return {\"entities\": []}. "
                "Do not include any explanation or markdown formatting."
            )
            client = self.clients["common"] if model != "lapa" else self.clients["lapa"]
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]

            data = json.loads(content)
            return data.get("entities", [])

        except Exception as e:
            logger.error(f"NER Extraction Error: {str(e)}")
            return []

    async def translate_text(self, text: str, source: str, target: str, model: str, use_ner: bool = True) -> str:
        transliterated_values = []
        text_to_translate = text
        client = self.clients["common"] if model != "lapa" else self.clients["lapa"]

        if use_ner and source == 'uk':
            entities = await self._extract_entities_llm(text, model)

            if entities:
                unique_entities = sorted(list(set(entities)), key=len, reverse=True)

                if unique_entities:
                    pattern = re.compile("|".join(map(re.escape, unique_entities)))

                    def replace_callback(match):
                        word = match.group(0)
                        transliterated_val = self._transliterate_entity(word)
                        transliterated_values.append(transliterated_val)
                        return "{}"

                    text_to_translate = pattern.sub(replace_callback, text_to_translate)

        try:
            system_prompt = (
                f"You are a professional translator. "
                f"Translate the following text from {source} to {target}. "
                f"Return ONLY the translated text without quotes or explanations. "
            )

            if transliterated_values:
                system_prompt += " The text contains Python format placeholders '{}'. PRESERVE them exactly as they are in the translated output. Do not change their order or count."

            translated_text = "{}"
            if len(text_to_translate.replace("{}", "").strip()) > 0:
                logger.info(f"Translating text: {text_to_translate}")
                response = await client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text_to_translate}
                    ]
                )
                translated_text = response.choices[0].message.content.strip()

            if transliterated_values:
                placeholder_count = translated_text.count("{}")
                if placeholder_count == len(transliterated_values):
                    translated_text = translated_text.format(*transliterated_values)
                else:
                    logger.warning(f"Placeholder mismatch: Text has {placeholder_count} '{{}}', but we have {len(transliterated_values)} values. Fallback: returning raw text.")
                    return translated_text

            return translated_text

        except Exception as e:
            logger.error(f"LLM Translation Error: {str(e)}")
            return f"[Translation Error: {str(e)}]"
