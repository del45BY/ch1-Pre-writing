"""
Mesin menggambar jalur untuk template pra-menulis (garis tegak, datar, miring, zigzag, lengkung,
gelombang, lingkaran, spiral, pola campuran, jalur, bentuk).

Prinsip: SEMUA garis = daftar titik [(x, y), ...].
  1. geometri  -> membuat daftar titik (straight, zigzag, wave, arch, spiral, ...)
  2. trace_path -> menggambar daftar titik itu dalam 5 gaya kesulitan
  3. marker_*  -> tanda mulai (hijau) dan selesai (merah)
Template baru cukup membuat daftar titik; cara menggambarnya sudah tersedia.
"""
import math
from reportlab.lib.colors import white
from reportlab.pdfbase.pdfmetrics import stringWidth
from .art import draw_object
from .components import text_fit
from .config import FONT_BOLD, FONT_REG, MARGIN, PALETTE, hx

# gaya garis (urutan mudah -> sulit)
DOTS, DASHES, SMALL_DOTS, ROAD, FREE = 0, 1, 2, 3, 4


# ================================================================== GEOMETRI (semua mengembalikan list titik)
def _lin(p1, p2, t):
    return (p1[0] + (p2[0] - p1[0]) * t, p1[1] + (p2[1] - p1[1]) * t)


def straight(p1, p2):
    return [p1, p2]


def zigzag(p1, p2, amp, teeth):
    """Gigi gergaji: mulai dan selesai di garis tengah. teeth = jumlah puncak."""
    n = 2 * teeth
    pts = []
    for k in range(n + 1):
        x, y = _lin(p1, p2, k / n)
        off = 0 if k % 2 == 0 else (amp if (k // 2) % 2 == 0 else -amp)
        pts.append((x, y + off))
    return pts


def wave(p1, p2, amp, cycles, per_cycle=28):
    n = per_cycle * cycles
    return [(_lin(p1, p2, i / n)[0], p1[1] + amp * math.sin(2 * math.pi * cycles * i / n)) for i in range(n + 1)]


def arch(p1, p2, h, n=60):
    """h>0 = busur ke atas (lengkung ∩), h<0 = ke bawah (∪)."""
    return [(_lin(p1, p2, i / n)[0], p1[1] + h * math.sin(math.pi * i / n)) for i in range(n + 1)]


def scallops(p1, p2, h, count, per=24):
    pts = []
    for j in range(count):
        a, b = _lin(p1, p2, j / count), _lin(p1, p2, (j + 1) / count)
        seg = arch(a, b, h, per)
        pts += seg if j == 0 else seg[1:]
    return pts


def stairs(p1, p2, amp):
    """Tangga naik lalu turun (mulai dan selesai di garis tengah)."""
    levels = [0, .5, 1, 1, .5, 0]              # 6 kolom: naik, datar di puncak, turun
    cols = len(levels)
    pts = []
    for i, lv in enumerate(levels):
        a, b = _lin(p1, p2, i / cols), _lin(p1, p2, (i + 1) / cols)
        pts += [(a[0], p1[1] + lv * amp), (b[0], p1[1] + lv * amp)]
    return pts


def square_wave(p1, p2, amp, pulses):
    segs = 2 * pulses + 1
    pts = []
    for k in range(segs):
        a, b = _lin(p1, p2, k / segs), _lin(p1, p2, (k + 1) / segs)
        lv = 0 if k % 2 == 0 else amp
        pts += [(a[0], p1[1] + lv), (b[0], p1[1] + lv)]
    return pts


def loops(p1, p2, a, k, per=28, yscale=0.7):
    """Simpul seperti tulisan sambung 'eeee' (trochoid). a besar = simpul besar;
    yscale<1 memipihkan simpul agar muat di baris yang pendek."""
    dx = p2[0] - p1[0]
    b = dx / (2 * math.pi * k)
    n = per * k
    pts = []
    for i in range(n + 1):
        u = 2 * math.pi * k * i / n
        pts.append((p1[0] + b * u - a * math.sin(u), p1[1] + yscale * a * (1 - math.cos(u))))
    return pts


def join(*parts):
    out = list(parts[0])
    for p in parts[1:]:
        out += p[1:]
    return out


def circle_pts(cx, cy, r, n=120):
    """Searah jarum jam, mulai dari titik atas; titik terakhir = titik pertama."""
    return [(cx + r * math.sin(2 * math.pi * i / n), cy + r * math.cos(2 * math.pi * i / n)) for i in range(n + 1)]


def oval_pts(cx, cy, rx, ry, n=120):
    return [(cx + rx * math.sin(2 * math.pi * i / n), cy + ry * math.cos(2 * math.pi * i / n)) for i in range(n + 1)]


def spiral_in(cx, cy, r0, r1, turns, n=200):
    """Spiral dari luar (atas) ke dalam, searah jarum jam."""
    pts = []
    for i in range(n + 1):
        t = i / n
        r = r0 + (r1 - r0) * t
        a = 2 * math.pi * turns * t
        pts.append((cx + r * math.sin(a), cy + r * math.cos(a)))
    return pts


def polygon(points):
    return list(points) + [points[0]]


def catmull(points, per_seg=18):
    """Kurva halus yang melewati semua titik jalan (waypoints)."""
    P = [points[0]] + list(points) + [points[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for s in range(per_seg):
            t = s / per_seg
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                                    + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in (0, 1)))
    out.append(tuple(points[-1]))
    return out


# ================================================================== PENGGAMBAR JALUR
def _resample(pts, spacing, corners=False):
    """Titik-titik berjarak rata sepanjang garis. corners=True: tiap sudut pasti kebagian titik."""
    def seg_points(a, b):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, round(L / spacing))
        return [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n)]
    if corners:
        out = []
        for a, b in zip(pts, pts[1:]):
            out += seg_points(a, b)
        return out + [pts[-1]]
    cum = [0.0]
    for a, b in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    total = cum[-1]
    n = max(2, round(total / spacing))
    out, j = [], 0
    for i in range(n + 1):
        d = total * i / n
        while j < len(cum) - 2 and cum[j + 1] < d:
            j += 1
        seg = cum[j + 1] - cum[j] or 1
        t = (d - cum[j]) / seg
        out.append((pts[j][0] + (pts[j + 1][0] - pts[j][0]) * t, pts[j][1] + (pts[j + 1][1] - pts[j][1]) * t))
    return out


