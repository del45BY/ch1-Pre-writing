"""Reusable page modules (Header / Instruction / Footer / helpers). Every template composes these."""
import math
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.colors import white
from .config import (BRAND, BRAND_STRIPE, CONTENT_W, FONT_BOLD, FONT_REG, MARGIN, PAGE_H,
                     PAGE_W, PALETTE, TINT, hx)


# ------------------------------------------------------------------ text helpers
def fit_size(text, font, max_size, max_w, min_size=8):
    size = max_size
    while size > min_size and stringWidth(text, font, size) > max_w:
        size -= 0.5
    return size


def text_fit(c, x, y, text, font, max_size, max_w, color, align="left", min_size=8):
    size = fit_size(text, font, max_size, max_w, min_size)
    c.setFont(font, size); c.setFillColor(hx(color) if isinstance(color, str) else color)
    {"left": c.drawString, "center": c.drawCentredString, "right": c.drawRightString}[align](x, y, text)
    return size


def dotted_text(c, x, y, text, size, color="#8A8AA0", max_w=None):
    """Tracing text: dotted outline letters."""
    if max_w:
        size = fit_size(text, FONT_BOLD, size, max_w, 12)
    c.saveState()
    t = c.beginText(x, y); t.setFont(FONT_BOLD, size); t.setTextRenderMode(1)
    c.setStrokeColor(hx(color)); c.setLineWidth(1.9); c.setDash(2.6, 3.4)
    t.textOut(text); c.drawText(t)
    c.restoreState()


def tracing_line(c, x, y, w, color="#C9C9D6"):
    """Writing guide: baseline + dashed mid-line."""
    c.saveState()
    c.setStrokeColor(hx(color)); c.setLineWidth(1)
    c.line(x, y, x + w, y)
    c.setDash(4, 4); c.line(x, y + 22, x + w, y + 22)
    c.restoreState()


# ------------------------------------------------------------------ shapes
def star(c, cx, cy, r, color):
    pts = []
    for i in range(10):
        ang = math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    p = c.beginPath(); p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    p.close(); c.setFillColor(hx(color)); c.setStrokeColor(hx(PALETTE["ink"])); c.setLineWidth(1.4)
    c.drawPath(p, stroke=1, fill=1)


def panel(c, x, y, w, h, fill=None, stroke=None, lw=2.2, r=16, dash=None):
    c.saveState()
    if dash:
        c.setDash(*dash)
    c.setLineWidth(lw)
    if fill:
        c.setFillColor(hx(fill))
    if stroke:
        c.setStrokeColor(hx(stroke))
    c.roundRect(x, y, w, h, r, stroke=1 if stroke else 0, fill=1 if fill else 0)
    c.restoreState()


def dot(c, x, y, r=7, color=PALETTE["ink"]):
    c.setFillColor(hx(color)); c.setStrokeColor(white); c.setLineWidth(2)
    c.circle(x, y, r, stroke=1, fill=1)


def arrow(c, x1, y, x2, color=PALETTE["grey"], w=4):
    c.saveState()
    c.setStrokeColor(hx(color)); c.setFillColor(hx(color)); c.setLineWidth(w); c.setLineCap(1)
    c.line(x1, y, x2 - 8, y)
    p = c.beginPath(); p.moveTo(x2, y); p.lineTo(x2 - 14, y + 9); p.lineTo(x2 - 14, y - 9); p.close()
    c.drawPath(p, stroke=0, fill=1)
    c.restoreState()


def scissors_line(c, x1, x2, y):
    c.saveState()
    c.setStrokeColor(hx(PALETTE["grey"])); c.setLineWidth(1.6); c.setDash(7, 5)
    c.line(x1 + 26, y, x2, y)
    c.setDash()
    # scissors icon (two blades + two rings)
    c.setLineWidth(2.2); c.setStrokeColor(hx(PALETTE["ink"]))
    c.line(x1 + 4, y + 7, x1 + 24, y - 3); c.line(x1 + 4, y - 7, x1 + 24, y + 3)
    c.setFillColor(white)
    c.circle(x1 + 3, y + 7, 3.6, stroke=1, fill=1); c.circle(x1 + 3, y - 7, 3.6, stroke=1, fill=1)
    c.restoreState()


