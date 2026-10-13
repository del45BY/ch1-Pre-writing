"""
Worksheet templates. Each template = metadata (text with {PLACEHOLDERS}) + a layout function.
Add a new template: write a function draw_x(c, row, pool, rng, accent) and register it in TEMPLATES.
"""
import math
from reportlab.lib.colors import white
from reportlab.pdfbase.pdfmetrics import stringWidth
from .art import draw_object
from .components import (arrow, dot, dotted_text, instruction, panel, scissors_line, star,
                         text_fit, tracing_line, word_pair)
from .config import (CONTENT_BOTTOM, CONTENT_TOP, CONTENT_W, FONT_BOLD, FONT_REG, MARGIN,
                     PAGE_W, PALETTE, TINT, hx)


# ------------------------------------------------------------------ distractor helpers
def pick_pairs(pool, n, rng):
    pool = list(pool); rng.shuffle(pool)
    return pool[:n]


def pick_items(pool, n, rng, exclude):
    items, seen = [], {e.lower() for e in exclude}
    flat = [(p[0], p[1]) for p in pool] + [(p[2], p[3]) for p in pool]
    rng.shuffle(flat)
    for en, id_ in flat:
        if en.lower() not in seen:
            seen.add(en.lower()); items.append((en, id_))
        if len(items) == n:
            break
    return items


# ------------------------------------------------------------------ shared: two-column matching
def match_columns(c, row, y_top, left, right, accent, left_mode="color", right_mode="color",
                  right_words=True, star_idx=None):
    """left/right: lists of (en, id). Dots on the inner edges for the child to connect."""
    n = len(left)
    area = y_top - CONTENT_BOTTOM
    row_h = area / n
    card_w, card_h = 200, min(row_h - 14, 160)
    for i in range(n):
        cy = y_top - row_h * (i + 0.5)
        for side, items, mode in (("L", left, left_mode), ("R", right, right_mode)):
            x = MARGIN if side == "L" else PAGE_W - MARGIN - card_w
            panel(c, x, cy - card_h / 2, card_w, card_h, fill=TINT[accent], stroke=PALETTE[accent], lw=2, r=18)
            en, id_ = items[i]
            words = right_words or side == "L"
            img = min(card_h - (62 if words else 20), 110)
            draw_object(c, en, x + card_w / 2, cy + (card_h / 2 - 12 - img / 2) if words else cy, img, mode)
            if words:
                text_fit(c, x + card_w / 2, cy - card_h / 2 + 30, en, FONT_BOLD, 17, card_w - 20, PALETTE["ink"], "center")
                text_fit(c, x + card_w / 2, cy - card_h / 2 + 12, id_, FONT_BOLD, 13, card_w - 20, PALETTE[accent], "center")
            dot(c, x + card_w if side == "L" else x, cy, 8, PALETTE["ink"])
            if side == "L" and star_idx == i:
                star(c, x + 20, cy + card_h / 2 - 20, 12, PALETTE["sun"])


# ================================================================== TEMPLATE A  Animal Matching
def draw_a(c, row, pool, rng, accent):
    y = instruction(c, row, CONTENT_TOP, "Match the pictures that go together.",
                    "Jodohkan gambar yang berpasangan.", accent, "A")
    c.setFont(FONT_REG, 12); c.setFillColor(hx(PALETTE["grey"]))
    c.drawString(MARGIN + 4, y - 18, row.fmt("Start with the {OBJECT_EN_LOWER}! / Mulai dari {OBJECT_ID_LOWER}!"))
    pairs = [(row.obj_en, row.obj_id, row.rel_en, row.rel_id)] + pick_pairs(pool, 2, rng)
    left_idx = list(range(3)); right_idx = list(range(3))
    rng.shuffle(left_idx)
    while True:
        rng.shuffle(right_idx)
        if right_idx != left_idx:
            break
    left = [(pairs[i][0], pairs[i][1]) for i in left_idx]
    right = [(pairs[i][2], pairs[i][3]) for i in right_idx]
    match_columns(c, row, y - 26, left, right, accent, star_idx=left_idx.index(0))


