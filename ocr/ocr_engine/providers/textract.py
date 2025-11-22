import os
from typing import Optional
import boto3
from ..base import OCRProvider
from ..models import OCRDocument, OCRBlock

class TextractOCRProvider(OCRProvider):
    """
    Amazon Textract OCR Provider.
    Requires AWS credentials to be configured in the environment.
    """
    def __init__(self, region_name: Optional[str] = None):
        region_name = region_name or os.getenv("AWS_REGION")
        # We allow None here and let boto3 handle it or fail later if not configured
        
        self.client = boto3.client("textract", region_name=region_name)

    def process(self, document: OCRDocument) -> None:
        for page in document.pages:
            try:
                response = self.client.detect_document_text(Document={"Bytes": page.image_bytes})
            except self.client.exceptions.UnsupportedDocumentException:
                # This shouldn't happen if we feed it PNG/JPEG bytes from pymupdf/file
                print(f"Warning: Unsupported document format for page {page.page_number}")
                continue
            except Exception as e:
                print(f"Error processing page {page.page_number}: {e}")
                continue

            blocks = []
            for item in response["Blocks"]:
                if item["BlockType"] == "LINE":
                    blocks.append(
                        OCRBlock(
                            text=item["Text"],
                            confidence=item["Confidence"] / 100.0,
                            geometry=item["Geometry"],
                        )
                    )
            
            page.blocks.extend(blocks)
