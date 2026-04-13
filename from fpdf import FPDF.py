from fpdf import FPDF

class LastFMPDF(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 15)
        self.cell(0, 10, "Unstructured Data Analysis: Last.fm Case Study", border=0, ln=1, align="C")
        self.ln(5)

    def add_lastfm_table(self, has_border=True):
        self.set_font("helvetica", "B", 10)
        border_val = 1 if has_border else 0
        
        # Table Header
        columns = ["Artist", "Top Track", "Playcount"]
        for col in columns:
            self.cell(60, 10, col, border=border_val)
        self.ln()
        
        # Table Data
        self.set_font("helvetica", "", 10)
        data = [
            ["Radiohead", "Creep", "2,500,120"],
            ["The Weeknd", "Blinding Lights", "4,100,500"],
            ["Arctic Monkeys", "Do I Wanna Know?", "3,200,800"]
        ]
        for row in data:
            for item in row:
                self.cell(60, 10, item, border=border_val)
            self.ln()

# --- 1. CREATE NORMAL PDF ---
pdf = LastFMPDF()
pdf.add_page()
pdf.set_font("helvetica", "", 11)

pdf.multi_cell(0, 8, "Last.fm provides a massive repository of unstructured and semi-structured data via its API. This includes user-generated tags, scrobble history, and artist biographies. Managing this requires handling JSON formats and Natural Language Processing (NLP) for sentiment analysis of reviews.")

pdf.ln(5)
pdf.set_font("helvetica", "B", 12)
pdf.cell(0, 10, "Table 1: Bordered Data (Top Global Artists)", ln=1)
pdf.add_lastfm_table(has_border=True)

pdf.ln(10)
pdf.cell(0, 10, "Table 2: Borderless Layout (User Metadata)", ln=1)
pdf.add_lastfm_table(has_border=False)

# To add images, uncomment and ensure you have image files in the folder:
# pdf.image("lastfm_logo.png", x=10, y=None, w=30)

pdf.output("LastFM_Normal.pdf")

# --- 2. CREATE TWO-COLUMN PDF ---
pdf_col = FPDF()
pdf_col.add_page()
col_width = (pdf_col.w - 30) / 2

# Left Column
pdf_col.set_font("helvetica", "B", 14)
pdf_col.cell(col_width, 10, "Section 1: The API", ln=0)
pdf_col.set_font("helvetica", "", 10)
pdf_col.set_xy(10, 25)
api_text = "The Last.fm API allows users to interact with music data. It serves JSON and XML formats, which are classic examples of semi-structured data. Researchers use this to build recommendation engines based on collaborative filtering."
pdf_col.multi_cell(col_width, 7, api_text)

# Right Column
pdf_col.set_xy(col_width + 20, 15)
pdf_col.set_font("helvetica", "B", 14)
pdf_col.cell(col_width, 10, "Section 2: Folksonomy", ln=0)
pdf_col.set_xy(col_width + 20, 25)
pdf_col.set_font("helvetica", "", 10)
tag_text = "User tags (e.g., 'chill', '90s synthwave') represent a folksonomy. This unstructured labeling creates a unique challenge for data cleaning and normalization in big data pipelines."
pdf_col.multi_cell(col_width, 7, tag_text)

pdf_col.output("LastFM_TwoColumn.pdf")

print("Files 'LastFM_Normal.pdf' and 'LastFM_TwoColumn.pdf' created!")