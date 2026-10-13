"""
Illustration layer.

draw_object(c, name, cx, cy, size, mode)  draws an object centred at (cx, cy) inside a size x size box.

Lookup order for every object:
  1. assets/images/<slug>.png          (AI / designer artwork, transparent PNG)
       - mode "outline" uses assets/images/<slug>_line.png if present, else auto-edges
       - mode "shadow"  uses the PNG's alpha channel as a silhouette
  2. built-in vector drawer below      (consistent house style, works offline)
  3. generic friendly badge            (flagged by QC as 'needs artwork')

Modes: "color" | "outline" (colouring page) | "shadow" (shadow matching)
"""
import math
from contextlib import contextmanager
from pathlib import Path
from PIL import Image, ImageFilter, ImageChops, ImageOps
from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import ImageReader
from .config import ASSETS, FONT_BOLD, PALETTE, ROOT
from .database import slug

INK = HexColor(PALETTE["ink"])
SHADOW = HexColor("#8E8EA0")
BASE_LW = 3.4


class Ink:
    """Tiny drawing kit working in a 100x100 unit box centred on (0,0)."""

    def __init__(self, c, mode="color"):
        self.c, self.mode = c, mode

    # -- colour handling per mode
    def _set(self, color, keep=False, stroke_on=True):
        c = self.c
        if self.mode == "shadow":
            c.setFillColor(SHADOW); c.setStrokeColor(SHADOW)
        elif self.mode == "outline":
            c.setFillColor(HexColor(color) if keep else white); c.setStrokeColor(INK)
        else:
            c.setFillColor(HexColor(color)); c.setStrokeColor(INK)

    def _lw(self, mult=1.0):
        self.c.setLineWidth(BASE_LW * mult)

    # -- shapes
    def circle(self, x, y, r, color, keep=False, stroke=1):
        self._set(color, keep); self._lw()
        self.c.circle(x, y, r, stroke=stroke, fill=1)

    def ellipse(self, x, y, rx, ry, color, keep=False, stroke=1):
        self._set(color, keep); self._lw()
        self.c.ellipse(x - rx, y - ry, x + rx, y + ry, stroke=stroke, fill=1)

    def rrect(self, x, y, w, h, r, color, keep=False, stroke=1):
        self._set(color, keep); self._lw()
        self.c.roundRect(x, y, w, h, r, stroke=stroke, fill=1)

    def poly(self, pts, color, keep=False, stroke=1):
        self._set(color, keep); self._lw()
        p = self.c.beginPath(); p.moveTo(*pts[0])
        for q in pts[1:]:
            p.lineTo(*q)
        p.close(); self.c.drawPath(p, stroke=stroke, fill=1)

    def path(self, fn, color, keep=False, stroke=1):
        self._set(color, keep); self._lw()
        p = self.c.beginPath(); fn(p); self.c.drawPath(p, stroke=stroke, fill=1)

    def line(self, x1, y1, x2, y2, color="#2B2B3A", w=1.2):
        c = self.c
        c.setStrokeColor(SHADOW if self.mode == "shadow" else (INK if self.mode == "outline" else HexColor(color)))
        c.setLineWidth(BASE_LW * w); c.line(x1, y1, x2, y2)

    def stroke_path(self, fn, color="#2B2B3A", w=0.8):
        c = self.c
        c.setStrokeColor(SHADOW if self.mode == "shadow" else (INK if self.mode == "outline" else HexColor(color)))
        c.setLineWidth(BASE_LW * w)
        p = c.beginPath(); fn(p); c.drawPath(p, stroke=1, fill=0)

    def blob(self, circles, color):
        """Union of circles drawn as ONE outlined cloud shape."""
        self._set(color)
        self.c.setLineWidth(BASE_LW * 2)
        for x, y, r in circles:
            self.c.circle(x, y, r, stroke=1, fill=1)
        for x, y, r in circles:
            self.c.circle(x, y, r, stroke=0, fill=1)

    @contextmanager
    def clip_ellipse(self, x, y, rx, ry):
        self.c.saveState()
        p = self.c.beginPath(); p.ellipse(x - rx, y - ry, 2 * rx, 2 * ry)
        self.c.clipPath(p, stroke=0, fill=0)
        yield
        self.c.restoreState()

    @contextmanager
    def clip_rrect(self, x, y, w, h, r):
        self.c.saveState()
        p = self.c.beginPath(); p.roundRect(x, y, w, h, r)
        self.c.clipPath(p, stroke=0, fill=0)
        yield
        self.c.restoreState()

    # -- face parts (hidden in shadow mode)
    def eyes(self, x, y, gap, r=3.6, light=False):
        if self.mode == "shadow":
            return
        for dx in (-gap / 2, gap / 2):
            self.eye(x + dx, y, r, light)

    def eye(self, x, y, r=3.6, light=False):
        if self.mode == "shadow":
            return
        c = self.c
        if light:
            c.setFillColor(white); c.setStrokeColor(INK); c.setLineWidth(BASE_LW * 0.6)
            c.circle(x, y, r * 1.4, stroke=1, fill=1)
        c.setFillColor(INK); c.circle(x, y, r * (0.7 if light else 1), stroke=0, fill=1)
        c.setFillColor(white); c.circle(x + r * 0.3, y + r * 0.35, r * 0.28, stroke=0, fill=1)

    def smile(self, x, y, w=7):
        if self.mode == "shadow":
            return
        c = self.c
        c.setStrokeColor(INK); c.setLineWidth(BASE_LW * 0.7)
        c.arc(x - w, y - w, x + w, y + w, startAng=205, extent=130)

    def blush(self, x, y, gap, r=4.5):
        if self.mode != "color":
            return
        self.c.setFillColor(HexColor("#FFB3B3"))
        for dx in (-gap / 2, gap / 2):
            self.c.circle(x + dx, y, r, stroke=0, fill=1)

    def shine(self, fn, w=0.7):
        """Highlights only in colour mode."""
        if self.mode != "color":
            return
        self.c.setStrokeColor(white); self.c.setLineWidth(BASE_LW * w)
        self.c.setLineCap(1)
        p = self.c.beginPath(); fn(p); self.c.drawPath(p, stroke=1, fill=0)


