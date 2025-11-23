import cv2
import numpy as np
from pathlib import Path
from .models import OCRDocument, OCRBlock
from .text_inpainter import TextInpainter
import boto3
import tempfile

s3 = boto3.client('s3')
bucket = "diia-translation-bucket"

def _unpack_bbox(bbox: dict[str, float]) -> tuple[float, float, float, float]:
    return bbox["Left"], bbox["Top"], bbox["Width"], bbox["Height"]


def _iou(
    bbox1: tuple[float, float, float, float], bbox2: tuple[float, float, float, float]
) -> float:
    x1, y1, w1, h1 = bbox1
    x2, y2, w2, h2 = bbox2

    intersection = max(0, min(x1 + w1, x2 + w2) - max(x1, x2)) * max(
        0, min(y1 + h1, y2 + h2) - max(y1, y2)
    )
    union = w1 * h1 + w2 * h2 - intersection + 1e-6
    return intersection / union


def _nms_filter(
    blocks: list[OCRBlock],
    min_confidence: float = 0.8,
    max_iou: float = 0.35,
    max_aspect_discrepancy: float = 3,
) -> list[OCRBlock]:
    block_idx_by_confidence = list(range(len(blocks)))
    block_idx_by_confidence.sort(key=lambda i: blocks[i].confidence, reverse=True)
    bboxes = [_unpack_bbox(block.geometry["BoundingBox"]) for block in blocks]
    dropped_idxs = set()

    for i, bbox in enumerate(bboxes):
        text_len = len(blocks[i].text)
        box_w, box_h = bbox[2], bbox[3]
        bbox_aspect = box_w / box_h

        if text_len / bbox_aspect > max_aspect_discrepancy and len(blocks[i].text) < 20:
            dropped_idxs.add(i)

    for j, idx in enumerate(block_idx_by_confidence):
        if idx in dropped_idxs:
            continue

        for other_idx in block_idx_by_confidence[j + 1 :]:
            if other_idx in dropped_idxs:
                continue

            if blocks[other_idx].confidence < min_confidence:
                dropped_idxs.add(other_idx)
                continue

            iou = _iou(bboxes[idx], bboxes[other_idx])
            if iou > max_iou:
                dropped_idxs.add(idx)
                dropped_idxs.add(other_idx)

    return [blocks[i] for i in block_idx_by_confidence if i not in dropped_idxs]


def visualize_results(document: OCRDocument, output_path: Path):
    for page in document.pages:
        page.blocks = _nms_filter(page.blocks)

    document = document.copy()
    painter = TextInpainter.from_document(document)

    for page in document.pages:
        nparr = np.frombuffer(page.image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            print(f"Could not decode image for page {page.page_number}.")
            continue

        height, width, _ = image.shape

        for block in page.blocks:
            if block.geometry and "BoundingBox" in block.geometry:
                box = block.geometry["BoundingBox"]
                x, y, w, h = _unpack_bbox(box)

                painter.add_text_box(
                    page.page_number - 1,
                    block.text,
                    (x, y, x + w, y + h),
                )

    print("Saving image...")
    with tempfile.TemporaryDirectory() as tmpdirname:
        painter.save(f"{tmpdirname}/result.pdf")
        print(f"{output_path=}")
        with open(f"{tmpdirname}/result.pdf", "rb") as f:
            s3.put_object(Bucket=bucket, Key=output_path, Body=f.read())


