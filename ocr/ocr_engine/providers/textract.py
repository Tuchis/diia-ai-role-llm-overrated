import os
from typing import Optional
import boto3
from ..base import OCRProvider
from ..models import OCRResult, OCRBlock

class TextractOCRProvider(OCRProvider):
    """
    Amazon Textract OCR Provider.
    Requires AWS credentials to be configured in the environment.
    """
    def __init__(self, region_name: Optional[str] = None):
        region_name = region_name or os.getenv("AWS_REGION")
        
        self.client = boto3.client("textract", region_name=region_name)

    def process(self, file_path: str) -> OCRResult:
        with open(file_path, "rb") as document:
            image_bytes = document.read()

        try:
            response = self.client.detect_document_text(Document={"Bytes": image_bytes})
        except self.client.exceptions.UnsupportedDocumentException:
            raise ValueError("Unsupported document format. Please use JPEG or PNG.")
        except Exception as e:
            raise RuntimeError(f"AWS Textract error: {e}")

        blocks = []
        for item in response["Blocks"]:
            if item["BlockType"] == "LINE":
                blocks.append(
                    OCRBlock(
                        text=item["Text"],
                        confidence=item["Confidence"],
                        geometry=item["Geometry"],
                    )
                )

        return OCRResult(blocks=blocks, raw_response=response)
