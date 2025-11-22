# OCR Engine

Vendor-agnostic OCR engine with Amazon Textract support.

## Installation

```bash
pip install ocr-engine
```

## Usage

### CLI

```bash
ocr-cli path/to/document.pdf --visualize
```

### Python

```python
from ocr_engine import OCREngine, TextractOCRProvider

provider = TextractOCRProvider()
engine = OCREngine(provider=provider)
document = engine.process("path/to/document.pdf")
print(document.model_dump_json())
```
