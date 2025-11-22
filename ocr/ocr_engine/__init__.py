from typing import Optional
from .models import OCRResult, OCRBlock
from .base import OCRProvider
from .providers.textract import TextractOCRProvider
from .visualization import visualize_results

def process_document(
    file_path: str, provider: Optional[OCRProvider] = None
) -> OCRResult:
    """
    Process a document and return OCR results.

    Args:
        file_path: Path to the image file.
        provider: OCRProvider instance. If None, uses TextractOCRProvider.
    """
    if provider is None:
        provider = TextractOCRProvider()

    return provider.process(file_path)

__all__ = [
    "OCRResult",
    "OCRBlock",
    "OCRProvider",
    "TextractOCRProvider",
    "process_document",
    "visualize_results",
]
