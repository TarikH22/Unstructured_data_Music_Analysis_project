import os

from PIL import Image, ExifTags


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
EXIF_DIR = os.path.join(ROOT_DIR, "data", "raw", "exif_samples")


def extract_exif_tags(image_path):
    with Image.open(image_path) as img:
        exif = img.getexif()
    if not exif:
        return {}

    exif_data = {}
    for tag_id, value in exif.items():
        tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
        exif_data[tag_name] = value

    # Pillow may expose GPSInfo as an offset/int in generic EXIF items.
    # Resolve the dedicated GPS IFD when available.
    try:
        gps_ifd = exif.get_ifd(34853)  # 34853 == GPSInfo tag id
        if gps_ifd:
            exif_data["GPSInfo"] = gps_ifd
    except Exception:
        pass

    return exif_data


def _gps_to_decimal(gps_tuple, gps_ref):
    if not gps_tuple:
        return None

    def _to_float(value):
        try:
            return float(value)
        except Exception:
            pass
        try:
            return value[0] / value[1]
        except Exception:
            return None

    d = _to_float(gps_tuple[0])
    m = _to_float(gps_tuple[1])
    s = _to_float(gps_tuple[2])
    if d is None or m is None or s is None:
        return None

    if isinstance(gps_ref, bytes):
        gps_ref = gps_ref.decode(errors="ignore")

    decimal = d + (m / 60.0) + (s / 3600.0)
    if gps_ref in ["S", "W"]:
        decimal *= -1
    return decimal


def extract_gps(exif_data):
    gps_info = exif_data.get("GPSInfo")
    if not gps_info or not hasattr(gps_info, "items"):
        return None

    gps_named = {}
    for key, val in gps_info.items():
        gps_named[ExifTags.GPSTAGS.get(key, str(key))] = val

    lat = _gps_to_decimal(gps_named.get("GPSLatitude"), gps_named.get("GPSLatitudeRef"))
    lon = _gps_to_decimal(gps_named.get("GPSLongitude"), gps_named.get("GPSLongitudeRef"))
    if lat is None or lon is None:
        return None
    return {"latitude": lat, "longitude": lon}


def exif_summary(image_path):
    exif_data = extract_exif_tags(image_path)
    summary = {
        "camera_make": exif_data.get("Make"),
        "camera_model": exif_data.get("Model"),
        "datetime_original": exif_data.get("DateTimeOriginal"),
        "datetime": exif_data.get("DateTime"),
        "lens_model": exif_data.get("LensModel"),
        "focal_length": exif_data.get("FocalLength"),
        "iso": exif_data.get("ISOSpeedRatings") or exif_data.get("PhotographicSensitivity"),
        "gps": extract_gps(exif_data),
    }
    return summary


def save_without_exif(image_path, output_path=None):
    if output_path is None:
        base, ext = os.path.splitext(image_path)
        output_path = f"{base}_no_exif{ext}"

    with Image.open(image_path) as img:
        clean = Image.new(img.mode, img.size)
        clean.putdata(list(img.getdata()))
        clean.save(output_path)
    return output_path
