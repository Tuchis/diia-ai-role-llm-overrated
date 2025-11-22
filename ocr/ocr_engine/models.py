from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class OCRBlock(BaseModel):
    text: str
    confidence: float
    geometry: Optional[Dict[str, Any]] = None

class OCRResult(BaseModel):
    blocks: List[OCRBlock]
    raw_response: Optional[Dict[str, Any]] = None
