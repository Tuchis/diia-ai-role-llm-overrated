from typing import List
from google.cloud import vision
from ..base import OCRProvider
from ..models import OCRDocument, OCRBlock
import os

class CloudVisionOCRProvider(OCRProvider):
    """
    Google Cloud Vision OCR Provider.
    Requires GOOGLE_APPLICATION_CREDENTIALS to be configured in the environment.
    """

    def __init__(self):
        self.client = vision.ImageAnnotatorClient()

    def process(self, document: OCRDocument) -> None:
        for page in document.pages:
            try:
                image = vision.Image(content=page.image_bytes)

                # Use document_text_detection for dense text (PDF/TIFF/Handwriting)
                # or text_detection for sparse text.
                # Given we are doing OCR on documents, document_text_detection is usually better.
                # We also add language hint for Ukrainian.
                image_context = vision.ImageContext(language_hints=["uk"])

                response = self.client.document_text_detection(
                    image=image, image_context=image_context
                )

                if response.error.message:
                    print(
                        f"Error processing page {page.page_number}: {response.error.message}"
                    )
                    continue

                blocks: List[OCRBlock] = []

                for page_annotation in response.full_text_annotation.pages:
                    page_width = page_annotation.width
                    page_height = page_annotation.height

                    for block in page_annotation.blocks:
                        for paragraph in block.paragraphs:
                            line_words = []
                            line_text_parts = []

                            for word in paragraph.words:
                                # Build word text and preserve spacing based on detected break after each symbol
                                word_text = "".join([symbol.text for symbol in word.symbols])
                                # Determine spacing after the word based on the break type of the last symbol
                                last_symbol = word.symbols[-1]
                                break_type = last_symbol.property.detected_break.type
                                # Append a space if the break indicates a space (including EOL_SURE_SPACE)
                                space_suffix = ""
                                if break_type in [
                                    vision.TextAnnotation.DetectedBreak.BreakType.SPACE,
                                    vision.TextAnnotation.DetectedBreak.BreakType.EOL_SURE_SPACE,
                                ]:
                                    space_suffix = " "
                                line_words.append(word)
                                line_text_parts.append(word_text + space_suffix)

                                if break_type in [
                                    vision.TextAnnotation.DetectedBreak.BreakType.EOL_SURE_SPACE,
                                    vision.TextAnnotation.DetectedBreak.BreakType.LINE_BREAK,
                                ]:
                                    self._add_line_block(
                                        blocks,
                                        line_text_parts,
                                        line_words,
                                        page_width,
                                        page_height,
                                    )
                                    line_words = []
                                    line_text_parts = []

                            # End of paragraph is also a line break implicitly if not empty
                            if line_words:
                                self._add_line_block(
                                    blocks,
                                    line_text_parts,
                                    line_words,
                                    page_width,
                                    page_height,
                                )

                page.blocks.extend(blocks)

            except Exception as e:
                print(f"Error processing page {page.page_number}: {e}")
                continue

    def _add_line_block(self, blocks, text_parts, words, page_width, page_height):
        if not words:
            return

        final_text = "".join(text_parts)

        total_conf = sum(w.confidence for w in words if hasattr(w, "confidence"))
        final_conf = total_conf / len(words) if words else 0.0

        min_x, min_y = 1.0, 1.0
        max_x, max_y = 0.0, 0.0

        for word in words:
            for vertex in word.bounding_box.vertices:
                norm_x = vertex.x / page_width if page_width > 0 else 0.0
                norm_y = vertex.y / page_height if page_height > 0 else 0.0

                min_x = min(min_x, norm_x)
                min_y = min(min_y, norm_y)
                max_x = max(max_x, norm_x)
                max_y = max(max_y, norm_y)

        width = max_x - min_x
        height = max_y - min_y

        polygon = [
            {"X": min_x, "Y": min_y},
            {"X": max_x, "Y": min_y},
            {"X": max_x, "Y": max_y},
            {"X": min_x, "Y": max_y},
        ]

        geometry = {
            "BoundingBox": {
                "Width": width,
                "Height": height,
                "Left": min_x,
                "Top": min_y,
            },
            "Polygon": polygon,
        }

        blocks.append(
            OCRBlock(text=final_text, confidence=final_conf, geometry=geometry)
        )
