import pytest

from ocr_engine.models import OCRDocument
import fitz

def test_load_image(tmp_path):
    # Create a dummy image
    image_path = tmp_path / "test_image.png"
    
    # Create a simple red image using fitz (or just bytes if we trust fitz to handle it)
    # Actually, let's just write some bytes. OCRDocument assumes image if not PDF.
    # But for it to be a valid image for visualization later, it should be real.
    # We can use fitz to create a pixmap and save it.
    # Create a simple red image using fitz
    pix = fitz.Pixmap(fitz.csRGB, fitz.Rect(0, 0, 100, 100), 0)
    pix.save(str(image_path))
    
    uri = f"file://{image_path.absolute()}"
    
    doc = OCRDocument.from_uri(uri)
    
    assert doc.uri == uri
    assert doc.file_format == "png"
    assert len(doc.pages) == 1
    assert doc.pages[0].page_number == 1
    assert len(doc.pages[0].image_bytes) > 0

def test_load_pdf(tmp_path):
    # Create a dummy PDF
    pdf_path = tmp_path / "test_doc.pdf"
    doc_pdf = fitz.open()
    page = doc_pdf.new_page()
    page.insert_text((50, 50), "Hello World")
    doc_pdf.save(str(pdf_path))
    doc_pdf.close()
    
    uri = f"file://{pdf_path.absolute()}"
    
    # Load with default DPI
    doc = OCRDocument.from_uri(uri)
    
    assert doc.uri == uri
    assert doc.file_format == "pdf"
    assert len(doc.pages) == 1
    assert doc.pages[0].page_number == 1
    assert len(doc.pages[0].image_bytes) > 0
    
    # Verify we can open the image bytes as an image
    pix = fitz.Pixmap(doc.pages[0].image_bytes)
    assert pix.width > 0
    assert pix.height > 0

def test_invalid_scheme():
    with pytest.raises(ValueError, match="Unsupported scheme"):
        OCRDocument.from_uri("ftp://example.com/doc.pdf")

def test_missing_scheme():
    with pytest.raises(ValueError, match="Invalid URI"):
        OCRDocument.from_uri("/path/to/doc.pdf")
