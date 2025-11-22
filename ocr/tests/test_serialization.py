import json
from ocr_engine.models import OCRDocument, OCRPage, OCRBlock

def test_ocr_document_serialization():
    # Create a document with some data
    block = OCRBlock(text="Hello", confidence=0.99, geometry={"x": 1, "y": 2})
    page = OCRPage(page_number=1, image_bytes=b"fake_image_data", blocks=[block])
    doc = OCRDocument(uri="file:///test.pdf", file_format="pdf", pages=[page])

    # Serialize to JSON
    json_str = doc.to_json()
    
    # Verify image_bytes is NOT in the JSON
    data = json.loads(json_str)
    assert "image_bytes" not in data["pages"][0]
    assert data["pages"][0]["page_number"] == 1
    assert data["pages"][0]["blocks"][0]["text"] == "Hello"

    # Deserialize from JSON
    doc_loaded = OCRDocument.from_json(json_str)

    # Verify loaded object
    assert doc_loaded.uri == doc.uri
    assert doc_loaded.file_format == doc.file_format
    assert len(doc_loaded.pages) == 1
    assert doc_loaded.pages[0].page_number == 1
    assert len(doc_loaded.pages[0].blocks) == 1
    assert doc_loaded.pages[0].blocks[0].text == "Hello"
    
    # Verify image_bytes is default (empty bytes)
    assert doc_loaded.pages[0].image_bytes == b""
