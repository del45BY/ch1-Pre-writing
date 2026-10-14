"""Turns one Row into: PDF + Preview.png + Cover.png + Thumbnail.png."""
import hashlib
import json
import random
from pathlib import Path
import pypdfium2 as pdfium
from PIL import Image, ImageDraw
from reportlab.lib.colors import white
from reportlab.pdfgen import canvas
from .art import ART_NAMES, ART_PAIRS, draw_object
from .components import footer, header, panel, star, text_fit
from .config import (BRAND, FONT_BOLD, FONT_REG, PAGE_H, PAGE_W, PALETTE, TEMPLATE_VERSION, TINT,
                     ASSETS, BRAND_STRIPE, hx)
from .templates import DEFAULT_SET, TEMPLATES

PDF_NAME = "English_Indonesian_Worksheet.pdf"


# ------------------------------------------------------------------ distractor pool
def build_pool(rows):
    """All (obj_en, obj_id, rel_en, rel_id) pairs known to the system: database + built-in art."""
    pairs = {(r.obj_en.lower(), r.rel_en.lower()): (r.obj_en, r.obj_id, r.rel_en, r.rel_id) for r in rows}
    for a, b in ART_PAIRS:
        pairs.setdefault((a, b), (*ART_NAMES[a], *ART_NAMES[b]))
    return list(pairs.values())


def pool_for(row, pool):
    mine = {row.obj_en.lower(), row.rel_en.lower()}
    return [p for p in pool if p[0].lower() not in mine and p[2].lower() not in mine]


# ------------------------------------------------------------------ change detection
def build_hash(row, templates):
    img_state = [(p.name, p.stat().st_mtime) for p in sorted((ASSETS / "images").glob("*.png"))]
    blob = json.dumps([row.__dict__, templates, TEMPLATE_VERSION, str(img_state), BRAND["name"]], default=str)
    return hashlib.sha1(blob.encode()).hexdigest()


# ------------------------------------------------------------------ PDF
def render_pdf(row, pool, templates, out_pdf):
    c = canvas.Canvas(str(out_pdf), pagesize=(PAGE_W, PAGE_H))
    c.setTitle(f"{row.obj_en} & {row.rel_en} - English / Indonesian Worksheet")
    c.setAuthor(BRAND["name"]); c.setSubject(f"{row.obj_id} & {row.rel_id} - Lembar Kerja Dwibahasa")
    c.setKeywords(f"{row.category}, preschool, bilingual, Indonesian, ages 3-5")
    total = len(templates)
    for n, key in enumerate(templates, 1):
        t = TEMPLATES[key]
        seed_key = key[1:] if key.startswith("L") else key  # template lama LA..LI memakai kunci acak lamanya (A..I)
        rng = random.Random(f"{row.id}-{seed_key}")        # deterministic layout per row/template
        header(c, row, t, t["accent"])
        t["fn"](c, row, pool_for(row, pool), rng, t["accent"])
        footer(c, n, total, f"Activity {key}: {t['name_en']} / {t['name_id']}")
        c.showPage()
    c.save()


def pdf_to_images(pdf_path, scale):
    pdf = pdfium.PdfDocument(str(pdf_path))
    return [pdf[i].render(scale=scale).to_pil().convert("RGB") for i in range(len(pdf))]


