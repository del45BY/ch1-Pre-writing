"""
10 TEMPLATE PRA-MENULIS (v2.0).  Semua mengikuti tema produk: dari {OBJECT} ke {RELATION}.

  A Garis Tegak     B Garis Datar      C Garis Miring    D Garis Zigzag     E Garis Lengkung
  F Garis Gelombang G Lingkaran&Spiral H Pola Campuran   I Mengikuti Jalur  J Menebalkan Bentuk Dasar

Template lama (matching, kosakata, dll) ada di templates_legacy.py dan tetap bisa dipakai: LA..LI.
Template baru: tulis fungsi draw_x(c, row, pool, rng, accent), daftarkan di TEMPLATES.
"""
import math
from reportlab.lib.colors import white
from .art import draw_object
from .components import instruction, panel, text_fit
from .config import (CONTENT_BOTTOM, CONTENT_TOP, CONTENT_W, FONT_BOLD, FONT_REG, MARGIN, PAGE_W, PALETTE, hx)
from .templates_legacy import TEMPLATES as _LEGACY, pick_items
from .tracing import (DASHES, DOTS, FREE, ROAD, SMALL_DOTS, arch, catmull, circle_pts, hint_with_arrows,
                      join, loops, marker_end, marker_start, obj_block, oval_pts, polygon, scallops,
                      small_label, spiral_in, square_wave, stairs, straight, trace_path, wave, zigzag)

ROW_H, GAP = 88, 8


# ================================================================== layout 1: BARIS (B, D, E, F, H)
def rows_template(c, row, accent, badge, en, id_, hint, specs):
    """5 baris selebar halaman: gambar objek di kiri, pasangan di kanan, satu jalur di antaranya.
    specs = [(fungsi_geometri(p1, p2) -> titik, gaya, sudut_tajam?), ...]  mudah -> sulit."""
    y = instruction(c, row, CONTENT_TOP, en, id_, accent, badge)
    hint_with_arrows(c, y - 18, hint, [0])
    top = y - 26
    for i, (geom, style, corners) in enumerate(specs):
        yy = top - ROW_H
        cy = yy + ROW_H / 2 + 6
        panel(c, MARGIN, yy, CONTENT_W, ROW_H, fill=white, stroke=PALETTE["line"], lw=1.6, r=16)
        obj_block(c, row.obj_en, row.obj_id, MARGIN + 62, yy + 58, 52, accent)
        obj_block(c, row.rel_en, row.rel_id, PAGE_W - MARGIN - 62, yy + 58, 52, accent)
        pts = geom((MARGIN + 128, cy), (PAGE_W - MARGIN - 128, cy))
        trace_path(c, style, pts, accent, corners)
        marker_start(c, pts[0], "right"); marker_end(c, pts[-1])
        if i == 0:
            small_label(c, pts[0][0], yy + 7, "Start / Mulai", "center")
            small_label(c, pts[-1][0], yy + 7, "Finish / Selesai", "center")
        if style == FREE:
            small_label(c, PAGE_W / 2, yy + ROW_H - 13, "Draw it yourself! / Gambar sendiri!", "center", True, PALETTE[accent], 9)
        top = yy - GAP