# ------------------------------------------------------------------ MODULE 1: header
def header(c, row, tpl, accent):
    top = PAGE_H
    # brand stripe
    seg = PAGE_W / len(BRAND_STRIPE)
    for i, name in enumerate(BRAND_STRIPE):
        c.setFillColor(hx(PALETTE[name])); c.rect(i * seg, top - 12, seg + 1, 12, stroke=0, fill=1)

    # age pill + name line
    y = top - 46
    pill_txt = "AGES 3-5  \u2022  USIA 3-5 TAHUN"
    c.setFont(FONT_BOLD, 9.5)
    w = stringWidth(pill_txt, FONT_BOLD, 9.5) + 22
    panel(c, MARGIN, y - 5, w, 22, fill=PALETTE[accent], r=11)
    c.setFillColor(white); c.drawString(MARGIN + 11, y + 2, pill_txt)

    c.setFont(FONT_REG, 10); c.setFillColor(hx(PALETTE["grey"]))
    label = "Name / Nama:"
    lw = stringWidth(label, FONT_REG, 10)
    x0 = PAGE_W - MARGIN - 190
    c.drawString(x0, y + 2, label)
    c.setStrokeColor(hx(PALETTE["line"])); c.setLineWidth(1.2)
    c.line(x0 + lw + 6, y, PAGE_W - MARGIN, y)

    # titles
    title_en = row.fmt("{OBJECT_EN} & {RELATION_EN}")
    title_id = row.fmt("{OBJECT_ID} & {RELATION_ID}")
    text_fit(c, MARGIN, top - 92, title_en, FONT_BOLD, 38, CONTENT_W, PALETTE["ink"])
    text_fit(c, MARGIN, top - 119, title_id, FONT_BOLD, 21, CONTENT_W, PALETTE[accent])

    # learning-objective strip
    by = top - 176
    panel(c, MARGIN, by, CONTENT_W, 44, fill=TINT[accent], r=12)
    star(c, MARGIN + 24, by + 22, 11, PALETTE["sun"])
    text_fit(c, MARGIN + 46, by + 26, "I can " + row.fmt(tpl["objective_en"]), FONT_BOLD, 12, CONTENT_W - 60, PALETTE["ink"])
    text_fit(c, MARGIN + 46, by + 9, "Saya bisa " + row.fmt(tpl["objective_id"]), FONT_REG, 10.5, CONTENT_W - 60, PALETTE["grey"])


# ------------------------------------------------------------------ MODULE: instruction bar
def instruction(c, row, y_top, en, id_, accent, badge, h=54, x=MARGIN, w=CONTENT_W):
    y = y_top - h
    panel(c, x, y, w, h, fill=white, stroke=PALETTE[accent], lw=3, r=14)
    c.setFillColor(hx(PALETTE[accent])); c.circle(x + 28, y + h / 2, 17, stroke=0, fill=1)
    c.setFillColor(white); c.setFont(FONT_BOLD, 18); c.drawCentredString(x + 28, y + h / 2 - 6.5, badge)
    text_fit(c, x + 56, y + h - 22, row.fmt(en), FONT_BOLD, 18, w - 70, PALETTE["ink"])
    text_fit(c, x + 56, y + 11, row.fmt(id_), FONT_REG, 13, w - 70, PALETTE["grey"])
    return y


# ------------------------------------------------------------------ MODULE: vocabulary pair
def word_pair(c, x, y, en, id_, size_en, size_id, color, max_w, align="left"):
    """English word above Indonesian word."""
    text_fit(c, x, y, en, FONT_BOLD, size_en, max_w, PALETTE["ink"], align)
    text_fit(c, x, y - size_id - 8, id_, FONT_BOLD, size_id, max_w, color, align)


# ------------------------------------------------------------------ MODULE: footer
def footer(c, page_no, total, tpl_label):
    y = 52
    c.setStrokeColor(hx(PALETTE["line"])); c.setLineWidth(1)
    c.line(MARGIN, y + 12, PAGE_W - MARGIN, y + 12)
    c.setFont(FONT_BOLD, 10); c.setFillColor(hx(PALETTE["ink"]))
    c.drawString(MARGIN, y - 4, BRAND["name"])
    c.setFont(FONT_REG, 8.5); c.setFillColor(hx(PALETTE["grey"]))
    c.drawString(MARGIN, y - 16, tpl_label)
    c.setFont(FONT_BOLD, 10); c.setFillColor(hx(PALETTE["grey"]))
    c.drawCentredString(PAGE_W / 2, y - 4, f"Page {page_no} / {total}")
    c.setFont(FONT_REG, 8.5)
    c.drawRightString(PAGE_W - MARGIN, y - 4, f"\u00a9 {BRAND['year']} {BRAND['name']}")
    c.setFont(FONT_REG, 7)
    c.drawCentredString(PAGE_W / 2, 18, BRAND["license_en"])
    c.drawCentredString(PAGE_W / 2, 9, BRAND["license_id"])
