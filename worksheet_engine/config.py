"""Design system + global settings. Change brand, colours, fonts HERE only."""
import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
DATA = ROOT / "data"

TEMPLATE_VERSION = "1.0"          # bump to force rebuild of every product

# ---------------------------------------------------------------- brand
BRAND = {
    "name": "Little Sprouts Learning",
    "year": datetime.date.today().year,
    "license_en": "For personal, homeschool and classroom use only. Do not resell or redistribute.",
    "license_id": "Hanya untuk penggunaan pribadi, homeschool dan kelas. Dilarang menjual ulang.",
}

# ---------------------------------------------------------------- page (A4 portrait)
PAGE_W, PAGE_H = A4            # 595.27 x 841.89 pt
MARGIN = 36
HEADER_H = 178                 # space reserved for header module
FOOTER_H = 70                  # space reserved for footer module
CONTENT_TOP = PAGE_H - HEADER_H - 8
CONTENT_BOTTOM = FOOTER_H + 10
CONTENT_W = PAGE_W - 2 * MARGIN

# ---------------------------------------------------------------- palette (bright, soft, child-friendly)
def hx(s): return HexColor(s) if isinstance(s, str) else s

PALETTE = {
    "ink":     "#2B2B3A",
    "grey":    "#7A7A8C",
    "line":    "#C9C9D6",
    "coral":   "#FF7A6B",
    "sky":     "#4FB3E8",
    "sun":     "#FFC83D",
    "mint":    "#4CC9A0",
    "grape":   "#9B7BE0",
}
TINT = {  # 12% tints for backgrounds
    "coral": "#FFE9E6", "sky": "#E3F4FD", "sun": "#FFF5D6",
    "mint": "#DFF7EF",  "grape": "#EFE9FB",
}
BRAND_STRIPE = ["coral", "sun", "mint", "sky", "grape"]

# ---------------------------------------------------------------- fonts
# Drop Fredoka / Baloo / Nunito .ttf files in assets/fonts to get a rounder look.
_CANDIDATES = [
    (ASSETS / "fonts" / "Fredoka-Bold.ttf", ASSETS / "fonts" / "Fredoka-Regular.ttf"),
    (ASSETS / "fonts" / "Baloo2-Bold.ttf",  ASSETS / "fonts" / "Baloo2-Regular.ttf"),
    (Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
     Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")),
]
FONT_BOLD, FONT_REG = "Helvetica-Bold", "Helvetica"
for b, r in _CANDIDATES:
    if b.exists() and r.exists():
        pdfmetrics.registerFont(TTFont("WS-Bold", str(b)))
        pdfmetrics.registerFont(TTFont("WS-Reg", str(r)))
        FONT_BOLD, FONT_REG = "WS-Bold", "WS-Reg"
        break

# ---------------------------------------------------------------- language helpers
# English nouns that take no "a/an" ("This is honey", not "This is a honey")
UNCOUNTABLE_EN = {
    "honey", "milk", "wool", "water", "bread", "butter", "cheese", "silk",
    "juice", "sugar", "salt", "rice", "flour", "cotton", "oil", "grass",
}

# ---------------------------------------------------------------- QC rules
QC = {
    "max_word_len": 12,
    "max_words": 2,
    "banned_prompt_words": [
        "realistic", "photo", "photograph", "scary", "angry", "blood",
        "gore", "weapon", "creepy", "horror", "3d render", "hyperreal",
    ],
    "min_vocab_font_pt": 30,
}

# ---------------------------------------------------------------- AI-image prompt "style lock"
STYLE_SUFFIX = (
    "cute cartoon vector illustration, thick dark navy outlines, flat bright colours, "
    "simple rounded shapes, friendly smiling face, centered, plain white background, "
    "no text, no shadow, no background details, children's educational style"
)
STYLE_NEGATIVE = "realistic, photo, scary, complex background, tiny details, text, watermark, gradient"
