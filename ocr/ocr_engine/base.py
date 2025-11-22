import abc
from .models import OCRDocument

class OCRProvider(abc.ABC):
    @abc.abstractmethod
    def process(self, document: OCRDocument) -> None:
        """
        Process the document and enrich it with OCR results.
        Modifies the document in-place.
        """
        pass
