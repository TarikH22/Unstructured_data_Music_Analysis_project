import json
from pathlib import Path

from fpdf import FPDF
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed" / "documents"
OUT.mkdir(parents=True, exist_ok=True)


def pdf_safe_text(text: str) -> str:
    replacements = {
        "\u2014": "-",
        "\u2013": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.encode("latin-1", "ignore").decode("latin-1")


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_text(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return f.read().strip()


def prepare_images(track_data):
    images_dir = OUT / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    local_webp = RAW / "images" / "Image 300x300.webp"
    local_png = images_dir / "local_cover.png"
    if local_webp.exists():
        Image.open(local_webp).convert("RGB").save(local_png, format="PNG")

    listeners = int(track_data.get("listeners", "0"))
    playcount = int(track_data.get("playcount", "0"))
    stat_image = images_dir / "track_stats.png"
    img = Image.new("RGB", (900, 300), (247, 250, 252))
    draw = ImageDraw.Draw(img)
    draw.rectangle((20, 20, 880, 280), outline=(30, 41, 59), width=3)
    draw.text((40, 45), "Last.fm Snapshot - Coldplay / The Scientist", fill=(15, 23, 42))
    draw.text((40, 110), f"Listeners: {listeners:,}", fill=(30, 41, 59))
    draw.text((40, 160), f"Playcount: {playcount:,}", fill=(30, 41, 59))
    draw.text((40, 220), "Source: data/raw/songs/coldplay_the_scientist.json", fill=(71, 85, 105))
    img.save(stat_image, format="PNG")

    results = []
    if local_png.exists():
        results.append(local_png)
    results.append(stat_image)
    return results


class LastFMPDF(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 14)
        self.cell(0, 10, "Unstructured Data Analysis: Last.fm Case Study", border=0, new_x="LMARGIN", new_y="NEXT", align="C")
        self.ln(3)

    def add_lastfm_table(self, rows, has_border=True):
        self.set_font("helvetica", "B", 10)
        border_val = 1 if has_border else 0
        widths = [55, 85, 45]
        columns = ["Field", "Value", "Source"]
        for idx, col in enumerate(columns):
            self.cell(widths[idx], 9, col, border=border_val)
        self.ln()

        self.set_font("helvetica", "", 10)
        for row in rows:
            for idx, item in enumerate(row):
                self.cell(widths[idx], 9, str(item), border=border_val)
            self.ln()


def create_normal_pdf(track, album, review_text, images):
    pdf = LastFMPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "", 11)

    intro = (
        "This report is generated from the Unstructured_data_Music_Analysis_project. "
        "The pipeline fetches Last.fm data, parses JSON/CSV/XML, stores records in MongoDB, "
        "and uploads selected artifacts to LocalStack S3."
    )
    pdf.multi_cell(0, 7, pdf_safe_text(intro))
    pdf.ln(4)

    rows = [
        ["Artist", track.get("artist", {}).get("name", ""), "track JSON"],
        ["Track", track.get("name", ""), "track JSON"],
        ["Album", album.get("name", ""), "album JSON"],
        ["Listeners", track.get("listeners", ""), "track JSON"],
        ["Playcount", track.get("playcount", ""), "track JSON"],
    ]

    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 9, "Table 1: Bordered Data", new_x="LMARGIN", new_y="NEXT")
    pdf.add_lastfm_table(rows, has_border=True)

    pdf.ln(5)
    pdf.cell(0, 9, "Table 2: Borderless Data", new_x="LMARGIN", new_y="NEXT")
    pdf.add_lastfm_table(rows, has_border=False)

    pdf.ln(6)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 9, "Review Excerpt", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(0, 6, pdf_safe_text(review_text[:900]))

    pdf.ln(5)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 9, "Images", new_x="LMARGIN", new_y="NEXT")
    y_start = pdf.get_y()
    x_start = pdf.get_x()
    for idx, image_path in enumerate(images[:2]):
        pdf.image(str(image_path), x=x_start + idx * 85, y=y_start, w=80)

    output_file = OUT / "LastFM_Normal.pdf"
    pdf.output(str(output_file))
    return output_file


def create_two_column_pdf(track, album):
    pdf = FPDF()
    pdf.add_page()

    margin = 10
    gap = 8
    col_width = (pdf.w - (margin * 2) - gap)
    col_width = col_width / 2

    left_title = "Section 1: Last.fm API"
    left_text = (
        "The Last.fm API provides semi-structured JSON data with track, artist, and album metadata. "
        "In this project, pagination is used to fetch multiple pages and save raw responses for downstream parsing."
    )

    right_title = "Section 2: Pipeline Results"
    right_text = (
        f"Current focus track: {track.get('name', '')} by {track.get('artist', {}).get('name', '')}. "
        f"Album: {album.get('name', '')}. The data is parsed and stored in MongoDB, then selected files are uploaded to mock S3."
    )

    pdf.set_xy(margin, 15)
    pdf.set_font("helvetica", "B", 13)
    pdf.multi_cell(col_width, 8, left_title)
    pdf.set_x(margin)
    pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(col_width, 6, pdf_safe_text(left_text))

    x_right = margin + col_width + gap
    pdf.set_xy(x_right, 15)
    pdf.set_font("helvetica", "B", 13)
    pdf.multi_cell(col_width, 8, right_title)
    pdf.set_x(x_right)
    pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(col_width, 6, pdf_safe_text(right_text))

    output_file = OUT / "LastFM_TwoColumn.pdf"
    pdf.output(str(output_file))
    return output_file


def main():
    track_data = load_json(RAW / "songs" / "coldplay_the_scientist.json").get("track", {})
    album_data = load_json(RAW / "albums" / "coldplay_a_rush_of_blood.json").get("album", {})
    review_text = load_text(RAW / "reviews" / "coldplay_my_universe_review.txt")

    images = prepare_images(track_data)

    normal_pdf = create_normal_pdf(track_data, album_data, review_text, images)
    two_column_pdf = create_two_column_pdf(track_data, album_data)

    print("Generated:")
    print(normal_pdf)
    print(two_column_pdf)


if __name__ == "__main__":
    main()
