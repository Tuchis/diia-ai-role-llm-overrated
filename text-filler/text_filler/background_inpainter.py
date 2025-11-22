from .models import OCRDocument, OCRPage
import io
import numpy as np
import cv2
import pymupdf as fitz
from typing import TypeAlias
from math import floor, ceil

def clamp(x: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(x, max_val))

BBox: TypeAlias = tuple[int, int, int, int]

class DummyInpainter:
    def __init__(self, document: OCRDocument):
        self.document = document

    def inpaint(self) -> tuple[OCRDocument, fitz.Document]:
        # decode pages into numpy arrays, bboxes into pixel coordinates
        # inpaint
        # encode back every page
        fitz_document = fitz.open()
        for page in self.document.pages:
            with (
                io.BytesIO(page.image_bytes) as stream,
                fitz.open(stream=stream) as tmp_document,
            ):
                rect = tmp_document[0].rect  # image dimensions

                new_page: fitz.Page = fitz_document.new_page(
                    width=rect.width, height=rect.height
                )

                new_page.insert_image(rect, stream=stream)
        return self.document, fitz_document

class BackgroundInpainterV1:
    """
    Per-block inpainting
    """
    def __init__(self, document: OCRDocument, block_mask_offset: float = 0.000):
        self.document = document
        self.block_mask_offset = block_mask_offset

    def inpaint(self) -> tuple[OCRDocument, fitz.Document]:
        # decode pages into numpy arrays, bboxes into pixel coordinates
        # inpaint
        # encode back every page
        fitz_document = fitz.open()
        for page in self.document.pages:
            page = self._inpaint_page(page)
            with (
                io.BytesIO(page.image_bytes) as stream,
                fitz.open(stream=stream) as tmp_document,
            ):
                rect = tmp_document[0].rect  # image dimensions

                new_page: fitz.Page = fitz_document.new_page(
                    width=rect.width, height=rect.height
                )

                new_page.insert_image(rect, stream=stream)
        return self.document, fitz_document

    def _inpaint_page(self, page: OCRPage) -> OCRPage:
        page_image = cv2.imdecode(np.frombuffer(page.image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)

        im_h, im_w = page_image.shape[:2]

        for block in page.blocks:
            x, y, w, h = block.decode_bbox_xywh()
            x = clamp(x - self.block_mask_offset, 0, 1)
            y = clamp(y - self.block_mask_offset, 0, 1)
            w = clamp(w + self.block_mask_offset * 2, 0, 1 - x)
            h = clamp(h + self.block_mask_offset * 2, 0, 1 - y)
            x, y, w, h = floor(x * im_w), floor(y * im_h), ceil(w * im_w), ceil(h * im_h)

            self._inpaint_block(page_image, (x, y, w, h))

        page.image_bytes = cv2.imencode(".png", page_image)[1].tobytes()

        return page

    def _inpaint_block(self, page_image: np.ndarray, block_bbox_xywh: BBox):
        x, y, w, h = block_bbox_xywh
        block_image = page_image[y:y+h, x:x+w]
        block_image_gray = cv2.cvtColor(block_image, cv2.COLOR_BGR2GRAY)

        otsu_threshold, inpaint_mask = cv2.threshold(block_image_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        inpaint_mask = cv2.morphologyEx(inpaint_mask, cv2.MORPH_DILATE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))

        cv2.inpaint(block_image, inpaint_mask, 3, cv2.INPAINT_TELEA, dst=block_image)
        
        gray_and_mask = cv2.cvtColor(np.vstack((block_image_gray, inpaint_mask)), cv2.COLOR_GRAY2BGR)

        cv2.imshow("block", np.vstack((gray_and_mask, block_image)))
        cv2.waitKey(0)
        cv2.destroyWindow("block")


class BackgroundInpainterV2:
    """
    Per-page inpainting
    """
    def __init__(self, document: OCRDocument, block_mask_offset: float = 0.000):
        self.document = document
        self.block_mask_offset = block_mask_offset

    def inpaint(self) -> tuple[OCRDocument, fitz.Document]:
        # decode pages into numpy arrays, bboxes into pixel coordinates
        # inpaint
        # encode back every page
        fitz_document = fitz.open()
        for page in self.document.pages:
            page = self._inpaint_page(page)
            with (
                io.BytesIO(page.image_bytes) as stream,
                fitz.open(stream=stream) as tmp_document,
            ):
                rect = tmp_document[0].rect  # image dimensions

                new_page: fitz.Page = fitz_document.new_page(
                    width=rect.width, height=rect.height
                )

                new_page.insert_image(rect, stream=stream)
        return self.document, fitz_document

    def _inpaint_page(self, page: OCRPage) -> OCRPage:
        page_image = cv2.imdecode(np.frombuffer(page.image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)

        im_h, im_w = page_image.shape[:2]

        page_inpaint_mask = np.zeros((im_h, im_w), dtype=np.uint8)

        for block in page.blocks:
            x, y, w, h = block.decode_bbox_xywh()
            x = clamp(x - self.block_mask_offset, 0, 1)
            y = clamp(y - self.block_mask_offset, 0, 1)
            w = clamp(w + self.block_mask_offset * 2, 0, 1 - x)
            h = clamp(h + self.block_mask_offset * 2, 0, 1 - y)
            x, y, w, h = floor(x * im_w), floor(y * im_h), ceil(w * im_w), ceil(h * im_h)

            self._inpaint_block(page_image, page_inpaint_mask, (x, y, w, h))

        cv2.inpaint(page_image, page_inpaint_mask, 3, cv2.INPAINT_TELEA, dst=page_image)

        page.image_bytes = cv2.imencode(".png", page_image)[1].tobytes()

        return page

    def _inpaint_block(self, page_image: np.ndarray, page_inpaint_mask: np.ndarray, block_bbox_xywh: BBox):
        x, y, w, h = block_bbox_xywh
        block_image = page_image[y:y+h, x:x+w]
        block_image_gray = cv2.cvtColor(block_image, cv2.COLOR_BGR2GRAY)

        otsu_threshold, inpaint_mask = cv2.threshold(block_image_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        inpaint_mask = cv2.morphologyEx(inpaint_mask, cv2.MORPH_DILATE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))

        page_inpaint_mask[y:y+h, x:x+w] = inpaint_mask

class BackgroundInpainterV3:
    """
    Median per-block inpainting
    """
    def __init__(self, document: OCRDocument, block_mask_offset: float = 0.000):
        self.document = document
        self.block_mask_offset = block_mask_offset

    def inpaint(self) -> tuple[OCRDocument, fitz.Document]:
        # decode pages into numpy arrays, bboxes into pixel coordinates
        # inpaint
        # encode back every page
        fitz_document = fitz.open()
        for page in self.document.pages:
            page = self._inpaint_page(page)
            with (
                io.BytesIO(page.image_bytes) as stream,
                fitz.open(stream=stream) as tmp_document,
            ):
                rect = tmp_document[0].rect  # image dimensions

                new_page: fitz.Page = fitz_document.new_page(
                    width=rect.width, height=rect.height
                )

                new_page.insert_image(rect, stream=stream)
        return self.document, fitz_document

    def _inpaint_page(self, page: OCRPage) -> OCRPage:
        page_image = cv2.imdecode(np.frombuffer(page.image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)

        im_h, im_w = page_image.shape[:2]

        for block in page.blocks:
            x, y, w, h = block.decode_bbox_xywh()
            x = clamp(x - self.block_mask_offset, 0, 1)
            y = clamp(y - self.block_mask_offset, 0, 1)
            w = clamp(w + self.block_mask_offset * 2, 0, 1 - x)
            h = clamp(h + self.block_mask_offset * 2, 0, 1 - y)
            x, y, w, h = floor(x * im_w), floor(y * im_h), ceil(w * im_w), ceil(h * im_h)

            self._inpaint_block(page_image, (x, y, w, h))

        page.image_bytes = cv2.imencode(".png", page_image)[1].tobytes()

        return page

    def _inpaint_block(self, page_image: np.ndarray, block_bbox_xywh: BBox):
        x, y, w, h = block_bbox_xywh
        block_image = page_image[y:y+h, x:x+w]
        block_image_gray = cv2.cvtColor(block_image, cv2.COLOR_BGR2GRAY)

        otsu_threshold, inpaint_mask = cv2.threshold(block_image_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        inpaint_mask = cv2.morphologyEx(inpaint_mask, cv2.MORPH_DILATE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))).astype(bool)

        inpaint_mask_inv = ~inpaint_mask
        pixel_values = block_image[inpaint_mask_inv]

        median_value = np.median(pixel_values, axis=0)
        block_image[:, :, :] = median_value
        
        gray_and_mask = cv2.cvtColor(np.vstack((block_image_gray, inpaint_mask.astype(np.uint8) * 255)), cv2.COLOR_GRAY2BGR)

        # cv2.imshow("block", np.vstack((gray_and_mask, block_image)))
        # chr_key = cv2.waitKey(0)
        # if chr_key == ord("q"):
        #     exit()
        # cv2.destroyWindow("block")