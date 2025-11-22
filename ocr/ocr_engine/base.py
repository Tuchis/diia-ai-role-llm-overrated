import abc
from .models import OCRResult

class OCRProvider(abc.ABC):
    @abc.abstractmethod
    def process(self, file_path: str) -> OCRResult:
        pass
