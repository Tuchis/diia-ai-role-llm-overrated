from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import pymupdf as fitz  # pymupdf
from urllib.parse import urlparse, unquote
from pathlib import Path

class OCRBlock(BaseModel):
    text: str
    confidence: float
    geometry: Optional[Dict[str, Any]] = None

class OCRPage(BaseModel):
    page_number: int
    image_bytes: bytes = Field(default=b"", exclude=True) # Exclude from JSON dump by default to avoid massive output
    blocks: List[OCRBlock] = []

class OCRDocument(BaseModel):
    uri: str
    file_format: str
    pages: List[OCRPage] = []

    @classmethod
    def _read_file_content(cls, uri: str) -> bytes:
        """
        Reads file content from a URI into bytes.
        Supports file:// and s3:// schemes.
        """
        parsed = urlparse(uri)
        
        if not parsed.scheme:
             raise ValueError(f"Invalid URI: {uri}. Must contain a scheme (e.g., file://)")

        if parsed.scheme == "file":
            file_path = unquote(parsed.path)
            with open(file_path, "rb") as f:
                return f.read()
        elif parsed.scheme == "s3":
            import boto3
            s3 = boto3.client("s3")
            bucket = parsed.netloc
            key = parsed.path.lstrip("/")
            response = s3.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()
        else:
            raise ValueError(f"Unsupported scheme: {parsed.scheme}")

    @classmethod
    def from_uri(cls, uri: str, dpi: int = 300) -> "OCRDocument":
        """
        Creates an OCRDocument from a URI.
        Loads the file content and converts PDF pages to images if necessary.
        """
        file_bytes = cls._read_file_content(uri)
        pages = []
        
        # Determine file type from extension
        parsed = urlparse(uri)
        path = unquote(parsed.path)
        ext = Path(path).suffix.lower().lstrip(".")
        file_format = ext if ext else "unknown"
        
        is_pdf = file_format == "pdf"
        
        if is_pdf:
            # Open PDF from bytes
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                for i, page in enumerate(doc):
                    # Render page to image (pixmap)
                    pix = page.get_pixmap(dpi=dpi) # High DPI for better OCR
                    image_bytes = pix.tobytes("png")
                    pages.append(OCRPage(page_number=i+1, image_bytes=image_bytes))
        else:
            # Assume image
            pages.append(OCRPage(page_number=1, image_bytes=file_bytes))
            
        return cls(uri=uri, pages=pages, file_format=file_format)

    def to_json(self) -> str:
        """
        Serializes the OCRDocument to a JSON string.
        """
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> "OCRDocument":
        """
        Deserializes an OCRDocument from a JSON string.
        """
        return cls.model_validate_json(json_str)