def _polyline(c, pts):
    p = c.beginPath(); p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    return p


def trace_path(c, style, pts, accent, corners=False, band=26):
    """Gambar satu jalur tracing. style: 0 titik besar | 1 putus-putus | 2 titik kecil | 3 jalur | 4 kosong."""
    c.saveState()
    c.setStrokeColor(hx(PALETTE["grey"])); c.setFillColor(hx(PALETTE["grey"]))
    c.setLineCap(1); c.setLineJoin(1)
    if style == DOTS:
        for x, y in _resample(pts, 17, corners):
            c.circle(x, y, 4, stroke=0, fill=1)
    elif style == SMALL_DOTS:
        for x, y in _resample(pts, 10, corners):
            c.circle(x, y, 2.3, stroke=0, fill=1)
    elif style == DASHES:
        c.setLineWidth(6); c.setDash(26, 14)
        c.drawPath(_polyline(c, pts), stroke=1, fill=0)
    elif style == ROAD:
        c.setStrokeColor(hx(PALETTE[accent])); c.setStrokeAlpha(0.22); c.setLineWidth(band)
        c.drawPath(_polyline(c, pts), stroke=1, fill=0)
        c.setStrokeAlpha(1); c.setStrokeColor(hx(PALETTE["line"])); c.setLineWidth(2); c.setDash(8, 8)
        c.drawPath(_polyline(c, pts), stroke=1, fill=0)
    c.restoreState()                              # FREE: tidak menggambar apa pun


# ================================================================== PENANDA
_TRI = {
    "right": [(-3, 5), (-3, -5), (5, 0)], "left": [(3, 5), (3, -5), (-5, 0)],
    "down": [(-5, 3), (5, 3), (0, -5)],   "up": [(-5, -3), (5, -3), (0, 5)],
}


def marker_start(c, pt, direction="right"):
    x, y = pt
    c.setFillColor(hx(PALETTE["mint"])); c.setStrokeColor(white); c.setLineWidth(2)
    c.circle(x, y, 11, stroke=1, fill=1)
    c.setFillColor(white)
    a, b, d = _TRI[direction]
    p = c.beginPath(); p.moveTo(x + a[0], y + a[1]); p.lineTo(x + b[0], y + b[1]); p.lineTo(x + d[0], y + d[1]); p.close()
    c.drawPath(p, stroke=0, fill=1)


def marker_end(c, pt):
    x, y = pt
    c.setFillColor(hx(PALETTE["coral"])); c.setStrokeColor(white); c.setLineWidth(2)
    c.circle(x, y, 11, stroke=1, fill=1)
    c.setFillColor(white); c.rect(x - 4.5, y - 4.5, 9, 9, stroke=0, fill=1)


# ================================================================== ELEMEN HALAMAN
def hint_with_arrows(c, y, text, angles=()):
    """Teks petunjuk abu-abu + panah GAMBAR (bukan huruf font, jadi aman untuk font apa pun)."""
    c.setFont(FONT_BOLD, 12); c.setFillColor(hx(PALETTE["grey"]))
    c.drawString(MARGIN + 4, y, text)
    x = MARGIN + 4 + stringWidth(text, FONT_BOLD, 12) + 16
    for a in angles:
        c.saveState(); c.translate(x, y + 4); c.rotate(a)
        c.setStrokeColor(hx(PALETTE["grey"])); c.setFillColor(hx(PALETTE["grey"]))
        c.setLineWidth(2.2); c.setLineCap(1)
        c.line(-10, 0, 6, 0)
        p = c.beginPath(); p.moveTo(12, 0); p.lineTo(5, 5); p.lineTo(5, -5); p.close()
        c.drawPath(p, stroke=0, fill=1)
        c.restoreState()
        x += 34


def obj_block(c, en, id_, cx, cy, size, accent, labels=True, wmax=100):
    """Gambar objek + kata Inggris di atas kata Indonesia di bawahnya."""
    draw_object(c, en, cx, cy, size, "color")
    if labels:
        text_fit(c, cx, cy - size / 2 - 13, en, FONT_BOLD, 11, wmax, PALETTE["ink"], "center")
        text_fit(c, cx, cy - size / 2 - 25, id_, FONT_REG, 9, wmax, PALETTE[accent], "center")


def small_label(c, x, y, text, align="left", bold=False, color=None, size=8.5):
    c.setFont(FONT_BOLD if bold else FONT_REG, size)
    c.setFillColor(hx(color or PALETTE["grey"]))
    {"left": c.drawString, "center": c.drawCentredString, "right": c.drawRightString}[align](x, y, text)
