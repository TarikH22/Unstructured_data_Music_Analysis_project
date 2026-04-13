import os
from datetime import datetime

try:
    from tqdm import tqdm
except Exception:
    def tqdm(iterable, **kwargs):
        return iterable

from image_processing.downloader import download_poster_images
from image_processing.exif_utils import exif_summary, save_without_exif
from image_processing.processor import (
    apply_enhancements,
    apply_filters,
    convert_to_grayscale,
    convert_to_jpeg,
    convert_to_png,
    convert_to_webp,
    crop_image,
    generate_fixed_thumbnail,
    generate_thumbnail,
    inspect_image,
    resize_image,
    resize_proportional,
    save_optimised_jpeg,
)
from utils.logger import logger
from utils.upload_utils import upload_batch


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
RAW_IMAGES_DIR = os.path.join(ROOT_DIR, "data", "raw", "images")
EXIF_DIR = os.path.join(ROOT_DIR, "data", "raw", "exif_samples")


def _valid_image(path):
    ext = os.path.splitext(path)[1].lower()
    return ext in {".jpg", ".jpeg", ".png", ".webp"}


def process_single(image_path, source="lastfm_api", item_type="poster"):
    info = inspect_image(image_path)

    resized = resize_image(image_path)
    resized_prop = resize_proportional(image_path)
    thumb = generate_thumbnail(image_path)
    thumb_fixed = generate_fixed_thumbnail(image_path, mode="fit")
    cropped_banner = crop_image(image_path, crop_type="banner")
    cropped_square = crop_image(image_path, crop_type="center_square")
    cropped_custom = crop_image(image_path, crop_type="custom_box")
    webp_file = convert_to_webp(image_path)
    png_file = convert_to_png(image_path)
    jpeg_quality_file = convert_to_jpeg(image_path, quality=82)
    gray_file = convert_to_grayscale(image_path)
    optim_jpeg = save_optimised_jpeg(image_path)
    filter_outputs = apply_filters(image_path)
    enhanced_file = apply_enhancements(image_path)

    exif_data = exif_summary(image_path)

    metadata = {
        "source": source,
        "type": item_type,
        "file_name": os.path.basename(image_path),
        "document_type": "image",
        "extraction_timestamp": datetime.utcnow().isoformat() + "Z",
        "original_path": image_path,
        "resized_path": resized,
        "resized_proportional_path": resized_prop,
        "thumbnail_path": thumb,
        "fixed_thumbnail_path": thumb_fixed,
        "cropped_banner_path": cropped_banner,
        "cropped_square_path": cropped_square,
        "cropped_custom_box_path": cropped_custom,
        "webp_path": webp_file,
        "png_path": png_file,
        "jpeg_quality_path": jpeg_quality_file,
        "grayscale_path": gray_file,
        "optimized_jpeg_path": optim_jpeg,
        "enhanced_path": enhanced_file,
        "filter_outputs": filter_outputs,
        "processed_at": datetime.utcnow().isoformat() + "Z",
    }

    return {
        "movie_id": None,
        "title": os.path.splitext(os.path.basename(image_path))[0],
        "format": info.get("format"),
        "mode": info.get("mode"),
        "width": info.get("width"),
        "height": info.get("height"),
        "aspect_ratio": info.get("aspect_ratio"),
        "file_size_bytes": info.get("file_size_bytes"),
        "file_size_kb": info.get("file_size_kb"),
        "exif": exif_data,
        "metadata": metadata,
    }


def _collect_input_images(max_images=50):
    downloaded = download_poster_images(max_images=max_images)
    images = [p for p in downloaded if os.path.exists(p) and _valid_image(p)]

    if not images and os.path.isdir(RAW_IMAGES_DIR):
        for name in sorted(os.listdir(RAW_IMAGES_DIR)):
            path = os.path.join(RAW_IMAGES_DIR, name)
            if os.path.isfile(path) and _valid_image(path):
                images.append(path)
            if len(images) >= max_images:
                break

    return images[:max_images]


def _process_exif_samples():
    records = []
    if not os.path.isdir(EXIF_DIR):
        return records

    sample_files = [
        name
        for name in sorted(os.listdir(EXIF_DIR))
        if os.path.isfile(os.path.join(EXIF_DIR, name)) and _valid_image(os.path.join(EXIF_DIR, name))
    ]
    if len(sample_files) < 2:
        logger.warning(
            f"EXIF requirement not met yet: found {len(sample_files)} sample photo(s), expected at least 2"
        )

    for name in sample_files:
        path = os.path.join(EXIF_DIR, name)
        try:
            summary = exif_summary(path)
            stripped = save_without_exif(path)
            records.append(
                {
                    "title": os.path.splitext(name)[0],
                    "format": inspect_image(path).get("format"),
                    "mode": inspect_image(path).get("mode"),
                    "width": inspect_image(path).get("width"),
                    "height": inspect_image(path).get("height"),
                    "aspect_ratio": inspect_image(path).get("aspect_ratio"),
                    "file_size_bytes": inspect_image(path).get("file_size_bytes"),
                    "file_size_kb": inspect_image(path).get("file_size_kb"),
                    "exif": summary,
                    "metadata": {
                        "source": "exif-sample",
                        "type": "exif-photo",
                        "document_type": "image",
                        "file_name": name,
                        "extraction_timestamp": datetime.utcnow().isoformat() + "Z",
                        "original_path": path,
                        "stripped_path": stripped,
                        "processed_at": datetime.utcnow().isoformat() + "Z",
                    },
                }
            )
        except Exception as e:
            logger.error(f"Failed EXIF sample processing for {path}: {e}")
    return records


def batch_process_images(max_images=50, upload_to_drive=True):
    image_paths = _collect_input_images(max_images=max_images)
    records = []
    upload_candidates = []

    for image_path in tqdm(image_paths, desc="Processing images"):
        try:
            record = process_single(image_path)
            records.append(record)
            upload_candidates.append(record["metadata"]["webp_path"])
            upload_candidates.append(record["metadata"]["thumbnail_path"])
        except Exception as e:
            logger.error(f"Failed processing image {image_path}: {e}")

    exif_records = _process_exif_samples()
    records.extend(exif_records)

    drive_results = []
    if upload_to_drive and upload_candidates:
        drive_results = upload_batch(upload_candidates)

    logger.info(
        f"Image batch complete: inputs={len(image_paths)}, processed={len(records)}, drive_uploads={len(drive_results)}"
    )
    return records
