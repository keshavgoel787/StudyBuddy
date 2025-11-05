import pytesseract
from PIL import Image
from pathlib import Path


def extract_text_from_image(image_path: Path) -> str:
    """
    Extract text from an image using Tesseract OCR.

    Args:
        image_path: Path to the image file

    Returns:
        Extracted text as string
    """
    try:
        # Open image
        image = Image.open(image_path)

        # Perform OCR
        text = pytesseract.image_to_string(image)

        return text.strip()
    except Exception as e:
        raise Exception(f"OCR failed: {str(e)}")
