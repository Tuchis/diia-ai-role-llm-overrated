from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class OCRBlock(BaseModel):
    text: str
    translated_text: Optional[str] = Field(default=None)
    confidence: float
    geometry: Optional[Dict[str, Any]] = None

class OCRPage(BaseModel):
    page_number: int
    image_bytes: bytes = Field(exclude=True) # Exclude from JSON dump by default to avoid massive output
    blocks: List[OCRBlock] = []

class OCRDocument(BaseModel):
    file_path: str
    pages: List[OCRPage] = []
