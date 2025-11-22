import fitz  # pymupdf

from .models import OCRDocument, OCRPage
from .base import OCRProvider

class OCREngine:
    def __init__(self, provider: OCRProvider, pdf_render_dpi: int = 300):
        self.provider = provider
        self.dpi = pdf_render_dpi

    def _load_document(self, file_path: str) -> OCRDocument:
        """
        Loads a document from a file path.
        Converts PDF pages to images if necessary.
        """
        pages = []
        
        # Check if PDF
        if file_path.lower().endswith(".pdf"):
            doc = fitz.open(file_path)
            for i, page in enumerate(doc):
                # Render page to image (pixmap)
                pix = page.get_pixmap(dpi=self.dpi) # High DPI for better OCR
                image_bytes = pix.tobytes("png")
                pages.append(OCRPage(page_number=i+1, image_bytes=image_bytes))
            doc.close()
        else:
            # Assume image
            with open(file_path, "rb") as f:
                image_bytes = f.read()
            pages.append(OCRPage(page_number=1, image_bytes=image_bytes))
            
        return OCRDocument(file_path=file_path, pages=pages)

    def process(self, file_path: str) -> OCRDocument:
        """
        Process the document with the configured provider.
        """
        document = self._load_document(file_path)
        self.provider.process(document)
        return document