# ================================================================== TEMPLATE B  Vocabulary Learning
def vocab_card(c, row, x, y, w, h, en, id_, article_en, accent, label):
    panel(c, x, y, w, h, fill=white, stroke=PALETTE[accent], lw=3, r=20)
    panel(c, x + 14, y + 14, 170, h - 28, fill=TINT[accent], r=16)
    draw_object(c, en, x + 99, y + h / 2, 140, "color")
    x0, wt = x + 200, w - 214
    top = y + h
    c.setFont(FONT_REG, 13); c.setFillColor(hx(PALETTE["grey"]))
    c.drawString(x0, top - 30, f"This is {article_en}.")
    c.drawString(x0, top - 47, f"Ini adalah {id_.lower()}.")
    text_fit(c, x0, top - 98, en, FONT_BOLD, 42, wt, PALETTE["ink"])
    text_fit(c, x0, top - 134, id_, FONT_BOLD, 31, wt, PALETTE[accent])
    # tracing area
    tracing_line(c, x0, y + 52, wt); dotted_text(c, x0 + 2, y + 52, en, 30, max_w=wt - 6)
    tracing_line(c, x0, y + 14, wt); dotted_text(c, x0 + 2, y + 14, id_, 26, max_w=wt - 6)


def draw_b(c, row, pool, rng, accent):
    y = instruction(c, row, CONTENT_TOP, "Look, say and trace the words.",
                    "Lihat, ucapkan, dan telusuri kata-katanya.", accent, "B")
    h = 236
    t = row.tokens()
    vocab_card(c, row, MARGIN, y - 10 - h, CONTENT_W, h, row.obj_en, row.obj_id, t["A_OBJECT_EN"], accent, "1")
    vocab_card(c, row, MARGIN, y - 10 - h - 12 - h, CONTENT_W, h, row.rel_en, row.rel_id, t["A_RELATION_EN"], accent, "2")


# ================================================================== TEMPLATE C  Find and Circle
def circle_section(c, row, y_top, target, accent, badge, rng, pool, en, id_):
    y = instruction(c, row, y_top, en, id_, accent, badge, h=50)
    distract = pick_items(pool, 4, rng, [target[0]])
    cells = [target, target] + distract
    rng.shuffle(cells)
    gap, cols = 14, 3
    cw = (CONTENT_W - gap * (cols - 1)) / cols
    ch = 104
    for i, (item_en, _) in enumerate(cells):
        r_, c_ = divmod(i, cols)
        x = MARGIN + c_ * (cw + gap)
        yy = y - 8 - (r_ + 1) * ch - r_ * 8
        panel(c, x, yy, cw, ch, fill=white, stroke=PALETTE["line"], lw=1.6, r=14)
        draw_object(c, item_en, x + cw / 2, yy + ch / 2, 84, "color")
    return y - 8 - 2 * ch - 8


def draw_c(c, row, pool, rng, accent):
    y = circle_section(c, row, CONTENT_TOP, (row.rel_en, row.rel_id), accent, "1", rng, pool,
                       "Circle the {RELATION_EN_LOWER}.", "Lingkari {RELATION_ID_LOWER}.")
    circle_section(c, row, y - 6, (row.obj_en, row.obj_id), accent, "2", rng, pool,
                   "Circle the {OBJECT_EN_LOWER}.", "Lingkari {OBJECT_ID_LOWER}.")


# ================================================================== TEMPLATE D  Cut and Paste
def draw_d(c, row, pool, rng, accent):
    y = instruction(c, row, CONTENT_TOP, "Cut the pictures. Paste them in the right place.",
                    "Gunting gambarnya. Tempel di tempat yang benar.", accent, "D")
    pairs = [(row.obj_en, row.obj_id, row.rel_en, row.rel_id)] + pick_pairs(pool, 2, rng)
    rng.shuffle(pairs)
    rh, gap = 116, 10
    yy = y - 10
    for p in pairs:
        yy -= rh
        panel(c, MARGIN, yy, 240, rh, fill=TINT[accent], stroke=PALETTE[accent], lw=2, r=16)
        draw_object(c, p[0], MARGIN + 56, yy + rh / 2, 88, "color")
        word_pair(c, MARGIN + 112, yy + rh / 2 + 8, p[0], p[1], 24, 17, PALETTE[accent], 120)
        arrow(c, MARGIN + 246, yy + rh / 2, MARGIN + 290)
        bx = MARGIN + 300; bw = PAGE_W - MARGIN - bx
        panel(c, bx, yy, bw, rh, fill=None, stroke=PALETTE["grey"], lw=2, r=16, dash=(7, 5))
        c.setFont(FONT_REG, 10.5); c.setFillColor(hx(PALETTE["line"]))
        c.drawCentredString(bx + bw / 2, yy + rh / 2 + 2, "Paste here")
        c.drawCentredString(bx + bw / 2, yy + rh / 2 - 12, "Tempel di sini")
        yy -= gap
    sy = yy - 4
    scissors_line(c, MARGIN, PAGE_W - MARGIN, sy)
    pieces = [(p[2], p[3]) for p in pairs]
    rng.shuffle(pieces)
    pw, ph = 160, 110
    pgap = (CONTENT_W - 3 * pw) / 2
    for i, (en, _) in enumerate(pieces):
        px = MARGIN + i * (pw + pgap)
        panel(c, px, CONTENT_BOTTOM + 4, pw, ph, fill=white, stroke=PALETTE["grey"], lw=1.6, r=12, dash=(5, 4))
        draw_object(c, en, px + pw / 2, CONTENT_BOTTOM + 4 + ph / 2, 86, "color")


