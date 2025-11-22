import cv2
import numpy as np
from .models import OCRDocument

def visualize_results(document: OCRDocument):
    """
    Visualize OCR results using OpenCV.
    Iterates through pages and shows them one by one.
    """
    for page in document.pages:
        # Convert bytes to numpy array
        nparr = np.frombuffer(page.image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            print(f"Could not decode image for page {page.page_number}.")
            continue

        height, width, _ = image.shape

        for block in page.blocks:
            if block.geometry and "BoundingBox" in block.geometry:
                box = block.geometry["BoundingBox"]
                x = int(box["Left"] * width)
                y = int(box["Top"] * height)
                w = int(box["Width"] * width)
                h = int(box["Height"] * height)

                # Color based on confidence
                if block.confidence > 0.9:
                    color = (0, 255, 0)  # Green
                elif block.confidence > 0.5:
                    color = (0, 165, 255) # Orange (BGR)
                else:
                    color = (0, 0, 255)  # Red

                # Draw rectangle
                cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)

        max_im_size = max(width, height)
        if max_im_size > 1024:
            scale = 1024 / max_im_size
            image = cv2.resize(image, (int(width * scale), int(height * scale)))

        cv2.imshow(f"OCR Results - Page {page.page_number}", image)
        print(f"Showing page {page.page_number}. Press any key to continue to next page (or exit if last).")
        cv2.waitKey(0)
        cv2.destroyWindow(f"OCR Results - Page {page.page_number}")
    
    cv2.destroyAllWindows()
