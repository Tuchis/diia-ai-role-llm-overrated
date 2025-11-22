import cv2
import numpy as np
from pathlib import Path
from .models import OCRDocument
from .text_inpainter import TextInpainter


def _unpack_bbox(bbox: dict[str, float]) -> tuple[float, float, float, float]:
    return bbox["Left"], bbox["Top"], bbox["Width"], bbox["Height"]


def visualize_results(document: OCRDocument, output_path: Path):
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
                    font_size=12,
                    font_name="Times-Roman",
                    align="justify",
                    color=(0, 0, 0),
                )

                # Color based on confidence
                # if block.confidence > 0.9:
                #     color = (0, 255, 0)  # Green
                # elif block.confidence > 0.5:
                #     color = (0, 165, 255) # Orange (BGR)
                # else:
                #     color = (0, 0, 255)  # Red

                # # Draw rectangle
                # cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)

    # for i, page in enumerate(document.pages):
    #     image = painter.render_page_to_pixmap(i)

    #     height, width, _ = image.shape

    #     max_im_size = max(width, height)
    #     if max_im_size > 1024:
    #         scale = 1024 / max_im_size
    #         image = cv2.resize(image, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_AREA)

    #     window_title = f"OCR Results - Page {i + 1}"

    #     cv2.imshow(window_title, image)
    #     print(
    #         f"Showing page {i + 1}. Press any key to continue to next page (or exit if last)."
    #     )
    #     cv2.waitKey(0)
    #     cv2.destroyWindow(window_title)
    # cv2.destroyAllWindows()

    painter.save(output_path)

