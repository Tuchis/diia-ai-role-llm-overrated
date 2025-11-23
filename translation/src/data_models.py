from pydantic import BaseModel, Field
from typing import Any
from engine import DEFAULT_MODEL

class TranslationRequest(BaseModel):
    source_lang: str = Field(..., example="uk", description="Source language code (e.g., 'uk')")
    target_lang: str = Field(..., example="en", description="Target language code (e.g., 'en', 'de', 'es')")
    content: dict[str, Any] = Field(
        ..., 
        example={
            "title": "Привіт Світ", 
            "body": "Це тестовий документ.", 
            "meta": {"author": "Іван", "tags": ["новини", "технології"]}
        },
        description="Arbitrary JSON content. The service will recurse through this and translate string values."
    )
    ignore_keys: list[str] = Field(default=["id", "uid", "url", "email"], description="JSON keys to skip translation for.")
    model: str = Field(default=DEFAULT_MODEL, example="lapa", description="LLM Model to use")

class TranslationResponse(BaseModel):
    job_id: str
    source_lang: str
    target_lang: str
    translated_content: dict[str, Any]
    initial_content: dict[str, Any]