# ================================================================== TEMPLATE E  Coloring
def draw_e(c, row, pool, rng, accent):
    y = instruction(c, row, CONTENT_TOP, row.fmt("Color the {OBJECT_EN_LOWER} and the {RELATION_EN_LOWER}."),
                    row.fmt("Warnai {OBJECT_ID_LOWER} dan {RELATION_ID_LOWER}."), accent, "E")
    specs = [(row.obj_en, row.obj_id, 262, 230), (row.rel_en, row.rel_id, 232, 200)]
    top = y - 10
    for en, id_, h, img in specs:
        yb = top - h
        panel(c, MARGIN, yb, CONTENT_W, h, fill=white, stroke=PALETTE["line"], lw=2.4, r=22)
        draw_object(c, en, PAGE_W / 2, yb + h / 2, img, "outline")
        word_pair(c, MARGIN + 20, yb + h - 32, en, id_, 20, 14, PALETTE[accent], 150)
        for i, col in enumerate(["coral", "sun", "mint", "sky", "grape"]):
            c.setFillColor(hx(PALETTE[col])); c.setStrokeColor(hx(PALETTE["ink"])); c.setLineWidth(1.4)
            c.circle(PAGE_W - MARGIN - 24 - i * 0 , yb + h - 28 - i * 26, 9, stroke=1, fill=1)
        top = yb - 10


# ================================================================== TEMPLATE F  Shadow Matching (optional)
def draw_f(c, row, pool, rng, accent):
    y = instruction(c, row, CONTENT_TOP, "Match each picture with its shadow.",
                    "Jodohkan setiap gambar dengan bayangannya.", accent, "F")
    extra = pick_items(pool, 1, rng, [row.obj_en, row.rel_en])
    items = [(row.obj_en, row.obj_id), (row.rel_en, row.rel_id)] + extra
    rng.shuffle(items)
    shadows = list(items)
    while True:
        rng.shuffle(shadows)
        if shadows != items:
            break
    match_columns(c, row, y - 10, items, shadows, accent, left_mode="color", right_mode="shadow",
                  right_words=False)


# ================================================================== TEMPLATE G  Counting (how many?)
NUM_EN = ["one", "two", "three", "four", "five"]
NUM_ID = ["satu", "dua", "tiga", "empat", "lima"]


def count_section(c, row, y_top, item_en, count, accent, badge, en, id_):
    """One block: instruction -> row of N pictures -> number choices 1..5 to circle."""
    y = instruction(c, row, y_top, en, id_, accent, badge, h=50)
    ph = 120
    panel(c, MARGIN, y - 8 - ph, CONTENT_W, ph, fill=white, stroke=PALETTE["line"], lw=1.6, r=14)
    step, size = 100, 92
    x0 = PAGE_W / 2 - step * (count - 1) / 2
    for i in range(count):
        draw_object(c, item_en, x0 + i * step, y - 8 - ph / 2, size, "color")
    top = y - 8 - ph - 10
    cy = top - 24
    cell = CONTENT_W / 5
    for n in range(1, 6):
        cx = MARGIN + cell * (n - 0.5)
        c.setFillColor(white); c.setStrokeColor(hx(PALETTE[accent])); c.setLineWidth(3)
        c.circle(cx, cy, 22, stroke=1, fill=1)
        c.setFillColor(hx(PALETTE["ink"])); c.setFont(FONT_BOLD, 24)
        c.drawCentredString(cx, cy - 8.5, str(n))
        text_fit(c, cx, cy - 38, f"{NUM_EN[n - 1]} / {NUM_ID[n - 1]}", FONT_REG, 11, cell - 6, PALETTE["grey"], "center")
    return cy - 46