# =============================================================== drawers
def chicken(k):
    k.circle(-9, 31, 7, "#FF5A5F"); k.circle(0, 35, 8, "#FF5A5F"); k.circle(9, 31, 7, "#FF5A5F")
    for x in (-10, 10):
        k.line(x, -38, x, -50, "#FF9F1C", w=1.4); k.line(x - 8, -50, x + 7, -50, "#FF9F1C", w=1.4)
    k.poly([(-30, 4), (-52, 28), (-44, 6), (-54, -4), (-32, -16)], "#FFC94D")
    k.circle(0, -6, 34, "#FFE27A")
    k.ellipse(-8, -10, 17, 12, "#FFC94D")
    k.poly([(27, 9), (47, 3), (27, -3)], "#FF9F1C")
    k.circle(24, -11, 5, "#FF5A5F")
    k.eye(13, 15, 3.8)


def egg(k):
    def shape(p):
        p.moveTo(0, 42); p.curveTo(24, 42, 34, 6, 34, -12)
        p.curveTo(34, -34, 18, -42, 0, -42); p.curveTo(-18, -42, -34, -34, -34, -12)
        p.curveTo(-34, 6, -24, 42, 0, 42); p.close()
    k.path(shape, "#FFEFD6")
    if k.mode == "color":
        k.c.setFillColor(HexColor("#E8C9A0"))
        for x, y in [(-16, 18), (14, 24), (20, -6), (-22, -14), (6, -30)]:
            k.c.circle(x, y, 2.4, stroke=0, fill=1)
    k.eyes(0, 6, 22, 4); k.smile(0, -2, 8); k.blush(0, -6, 38, 5)
    k.shine(lambda p: (p.moveTo(-20, 22), p.curveTo(-24, 14, -24, 8, -22, 2)))


def bee(k):
    k.ellipse(-14, 32, 13, 19, "#BEE6FF"); k.ellipse(6, 34, 13, 19, "#BEE6FF")
    k.poly([(-34, -5), (-50, 0), (-34, 6)], "#2B2B3A", keep=True)
    k.ellipse(-6, 0, 34, 26, "#FFD23F")
    with k.clip_ellipse(-6, 0, 33, 25):
        k.rrect(-24, -30, 11, 60, 0, "#2B2B3A", keep=True)
        k.rrect(-4, -30, 11, 60, 0, "#2B2B3A", keep=True)
    k.circle(30, 3, 17, "#FFD23F")
    k.line(34, 18, 41, 36, w=0.8); k.circle(42, 38, 3.6, "#2B2B3A", keep=True)
    k.line(26, 18, 22, 36, w=0.8); k.circle(21.5, 38, 3.6, "#2B2B3A", keep=True)
    k.eyes(30, 7, 12, 3.4); k.smile(30, 1, 6); k.blush(30, -1, 24, 3.5)


def honey(k):
    k.rrect(-28, -44, 56, 68, 12, "#FFB627")
    k.rrect(-20, -36, 40, 30, 8, "#FFF1C9")
    k.poly([(0, -13), (8, -18), (8, -27), (0, -32), (-8, -27), (-8, -18)], "#FFB627")
    k.rrect(-32, 24, 64, 14, 5, "#8B5E3C")
    k.ellipse(-14, 23, 6.5, 8, "#FFB627", stroke=1); k.ellipse(12, 22, 7, 10, "#FFB627", stroke=1)
    k.eyes(0, 10, 18, 3.4); k.smile(0, 3, 6); k.blush(0, 5, 34, 4)
    k.shine(lambda p: (p.moveTo(-21, -2), p.lineTo(-21, 14)))


