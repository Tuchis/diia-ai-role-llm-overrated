from .models import OCRDocument
from typing import Tuple, Literal, Optional, Dict, List, Any

import pymupdf as fitz
import io
import numpy as np
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from reportlab.pdfbase.pdfmetrics import stringWidth

from .background_inpainter import DummyInpainter, BackgroundInpainterV1, BackgroundInpainterV2, BackgroundInpainterV3


# Register the font once
try:
    pdfmetrics.registerFont(TTFont('Times-New-Roman', 'times.ttf'))
except Exception as e:
    print(f"Warning: Could not register font: {e}")

Align = Literal["left", "right", "center", "justify"]


class TextInpainter:
    def __init__(self, document: OCRDocument):
        self.text_ops: dict[int, list[dict[str, Any]]] = {}

        # bkg_inpainter = DummyInpainter(document)
        bkg_inpainter = BackgroundInpainterV2(document)
        self.document, self.fitz_document = bkg_inpainter.inpaint()

    @staticmethod
    def from_document(document: OCRDocument) -> "TextInpainter":
        return TextInpainter(document)

    @staticmethod
    def _align_to_reportlab(align: Align) -> int:
        if align == "left":
            return TA_LEFT
        if align == "right":
            return TA_RIGHT
        if align == "center":
            return TA_CENTER
        if align == "justify":
            return TA_JUSTIFY
        # fallback
        return TA_LEFT

    @staticmethod
    def _norm_rect_to_page_rect(
        norm_rect: Tuple[float, float, float, float],
        page: fitz.Page,
    ) -> fitz.Rect:
        """
        Convert normalized rect (x0, y0, x1, y1 in 0..1) to page coordinates.
        """
        x0n, y0n, x1n, y1n = norm_rect
        # clamp, just in case
        x0n = max(0.0, min(1.0, x0n))
        x1n = max(0.0, min(1.0, x1n))
        y0n = max(0.0, min(1.0, y0n))
        y1n = max(0.0, min(1.0, y1n))

        pw, ph = page.rect.width, page.rect.height

        x0 = page.rect.x0 + x0n * pw
        y0 = page.rect.y0 + y0n * ph
        x1 = page.rect.x0 + x1n * pw
        y1 = page.rect.y0 + y1n * ph

        return fitz.Rect(x0, y0, x1, y1)

    def add_text_box(
        self,
        page_index: int,
        text: str,
        norm_rect: Tuple[float, float, float, float],
        font_size: float = 12.0,
        font_name: str = "Times-Roman",
        align: Align = "justify",
        color: Tuple[float, float, float] = (0, 0, 0),
        overlay: bool = True,
        encoding: Optional[str] = "utf8",
    ) -> None:
        if page_index not in self.text_ops:
            self.text_ops[page_index] = []

        self.text_ops[page_index].append(
            {
                "text": text,
                "norm_rect": norm_rect,
                "align": align,
            }
        )

    

    def _flush_text_ops(self, page_index: int) -> None:
        if page_index not in self.text_ops or not self.text_ops[page_index]:
            return

        page = self.fitz_document[page_index]
        page_width = page.rect.width
        page_height = page.rect.height

        # Create a ReportLab canvas
        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=(page_width, page_height))

        styles = getSampleStyleSheet()
        style = styles["Normal"]

        # Default font size and family are used as per requirements (styles["Normal"] defaults)

        for op in self.text_ops[page_index]:
            rect = self._norm_rect_to_page_rect(op["norm_rect"], page)

            rl_x = rect.x0
            rl_y = page_height - rect.y1
            rl_width = rect.width
            rl_height = rect.height

            # Draw white background
            # c.saveState()
            # c.setFillColorRGB(1, 1, 1)
            # c.rect(rl_x, rl_y, rl_width, rl_height, fill=1, stroke=0)
            # c.restoreState()

            style.alignment = TA_JUSTIFY
            style.fontSize = rl_height * 0.75
            style.fontName = "Times-New-Roman"

            p = Paragraph(op["text"] + "\n\n", style)
            w, h = p.wrap(rl_width, rl_height)

            draw_y = rl_y + rl_height - h
            p.drawOn(c, rl_x, draw_y)

        c.save()
        packet.seek(0)

        # Overlay the generated PDF onto the existing page
        with fitz.open("pdf", packet) as overlay_doc:
            page.show_pdf_page(page.rect, overlay_doc, 0)

        # Clear operations for this page
        self.text_ops[page_index] = []

    def save(self, out_path: str) -> None:
        # Flush all pending operations before saving
        for page_index in list(self.text_ops.keys()):
            self._flush_text_ops(page_index)
        self.fitz_document.save(out_path)

    def close(self) -> None:
        self.fitz_document.close()

    def render_page_to_pixmap(
        self,
        page_index: int,
        zoom: float = 1.0,
        alpha: bool = False,
    ) -> fitz.Pixmap:
        # Flush operations for this page before rendering
        self._flush_text_ops(page_index)

        page = self.fitz_document[page_index]
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=alpha)

        data = pix.samples
        w, h = pix.width, pix.height
        n = pix.n

        arr = np.frombuffer(data, dtype=np.uint8).reshape(h, w, n)

        if n == 1:
            return arr.copy()

        if n == 3:
            # Convert RGB to BGR
            return arr[:, :, ::-1].copy()

        if n == 4:
            # Convert RGBA to BGRA
            bgr = arr[:, :, [2, 1, 0, 3]].copy()
            return bgr

        raise ValueError(f"Unsupported number of components: {n}")