def draw_g(c, row, pool, rng, accent):
    n1 = rng.randint(1, 5)
    n2 = rng.choice([n for n in range(1, 6) if n != n1])   # different numbers on the two blocks
    y = count_section(c, row, CONTENT_TOP, row.obj_en, n1, accent, "1",
                      "Count the {OBJECT_EN_LOWER}. Circle the number.",
                      "Hitung {OBJECT_ID_LOWER}. Lingkari angkanya.")
    count_section(c, row, y - 10, row.rel_en, n2, accent, "2",
                  "Count the {RELATION_EN_LOWER}. Circle the number.",
                  "Hitung {RELATION_ID_LOWER}. Lingkari angkanya.")


# ================================================================== shared tracing engine (used by H and I)
def _dotted(c, x1, y1, x2, y2, width, gap_target):
    """Round dots spaced evenly so the last dot lands exactly on the end point (works at ANY angle)."""
    length = math.hypot(x2 - x1, y2 - y1)
    n = max(2, int(length / gap_target))
    period = length / n
    c.setLineCap(1); c.setLineWidth(width); c.setDash(0.1, period - 0.1)
    c.line(x1, y1, x2, y2)


def trace_line_xy(c, style, p1, p2, accent, inset=4):
    """One tracing line from p1=(x,y) to p2=(x,y). Horizontal (H) and diagonal (I) both use this.
    style 0 big dots | 1 dashes | 2 small dots | 3 road (stay inside band) | 4 nothing (free draw)"""
    (x1, y1), (x2, y2) = p1, p2
    length = math.hypot(x2 - x1, y2 - y1)
    ux, uy = (x2 - x1) / length, (y2 - y1) / length          # direction of the line
    x1, y1, x2, y2 = x1 + ux * inset, y1 + uy * inset, x2 - ux * inset, y2 - uy * inset
    c.saveState()
    c.setStrokeColor(hx(PALETTE["grey"]))
    if style == 0:
        _dotted(c, x1, y1, x2, y2, 8, 17)
    elif style == 1:
        c.setLineCap(1); c.setLineWidth(6); c.setDash(26, 14); c.line(x1, y1, x2, y2)
    elif style == 2:
        _dotted(c, x1, y1, x2, y2, 4.5, 10)
    elif style == 3:
        c.setStrokeColor(hx(PALETTE[accent])); c.setStrokeAlpha(0.22)
        c.setLineCap(1); c.setLineWidth(26); c.line(x1, y1, x2, y2)
        c.setStrokeAlpha(1); c.setStrokeColor(hx(PALETTE["line"]))
        c.setLineWidth(2); c.setDash(8, 8); c.line(x1, y1, x2, y2)
    c.restoreState()


def start_finish(c, p1, p2):
    """Green 'play' circle at the start, red 'stop' circle at the end.
    The play triangle always points right: every line in H and I runs left -> right."""
    for (x, y), col, kind in ((p1, PALETTE["mint"], "go"), (p2, PALETTE["coral"], "stop")):
        c.setFillColor(hx(col)); c.setStrokeColor(white); c.setLineWidth(2)
        c.circle(x, y, 11, stroke=1, fill=1)
        c.setFillColor(white)
        if kind == "go":
            pth = c.beginPath(); pth.moveTo(x - 3, y + 5); pth.lineTo(x - 3, y - 5); pth.lineTo(x + 5, y)
            pth.close(); c.drawPath(pth, stroke=0, fill=1)
        else:
            c.rect(x - 4.5, y - 4.5, 9, 9, stroke=0, fill=1)