# ================================================================== A  Garis Tegak (Vertical Lines)
def draw_a(c, row, pool, rng, accent):
    y = instruction(c, row, CONTENT_TOP, "Trace the lines from {OBJECT_EN_LOWER} down to {RELATION_EN_LOWER}.",
                    "Telusuri garis dari {OBJECT_ID_LOWER} ke bawah sampai {RELATION_ID_LOWER}.", accent, "A")
    hint_with_arrows(c, y - 18, "Top to bottom  /  Dari atas ke bawah", [-90])
    top = y - 26
    pw = (CONTENT_W - 3 * GAP) / 4                       # 4 kolom tinggi
    ph = top - (CONTENT_BOTTOM + 6)
    for i, style in enumerate([DOTS, DASHES, ROAD, FREE]):
        x = MARGIN + i * (pw + GAP)
        yb = top - ph
        cx = x + pw / 2
        panel(c, x, yb, pw, ph, fill=white, stroke=PALETTE["line"], lw=1.6, r=16)
        y_top_img, y_bot_img = yb + ph - 46, yb + 66
        obj_block(c, row.obj_en, row.obj_id, cx, y_top_img, 58, accent, wmax=pw - 10)
        obj_block(c, row.rel_en, row.rel_id, cx, y_bot_img, 58, accent, wmax=pw - 10)
        p1, p2 = (cx, y_top_img - 74), (cx, y_bot_img + 55)       # DUA tinggi berbeda, x SAMA => tegak
        pts = straight(p1, p2)
        trace_path(c, style, pts, accent)
        marker_start(c, p1, "down"); marker_end(c, p2)
        if i == 0:
            small_label(c, cx + 16, p1[1] - 2, "Start"); small_label(c, cx + 16, p1[1] - 12, "Mulai")
            small_label(c, cx + 16, p2[1] - 2, "Finish"); small_label(c, cx + 16, p2[1] - 12, "Selesai")
        if style == FREE:
            ym = (p1[1] + p2[1]) / 2
            for k, t in enumerate(["Draw it", "yourself!", "Gambar", "sendiri!"]):
                small_label(c, cx, ym + 16 - k * 12, t, "center", True, PALETTE[accent], 9.5)


# ================================================================== B  Garis Datar (Horizontal Lines)
def draw_b(c, row, pool, rng, accent):
    rows_template(c, row, accent, "B", "Trace the lines from {OBJECT_EN_LOWER} to {RELATION_EN_LOWER}.",
                  "Telusuri garis dari {OBJECT_ID_LOWER} ke {RELATION_ID_LOWER}.", "Left to right  /  Dari kiri ke kanan",
                  [(straight, DOTS, False), (straight, DASHES, False), (straight, SMALL_DOTS, False),
                   (straight, ROAD, False), (straight, FREE, False)])


# ================================================================== C  Garis Miring (Diagonal Lines)
def diag_panel(c, row, x, yb, w, h, up, style, accent, first=False):
    """up=True: objek di kiri-bawah -> pasangan kanan-atas.  up=False: kiri-atas -> kanan-bawah."""
    panel(c, x, yb, w, h, fill=white, stroke=PALETTE["line"], lw=1.6, r=16)
    y_hi, y_lo = yb + h - 34, yb + 62
    ay, by = (y_lo, y_hi) if up else (y_hi, y_lo)
    ax, bx = x + 38, x + w - 38
    obj_block(c, row.obj_en, row.obj_id, ax, ay, 52, accent, wmax=78)
    obj_block(c, row.rel_en, row.rel_id, bx, by, 52, accent, wmax=78)
    p1, p2 = (ax + 40, ay), (bx - 40, by)
    trace_path(c, style, straight(p1, p2), accent)
    marker_start(c, p1, "right"); marker_end(c, p2)
    if first:
        small_label(c, p1[0] + 16, p1[1] - 4, "Start / Mulai")
        small_label(c, p2[0] - 16, p2[1] - 4, "Finish / Selesai", "right")
    if style == FREE:
        small_label(c, x + w - 62, yb + h - 22, "Draw it yourself!", "center", True, PALETTE[accent], 10)
        small_label(c, x + w - 62, yb + h - 35, "Gambar sendiri!", "center", True, PALETTE[accent], 10)


