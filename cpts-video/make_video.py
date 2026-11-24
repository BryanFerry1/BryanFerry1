"""CPTS Entre Doubs et Jura - "Trouver un médecin traitant via Doctolib" (16:9, 1920x1080, 30 fps).

Re-animated version of the Canva project "Étapes Recherche Médecin Traitant":
the visuals (characters, screenshots, bubbles, background) come from Canva
(see extract_layers.py), the voice-over from ElevenLabs (assets/voice), and
the motion design / sound design is done here.

    python cpts-video/make_video.py --stills   # contact sheet -> out/stills.png
    python cpts-video/make_video.py            # full render  -> out/cpts_medecin_traitant.mp4
"""
import json
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tiktok-concepts", "lib"))
import sfx  # noqa: E402  (procedural sounds shared with the TikTok series)

W, H, FPS = 1920, 1080, 30
LAY = os.path.join(HERE, "assets", "layers")
FONTS = os.path.join(HERE, "assets", "fonts")
VOICE = os.path.join(HERE, "assets", "voice")
OUT = os.path.join(HERE, "out")
INTER = "/usr/share/fonts/opentype/inter"

NAVY = (10, 35, 66)
BLUE = (16, 122, 202)
YELLOW = (255, 201, 60)
WHITE = (255, 255, 255)
GREEN = (46, 184, 114)

# ----------------------------------------------------------------- timeline
VO_START = [0.8, 3.4, 10.4, 16.7, 22.5, 26.2, 34.9, 42.2, 45.3, 50.6]
SCENES = [  # (name, start, end)
    ("intro", 0.0, 10.0),
    ("google", 10.0, 16.4),
    ("doctolib", 16.4, 22.3),
    ("cpts", 22.3, 25.9),
    ("login", 25.9, 34.6),
    ("quest", 34.6, 41.9),
    ("sent", 41.9, 45.0),
    ("team", 45.0, 50.3),
    ("end", 50.3, 54.0),
]
DUR = 54.0
WHIP = 0.32
ALIGN = json.load(open(os.path.join(VOICE, "alignment.json")))


def words_of(i):
    """[(word, abs_start, abs_end)] for voice line i (0-based)."""
    a = ALIGN[i]
    out, cur, st, en = [], "", None, None
    for c, s, e in zip(a["chars"], a["start"], a["end"]):
        if c == " ":
            if cur:
                out.append((cur, st + VO_START[i], en + VO_START[i]))
            cur = ""
        else:
            if not cur:
                st = s
            cur += c
            en = e
    if cur:
        out.append((cur, st + VO_START[i], en + VO_START[i]))
    # the voice says "Dou" (phonetic spelling) but the screen must read "Doubs"
    return [("Doubs" if w == "Dou" else w, s0, s1) for w, s0, s1 in out]


def wt(i, word, nth=0):
    """absolute start time of a word in voice line i."""
    k = 0
    for w, s, _ in words_of(i):
        if w.strip("«»,.!?").lower().startswith(word.lower()):
            if k == nth:
                return s
            k += 1
    raise KeyError(word)