def cow(k):
    k.poly([(-22, 24), (-31, 46), (-11, 31)], "#FFF1C9"); k.poly([(22, 24), (31, 46), (11, 31)], "#FFF1C9")
    k.ellipse(-42, 14, 14, 8, "#FFFFFF"); k.ellipse(42, 14, 14, 8, "#FFFFFF")
    if k.mode == "color":
        k.c.setFillColor(HexColor("#FFB3C1"))
        k.c.ellipse(-48, 11, -36, 17, stroke=0, fill=1); k.c.ellipse(36, 11, 48, 17, stroke=0, fill=1)
    k.ellipse(0, 6, 32, 34, "#FFFFFF")
    with k.clip_ellipse(0, 6, 31, 33):
        k.ellipse(-22, 26, 15, 13, "#2B2B3A", keep=True, stroke=0)
        k.ellipse(24, 4, 9, 14, "#2B2B3A", keep=True, stroke=0)
    k.ellipse(0, -14, 23, 15, "#FFB3C1")
    k.circle(-8, -14, 3, "#2B2B3A", keep=True, stroke=0); k.circle(8, -14, 3, "#2B2B3A", keep=True, stroke=0)
    k.eyes(0, 14, 28, 4.2)


def milk(k):
    k.rrect(-14, 38, 28, 8, 2, "#CFE8FF")
    k.poly([(-26, 18), (-14, 40), (14, 40), (26, 18)], "#CFE8FF")
    k.rrect(-26, -44, 52, 62, 3, "#FFFFFF")
    with k.clip_rrect(-26, -44, 52, 62, 3):
        k.rrect(-30, -44, 60, 30, 0, "#4FB3E8", stroke=0)
    k.line(-26, -14, 26, -14, w=0.7)
    if k.mode == "color":
        k.c.setFillColor(white)
        k.c.circle(0, -32, 7, stroke=0, fill=1)
        p = k.c.beginPath(); p.moveTo(-6, -29); p.lineTo(6, -29); p.lineTo(0, -17); p.close()
        k.c.drawPath(p, stroke=0, fill=1)
    k.eyes(0, 5, 18, 3.6); k.smile(0, -3, 7); k.blush(0, -1, 34, 4)


def sheep(k):
    for x in (-14, 14):
        k.rrect(x - 4.5, -52, 9, 18, 3, "#6E6E80")
    ring = [(26 * math.cos(math.radians(a)), 2 + 26 * math.sin(math.radians(a)), 16) for a in range(0, 360, 36)]
    k.blob(ring + [(0, 2, 26)], "#FFFFFF")
    k.ellipse(-25, 0, 11, 6, "#6E6E80"); k.ellipse(25, 0, 11, 6, "#6E6E80")
    k.ellipse(0, -5, 19, 22, "#6E6E80")
    k.eyes(0, 0, 18, 3.4, light=True)
    k.ellipse(0, -14, 6, 4, "#FFB3C1", stroke=0)


def wool(k):
    k.circle(0, 2, 33, "#F78FB3")
    with k.clip_ellipse(0, 2, 32, 32):
        for fn in (
            lambda p: (p.moveTo(-36, 18), p.curveTo(-12, 38, 12, 34, 36, 10)),
            lambda p: (p.moveTo(-36, -4), p.curveTo(-10, 16, 14, 12, 36, -14)),
            lambda p: (p.moveTo(-34, -26), p.curveTo(-8, -8, 14, -12, 34, -34)),
            lambda p: (p.moveTo(-14, 36), p.curveTo(-28, 10, -28, -14, -12, -36)),
            lambda p: (p.moveTo(12, 36), p.curveTo(-2, 10, -2, -14, 14, -36)),
        ):
            k.stroke_path(fn, "#D9577F", 0.6)
    k.stroke_path(lambda p: (p.moveTo(26, -20), p.curveTo(48, -30, 34, -46, 54, -44)), "#D9577F", 1.0)
    k.eyes(0, 8, 20, 3.6); k.smile(0, 1, 7)


def tree(k):
    k.ellipse(0, -48, 30, 5, "#A8E6A1")
    k.rrect(-9, -48, 18, 46, 3, "#A9744F")
    k.blob([(0, 14, 27), (-24, 0, 21), (24, 0, 21), (-12, 30, 18), (14, 30, 18)], "#5CCB6B")
    for x, y in [(-12, 12), (14, 22), (-24, -2), (10, -2)]:
        k.circle(x, y, 6.5, "#FF5A5F")
    k.eyes(0, -22, 9, 2.6); k.smile(0, -28, 4)