def draw_c(c, row, pool, rng, accent):
    y = instruction(c, row, CONTENT_TOP, "Trace the slanted lines from {OBJECT_EN_LOWER} to {RELATION_EN_LOWER}.",
                    "Telusuri garis miring dari {OBJECT_ID_LOWER} ke {RELATION_ID_LOWER}.", accent, "C")
    hint_with_arrows(c, y - 18, "Follow the slanted line  /  Ikuti garis miring", [35, -35])
    pw, ph = (CONTENT_W - GAP) / 2, 240
    top = y - 26
    for i, (up, style) in enumerate([(True, DOTS), (False, DASHES), (True, ROAD), (False, FREE)]):
        r_, c_ = divmod(i, 2)
        diag_panel(c, row, MARGIN + c_ * (pw + GAP), top - (r_ + 1) * ph - r_ * GAP, pw, ph, up, style, accent, i == 0)


# ================================================================== D  Garis Zigzag
def draw_d(c, row, pool, rng, accent):
    zz = lambda amp, n: (lambda p1, p2: zigzag(p1, p2, amp, n))
    rows_template(c, row, accent, "D", "Trace the zigzag lines from {OBJECT_EN_LOWER} to {RELATION_EN_LOWER}.",
                  "Telusuri garis zigzag dari {OBJECT_ID_LOWER} ke {RELATION_ID_LOWER}.", "Up and down  /  Naik turun, ke kanan",
                  [(zz(22, 3), DOTS, True), (zz(22, 4), DASHES, True), (zz(20, 5), SMALL_DOTS, True),
                   (zz(20, 4), ROAD, True), (zz(22, 3), FREE, True)])


# ================================================================== E  Garis Lengkung (Curved Lines)
def draw_e(c, row, pool, rng, accent):
    hill = lambda p1, p2: arch(p1, p2, 30)           # ∩
    valley = lambda p1, p2: arch(p1, p2, -30)        # ∪
    s_curve = lambda p1, p2: wave(p1, p2, 24, 1)     # S
    big = lambda p1, p2: arch(p1, p2, 24)
    rows_template(c, row, accent, "E", "Trace the curved lines from {OBJECT_EN_LOWER} to {RELATION_EN_LOWER}.",
                  "Telusuri garis lengkung dari {OBJECT_ID_LOWER} ke {RELATION_ID_LOWER}.", "Follow the curve  /  Ikuti lengkungannya",
                  [(hill, DOTS, False), (valley, DASHES, False), (s_curve, SMALL_DOTS, False),
                   (big, ROAD, False), (s_curve, FREE, False)])


# ================================================================== F  Garis Gelombang (Wavy Lines)
def draw_f(c, row, pool, rng, accent):
    wv = lambda amp, n: (lambda p1, p2: wave(p1, p2, amp, n))
    rows_template(c, row, accent, "F", "Trace the wavy lines from {OBJECT_EN_LOWER} to {RELATION_EN_LOWER}.",
                  "Telusuri garis gelombang dari {OBJECT_ID_LOWER} ke {RELATION_ID_LOWER}.", "Ride the waves  /  Ikuti gelombangnya",
                  [(wv(16, 2), DOTS, False), (wv(18, 3), DASHES, False), (wv(18, 4), SMALL_DOTS, False),
                   (wv(20, 3), ROAD, False), (wv(18, 4), FREE, False)])


