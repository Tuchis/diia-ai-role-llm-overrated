from pydantic import BaseModel, Field
from typing import Literal

class OCRRequest(BaseModel):
    uri: str = Field(..., description="The URI (s3://, http://) or local path to the document.")
    provider: Literal["google", "aws"] = Field(default="google", description="OCR Provider to use.")
