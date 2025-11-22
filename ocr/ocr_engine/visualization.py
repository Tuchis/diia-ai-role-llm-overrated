import cv2
from .models import OCRResult

def visualize_results(file_path: str, result: OCRResult):
    """
    Visualize OCR results using OpenCV.
    """
    image = cv2.imread(file_path)
    if image is None:
        print(f"Could not read image {file_path} for visualization.")
        return

    height, width, _ = image.shape

    for block in result.blocks:
        if block.geometry and "BoundingBox" in block.geometry:
            box = block.geometry["BoundingBox"]
            x = int(box["Left"] * width)
            y = int(box["Top"] * height)
            w = int(box["Width"] * width)
            h = int(box["Height"] * height)

            # Draw rectangle
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Put text
            cv2.putText(
                image,
                block.text,
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )

    max_im_size = max(width, height)
    if max_im_size > 1024:
        scale = 1024 / max_im_size
        image = cv2.resize(image, (int(width * scale), int(height * scale)))

    cv2.imshow("OCR Results", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