# ================================================================== G  Lingkaran & Spiral
def draw_g(c, row, pool, rng, accent):
    y = instruction(c, row, CONTENT_TOP, "Trace the circles and spirals.",
                    "Telusuri lingkaran dan spiral.", accent, "G")
    hint_with_arrows(c, y - 18, "Go round and round  /  Berputar mengikuti garis", [])
    pw, ph = (CONTENT_W - GAP) / 2, 158
    top = y - 26
    plan = [("circle", DOTS, "main"), ("circle", DASHES, "rel"), ("spiral", DOTS, "main"),
            ("spiral", DASHES, "rel"), ("circle", ROAD, "main"), ("circle", FREE, "rel")]
    for i, (kind, style, who) in enumerate(plan):
        r_, c_ = divmod(i, 2)
        x, yb = MARGIN + c_ * (pw + GAP), top - (r_ + 1) * ph - r_ * GAP
        cx, cy = x + pw / 2, yb + 88
        panel(c, x, yb, pw, ph, fill=white, stroke=PALETTE["line"], lw=1.6, r=16)
        en, id_ = (row.obj_en, row.obj_id) if who == "main" else (row.rel_en, row.rel_id)
        draw_object(c, en, cx, cy, 40 if kind == "spiral" else 48, "color")
        text_fit(c, cx, yb + 21, en, FONT_BOLD, 10, pw - 20, PALETTE["ink"], "center")
        text_fit(c, cx, yb + 9, id_, FONT_REG, 8.5, pw - 20, PALETTE[accent], "center")
        pts = circle_pts(cx, cy, 50) if kind == "circle" else spiral_in(cx, cy, 54, 33, 1.6)
        trace_path(c, style, pts, accent, band=22)
        marker_start(c, pts[0], "right")
        if kind == "spiral":
            marker_end(c, pts[-1])
        if style == FREE:
            small_label(c, x + 12, yb + ph - 16, "Draw a circle!", "left", True, PALETTE[accent], 9)
            small_label(c, x + 12, yb + ph - 28, "Buat lingkaran!", "left", False, PALETTE["grey"], 8.5)


# ================================================================== H  Pola Campuran (Mixed Patterns)
def draw_h(c, row, pool, rng, accent):
    zig_wave = lambda p1, p2: join(zigzag(p1, _mid(p1, p2), 20, 2), wave(_mid(p1, p2), p2, 18, 2))
    rows_template(c, row, accent, "H", "Trace the patterns from {OBJECT_EN_LOWER} to {RELATION_EN_LOWER}.",
                  "Telusuri pola dari {OBJECT_ID_LOWER} ke {RELATION_ID_LOWER}.", "Follow each pattern  /  Ikuti setiap pola",
                  [(lambda a, b: stairs(a, b, 28), DOTS, True),
                   (lambda a, b: scallops(a, b, 24, 4), DOTS, False),
                   (lambda a, b: loops(a, b, 22, 5, yscale=0.68), SMALL_DOTS, False),
                   (zig_wave, DOTS, False),
                   (lambda a, b: square_wave(a, b, 24, 3), SMALL_DOTS, True)])


def _mid(p1, p2):
    return ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)


# ================================================================== I  Mengikuti Jalur (Path Tracing)
def _rel(x1, x2, cy, pts_t):
    """Titik jalan relatif (t 0..1, dy) -> koordinat halaman."""
    return [(x1 + (x2 - x1) * t, cy + dy) for t, dy in pts_t]