# ------------------------------------------------------------------ preview contact sheet
def render_preview(pdf_path, out_png):
    many = len(pdfium.PdfDocument(str(pdf_path))) > 6           # banyak halaman -> kotak lebih kecil
    pages = pdf_to_images(pdf_path, 0.62 if many else 0.9)
    cols = 5 if many else (3 if len(pages) > 2 else len(pages))
    rows_n = -(-len(pages) // cols)
    pw, ph = pages[0].size
    gap = 36
    W = cols * pw + (cols + 1) * gap
    H = rows_n * ph + (rows_n + 1) * gap
    sheet = Image.new("RGB", (W, H), "#F1EFFA")
    d = ImageDraw.Draw(sheet)
    for i, pg in enumerate(pages):
        x = gap + (i % cols) * (pw + gap)
        y = gap + (i // cols) * (ph + gap)
        d.rectangle([x + 8, y + 8, x + pw + 8, y + ph + 8], fill="#D9D5EA")
        sheet.paste(pg, (x, y))
    sheet.save(out_png, optimize=True)


# ------------------------------------------------------------------ cover (square, 2000 px)
def render_cover(row, templates, out_cover, out_thumb, tmp_pdf):
    S = 640
    c = canvas.Canvas(str(tmp_pdf), pagesize=(S, S))
    accent = "sky"
    c.setFillColor(hx(TINT["sun"])); c.rect(0, 0, S, S, stroke=0, fill=1)
    seg = S / len(BRAND_STRIPE)
    for i, nm in enumerate(BRAND_STRIPE):
        c.setFillColor(hx(PALETTE[nm])); c.rect(i * seg, S - 18, seg + 1, 18, stroke=0, fill=1)
    panel(c, 30, 30, S - 60, S - 90, fill=white, stroke=PALETTE["ink"], lw=4, r=34)

    text_fit(c, S / 2, S - 126, f"{row.obj_en} & {row.rel_en}", FONT_BOLD, 52, S - 130, PALETTE["ink"], "center")
    text_fit(c, S / 2, S - 164, f"{row.obj_id} & {row.rel_id}", FONT_BOLD, 32, S - 120, PALETTE["coral"], "center")

    panel(c, 70, 206, 220, 220, fill=TINT["sky"], r=26); panel(c, S - 290, 206, 220, 220, fill=TINT["mint"], r=26)
    draw_object(c, row.obj_en, 180, 316, 190)
    draw_object(c, row.rel_en, S - 180, 316, 190)
    c.setFillColor(hx(PALETTE["sun"])); c.setStrokeColor(hx(PALETTE["ink"])); c.setLineWidth(3)
    c.circle(S / 2, 316, 24, stroke=1, fill=1)
    c.setFillColor(hx(PALETTE["ink"])); c.setFont(FONT_BOLD, 34); c.drawCentredString(S / 2, 304, "+")

    panel(c, 110, 120, S - 220, 58, fill=PALETTE["coral"], r=29)
    c.setFillColor(white); c.setFont(FONT_BOLD, 22)
    c.drawCentredString(S / 2, 156, f"{len(templates)} Printable Worksheets")
    c.setFont(FONT_REG, 14); c.drawCentredString(S / 2, 133, f"{len(templates)} Lembar Kerja Siap Cetak")

    c.setFillColor(hx(PALETTE["grey"])); c.setFont(FONT_BOLD, 15)
    c.drawCentredString(S / 2, 92, "English \u2022 Bahasa Indonesia   |   Ages 3-5 \u2022 Usia 3-5")
    c.setFont(FONT_REG, 11); c.drawCentredString(S / 2, 62, BRAND["name"])
    star(c, 64, S - 78, 20, PALETTE["sun"]); star(c, S - 64, S - 78, 20, PALETTE["sun"])
    c.save()
    img = pdf_to_images(tmp_pdf, 2000 / S)[0]
    img.save(out_cover, optimize=True)
    img.resize((600, 600), Image.LANCZOS).save(out_thumb, optimize=True)
    Path(tmp_pdf).unlink(missing_ok=True)


# ------------------------------------------------------------------ one product
def build_product(row, pool, out_root, templates=None, force=False):
    templates = templates or ([t.strip().upper() for t in row.templates.split(",") if t.strip()] or DEFAULT_SET)
    folder = Path(out_root) / row.folder
    folder.mkdir(parents=True, exist_ok=True)
    stamp = folder / ".build_hash"
    h = build_hash(row, templates)
    pdf = folder / PDF_NAME
    if not force and stamp.exists() and stamp.read_text() == h and pdf.exists():
        return {"id": row.id, "folder": str(folder), "built": False, "pages": len(templates)}
    render_pdf(row, pool, templates, pdf)
    render_preview(pdf, folder / "Preview.png")
    render_cover(row, templates, folder / "Cover.png", folder / "Thumbnail.png", folder / "_cover.pdf")
    stamp.write_text(h)
    return {"id": row.id, "folder": str(folder), "built": True, "pages": len(templates)}
