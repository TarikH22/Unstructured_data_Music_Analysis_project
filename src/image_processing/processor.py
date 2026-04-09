import os

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
PROCESSED_DIR = os.path.join(ROOT_DIR, "data", "processed")
RESIZED_DIR = os.path.join(PROCESSED_DIR, "resized")
THUMB_DIR = os.path.join(PROCESSED_DIR, "thumbnails")
CROPPED_DIR = os.path.join(PROCESSED_DIR, "cropped")
WEBP_DIR = os.path.join(PROCESSED_DIR, "webp")


def _ensure_dirs():
    for path in [RESIZED_DIR, THUMB_DIR, CROPPED_DIR, WEBP_DIR]:
        os.makedirs(path, exist_ok=True)


def inspect_image(path):
    with Image.open(path) as img:
        file_size = os.path.getsize(path)
        return {
            "path": path,
            "format": img.format,
            "mode": img.mode,
            "size": img.size,
            "width": img.width,
            "height": img.height,
            "file_size_bytes": file_size,
            "file_size_kb": round(file_size / 1024, 2),
            "aspect_ratio": round(img.width / img.height, 4) if img.height else None,
        }


def resize_proportional(path, max_size=(640, 960), resample=Image.Resampling.LANCZOS):
    _ensure_dirs()
    with Image.open(path) as img:
        copy_img = img.copy()
        copy_img.thumbnail(max_size, resample=resample)
        base = os.path.splitext(os.path.basename(path))[0]
        output = os.path.join(RESIZED_DIR, f"{base}_prop.jpg")
        copy_img.convert("RGB").save(output, quality=90)
    return output


def resize_image(path, size=(640, 960), resample=Image.Resampling.BICUBIC):
    _ensure_dirs()
    with Image.open(path) as img:
        resized = img.resize(size, resample=resample)
        base = os.path.splitext(os.path.basename(path))[0]
        output = os.path.join(RESIZED_DIR, f"{base}_fixed.jpg")
        resized.convert("RGB").save(output, quality=90)
    return output


def generate_thumbnail(path, size=(256, 256)):
    _ensure_dirs()
    with Image.open(path) as img:
        thumb = img.copy()
        thumb.thumbnail(size, Image.Resampling.LANCZOS)
        base = os.path.splitext(os.path.basename(path))[0]
        output = os.path.join(THUMB_DIR, f"{base}_thumb.jpg")
        thumb.convert("RGB").save(output, quality=88)
    return output


def generate_fixed_thumbnail(path, size=(256, 256), mode="fit"):
    _ensure_dirs()
    with Image.open(path) as img:
        if mode == "contain":
            out_img = ImageOps.contain(img, size, Image.Resampling.LANCZOS)
        elif mode == "cover":
            out_img = ImageOps.cover(img, size, Image.Resampling.LANCZOS)
        elif mode == "pad":
            out_img = ImageOps.pad(img, size, color=(16, 16, 16))
        else:
            out_img = ImageOps.fit(img, size, Image.Resampling.LANCZOS)

        base = os.path.splitext(os.path.basename(path))[0]
        output = os.path.join(THUMB_DIR, f"{base}_thumb_fixed.jpg")
        out_img.convert("RGB").save(output, quality=88)
    return output


def crop_image(path, crop_type="banner"):
    _ensure_dirs()
    with Image.open(path) as img:
        w, h = img.size
        if crop_type == "center_square":
            side = min(w, h)
            left = (w - side) // 2
            top = (h - side) // 2
            box = (left, top, left + side, top + side)
        elif crop_type == "custom_box":
            # Custom crop box tuned for portrait poster images.
            left = int(w * 0.1)
            top = int(h * 0.2)
            right = int(w * 0.9)
            bottom = int(h * 0.85)
            box = (left, top, right, bottom)
        elif crop_type == "top_half":
            box = (0, 0, w, h // 2)
        else:
            # banner default
            banner_h = int(h * 0.35)
            box = (0, 0, w, banner_h)

        cropped = img.crop(box)
        base = os.path.splitext(os.path.basename(path))[0]
        output = os.path.join(CROPPED_DIR, f"{base}_{crop_type}.jpg")
        cropped.convert("RGB").save(output, quality=90)
    return output


def convert_to_webp(path, quality=85):
    _ensure_dirs()
    with Image.open(path) as img:
        base = os.path.splitext(os.path.basename(path))[0]
        output = os.path.join(WEBP_DIR, f"{base}.webp")
        img.convert("RGB").save(output, "WEBP", quality=quality, method=6)
    return output


def convert_to_png(path, compress_level=6):
    _ensure_dirs()
    with Image.open(path) as img:
        base = os.path.splitext(os.path.basename(path))[0]
        output = os.path.join(WEBP_DIR, f"{base}.png")
        img.convert("RGB").save(output, "PNG", optimize=True, compress_level=compress_level)
    return output


def convert_to_jpeg(path, quality=88):
    _ensure_dirs()
    with Image.open(path) as img:
        base = os.path.splitext(os.path.basename(path))[0]
        output = os.path.join(RESIZED_DIR, f"{base}_q{quality}.jpg")
        img.convert("RGB").save(output, "JPEG", quality=quality, optimize=True, progressive=True)
    return output


def convert_to_grayscale(path):
    _ensure_dirs()
    with Image.open(path) as img:
        gray = img.convert("L")
        base = os.path.splitext(os.path.basename(path))[0]
        output = os.path.join(WEBP_DIR, f"{base}_gray.jpg")
        gray.save(output, quality=90)
    return output


def save_optimised_jpeg(path, quality=82):
    _ensure_dirs()
    with Image.open(path) as img:
        base = os.path.splitext(os.path.basename(path))[0]
        output = os.path.join(RESIZED_DIR, f"{base}_optim.jpg")
        img.convert("RGB").save(output, "JPEG", quality=quality, optimize=True, progressive=True)
    return output


def apply_filters(path):
    _ensure_dirs()
    outputs = {}
    with Image.open(path) as img:
        base = os.path.splitext(os.path.basename(path))[0]
        blur = img.filter(ImageFilter.GaussianBlur(radius=3))
        blur_path = os.path.join(CROPPED_DIR, f"{base}_blur.jpg")
        blur.convert("RGB").save(blur_path, quality=88)
        outputs["blur"] = blur_path

        sharpen = img.filter(ImageFilter.SHARPEN)
        sharpen_path = os.path.join(CROPPED_DIR, f"{base}_sharpen.jpg")
        sharpen.convert("RGB").save(sharpen_path, quality=88)
        outputs["sharpen"] = sharpen_path

        edge = img.filter(ImageFilter.FIND_EDGES)
        edge_path = os.path.join(CROPPED_DIR, f"{base}_edges.jpg")
        edge.convert("RGB").save(edge_path, quality=88)
        outputs["edges"] = edge_path

    return outputs


def apply_enhancements(path, brightness=1.1, contrast=1.15, color=1.1, sharpness=1.2):
    _ensure_dirs()
    with Image.open(path) as img:
        result = ImageEnhance.Brightness(img).enhance(brightness)
        result = ImageEnhance.Contrast(result).enhance(contrast)
        result = ImageEnhance.Color(result).enhance(color)
        result = ImageEnhance.Sharpness(result).enhance(sharpness)
        base = os.path.splitext(os.path.basename(path))[0]
        output = os.path.join(RESIZED_DIR, f"{base}_enhanced.jpg")
        result.convert("RGB").save(output, quality=90)
    return output
