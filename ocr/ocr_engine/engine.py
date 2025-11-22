


from .models import OCRDocument
from .base import OCRProvider

class OCREngine:
    def __init__(self, provider: OCRProvider, pdf_render_dpi: int = 300):
        self.provider = provider
        self.dpi = pdf_render_dpi

    def process(self, uri: str) -> OCRDocument:
        """
        Process the document with the configured provider.
        """
        document = OCRDocument.from_uri(uri, dpi=self.dpi)
        self.provider.process(document)
        return document