def hint_with_arrows(c, y, text, angles):
    """Grey hint text followed by small DRAWN arrows (not font glyphs, so any font works)."""
    c.setFont(FONT_BOLD, 12); c.setFillColor(hx(PALETTE["grey"]))
    c.drawString(MARGIN + 4, y, text)
    x = MARGIN + 4 + stringWidth(text, FONT_BOLD, 12) + 16
    for a in angles:
        c.saveState(); c.translate(x, y + 4); c.rotate(a)
        c.setStrokeColor(hx(PALETTE["grey"])); c.setFillColor(hx(PALETTE["grey"]))
        c.setLineWidth(2.2); c.setLineCap(1)
        c.line(-10, 0, 6, 0)
        pth = c.beginPath(); pth.moveTo(12, 0); pth.lineTo(5, 5); pth.lineTo(5, -5); pth.close()
        c.drawPath(pth, stroke=0, fill=1)
        c.restoreState()
        x += 34


# ================================================================== TEMPLATE H  Horizontal Lines (pre-writing)
def draw_h(c, row, pool, rng, accent):
    y = instruction(c, row, CONTENT_TOP, "Trace the lines from {OBJECT_EN_LOWER} to {RELATION_EN_LOWER}.",
                    "Telusuri garis dari {OBJECT_ID_LOWER} ke {RELATION_ID_LOWER}.", accent, "H")
    hint_with_arrows(c, y - 18, "Left to right  /  Dari kiri ke kanan", [0])
    rh, gap = 88, 8
    top = y - 26
    for i in range(5):                         # 5 stacked rows, full width
        yy = top - rh
        cy = yy + rh / 2 + 6                   # ONE height for both ends -> the line is flat
        panel(c, MARGIN, yy, CONTENT_W, rh, fill=white, stroke=PALETTE["line"], lw=1.6, r=16)
        for en, id_, cx in ((row.obj_en, row.obj_id, MARGIN + 62), (row.rel_en, row.rel_id, PAGE_W - MARGIN - 62)):
            draw_object(c, en, cx, yy + 58, 52, "color")
            text_fit(c, cx, yy + 21, en, FONT_BOLD, 11.5, 100, PALETTE["ink"], "center")
            text_fit(c, cx, yy + 8, id_, FONT_REG, 9.5, 100, PALETTE[accent], "center")
        p1, p2 = (MARGIN + 128, cy), (PAGE_W - MARGIN - 128, cy)    # same y  => horizontal
        trace_line_xy(c, i, p1, p2, accent)
        start_finish(c, p1, p2)
        if i == 0:
            c.setFont(FONT_REG, 8.5); c.setFillColor(hx(PALETTE["grey"]))
            c.drawCentredString(p1[0], cy + 20, "Start / Mulai")
            c.drawCentredString(p2[0], cy + 20, "Finish / Selesai")
        if i == 4:
            c.setFont(FONT_BOLD, 10); c.setFillColor(hx(PALETTE[accent]))
            c.drawCentredString((p1[0] + p2[0]) / 2, cy + 20, "Draw it yourself! / Gambar sendiri!")
        top = yy - gap


# ================================================================== TEMPLATE I  Diagonal Lines (pre-writing)
def diag_panel(c, row, x, yb, w, h, up, style, accent, first=False):
    """One square-ish panel: partner picture in the opposite corner, one slanted line between them.
    up=True : main object bottom-left  -> partner top-right   (line goes UP)
    up=False: main object top-left     -> partner bottom-right (line goes DOWN)"""
    panel(c, x, yb, w, h, fill=white, stroke=PALETTE["line"], lw=1.6, r=16)
    y_hi, y_lo = yb + h - 34, yb + 62          # TWO different heights -> the line is slanted
    ay, by = (y_lo, y_hi) if up else (y_hi, y_lo)
    ax, bx = x + 38, x + w - 38
    for en, id_, cx, cy in ((row.obj_en, row.obj_id, ax, ay), (row.rel_en, row.rel_id, bx, by)):
        draw_object(c, en, cx, cy, 52, "color")
        text_fit(c, cx, cy - 40, en, FONT_BOLD, 11, 78, PALETTE["ink"], "center")
        text_fit(c, cx, cy - 52, id_, FONT_REG, 9, 78, PALETTE[accent], "center")
    p1, p2 = (ax + 40, ay), (bx - 40, by)      # start next to the left picture, end next to the right
    trace_line_xy(c, style, p1, p2, accent)
    start_finish(c, p1, p2)
    c.setFont(FONT_REG, 8.5); c.setFillColor(hx(PALETTE["grey"]))
    if first:
        c.drawString(p1[0] + 16, p1[1] - 4, "Start / Mulai")
        c.drawRightString(p2[0] - 16, p2[1] - 4, "Finish / Selesai")
    if style == 4:                             # free draw: write the hint in the empty corner
        c.setFont(FONT_BOLD, 10); c.setFillColor(hx(PALETTE[accent]))
        c.drawCentredString(x + w - 62, yb + h - 22, "Draw it yourself!")
        c.drawCentredString(x + w - 62, yb + h - 35, "Gambar sendiri!")