def draw_i(c, row, pool, rng, accent):
    y = instruction(c, row, CONTENT_TOP, "Follow the road from {OBJECT_EN_LOWER} to {RELATION_EN_LOWER}.",
                    "Ikuti jalur dari {OBJECT_ID_LOWER} ke {RELATION_ID_LOWER}.", accent, "I")
    hint_with_arrows(c, y - 18, "Stay on the road  /  Tetap di dalam jalur", [0])
    rh = 156
    top = y - 26
    x1, x2 = MARGIN + 112, PAGE_W - MARGIN - 112
    decoy = pick_items(pool, 1, rng, [row.obj_en, row.rel_en])[0]
    # (lebar jalan, bentuk): 0 = satu jalan, 1 = bercabang 2 (satu benar, satu pengecoh)
    plan = [(34, 0), (28, 1), (24, 1)]
    for i, (width, fork) in enumerate(plan):
        yy = top - rh
        cy = yy + rh / 2
        panel(c, MARGIN, yy, CONTENT_W, rh, fill=white, stroke=PALETTE["line"], lw=1.6, r=16)
        obj_block(c, row.obj_en, row.obj_id, MARGIN + 52, cy + 8, 52, accent, wmax=90)
        if not fork:
            obj_block(c, row.rel_en, row.rel_id, PAGE_W - MARGIN - 52, cy + 8, 52, accent, wmax=90)
            pts = catmull(_rel(x1, x2, cy, [(0, 0), (.18, 38), (.38, -38), (.58, 38), (.78, -38), (1, 0)]))
            trace_path(c, ROAD, pts, accent, band=width)
            marker_start(c, pts[0]); marker_end(c, pts[-1])
        else:
            correct_top = rng.random() < 0.5
            ends = {"rel": (cy + 38 if correct_top else cy - 38), "decoy": (cy - 38 if correct_top else cy + 38)}
            draw_object(c, row.rel_en, PAGE_W - MARGIN - 52, ends["rel"], 48, "color")
            draw_object(c, decoy[0], PAGE_W - MARGIN - 52, ends["decoy"], 48, "color")
            a = 28 if i == 2 else 0
            stem = [(0, 0), (.10, a), (.20, -a), (.32, 0)] if a else [(0, 0), (.15, 14), (.32, 0)]
            up_br = [(.32, 0), (.48, 26), (.62, 22 if i == 1 else 30), (.80, 34), (1, 38)]
            dn_br = [(.32, 0), (.45, -30), (.62, -22 if i == 1 else -28), (.80, -36), (1, -38)]
            paths = [catmull(_rel(x1, x2, cy, stem + b[1:])) for b in (up_br, dn_br)]
            for pts in paths:
                trace_path(c, ROAD, pts, accent, band=width)
            marker_start(c, paths[0][0])
            for pts in paths:
                marker_end(c, pts[-1])
            small_label(c, PAGE_W / 2, yy + rh - 13, row.fmt("Find the {RELATION_EN_LOWER}!  /  Temukan {RELATION_ID_LOWER}!"),
                        "center", True, PALETTE[accent], 9.5)
        top = yy - GAP


# ================================================================== J  Menebalkan Bentuk Dasar (Shape Tracing)
def draw_j(c, row, pool, rng, accent):
    y = instruction(c, row, CONTENT_TOP, "Trace over the shapes.", "Tebalkan bentuk-bentuknya.", accent, "J")
    hint_with_arrows(c, y - 18, "Start at the green circle  /  Mulai dari lingkaran hijau", [])
    pw, ph = (CONTENT_W - GAP) / 2, 158
    top = y - 26

    def shapes(cx, cy):
        return [
            ("Circle", "Lingkaran", circle_pts(cx, cy, 50), False, 0),
            ("Square", "Persegi", polygon([(cx - 48, cy + 48), (cx + 48, cy + 48), (cx + 48, cy - 48), (cx - 48, cy - 48)]), True, 0),
            ("Triangle", "Segitiga", polygon([(cx, cy + 52), (cx + 56, cy - 46), (cx - 56, cy - 46)]), True, -10),
            ("Rectangle", "Persegi Panjang", polygon([(cx - 62, cy + 40), (cx + 62, cy + 40), (cx + 62, cy - 40), (cx - 62, cy - 40)]), True, 0),
            ("Oval", "Oval", oval_pts(cx, cy, 64, 42), False, 0),
            ("Diamond", "Belah Ketupat", polygon([(cx, cy + 54), (cx + 62, cy), (cx, cy - 54), (cx - 62, cy)]), True, 0),
        ]
    styles = [DOTS, DOTS, DASHES, DASHES, SMALL_DOTS, SMALL_DOTS]
    for i in range(6):
        r_, c_ = divmod(i, 2)
        x, yb = MARGIN + c_ * (pw + GAP), top - (r_ + 1) * ph - r_ * GAP
        cx, cy = x + pw / 2, yb + 86
        panel(c, x, yb, pw, ph, fill=white, stroke=PALETTE["line"], lw=1.6, r=16)
        name_en, name_id, pts, corners, dy = shapes(cx, cy)[i]
        en = row.obj_en if i % 2 == 0 else row.rel_en
        draw_object(c, en, cx, cy + dy, 40, "color")
        trace_path(c, styles[i], pts, accent, corners)
        marker_start(c, pts[0], "right")
        text_fit(c, cx, yb + 20, name_en, FONT_BOLD, 10.5, pw - 20, PALETTE["ink"], "center")
        text_fit(c, cx, yb + 8, name_id, FONT_REG, 9, pw - 20, PALETTE[accent], "center")