def apple(k):
    def shape(p):
        p.moveTo(0, 26); p.curveTo(-12, 38, -46, 30, -42, -6)
        p.curveTo(-40, -34, -22, -46, -6, -40); p.curveTo(-3, -39, 3, -39, 6, -40)
        p.curveTo(22, -46, 40, -34, 42, -6); p.curveTo(46, 30, 12, 38, 0, 26); p.close()
    k.path(shape, "#FF5A5F")
    k.rrect(-2.5, 24, 5, 16, 2, "#8B5E3C")
    k.ellipse(12, 38, 12, 6, "#5CCB6B")
    k.eyes(0, 2, 24, 4); k.smile(0, -8, 8); k.blush(0, -6, 46, 5)
    k.shine(lambda p: (p.moveTo(-30, 16), p.curveTo(-36, 8, -36, 0, -34, -6)))


def generic(k, label="?"):
    h = sum(ord(ch) for ch in label)
    col = ["#FFB3A7", "#9ED8F5", "#FFE08A", "#9BE3C8", "#CBB8F2"][h % 5]
    k.blob([(0, 0, 36)], col)
    if k.mode != "shadow":
        k.c.setFillColor(INK); k.c.setFont(FONT_BOLD, 54)
        k.c.drawCentredString(0, -19, (label[:1] or "?").upper())


DRAWERS = {
    "chicken": chicken, "egg": egg, "bee": bee, "honey": honey, "cow": cow,
    "milk": milk, "sheep": sheep, "wool": wool, "tree": tree, "apple": apple,
}
# built-in vocabulary of the vector library; used as distractor pool fallback
ART_NAMES = {
    "chicken": ("Chicken", "Ayam"), "egg": ("Egg", "Telur"), "bee": ("Bee", "Lebah"),
    "honey": ("Honey", "Madu"), "cow": ("Cow", "Sapi"), "milk": ("Milk", "Susu"),
    "sheep": ("Sheep", "Domba"), "wool": ("Wool", "Wol"), "tree": ("Tree", "Pohon"),
    "apple": ("Apple", "Apel"),
}
ART_PAIRS = [("chicken", "egg"), ("bee", "honey"), ("cow", "milk"), ("sheep", "wool"), ("tree", "apple")]


def has_art(name_en: str) -> bool:
    s = slug(name_en)
    return s in DRAWERS or (ASSETS / "images" / f"{s}.png").exists()


# =============================================================== PNG support
_CACHE = ROOT / ".cache"


def _derived(png: Path, mode: str) -> Path:
    _CACHE.mkdir(exist_ok=True)
    out = _CACHE / f"{png.stem}_{mode}_{int(png.stat().st_mtime)}.png"
    if out.exists():
        return out
    im = Image.open(png).convert("RGBA")
    alpha = im.split()[3]
    if mode == "shadow":
        sil = Image.new("RGBA", im.size, (142, 142, 160, 0)); sil.putalpha(alpha); sil.save(out)
    else:  # outline: edges of alpha + luminance, black on white
        pad = 8
        bg = Image.new("RGB", (im.width + 2 * pad, im.height + 2 * pad), "white")
        bg.paste(im, (pad, pad), mask=alpha)
        edges = bg.convert("L").filter(ImageFilter.FIND_EDGES).crop((pad, pad, pad + im.width, pad + im.height))
        edges = ImageOps.autocontrast(edges).point(lambda v: 0 if v > 40 else 255)
        edges = edges.filter(ImageFilter.MinFilter(3))           # thicken
        line = Image.new("RGBA", im.size, (43, 43, 58, 0))
        line.putalpha(ImageChops.invert(edges)); line.save(out)
    return out


def draw_png(c, png: Path, cx, cy, size, mode):
    if mode == "outline" and (png.parent / f"{png.stem}_line.png").exists():
        path = png.parent / f"{png.stem}_line.png"
    elif mode in ("outline", "shadow"):
        path = _derived(png, mode)
    else:
        path = png
    c.drawImage(ImageReader(str(path)), cx - size / 2, cy - size / 2, size, size,
                mask="auto", preserveAspectRatio=True, anchor="c")


# =============================================================== public API
def draw_object(c, name_en: str, cx, cy, size, mode="color"):
    s = slug(name_en)
    png = ASSETS / "images" / f"{s}.png"
    if png.exists():
        draw_png(c, png, cx, cy, size, mode)
        return
    c.saveState()
    c.translate(cx, cy); c.scale(size / 110.0, size / 110.0)
    c.setLineCap(1); c.setLineJoin(1)
    k = Ink(c, mode)
    if s in DRAWERS:
        DRAWERS[s](k)
    else:
        generic(k, name_en)
    c.restoreState()
