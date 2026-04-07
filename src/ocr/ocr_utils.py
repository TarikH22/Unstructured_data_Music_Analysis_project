import os
from datetime import datetime

import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from PIL import Image, ImageDraw

from utils.logger import logger


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
RAW_IMAGES_DIR = os.path.join(ROOT_DIR, "data", "raw", "images")
RAW_SCANNED_DIR = os.path.join(ROOT_DIR, "data", "raw", "scanned")


def _metadata(source, file_name, extraction_type, page_number=None):
    return {
        "source": source,
        "file_name": file_name,
        "type": extraction_type,
        "page_number": page_number,
        "extraction_timestamp": datetime.utcnow().isoformat() + "Z",
    }


def create_test_scan_image(path):
    image = Image.new("RGB", (1000, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.text((50, 60), "Last.fm OCR Test - Coldplay The Scientist", fill=(0, 0, 0))
    draw.text((50, 120), "Listeners: 2,800,000", fill=(0, 0, 0))
    draw.text((50, 180), "Playcount: 75,000,000", fill=(0, 0, 0))
    image.save(path)


def create_scanned_pdf_from_image(image_path, pdf_path):
    image = Image.open(image_path).convert("RGB")
    image.save(pdf_path, "PDF", resolution=100.0)


def preprocess_image(image):
    gray = image.convert("L")
    return gray.point(lambda p: 255 if p > 150 else 0)


def ocr_image(image_path):
    image = Image.open(image_path)
    processed = preprocess_image(image)

    raw_text = pytesseract.image_to_string(image)
    processed_text = pytesseract.image_to_string(processed)

    return {
        "raw_text": raw_text.strip(),
        "processed_text": processed_text.strip(),
        "metadata": _metadata("ocr-image", os.path.basename(image_path), "ocr-image"),
    }


def ocr_scanned_pdf(pdf_path):
    results = []
    with pdfplumber.open(pdf_path) as pdf:
        native_text = [(page.extract_text() or "").strip() for page in pdf.pages]

    if any(native_text):
        for idx, text in enumerate(native_text, start=1):
            results.append(
                {
                    "raw_text": text,
                    "processed_text": text,
                    "metadata": _metadata(
                        "pdfplumber-native", os.path.basename(pdf_path), "pdf-native", page_number=idx
                    ),
                }
            )
        return results

    images = convert_from_path(pdf_path)
    for idx, image in enumerate(images, start=1):
        processed = preprocess_image(image)
        raw_text = pytesseract.image_to_string(image)
        processed_text = pytesseract.image_to_string(processed)
        results.append(
            {
                "raw_text": raw_text.strip(),
                "processed_text": processed_text.strip(),
                "metadata": _metadata(
                    "scanned-pdf-ocr",
                    os.path.basename(pdf_path),
                    "ocr-pdf",
                    page_number=idx,
                ),
            }
        )

    return results


def process_ocr_assets():
    os.makedirs(RAW_IMAGES_DIR, exist_ok=True)
    os.makedirs(RAW_SCANNED_DIR, exist_ok=True)

    image_path = os.path.join(RAW_IMAGES_DIR, "test_scan.png")
    if not os.path.exists(image_path):
        create_test_scan_image(image_path)

    scanned_pdf_path = os.path.join(RAW_SCANNED_DIR, "test_scanned.pdf")
    if not os.path.exists(scanned_pdf_path):
        create_scanned_pdf_from_image(image_path, scanned_pdf_path)

    records = []
    try:
        records.append(ocr_image(image_path))
        logger.info("OCR image extraction completed")
    except Exception as e:
        logger.error(f"OCR image extraction failed: {e}")

    try:
        records.extend(ocr_scanned_pdf(scanned_pdf_path))
        logger.info("OCR scanned PDF extraction completed")
    except Exception as e:
        logger.error(f"OCR scanned PDF extraction failed: {e}")

    return records