def draw_i(c, row, pool, rng, accent):
    y = instruction(c, row, CONTENT_TOP, "Trace the slanted lines from {OBJECT_EN_LOWER} to {RELATION_EN_LOWER}.",
                    "Telusuri garis miring dari {OBJECT_ID_LOWER} ke {RELATION_ID_LOWER}.", accent, "I")
    hint_with_arrows(c, y - 18, "Follow the slanted line  /  Ikuti garis miring", [35, -35])
    gap = 8
    pw, ph = (CONTENT_W - gap) / 2, 240        # 2 columns x 2 rows (H used 1 column x 5 rows)
    plan = [(True, 0), (False, 1), (True, 3), (False, 4)]    # (goes up?, line style) easy -> hard
    top = y - 26
    for i, (up, style) in enumerate(plan):
        r_, c_ = divmod(i, 2)
        x = MARGIN + c_ * (pw + gap)
        yb = top - (r_ + 1) * ph - r_ * gap
        diag_panel(c, row, x, yb, pw, ph, up, style, accent, first=(i == 0))


TEMPLATES = {
    "A": dict(name_en="Animal Matching", name_id="Menjodohkan", accent="coral", fn=draw_a,
              objective_en="match things that go together.", objective_id="menjodohkan hal yang berpasangan."),
    "B": dict(name_en="Vocabulary Learning", name_id="Belajar Kosakata", accent="sky", fn=draw_b,
              objective_en="say and write {OBJECT_EN_LOWER} and {RELATION_EN_LOWER}.",
              objective_id="mengucapkan dan menulis {OBJECT_ID_LOWER} dan {RELATION_ID_LOWER}."),
    "C": dict(name_en="Find and Circle", name_id="Temukan dan Lingkari", accent="mint", fn=draw_c,
              objective_en="find the {RELATION_EN_LOWER} and the {OBJECT_EN_LOWER}.",
              objective_id="menemukan {RELATION_ID_LOWER} dan {OBJECT_ID_LOWER}."),
    "D": dict(name_en="Cut and Paste", name_id="Gunting dan Tempel", accent="grape", fn=draw_d,
              objective_en="cut and paste each picture in the right place.",
              objective_id="menggunting dan menempel gambar di tempat yang benar."),
    "E": dict(name_en="Coloring", name_id="Mewarnai", accent="sun", fn=draw_e,
              objective_en="color the {OBJECT_EN_LOWER} and the {RELATION_EN_LOWER}.",
              objective_id="mewarnai {OBJECT_ID_LOWER} dan {RELATION_ID_LOWER}."),
    "F": dict(name_en="Shadow Matching", name_id="Menjodohkan Bayangan", accent="coral", fn=draw_f,
              objective_en="match each picture with its shadow.",
              objective_id="menjodohkan gambar dengan bayangannya."),
    "G": dict(name_en="Counting", name_id="Berhitung", accent="sky", fn=draw_g,
              objective_en="count {OBJECT_EN_LOWER} and {RELATION_EN_LOWER} from 1 to 5.",
              objective_id="menghitung {OBJECT_ID_LOWER} dan {RELATION_ID_LOWER} dari 1 sampai 5."),
    "H": dict(name_en="Horizontal Lines", name_id="Garis Datar", accent="mint", fn=draw_h,
              objective_en="trace a straight line from {OBJECT_EN_LOWER} to {RELATION_EN_LOWER}.",
              objective_id="menelusuri garis lurus dari {OBJECT_ID_LOWER} ke {RELATION_ID_LOWER}."),
    "I": dict(name_en="Diagonal Lines", name_id="Garis Miring", accent="grape", fn=draw_i,
              objective_en="trace a slanted line from {OBJECT_EN_LOWER} to {RELATION_EN_LOWER}.",
              objective_id="menelusuri garis miring dari {OBJECT_ID_LOWER} ke {RELATION_ID_LOWER}."),
}
DEFAULT_SET = ["A", "B", "C", "D", "E"]
