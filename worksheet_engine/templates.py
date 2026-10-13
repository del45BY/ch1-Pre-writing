"""
Worksheet templates. Each template = metadata (text with {PLACEHOLDERS}) + a layout function.
Add a new template: write a function draw_x(c, row, pool, rng, accent) and register it in TEMPLATES.
"""
from reportlab.lib.colors import white
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
}
DEFAULT_SET = ["A", "B", "C", "D", "E"]