# ================================================================== daftar template
TEMPLATES = {
    "A": dict(name_en="Vertical Lines", name_id="Garis Tegak", accent="coral", fn=draw_a,
              objective_en="trace a straight line down from {OBJECT_EN_LOWER} to {RELATION_EN_LOWER}.",
              objective_id="menelusuri garis tegak dari {OBJECT_ID_LOWER} ke {RELATION_ID_LOWER}."),
    "B": dict(name_en="Horizontal Lines", name_id="Garis Datar", accent="sky", fn=draw_b,
              objective_en="trace a straight line across from {OBJECT_EN_LOWER} to {RELATION_EN_LOWER}.",
              objective_id="menelusuri garis datar dari {OBJECT_ID_LOWER} ke {RELATION_ID_LOWER}."),
    "C": dict(name_en="Diagonal Lines", name_id="Garis Miring", accent="mint", fn=draw_c,
              objective_en="trace a slanted line from {OBJECT_EN_LOWER} to {RELATION_EN_LOWER}.",
              objective_id="menelusuri garis miring dari {OBJECT_ID_LOWER} ke {RELATION_ID_LOWER}."),
    "D": dict(name_en="Zigzag Lines", name_id="Garis Zigzag", accent="grape", fn=draw_d,
              objective_en="trace zigzag lines from {OBJECT_EN_LOWER} to {RELATION_EN_LOWER}.",
              objective_id="menelusuri garis zigzag dari {OBJECT_ID_LOWER} ke {RELATION_ID_LOWER}."),
    "E": dict(name_en="Curved Lines", name_id="Garis Lengkung", accent="coral", fn=draw_e,
              objective_en="trace curved lines from {OBJECT_EN_LOWER} to {RELATION_EN_LOWER}.",
              objective_id="menelusuri garis lengkung dari {OBJECT_ID_LOWER} ke {RELATION_ID_LOWER}."),
    "F": dict(name_en="Wavy Lines", name_id="Garis Gelombang", accent="sky", fn=draw_f,
              objective_en="trace wavy lines from {OBJECT_EN_LOWER} to {RELATION_EN_LOWER}.",
              objective_id="menelusuri garis gelombang dari {OBJECT_ID_LOWER} ke {RELATION_ID_LOWER}."),
    "G": dict(name_en="Circles & Spirals", name_id="Lingkaran & Spiral", accent="mint", fn=draw_g,
              objective_en="trace circles and spirals around {OBJECT_EN_LOWER} and {RELATION_EN_LOWER}.",
              objective_id="menelusuri lingkaran dan spiral di sekitar {OBJECT_ID_LOWER} dan {RELATION_ID_LOWER}."),
    "H": dict(name_en="Mixed Patterns", name_id="Pola Campuran", accent="grape", fn=draw_h,
              objective_en="trace patterns made of steps, loops and waves.",
              objective_id="menelusuri pola dari tangga, simpul, dan gelombang."),
    "I": dict(name_en="Path Tracing", name_id="Mengikuti Jalur", accent="coral", fn=draw_i,
              objective_en="follow a road from {OBJECT_EN_LOWER} to {RELATION_EN_LOWER}.",
              objective_id="mengikuti jalur dari {OBJECT_ID_LOWER} ke {RELATION_ID_LOWER}."),
    "J": dict(name_en="Shape Tracing", name_id="Menebalkan Bentuk Dasar", accent="sky", fn=draw_j,
              objective_en="trace the basic shapes.",
              objective_id="menebalkan bentuk dasar."),
}
DEFAULT_SET = list("ABCDEFGHIJ")

# template lama tetap tersedia: LA..LI (= A..I versi 1.x)
for _k, _v in _LEGACY.items():
    TEMPLATES["L" + _k] = _v
