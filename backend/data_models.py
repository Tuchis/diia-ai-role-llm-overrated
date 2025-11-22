from pydantic import BaseModel, Field
from typing import Any


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
    model: str = Field(default=DEFAULT_MODEL, example="gemini-2.5-flash", description="LLM Model to use")

class TranslationResponse(BaseModel):
    job_id: str
    source_lang: str
    target_lang: str
    translated_content: dict[str, Any]

class OCRRequest(BaseModel):
    uri: str = Field(..., description="The URI (s3://, http://) or local path to the document.")
    provider: Literal["google", "aws"] = Field(default="google", description="OCR Provider to use.")