# ----------------------------------------------------------------- easing
def cl(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def prog(t, a, d):
    return cl((t - a) / d)


def o_cubic(p):
    return 1 - (1 - p) ** 3


def i_cubic(p):
    return p ** 3


def io_cubic(p):
    return 4 * p ** 3 if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2


def o_back(p, s=1.9):
    p = cl(p)
    return 1 + (s + 1) * (p - 1) ** 3 + s * (p - 1) ** 2


def lerp(a, b, p):
    return a + (b - a) * p


def pop(t, t0, d=0.45, s=1.9):
    """0 -> 1 with overshoot, starting at t0."""
    return o_back(prog(t, t0, d), s) if t >= t0 else 0.0


# ----------------------------------------------------------------- sprites
class Sprite:
    def __init__(self, rgba, base=1.0):
        """rgba: uint8 straight alpha. Stored premultiplied, with a small mip chain."""
        a = rgba[..., 3:4].astype(np.float32) / 255.0
        pm = np.concatenate([rgba[..., :3].astype(np.float32) * a, a * 255], -1).astype(np.uint8)
        self.mips = [pm]
        while min(self.mips[-1].shape[:2]) > 64:
            m = self.mips[-1]
            self.mips.append(cv2.resize(m, (m.shape[1] // 2, m.shape[0] // 2), interpolation=cv2.INTER_AREA))
        self.base = base
        self.h, self.w = rgba.shape[:2]


def load_sprite(path, base=1.0):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im.shape[2] == 3:
        im = np.dstack([im, np.full(im.shape[:2], 255, np.uint8)])
    return Sprite(cv2.cvtColor(im, cv2.COLOR_BGRA2RGBA), base)


def pil_sprite(img, base=0.5):
    return Sprite(np.array(img.convert("RGBA")), base)


class Seq:
    """Animated RGBA layer (frame sequence on disk), played ping-pong."""

    def __init__(self, name, base=1.0):
        self.dir = os.path.join(LAY, name)
        self.files = sorted(f for f in os.listdir(self.dir) if f.endswith(".png"))
        self.base = base
        self.cache = {}

    def at(self, t, speed=1.0):
        n = len(self.files)
        k = int(t * FPS * speed) % (2 * n - 2)
        i = k if k < n else 2 * n - 2 - k
        if i not in self.cache:
            if len(self.cache) > 40:
                self.cache.clear()
            self.cache[i] = load_sprite(os.path.join(self.dir, self.files[i]), self.base)
        return self.cache[i]


# ----------------------------------------------------------------- camera + blit
class Cam:
    z, cx, cy, ox = 1.0, W / 2, H / 2, 0.0


CAM = Cam()


def to_screen(x, y):
    return (x - CAM.cx) * CAM.z + W / 2 + CAM.ox, (y - CAM.cy) * CAM.z + H / 2


def blit(fr, sp, x, y, s=1.0, rot=0.0, alpha=1.0, ax=0.5, ay=0.5, cam=True, sx=1.0, sy=1.0):
    """Draw sprite so that its anchor (ax, ay) lands on world point (x, y)."""
    if alpha <= 0.003 or s <= 0.001:
        return
    S = s * sp.base * (CAM.z if cam else 1.0)
    X, Y = to_screen(x, y) if cam else (x, y)
    # choose mip level
    lvl = 0
    while lvl + 1 < len(sp.mips) and S * min(sx, sy) * (2 ** (lvl + 1)) <= 1.0:
        lvl += 1
    img = sp.mips[lvl]
    f = 2 ** lvl
    h, w = sp.h, sp.w
    c, sn = math.cos(rot), math.sin(rot)
    a11, a12 = c * S * sx, -sn * S * sy
    a21, a22 = sn * S * sx, c * S * sy
    tx = X - (a11 * ax * w + a12 * ay * h)
    ty = Y - (a21 * ax * w + a22 * ay * h)
    xs = [tx, tx + a11 * w, tx + a12 * h, tx + a11 * w + a12 * h]
    ys = [ty, ty + a21 * w, ty + a22 * h, ty + a21 * w + a22 * h]
    x0, x1 = max(0, int(min(xs)) - 1), min(W, int(max(xs)) + 2)
    y0, y1 = max(0, int(min(ys)) - 1), min(H, int(max(ys)) + 2)
    if x1 <= x0 or y1 <= y0:
        return
    M = np.array([[a11 * f, a12 * f, tx - x0], [a21 * f, a22 * f, ty - y0]], np.float32)
    warped = cv2.warpAffine(img, M, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR,
                            borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0)).astype(np.float32)
    a = warped[..., 3:4] * (alpha / 255.0)
    roi = fr[y0:y1, x0:x1]
    roi *= (1 - a)
    roi += warped[..., :3] * alpha


def at_frac(x, y, s, sp, fx, fy, ax=0.5, ay=0.5):
    """World position of fraction (fx, fy) of a sprite drawn at (x, y, s) with anchor (ax, ay)."""
    S = s * sp.base
    return x + (fx - ax) * sp.w * S, y + (fy - ay) * sp.h * S


# ----------------------------------------------------------------- text & shapes (PIL, 2x supersampled)
_FC = {}


def font(size, weight=700, family="fredoka"):
    key = (size, weight, family)
    if key not in _FC:
        if family == "fredoka":
            _FC[key] = ImageFont.truetype(os.path.join(FONTS, f"Fredoka-{weight}.ttf"), size)
        else:
            name = {400: "Inter-Regular", 500: "Inter-Medium", 600: "Inter-SemiBold", 700: "Inter-Bold"}[weight]
            _FC[key] = ImageFont.truetype(os.path.join(INTER, name + ".otf"), size)
    return _FC[key]


_TC = {}


def text(s, size, color=WHITE, weight=700, family="fredoka", shadow=None, align="center", spacing=1.12, maxw=None):
    """Sprite of (multi-line) text. size in output px. shadow: (rgb, offset_px, blur_px)."""
    key = (s, size, color, weight, family, shadow, align, spacing, maxw)
    if key in _TC:
        return _TC[key]
    k = 2
    f = font(size * k, weight, family)
    lines = []
    for para in s.split("\n"):
        if maxw:
            cur = ""
            for w in para.split(" "):
                trial = (cur + " " + w).strip()
                if f.getlength(trial) > maxw * k and cur:
                    lines.append(cur)
                    cur = w
                else:
                    cur = trial
            lines.append(cur)
        else:
            lines.append(para)
    asc, desc = f.getmetrics()
    lh = int((asc + desc) * spacing)
    tw = int(max(f.getlength(l) for l in lines)) + 8 * k
    pad = 30 * k if shadow else 6 * k
    img = Image.new("RGBA", (tw + 2 * pad, lh * len(lines) + 2 * pad), (0, 0, 0, 0))

    def draw_lines(d, col, dx=0, dy=0):
        for i, l in enumerate(lines):
            lw = f.getlength(l)
            x = pad + 4 * k + {"center": (tw - 8 * k - lw) / 2, "left": 0, "right": tw - 8 * k - lw}[align]
            d.text((x + dx, pad + i * lh + dy), l, font=f, fill=col)

    if shadow:
        col, off, blur = shadow
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw_lines(ImageDraw.Draw(sh), col + (200,), 0, off * k)
        img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(blur * k)))
    draw_lines(ImageDraw.Draw(img), color + (255,))
    sp = pil_sprite(img, 1.0 / k)
    _TC[key] = sp
    return sp


def rrect(w, h, r, fill, outline=None, ow=0, shadow=True):
    k = 2
    pad = 40 * k if shadow else 4 * k
    img = Image.new("RGBA", (w * k + 2 * pad, h * k + 2 * pad), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle([pad, pad + 14 * k, pad + w * k, pad + h * k + 14 * k], r * k,
                                             fill=(4, 30, 70, 90))
        img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(18 * k)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([pad, pad, pad + w * k, pad + h * k], r * k, fill=fill,
                        outline=outline, width=ow * k if outline else 0)
    return pil_sprite(img, 1.0 / k)


def circle(r, fill, outline=None, ow=0, shadow=False):
    return rrect(2 * r, 2 * r, r, fill, outline, ow, shadow)


def ring_sprite(w, h, r, color, ow):
    k = 2
    pad = 4 * k
    img = Image.new("RGBA", (w * k + 2 * pad, h * k + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle([pad, pad, pad + w * k, pad + h * k], r * k, outline=color + (255,),
                                          width=ow * k)
    return pil_sprite(img.filter(ImageFilter.GaussianBlur(1)), 1.0 / k)


def check_sprite(size, color=WHITE, width=10):
    k = 2
    img = Image.new("RGBA", (size * k, size * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pts = [(0.2 * size * k, 0.52 * size * k), (0.42 * size * k, 0.74 * size * k), (0.8 * size * k, 0.3 * size * k)]
    d.line(pts, fill=color + (255,), width=width * k, joint="curve")
    for p in (pts[0], pts[-1]):
        d.ellipse([p[0] - width * k / 2, p[1] - width * k / 2, p[0] + width * k / 2, p[1] + width * k / 2],
                  fill=color + (255,))
    return pil_sprite(img, 1.0 / k)


def star_sprite(size, color):
    k = 2
    s = size * k
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    c = s / 2
    pts = []
    for i in range(8):
        r = c if i % 2 == 0 else c * 0.32
        ang = i * math.pi / 4 - math.pi / 2
        pts.append((c + math.cos(ang) * r, c + math.sin(ang) * r))
    ImageDraw.Draw(img).polygon(pts, fill=color + (255,))
    return pil_sprite(img, 1.0 / k)


def warning_sprite(size):
    k = 2
    s = size * k
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, s, s], s // 2, fill=(0, 0, 0, 0))
    tri = [(s * 0.5, s * 0.08), (s * 0.95, s * 0.88), (s * 0.05, s * 0.88)]
    d.polygon(tri, fill=NAVY + (255,))
    d.rounded_rectangle([s * 0.46, s * 0.33, s * 0.54, s * 0.66], s * 0.03, fill=YELLOW + (255,))
    d.ellipse([s * 0.455, s * 0.71, s * 0.545, s * 0.8], fill=YELLOW + (255,))
    return pil_sprite(img, 1.0 / k)


def cursor_sprite():
    k = 4
    pts = [(0, 0), (0, 40), (10, 31), (17, 47), (24, 44), (17, 29), (30, 29)]
    img = Image.new("RGBA", (40 * k, 54 * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    P = [((x + 3) * k, (y + 3) * k) for x, y in pts]
    d.polygon(P, fill=(255, 255, 255, 255), outline=(20, 20, 20, 255), width=3 * k)
    return pil_sprite(img, 1.0 / k * 1.5)


def browser_sprite(w, h, url, content=WHITE):
    k = 2
    pad = 40 * k
    img = Image.new("RGBA", (w * k + 2 * pad, h * k + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([pad, pad + 18 * k, pad + w * k, pad + h * k + 18 * k], 26 * k,
                                         fill=(4, 30, 70, 110))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(22 * k)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([pad, pad, pad + w * k, pad + h * k], 26 * k, fill=content + (255,))
    bar = 74
    d.rounded_rectangle([pad, pad, pad + w * k, pad + bar * k], 26 * k, fill=(236, 240, 245, 255))
    d.rectangle([pad, pad + (bar - 30) * k, pad + w * k, pad + bar * k], fill=(236, 240, 245, 255))
    for i, col in enumerate([(255, 95, 87), (255, 189, 46), (40, 201, 64)]):
        cx, cy = pad + (34 + i * 30) * k, pad + bar / 2 * k
        d.ellipse([cx - 9 * k, cy - 9 * k, cx + 9 * k, cy + 9 * k], fill=col + (255,))
    d.rounded_rectangle([pad + 150 * k, pad + 16 * k, pad + (w - 40) * k, pad + (bar - 16) * k], 21 * k,
                        fill=(255, 255, 255, 255))
    f = font(24 * k, 500, "inter")
    d.text((pad + 180 * k, pad + 23 * k), url, font=f, fill=(90, 100, 115, 255))
    return pil_sprite(img, 1.0 / k)


# ----------------------------------------------------------------- assets
def load_assets():
    A = {}
    plate = cv2.cvtColor(cv2.imread(os.path.join(LAY, "plate.png")), cv2.COLOR_BGR2RGB)
    A["plate"] = plate.astype(np.float32)
    for n in ["burst", "google", "search", "cpts_card", "login_card", "bubble", "bulb"]:
        A[n] = load_sprite(os.path.join(LAY, n + ".png"), 0.5)  # 2x exports
    for n in ["char_thinking", "char_waving", "char_laptop1", "char_laptop2", "char_laptop3", "char_presenting",
              "char_questions", "char_highfive", "envelope"]:
        A[n] = Seq(n)
    A["logo_cpts"] = load_sprite(os.path.join(LAY, "logo_cpts.png"))
    A["logo_doctolib"] = load_sprite(os.path.join(LAY, "logo_doctolib.png"))
    A["cursor"] = cursor_sprite()
    A["browser_g"] = browser_sprite(1180, 760, "google.fr")
    A["browser_d"] = browser_sprite(1180, 760, "doctolib.fr", content=(16, 122, 202))
    return A


# ----------------------------------------------------------------- reusable bits
def ripple(fr, x, y, t, t0, color=(255, 255, 255)):
    p = prog(t, t0, 0.5)
    if 0 < p < 1:
        X, Y = to_screen(x, y)
        r = int(10 + 70 * o_cubic(p) * CAM.z)
        ov = fr.copy()
        cv2.circle(ov, (int(X), int(Y)), r, color, max(2, int(8 * (1 - p) * CAM.z)), cv2.LINE_AA)
        a = 0.9 * (1 - p)
        fr *= (1 - a)
        fr += ov * a


def cursor_path(t, keys):
    """keys: [(t, x, y)] -> position with eased moves."""
    if t <= keys[0][0]:
        return keys[0][1], keys[0][2]
    for (t0, x0, y0), (t1, x1, y1) in zip(keys, keys[1:]):
        if t <= t1:
            p = io_cubic(prog(t, t0, t1 - t0))
            # slight arc
            arc = math.sin(p * math.pi) * 40
            return lerp(x0, x1, p), lerp(y0, y1, p) - arc
    return keys[-1][1], keys[-1][2]


def draw_cursor(fr, A, t, keys, t_in, t_out, clicks=()):
    if not (t_in <= t <= t_out):
        return
    x, y = cursor_path(t, keys)
    press = 1.0
    for c in clicks:
        if c <= t < c + 0.18:
            press = 0.85
    a = min(prog(t, t_in, 0.2), 1 - prog(t, t_out - 0.2, 0.2))
    blit(fr, A["cursor"], x, y, press, ax=0.07, ay=0.05, alpha=a)


def typed(s, t, t0, cps=13.0):
    n = int(max(0, t - t0) * cps)
    return s[:min(len(s), n)]


def char_at(fr, A, name, t, x, y_bottom=1078, s=0.88, alpha=1.0, sx=1.0, sy=1.0, rot=0.0):
    sp = A[name].at(t)
    blit(fr, sp, x, y_bottom, s, rot=rot, alpha=alpha, ax=0.5, ay=0.985, sx=sx, sy=sy)


def word_block(lines, size, color=NAVY, weight=700, spacing=1.15, shadow=None):
    """Lay out words; returns [(sprite, dx, dy)] relative to the block centre."""
    f = font(size, weight)
    sp_w = f.getlength(" ")
    asc, desc = f.getmetrics()
    lh = (asc + desc) * spacing
    out = []
    top = -lh * len(lines) / 2
    for li, line in enumerate(lines):
        ws = line.split(" ")
        widths = [f.getlength(w) for w in ws]
        total = sum(widths) + sp_w * (len(ws) - 1)
        x = -total / 2
        for w, ww in zip(ws, widths):
            out.append((text(w, size, color, weight, shadow=shadow), x + ww / 2, top + lh * (li + 0.5)))
            x += ww + sp_w
    return out


def draw_words(fr, block, times, t, cx, cy, s=1.0, alpha=1.0, rot=0.0):
    c, sn = math.cos(rot), math.sin(rot)
    for (sp, dx, dy), t0 in zip(block, times):
        p = pop(t, t0, 0.35, 2.4)
        if p <= 0:
            continue
        x = cx + (dx * c - dy * sn) * s
        y = cy + (dx * sn + dy * c) * s
        blit(fr, sp, x, y, s * (0.4 + 0.6 * p), rot=rot, alpha=alpha * cl(p * 2))


# ----------------------------------------------------------------- scenes
def sc_intro(fr, A, t):
    # --- character: thinking, then waving
    e = o_back(prog(t, 0.1, 0.55), 1.4)
    swap = prog(t, 3.2, 0.25)
    if swap < 1:
        char_at(fr, A, "char_thinking", t, 330, 1078 + 700 * (1 - e), alpha=1 - swap)
    if swap > 0:
        hop = math.sin(prog(t, 3.2, 0.45) * math.pi) * 45
        sq = 1 + 0.06 * math.sin(prog(t, 3.2, 0.45) * math.pi * 2)
        char_at(fr, A, "char_waving", t, 330, 1078 - hop, alpha=swap, sy=sq, sx=2 - sq)

    # --- burst 1: "Vous recherchez un médecin traitant ?"
    b1 = pop(t, 0.5, 0.5, 1.6)
    out1 = i_cubic(prog(t, 3.0, 0.28))
    if b1 > 0 and out1 < 1:
        s = 1.7 * b1 * (1 - out1)
        rot = math.radians(math.sin(t * 2.2) * 1.5 - 25 * out1)
        blit(fr, A["burst"], 1110, 520, s, rot=rot)
        blk = word_block(["Vous recherchez", "un médecin traitant ?"], 70)
        times = [s0 for _, s0, _ in words_of(0)][:len(blk)]
        draw_words(fr, blk, times, t, 1115, 525, (1 - out1), rot=rot)

    # --- burst 2: "Prenez votre ordinateur et suivez-moi !"
    b2 = pop(t, 3.3, 0.5, 1.6)
    out2 = i_cubic(prog(t, 5.45, 0.28))
    if b2 > 0 and out2 < 1:
        s = 1.7 * b2 * (1 - out2)
        rot = math.radians(math.sin(t * 2.2 + 1) * 1.5 + 25 * out2)
        blit(fr, A["burst"], 1110, 520, s, rot=rot)
        blk = word_block(["Prenez votre", "ordinateur et", "suivez-moi !"], 68)
        ws = words_of(1)[:5]
        times = [ws[0][1], ws[1][1], ws[2][1], ws[3][1], ws[4][1], ws[4][1] + 0.15]
        draw_words(fr, blk, times, t, 1115, 525, (1 - out2), rot=rot)

    # --- "En 4 étapes simples" + step cards
    t_title = wt(1, "Nous")
    tp = pop(t, t_title, 0.5)
    if tp > 0:
        blit(fr, text("4 étapes simples", 86, WHITE, 700, shadow=(NAVY, 5, 6)), 1240, 265, tp)
    labels = ["Ouvrir\nDoctolib", "Trouver\nla CPTS", "Se\nconnecter", "Remplir le\nquestionnaire"]
    t_wave = wt(1, "étapes")
    for i, lab in enumerate(labels):
        t0 = t_title + 0.45 + i * 0.32
        p = pop(t, t0, 0.5, 1.7)
        if p <= 0:
            continue
        x = 775 + i * 310
        y = 610 - 30 * math.sin(cl((t - t_wave - i * 0.1) / 0.35) * math.pi)
        blit(fr, A.setdefault("card", rrect(280, 320, 34, WHITE)), x, y, p)
        blit(fr, A.setdefault("num_bg", circle(52, BLUE + (255,))), x, y - 75, p)
        blit(fr, text(str(i + 1), 64, WHITE, 700), x, y - 78, p)
        blit(fr, text(lab, 38, NAVY, 600, spacing=1.05), x, y + 70, p)


def sc_google(fr, A, t, a):
    u = t - a
    bp = o_back(prog(u, 0.0, 0.5), 1.3)
    bx, by = 760, 600
    blit(fr, A["browser_g"], bx, by, 0.9 + 0.1 * bp, alpha=cl(bp * 1.5))
    gs = (1060 / (A["google"].w * 0.5)) * (0.9 + 0.1 * bp)
    gx, gy = bx, by + 10
    blit(fr, A["google"], gx, gy, gs, alpha=cl(bp * 1.5))
    # typed text
    t_type = wt(2, "Doctolib")
    s_typed = typed("Doctolib", t, t_type, 12)
    fx, fy = at_frac(gx, gy, gs, A["google"], 0.16, 0.632)
    if t >= wt(2, "tapez"):
        tx = text(s_typed or " ", 30, (32, 33, 36), 500, "inter", align="left")
        blit(fr, tx, fx - 6, fy, 1.0, ax=0.0)
        # caret
        if int(t * 2.5) % 2 == 0 or (t_type <= t <= t_type + 0.8):
            cw = font(30, 500, "inter").getlength(s_typed)
            blit(fr, A.setdefault("caret", rrect(3, 34, 1, (26, 115, 232, 255), shadow=False)), fx + cw + 2, fy, 1)
    # enter glow on search bar
    t_enter = wt(2, "barre") + 0.35
    gp = prog(t, t_enter, 0.6)
    if 0 < gp < 1:
        bxc, byc = at_frac(gx, gy, gs, A["google"], 0.527, 0.632)
        blit(fr, A.setdefault("ring_g", ring_sprite(int(0.86 * 1060), int(0.16 * 408), 38, YELLOW, 6)),
             bxc, byc, 1 + 0.06 * o_cubic(gp), alpha=1 - gp)
    # character
    ce = o_cubic(prog(u, 0.1, 0.55))
    char_at(fr, A, "char_laptop1", t, 1590 + 500 * (1 - ce), 1078)
    # cursor
    tgt = at_frac(gx, gy, gs, A["google"], 0.3, 0.64)
    t_click = wt(2, "tapez")
    keys = [(t_click - 1.2, 1250, 980), (t_click - 0.05, tgt[0], tgt[1] + 10), (t_enter, tgt[0], tgt[1] + 10)]
    draw_cursor(fr, A, t, keys, t_click - 1.2, t_enter + 0.6, clicks=[t_click])
    ripple(fr, tgt[0], tgt[1] + 10, t, t_click, YELLOW)
    return {"focus": (at_frac(gx, gy, gs, A["google"], 0.36, 0.63)), "t_click": t_click, "t_enter": t_enter}


def sc_doctolib(fr, A, t, a):
    u = t - a
    bp = o_back(prog(u, 0.0, 0.5), 1.3)
    bx, by = 760, 600
    blit(fr, A["browser_d"], bx, by, 0.9 + 0.1 * bp, alpha=cl(bp * 1.5))
    ss = (1100 / (A["search"].w * 0.5)) * (0.9 + 0.1 * bp)
    sx, sy = bx, by - 60
    blit(fr, A["search"], sx, sy, ss, alpha=cl(bp * 1.5))
    t_click = wt(3, "recherchez") + 0.25
    t_type = wt(3, "CPTS")
    if t >= t_click:
        # hide placeholder, type the CPTS name
        px, py = at_frac(sx, sy, ss, A["search"], 0.28, 0.685)
        cover = A.setdefault("cover", rrect(int(0.36 * 1100), int(0.16 * 260), 6, (255, 255, 255, 255), shadow=False))
        blit(fr, cover, px, py, ss / (1100 / (A["search"].w * 0.5)))
        fx, fy = at_frac(sx, sy, ss, A["search"], 0.108, 0.685)
        s_typed = typed("CPTS Entre Doubs et Jura", t, t_type, 14)
        blit(fr, text(s_typed or " ", 25, NAVY, 600, "inter", align="left"), fx - 6, fy, 1.0, ax=0.0)
        if int(t * 2.5) % 2 == 0 or t_type <= t <= t_type + 1.8:
            cw = font(25, 600, "inter").getlength(s_typed)
            blit(fr, A.setdefault("caret2", rrect(3, 28, 1, (16, 122, 202, 255), shadow=False)), fx + cw + 2, fy, 1)
    # suggestion dropdown
    t_sug = t_type + 1.75
    sp = pop(t, t_sug, 0.4, 1.4)
    dx, dy = at_frac(sx, sy, ss, A["search"], 0.27, 1.0)
    dy += 75
    if sp > 0:
        blit(fr, A.setdefault("sug", rrect(560, 118, 18, WHITE)), dx, dy, sp)
        blit(fr, A.setdefault("pin", circle(30, BLUE + (255,))), dx - 220, dy, sp)
        blit(fr, text("CPTS Entre Doubs et Jura", 30, NAVY, 600, "inter", align="left"), dx - 175, dy - 18, sp, ax=0.0)
        blit(fr, text("Pontarlier · Centre de santé", 22, (90, 100, 115), 500, "inter", align="left"),
             dx - 175, dy + 22, sp, ax=0.0)
    t_pick = t_sug + 0.75
    hp = prog(t, t_pick, 0.5)
    if 0 < hp < 1:
        blit(fr, A.setdefault("ring_s", ring_sprite(570, 128, 22, YELLOW, 6)), dx, dy, 1 + 0.05 * o_cubic(hp),
             alpha=1 - hp)
    ce = o_cubic(prog(u, 0.1, 0.55))
    char_at(fr, A, "char_laptop2", t, 1590 + 500 * (1 - ce), 1078)
    tgt = at_frac(sx, sy, ss, A["search"], 0.3, 0.7)
    keys = [(t_click - 1.0, 1250, 980), (t_click - 0.05, tgt[0], tgt[1]), (t_sug + 0.2, tgt[0], tgt[1]),
            (t_pick - 0.05, dx - 60, dy + 5)]
    draw_cursor(fr, A, t, keys, t_click - 1.0, t_pick + 0.5, clicks=[t_click, t_pick])
    ripple(fr, tgt[0], tgt[1], t, t_click, YELLOW)
    ripple(fr, dx - 60, dy + 5, t, t_pick, YELLOW)
    return {"focus": at_frac(sx, sy, ss, A["search"], 0.3, 0.75), "t_click": t_click, "t_sug": t_sug,
            "drop": (dx, dy)}


def sc_cpts(fr, A, t, a):
    u = t - a
    bp = o_back(prog(u, 0.0, 0.5), 1.3)
    cs = (840 / (A["cpts_card"].h * 0.5)) * (0.9 + 0.1 * bp)
    cx, cy = 720, 575
    t_click = wt(4, "demande") + 0.1
    press = 1 - 0.03 * math.sin(prog(t, t_click, 0.25) * math.pi)
    blit(fr, A["cpts_card"], cx, cy, cs * press, alpha=cl(bp * 1.5))
    btn = at_frac(cx, cy, cs, A["cpts_card"], 0.485, 0.669)
    # highlight ring around the button when named
    t_name = wt(4, "Faire")
    hp = prog(t, t_name, 0.3)
    if hp > 0:
        pulse = 1 + 0.025 * math.sin((t - t_name) * 9)
        blit(fr, A.setdefault("ring_c", ring_sprite(int(0.81 * 840 * 816 / 1010), int(0.1 * 840) + 6, 16, YELLOW, 6)),
             btn[0], btn[1], pulse, alpha=hp)
    ce = o_cubic(prog(u, 0.1, 0.55))
    char_at(fr, A, "char_laptop3", t, 1590 + 500 * (1 - ce), 1078)
    keys = [(t_name - 0.9, 1300, 980), (t_click - 0.05, btn[0] + 40, btn[1] + 8)]
    draw_cursor(fr, A, t, keys, t_name - 0.9, a + 3.7, clicks=[t_click])
    ripple(fr, btn[0] + 40, btn[1] + 8, t, t_click, YELLOW)
    return {"btn": btn, "t_name": t_name, "t_click": t_click}


def sc_login(fr, A, t, a):
    u = t - a
    bp = o_back(prog(u, 0.0, 0.5), 1.3)
    ls = (720 / (A["login_card"].h * 0.5)) * (0.9 + 0.1 * bp)
    lx, ly = 650, 610
    blit(fr, A["login_card"], lx, ly, ls, alpha=cl(bp * 1.5))
    # ATTENTION banner
    t_att = VO_START[5]
    ap = pop(t, t_att, 0.45, 2.0)
    aout = i_cubic(prog(t, t_att + 2.4, 0.3))
    if ap > 0 and aout < 1:
        shake = math.sin((t - t_att) * 30) * 4 * (1 - prog(t, t_att, 0.9))
        s = ap * (1 - aout)
        blit(fr, A.setdefault("att_bg", rrect(520, 120, 60, YELLOW + (255,))), 650, 195, s, rot=math.radians(shake))
        blit(fr, A.setdefault("warn", warning_sprite(70)), 650 - 175, 193, s, rot=math.radians(shake))
        blit(fr, text("ATTENTION", 64, NAVY, 700), 650 + 40, 190, s, rot=math.radians(shake))
    b_conn = at_frac(lx, ly, ls, A["login_card"], 0.515, 0.893)
    b_insc = at_frac(lx, ly, ls, A["login_card"], 0.515, 0.614)
    bw = int(0.86 * A["login_card"].w * 0.5 * 720 / (A["login_card"].h * 0.5))
    bh = int(0.09 * 720) + 4
    for (bx, by), tn in ((b_conn, wt(5, "connecter")), (b_insc, wt(5, "créer"))):
        hp = prog(t, tn, 0.3)
        hout = prog(t, tn + 2.2, 0.4)
        if hp > 0 and hout < 1:
            pulse = 1 + 0.03 * math.sin((t - tn) * 9)
            blit(fr, A.setdefault("ring_l", ring_sprite(bw + 16, bh + 12, 22, YELLOW, 7)), bx, by, pulse,
                 alpha=hp * (1 - hout))
    # character + speech bubble
    ce = o_cubic(prog(u, 0.1, 0.55))
    char_at(fr, A, "char_presenting", t, 1260 + 600 * (1 - ce), 1078)
    t_bub = wt(5, "poursuivre")
    bpp = pop(t, t_bub, 0.5, 1.6)
    if bpp > 0:
        bs = (680 / (A["bubble"].w * 0.5))
        blit(fr, A["bubble"], 1545, 395, bs * bpp)
        blit(fr, text("Connectez-vous\nou créez un compte !", 42, NAVY, 600, spacing=1.08), 1535, 382, bpp)
        wig = math.sin(t * 5) * 8
        blit(fr, A["bulb"], 1850, 215, 0.42 * bpp, rot=math.radians(18 + wig))
    return {"conn": b_conn, "insc": b_insc}


QUESTIONS = [
    "Avez-vous actuellement un médecin traitant déclaré ?",
    "Souffrez-vous d’une ALD (Affection Longue Durée) ?",
    "Êtes-vous en capacité de vous déplacer pour consulter ?",
    "Votre numéro de sécurité sociale",
    "Pouvez-vous décrire la situation pour laquelle vous sollicitez un professionnel de santé ?",
]


def sc_quest(fr, A, t, a):
    u = t - a
    tp = pop(t, a + 0.15, 0.5)
    blit(fr, text("Le questionnaire", 70, WHITE, 700, shadow=(NAVY, 5, 6)), 345, 222, tp)
    ce = o_cubic(prog(u, 0.1, 0.55))
    char_at(fr, A, "char_questions", t, 345 - 600 * (1 - ce), 1078, s=0.8)
    t_q = wt(6, "questionnaire")
    t_ticks = [wt(6, "répondre") - 0.35 + i * 0.3 for i in range(5)]
    for i, q in enumerate(QUESTIONS):
        y = 245 + i * 128
        p = o_back(prog(t, t_q - 0.3 + i * 0.16, 0.5), 1.2)
        if p <= 0:
            continue
        x = 1235 + 900 * (1 - p)
        bump = 1 + 0.04 * math.sin(prog(t, t_ticks[i], 0.25) * math.pi)
        blit(fr, A.setdefault("pill", rrect(1080, 112, 30, WHITE)), x, y, bump)
        done = t >= t_ticks[i]
        if done:
            cp = o_back(prog(t, t_ticks[i], 0.3), 2.0)
            blit(fr, A.setdefault("cb_on", circle(26, GREEN + (255,))), x - 470, y, bump * cp)
            blit(fr, A.setdefault("chk", check_sprite(40, WHITE, 6)), x - 470, y, bump * cp)
        else:
            blit(fr, A.setdefault("cb_off", circle(26, WHITE + (255,), BLUE + (255,), 4)), x - 470, y, bump)
        sz = 30 if len(q) < 60 else 27
        blit(fr, text(q, sz, NAVY, 600, "inter", align="left", maxw=900, spacing=1.15), x - 425, y, bump, ax=0.0)
    # validate button
    t_btn = t_ticks[-1] + 0.35
    t_val = wt(6, "validez") + 0.15
    bp = pop(t, t_btn, 0.45, 1.8)
    if bp > 0:
        press = 1 - 0.06 * math.sin(prog(t, t_val, 0.25) * math.pi)
        ok = t >= t_val
        bg = A.setdefault("val_on", rrect(560, 104, 52, GREEN + (255,))) if ok else \
            A.setdefault("val", rrect(560, 104, 52, BLUE + (255,)))
        blit(fr, bg, 1235, 912, bp * press)
        blit(fr, text("Valider ma demande", 44, WHITE, 600), 1235, 908, bp * press)
    keys = [(t_btn, 1700, 1040), (t_val - 0.05, 1330, 925)]
    draw_cursor(fr, A, t, keys, t_btn, a + 7.3, clicks=[t_val])
    ripple(fr, 1330, 925, t, t_val, YELLOW)
    return {"t_ticks": t_ticks, "t_val": t_val, "t_q": t_q}


CONF_COLORS = [YELLOW, WHITE, (255, 99, 99), (99, 220, 150), (120, 200, 255)]
_conf_rng = np.random.default_rng(7)
CONF = [(_conf_rng.uniform(-1, 1), _conf_rng.uniform(0.4, 1.0), _conf_rng.uniform(0, 6.28), _conf_rng.uniform(-9, 9),
         CONF_COLORS[i % 5], _conf_rng.uniform(10, 22)) for i in range(140)]


def confetti(fr, t, t0, cx, cy):
    u = t - t0
    if u <= 0 or u > 3.2:
        return
    for dx, sp, ang, spin, col, size in CONF:
        vx = dx * 900 * sp
        vy = -(700 + 700 * sp)
        x = cx + vx * u * (1 - 0.25 * u)
        y = cy + vy * u + 900 * u * u
        X, Y = to_screen(x, y)
        if not (-20 < X < W + 20 and -20 < Y < H + 20):
            continue
        a = ang + spin * u
        w2, h2 = size * CAM.z, size * 0.55 * CAM.z * abs(math.cos(a * 1.3))
        c, s = math.cos(a), math.sin(a)
        pts = np.array([[X + c * w2 - s * h2, Y + s * w2 + c * h2], [X - c * w2 - s * h2, Y - s * w2 + c * h2],
                        [X - c * w2 + s * h2, Y - s * w2 - c * h2], [X + c * w2 + s * h2, Y + s * w2 - c * h2]],
                       np.int32)
        cv2.fillConvexPoly(fr, pts, col, cv2.LINE_AA)


def sc_sent(fr, A, t, a):
    t_v = wt(7, "voilà")
    t_env = wt(7, "envoyée")
    b = pop(t, a + 0.15, 0.5, 1.6)
    if b > 0:
        rot = math.radians(math.sin(t * 2.2) * 1.5)
        blit(fr, A["burst"], 880, 540, 1.8 * b, rot=rot)
        sw = prog(t, wt(7, "Votre") - 0.1, 0.2)
        if sw < 1:
            blk = word_block(["Et voilà !"], 110)
            draw_words(fr, blk, [wt(7, "Et"), t_v], t, 885, 540, 1 - sw, rot=rot)
        if sw > 0:
            blk = word_block(["Votre demande", "est envoyée !"], 80)
            ws = words_of(7)
            draw_words(fr, blk, [w[1] for w in ws[3:]] + [ws[-1][1] + 0.2], t, 885, 545, 1.0, rot=rot)
    # envelope flight
    ep = prog(t, wt(7, "Votre") - 0.2, 1.3)
    if 0 < ep < 1:
        p = io_cubic(ep)
        x = lerp(250, 2150, p)
        y = lerp(950, 120, p) - math.sin(p * math.pi) * 200
        blit(fr, A["envelope"].at(t, 1.5), x, y, 0.55, rot=math.radians(-12 + 10 * p))
    confetti(fr, t, t_env + 0.15, 880, 560)


def sc_team(fr, A, t, a):
    u = t - a
    cp = o_back(prog(u, 0.0, 0.55), 1.5)
    blit(fr, A.setdefault("circle", circle(390, WHITE + (255,), YELLOW + (255,), 14, shadow=True)), 1330, 590, cp)
    hp = o_cubic(prog(u, 0.1, 0.5))
    char_at(fr, A, "char_highfive", t, 1330, 1030 + 400 * (1 - hp), s=0.78)
    blk = word_block(["Notre équipe", "va la traiter !"], 92, WHITE, 700, shadow=(NAVY, 5, 6))
    ws = words_of(8)
    times = [ws[0][1], ws[1][1], ws[2][1], ws[4][1], ws[5][1]]
    draw_words(fr, blk, times, t, 560, 400)
    sp = pop(t, wt(8, "accompagner") - 0.1, 0.5, 1.5)
    if sp > 0:
        blit(fr, text("pour vous accompagner dans votre\nrecherche de médecin traitant", 46, WHITE, 500,
                      shadow=(NAVY, 3, 4), spacing=1.15), 560, 640, sp)
    # sparkles on the high five
    t_sp = wt(8, "traiter")
    for i in range(8):
        p = prog(t, t_sp + i * 0.03, 0.7)
        if 0 < p < 1:
            ang = i / 8 * 6.283
            r = 60 + 150 * o_cubic(p)
            blit(fr, A.setdefault("star", star_sprite(56, YELLOW)), 1330 + math.cos(ang) * r,
                 430 + math.sin(ang) * r, 1 - 0.6 * p, alpha=1 - p)


def sc_end(fr, A, t, a):
    blk = word_block(["À bientôt !"], 170, WHITE, 700, shadow=(NAVY, 7, 8))
    ws = words_of(9)
    draw_words(fr, blk, [ws[0][1], ws[1][1], ws[1][1] + 0.35], t, 960, 420)
    p = pop(t, a + 1.0, 0.5, 1.5)
    if p > 0:
        blit(fr, A.setdefault("end_pill", rrect(820, 110, 55, WHITE)), 960, 640, p)
        blit(fr, text("CPTS Entre Doubs et Jura", 54, NAVY, 600), 960, 636, p)
    p2 = pop(t, a + 1.35, 0.5, 1.5)
    if p2 > 0:
        blit(fr, text("Votre demande de médecin traitant, simplement, sur Doctolib.", 36, WHITE, 500,
                      shadow=(NAVY, 3, 4)), 960, 760, p2)
    confetti(fr, t, wt(9, "bientôt") + 0.2, 960, 520)


# ----------------------------------------------------------------- per-scene cameras
def cam_keys(name, a, b, info):
    """[(abs_t, zoom, cx, cy)] for the scene."""
    C = (1.0, W / 2, H / 2)
    if name == "intro":
        return [(a, 1.0, 960, 540), (a + 3.0, 1.05, 1000, 530), (a + 3.5, 1.0, 960, 540)]
    if name == "google":
        fx, fy = info["focus"]
        tc, te = info["t_click"], info["t_enter"]
        return [(a, *C), (tc - 0.4, *C), (tc + 0.4, 1.75, fx, fy), (te + 0.2, 1.75, fx, fy), (te + 0.8, *C)]
    if name == "doctolib":
        fx, fy = info["focus"]
        tc, ts = info["t_click"], info["t_sug"]
        dx, dy = info["drop"]
        return [(a, *C), (tc - 0.3, *C), (tc + 0.4, 1.6, fx + 60, fy), (ts - 0.1, 1.6, fx + 60, fy),
                (ts + 0.4, 1.35, dx - 20, dy - 80), (b - 0.5, 1.35, dx - 20, dy - 80), (b, 1.1, 900, 560)]
    if name == "cpts":
        bx, by = info["btn"]
        return [(a, *C), (info["t_name"] - 0.6, *C), (info["t_name"] - 0.05, 1.5, bx, by - 30),
                (b, 1.55, bx, by - 30)]
    if name == "login":
        cx, cy = info["conn"]
        ix, iy = info["insc"]
        tc, ti = wt(5, "connecter"), wt(5, "créer")
        return [(a, *C), (tc - 0.5, *C), (tc + 0.1, 1.45, cx + 60, cy - 120), (ti - 0.4, 1.45, cx + 60, cy - 120),
                (ti + 0.2, 1.45, ix + 60, iy - 60), (ti + 1.6, 1.45, ix + 60, iy - 60), (ti + 2.2, *C)]
    if name == "quest":
        tt = info["t_ticks"]
        return [(a, *C), (tt[0] - 0.6, *C), (tt[0] - 0.1, 1.18, 1180, 500), (tt[-1] + 0.2, 1.18, 1180, 500),
                (tt[-1] + 0.7, *C)]
    if name == "sent":
        return [(a, 1.0, 960, 540), (b, 1.06, 900, 540)]
    if name == "team":
        return [(a, 1.0, 960, 540), (b, 1.05, 960, 540)]
    return [(a, *C)]


def eval_cam(keys, t):
    if t <= keys[0][0]:
        return keys[0][1:]
    for k0, k1 in zip(keys, keys[1:]):
        if t <= k1[0]:
            p = io_cubic(prog(t, k0[0], max(1e-6, k1[0] - k0[0])))
            return tuple(lerp(x, y, p) for x, y in zip(k0[1:], k1[1:]))
    return keys[-1][1:]


SCENE_FN = {"intro": sc_intro, "google": sc_google, "doctolib": sc_doctolib, "cpts": sc_cpts, "login": sc_login,
            "quest": sc_quest, "sent": sc_sent, "team": sc_team, "end": sc_end}
STEP_OF = {"google": (1, "Rechercher Doctolib"), "doctolib": (2, "Trouver la CPTS"), "cpts": (2, "Trouver la CPTS"),
           "login": (3, "Se connecter"), "quest": (4, "Le questionnaire")}


# ----------------------------------------------------------------- overlay: step badge, captions, bg bubbles
def caption_chunks():
    out = []
    for i in range(len(ALIGN)):
        ws = words_of(i)
        cur = []
        for w in ws:
            if cur and (len(" ".join(x[0] for x in cur + [w])) > 44 or cur[-1][0][-1] in ".!?,"):
                out.append(cur)
                cur = []
            cur.append(w)
        if cur:
            out.append(cur)
    res = []
    for k, c in enumerate(out):
        start = c[0][1]
        end = c[-1][2] + 0.25
        if k + 1 < len(out):
            end = min(max(end, c[-1][2]), out[k + 1][0][1])
        res.append((start, end, " ".join(x[0] for x in c)))
    return res


CAPS = caption_chunks()
BUB_RNG = np.random.default_rng(3)
BUBBLES = [(BUB_RNG.uniform(0, W), BUB_RNG.uniform(0, H), BUB_RNG.uniform(14, 46), BUB_RNG.uniform(12, 30),
            BUB_RNG.uniform(0, 6.28)) for _ in range(14)]


def bg_bubbles(fr, t):
    ov = fr.copy()
    for x, y, r, v, ph in BUBBLES:
        yy = (y - v * t) % (H + 120) - 60
        xx = x + math.sin(t * 0.6 + ph) * 25
        cv2.circle(ov, (int(xx), int(yy)), int(r), (255, 255, 255), -1, cv2.LINE_AA)
    fr *= 0.93
    fr += ov * 0.07


def overlay(fr, A, t, scene_name):
    # step badge
    st = STEP_OF.get(scene_name)
    if st:
        n, label = st
        idx = [s[0] for s in SCENES].index(scene_name)
        _, a, b = SCENES[idx]
        prev_step = STEP_OF.get(SCENES[idx - 1][0], (0,))[0]
        next_step = STEP_OF.get(SCENES[idx + 1][0], (0,))[0] if idx + 1 < len(SCENES) else 0
        p = pop(t, a - 0.15, 0.45, 1.8) if prev_step != n else 1.0
        if next_step != n:
            p *= 1 - i_cubic(prog(t, b - WHIP, WHIP))
        if p > 0:
            blit(fr, A.setdefault("badge", rrect(600, 96, 48, WHITE)), 960, 78, p, cam=False)
            blit(fr, A.setdefault("badge_n", rrect(150, 64, 32, BLUE + (255,), shadow=False)), 960 - 205, 78, p,
                 cam=False)
            blit(fr, text(f"ÉTAPE {n}", 30, WHITE, 700), 960 - 205, 76, p, cam=False)
            blit(fr, text(label, 36, NAVY, 600, align="left"), 960 - 110, 75, p, ax=0.0, cam=False)
    # logos, always on top: CPTS on a white disc, Doctolib on a blue rounded rectangle
    blit(fr, A.setdefault("logo_disc", circle(118, WHITE + (255,), shadow=True)), 140, 935, 1, cam=False)
    blit(fr, A["logo_cpts"], 140, 935, 190 / max(A["logo_cpts"].w, A["logo_cpts"].h), cam=False)
    dcol = tuple(int(v) for v in A["logo_doctolib"].mips[0][5, 5, :3])
    blit(fr, A.setdefault("logo_rect", rrect(330, 110, 24, dcol + (255,), outline=(255, 255, 255, 255), ow=4, shadow=True)), 195, 82, 1, cam=False)
    blit(fr, A["logo_doctolib"], 195, 82, 300 / A["logo_doctolib"].w, cam=False)
    # captions
    for s0, s1, txt in CAPS:
        if s0 <= t < s1:
            sp = text(txt, 36, WHITE, 500)
            wpx = sp.w * sp.base
            key = ("capbg", int(wpx))
            if key not in A:
                A[key] = rrect(int(wpx) + 30, 62, 31, (8, 28, 60, 170), shadow=False)
            blit(fr, A[key], 960, 1022, 1, cam=False)
            blit(fr, sp, 960, 1020, 1, cam=False)


# ----------------------------------------------------------------- frame
def render_frame(A, t):
    fr = A["plate"].copy()
    bg_bubbles(fr, t)
    cur = None
    for i, (name, a, b) in enumerate(SCENES):
        enter = a - WHIP if i > 0 else a
        if not (enter <= t < b):
            continue
        # whip pan offsets
        ox = 0.0
        if i > 0 and t < a:
            ox = 2200 * (1 - io_cubic(prog(t, a - WHIP, WHIP)))
        if i < len(SCENES) - 1 and t >= b - WHIP:
            ox = -2200 * io_cubic(prog(t, b - WHIP, WHIP))
        # dry-run to get focus info for the camera (no drawing)
        CAM.z, CAM.cx, CAM.cy, CAM.ox = 1.0, W / 2, H / 2, ox
        info = None
        if name in ("google", "doctolib", "cpts", "login", "quest"):
            info = _info_only(A, name, a)
        z, cx, cy = eval_cam(cam_keys(name, a, b, info), t)
        CAM.z, CAM.cx, CAM.cy, CAM.ox = z, cx, cy, ox
        fn = SCENE_FN[name]
        if name in ("intro",):
            fn(fr, A, t)
        else:
            fn(fr, A, t, a)
        if cur is None or abs(ox) < 1100:
            cur = name
    CAM.z, CAM.cx, CAM.cy, CAM.ox = 1.0, W / 2, H / 2, 0.0
    overlay(fr, A, t, cur)
    # final fade
    fo = prog(t, DUR - 0.5, 0.5)
    if fo > 0:
        fr *= 1 - 0.85 * fo
    return np.clip(fr, 0, 255).astype(np.uint8)


_INFO = {}


def _info_only(A, name, a):
    """Static layout info (positions don't depend on time once the entrance is done)."""
    if name in _INFO:
        return _INFO[name]
    CAM.z, CAM.cx, CAM.cy, CAM.ox = 1.0, W / 2, H / 2, 0.0
    scratch = np.zeros((H, W, 3), np.float32)
    info = SCENE_FN[name](scratch, A, a + 2.0, a)
    _INFO[name] = info
    return info


# ----------------------------------------------------------------- audio
def load_mp3(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(sfx.SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def pop_snd(f0=700, f1=250, d=0.12, amp=0.5):
    x = sfx.sweep(d, f0, f1) * sfx.env_ad(int(d * sfx.SR), 0.002, d * 0.6, 3.0)
    return x * amp


def click_snd(seed=0):
    d = 0.05
    n = int(d * sfx.SR)
    x = sfx.bandnoise(d, 2000, 8000, seed) * sfx.env_ad(n, 0.001, 0.012, 5) * 0.5
    tk = sfx.tick(3200, 0.2)[:n]
    x[:len(tk)] += tk
    return x


def key_snd(seed=0):
    d = 0.06
    n = int(d * sfx.SR)
    rng = np.random.default_rng(seed)
    return sfx.bandnoise(d, 1500 + rng.uniform(0, 1500), 7000, seed) * sfx.env_ad(n, 0.001, 0.02, 5) * 0.35


def pluck(freq, dur, amp=0.25, seed=0):
    """Karplus-Strong plucked string (ukulele-ish)."""
    sr = sfx.SR
    N = max(2, int(sr / freq))
    n = int(dur * sr)
    rng = np.random.default_rng(seed)
    buf = rng.uniform(-1, 1, N)
    out = np.zeros(n)
    blocks = (n + N - 1) // N
    y = buf
    for bi in range(blocks):
        seg = y[: min(N, n - bi * N)]
        out[bi * N: bi * N + len(seg)] = seg
        y = 0.996 * 0.5 * (y + np.roll(y, -1))
    out *= sfx.env_ad(n, 0.002, dur, 1.5)
    return out * amp


def music(dur):
    """Soft, friendly ukulele-like loop: C - G - Am - F at 100 bpm."""
    sr = sfx.SR
    bpm = 100
    beat = 60 / bpm
    out = np.zeros(int(dur * sr) + sr)
    chords = [[261.6, 329.6, 392.0], [196.0, 246.9, 293.7], [220.0, 261.6, 329.6], [174.6, 220.0, 261.6]]
    basses = [130.8, 98.0, 110.0, 87.3]
    pattern = [0, 1, 2, 1, 0, 2, 1, 2]
    t = 0.0
    bar = 0
    while t < dur:
        ch = chords[bar % 4]
        for k, idx in enumerate(pattern):
            st = t + k * beat / 2
            if st >= dur:
                break
            f = ch[idx] * (2 if k in (2, 5) else 1)
            x = pluck(f, 0.9, 0.16 if k % 2 == 0 else 0.11, seed=bar * 8 + k)
            i0 = int(st * sr)
            out[i0:i0 + len(x)] += x[:len(out) - i0]
        # bass
        for k in (0, 2):
            st = t + k * beat
            n = int(beat * 1.6 * sr)
            tt = np.arange(n) / sr
            x = np.sin(2 * np.pi * basses[bar % 4] * tt) * sfx.env_ad(n, 0.01, beat * 1.4, 2.5) * 0.22
            i0 = int(st * sr)
            out[i0:i0 + n] += x[:len(out) - i0]
        # soft shaker on off-beats
        for k in range(4):
            st = t + k * beat + beat / 2
            x = sfx.bandnoise(0.07, 5000, 12000, bar * 4 + k) * sfx.env_ad(int(0.07 * sr), 0.004, 0.03, 4) * 0.05
            i0 = int(st * sr)
            out[i0:i0 + len(x)] += x[:len(out) - i0]
        t += 4 * beat
        bar += 1
    return out[: int(dur * sr)]


def build_audio(path, with_music=True):
    sr = sfx.SR
    n = int(DUR * sr)
    vo = np.zeros(n)
    for i in range(10):
        x = load_mp3(os.path.join(VOICE, f"vo_{i + 1:02d}.mp3"))
        i0 = int(VO_START[i] * sr)
        vo[i0:i0 + len(x)] += x[:n - i0]
    fx = np.zeros(n)

    def add(t, x, g=1.0):
        i0 = int(t * sr)
        if 0 <= i0 < n:
            fx[i0:i0 + len(x)] += (x * g)[:n - i0]

    # whooshes on scene changes
    for name, a, b in SCENES[1:]:
        add(a - WHIP - 0.05, sfx.whoosh(0.45, 400, 6000, 0.55, seed=int(a)), 0.55)
    # intro pops
    add(0.5, pop_snd(600, 200, 0.16), 0.9)
    for _, s0, _ in words_of(0):
        add(s0, pop_snd(900, 500, 0.06, 0.25))
    add(3.3, pop_snd(650, 220, 0.16), 0.9)
    t_title = wt(1, "Nous")
    add(t_title, pop_snd(500, 900, 0.14), 0.7)
    for i in range(4):
        add(t_title + 0.45 + i * 0.32, pop_snd(600 + 120 * i, 350 + 80 * i, 0.12), 0.8)
    # google: click + typing + enter
    tc = wt(2, "tapez")
    add(tc, click_snd(1), 0.9)
    t_type = wt(2, "Doctolib")
    for k in range(8):
        add(t_type + k / 12, key_snd(k), 0.9)
    add(wt(2, "barre") + 0.35, click_snd(2), 1.0)
    # doctolib: click, typing, suggestion, pick
    t_click = wt(3, "recherchez") + 0.25
    add(t_click, click_snd(3), 0.9)
    t_type = wt(3, "CPTS")
    for k in range(24):
        add(t_type + k / 14, key_snd(10 + k), 0.8)
    t_sug = t_type + 1.75
    add(t_sug, pop_snd(500, 800, 0.1), 0.5)
    add(t_sug + 0.75, click_snd(4), 0.9)
    # cpts click
    add(wt(4, "demande") + 0.1, click_snd(5), 1.0)
    add(wt(4, "Faire"), sfx.chime(1046, 0.2), 0.6)
    # login
    add(VO_START[5], pop_snd(400, 200, 0.18), 0.9)
    add(wt(5, "poursuivre"), pop_snd(650, 300, 0.14), 0.7)
    add(wt(5, "connecter"), sfx.chime(880, 0.2), 0.6)
    add(wt(5, "créer"), sfx.chime(988, 0.2), 0.6)
    # questionnaire: slide-ins, ticks, validate
    tq = wt(6, "questionnaire")
    for i in range(5):
        add(tq - 0.3 + i * 0.16, sfx.swish(i), 0.5)
    for i in range(5):
        add(wt(6, "répondre") - 0.35 + i * 0.3, sfx.chime(1046 + 110 * i, 0.22), 0.7)
    add(wt(6, "validez") + 0.15, click_snd(6), 1.0)
    # sent: success arpeggio + envelope whoosh + confetti
    add(41.9 + 0.15, pop_snd(600, 200, 0.18), 0.9)
    add(wt(7, "Votre") - 0.2, sfx.whoosh(1.1, 300, 7000, 0.5, seed=9), 0.6)
    te = wt(7, "envoyée")
    for k, f in enumerate([784, 988, 1175, 1568]):
        add(te + k * 0.08, sfx.chime(f, 0.25), 0.8)
    add(te + 0.15, sfx.sparkle(1.4, 70, 3), 0.35)
    # team: clap on high five
    add(wt(8, "traiter"), sfx.bandnoise(0.12, 800, 6000, 5) * sfx.env_ad(int(0.12 * sr), 0.001, 0.04, 5), 0.6)
    add(wt(8, "traiter"), sfx.sparkle(1.0, 60, 8), 0.3)
    # end
    add(wt(9, "bientôt") + 0.2, sfx.sparkle(1.6, 70, 4), 0.3)
    for k, f in enumerate([523, 659, 784, 1046]):
        add(wt(9, "À") + k * 0.09, sfx.chime(f, 0.2), 0.6)

    mix = vo * 1.0 + fx * 0.32
    if with_music:
        m = music(DUR)
        # duck under the voice
        env = np.abs(vo)
        win = int(0.25 * sr)
        env = np.convolve(env, np.ones(win) / win, mode="same")
        duck = 1 - 0.55 * np.clip(env / 0.05, 0, 1)
        fade = np.clip(np.arange(n) / (0.8 * sr), 0, 1) * np.clip((n - np.arange(n)) / (1.2 * sr), 0, 1)
        mix += m * 0.28 * duck * fade
    peak = np.abs(mix).max()
    mix = mix / peak * 0.89
    pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    import wave
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


# ----------------------------------------------------------------- main
def stills(A):
    times = [1.6, 4.6, 8.9, 12.0, 14.0, 19.5, 21.6, 24.5, 26.8, 30.0, 32.6, 37.0, 39.0, 40.6, 44.2, 47.5, 51.6, 15.3]
    tiles = []
    for t in sorted(times):
        fr = render_frame(A, t)
        sm = cv2.resize(fr, (640, 360), interpolation=cv2.INTER_AREA)
        cv2.putText(sm, f"{t:.1f}s", (8, 24), 0, 0.7, (255, 255, 0), 2)
        tiles.append(sm)
    rows = [np.hstack(tiles[i:i + 3]) for i in range(0, len(tiles), 3)]
    sheet = np.vstack(rows)
    os.makedirs(OUT, exist_ok=True)
    cv2.imwrite(os.path.join(OUT, "stills.png"), cv2.cvtColor(sheet, cv2.COLOR_RGB2BGR))
    print("stills ->", os.path.join(OUT, "stills.png"))


def full(A):
    os.makedirs(OUT, exist_ok=True)
    tmp_v = os.path.join(OUT, "_video.mp4")
    wav = os.path.join(OUT, "_audio.wav")
    wav_nm = os.path.join(OUT, "_audio_nomusic.wav")
    build_audio(wav, True)
    build_audio(wav_nm, False)
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                          "-pix_fmt", "yuv420p", tmp_v], stdin=subprocess.PIPE)
    nf = int(DUR * FPS)
    for k in range(nf):
        p.stdin.write(render_frame(A, k / FPS).tobytes())
        if k % 150 == 0:
            print(f"frame {k}/{nf}", flush=True)
    p.stdin.close()
    p.wait()
    for wavf, name in ((wav, "cpts_medecin_traitant.mp4"), (wav_nm, "cpts_medecin_traitant_sans_musique.mp4")):
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp_v, "-i", wavf, "-c:v", "copy", "-c:a", "aac",
                        "-b:a", "192k", "-shortest", "-movflags", "+faststart", os.path.join(OUT, name)], check=True)
    for f in (tmp_v, wav, wav_nm):
        os.remove(f)
    print("done ->", os.path.join(OUT, "cpts_medecin_traitant.mp4"))


if __name__ == "__main__":
    A = load_assets()
    if "--stills" in sys.argv:
        stills(A)
    elif "--frame" in sys.argv:
        t = float(sys.argv[sys.argv.index("--frame") + 1])
        cv2.imwrite(os.path.join(OUT, f"frame_{t:.2f}.png"), cv2.cvtColor(render_frame(A, t), cv2.COLOR_RGB2BGR))
    else:
        full(A)
