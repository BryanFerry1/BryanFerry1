"""Shared rendering engine for the black & white "concept" shorts.

Everything is drawn procedurally with Skia (anti-aliased vectors), then
composited with a multi-radius bloom in numpy/OpenCV to get the
"illuminated white figure on pure black" look. Accent colour: red.
"""
import math
import os
import subprocess

import cv2
import numpy as np
import skia

W, H, FPS = 1080, 1920, 30

WHITE = (1.0, 0.965, 0.92)
RED = (1.0, 0.13, 0.16)

FONT_DIR = "/usr/share/fonts/opentype/inter"
_TF = {}


def typeface(name="Inter-Bold"):
    if name not in _TF:
        _TF[name] = skia.Typeface.MakeFromFile(os.path.join(FONT_DIR, name + ".otf"))
    return _TF[name]


def font(size, name="Inter-Bold"):
    f = skia.Font(typeface(name), size)
    f.setSubpixel(True)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


def mix(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def smoothstep(a, b, x):
    t = clamp((x - a) / (b - a)) if b != a else float(x >= a)
    return t * t * (3 - 2 * t)


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def paint(color, alpha=1.0, stroke=None, cap=True):
    p = skia.Paint(AntiAlias=True)
    p.setColor4f(skia.Color4f(color[0], color[1], color[2], clamp(alpha)))
    if stroke is not None:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        if cap:
            p.setStrokeCap(skia.Paint.kRound_Cap)
            p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


class Layer:
    """An RGBA raster layer we draw into with skia, read back as float RGB."""

    def __init__(self):
        self.surface = skia.Surface(W, H)
        self.canvas = self.surface.getCanvas()

    def clear(self):
        self.canvas.clear(skia.Color4f(0, 0, 0, 0))

    def rgb(self):
        img = self.surface.makeImageSnapshot()
        arr = img.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType,
                          alphaType=skia.AlphaType.kPremul_AlphaType)
        return arr[:, :, :3].astype(np.float32) * (1.0 / 255.0)


def blur(img, sigma):
    d = max(1, int(sigma / 3))
    if d > 1:
        small = cv2.resize(img, (W // d, H // d), interpolation=cv2.INTER_AREA)
        small = cv2.GaussianBlur(small, (0, 0), sigma / d)
        return cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR)
    return cv2.GaussianBlur(img, (0, 0), sigma)


def bloom(img, spec):
    out = img * spec[0]
    for sigma, k in spec[1:]:
        out += blur(img, sigma) * k
    return out


def spaced_width(text, f, spacing):
    return sum(f.measureText(c) for c in text) + spacing * max(0, len(text) - 1)


def draw_spaced(canvas, text, cx, y, f, spacing, p):
    """Draw text centred on cx with manual letter spacing."""
    x = cx - spaced_width(text, f, spacing) / 2
    for c in text:
        canvas.drawString(c, x, y, f, p)
        x += f.measureText(c) + spacing


def draw_runs(canvas, runs, cx, y, f, spacing):
    """runs: list of (text, paint). Centred as one line."""
    total = sum(spaced_width(t, f, spacing) for t, _ in runs) + spacing * (len(runs) - 1)
    x = cx - total / 2
    for t, p in runs:
        for c in t:
            canvas.drawString(c, x, y, f, p)
            x += f.measureText(c) + spacing


class Post:
    """Vignette + film grain, precomputed."""

    def __init__(self, seed=3):
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        nx, ny = (xx / W - 0.5) * 2, (yy / H - 0.5) * 2
        r = np.sqrt(nx ** 2 * 1.0 + ny ** 2 * 0.55)
        self.vig = (1.0 - 0.55 * np.clip(r - 0.35, 0, 1) ** 1.6)[..., None]
        rng = np.random.default_rng(seed)
        self.grain = [rng.normal(0, 1, (H, W, 1)).astype(np.float32) for _ in range(6)]
        # faint warm background haze so the black isn't dead flat
        self.bg = (0.012 * np.exp(-((nx) ** 2 * 0.8 + (ny + 0.1) ** 2 * 0.9)))[..., None] * \
            np.array([1.0, 0.95, 0.9], np.float32)

    def apply(self, img, frame):
        img = img + self.bg
        img = img * self.vig
        img = img + self.grain[frame % len(self.grain)] * 0.012
        return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)


class VideoWriter:
    def __init__(self, path):
        self.p = subprocess.Popen([
            "ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)

    def write(self, rgb8):
        self.p.stdin.write(rgb8.tobytes())

    def close(self):
        self.p.stdin.close()
        self.p.wait()


def mux(video, audio, out):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", audio,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", out], check=True)


# ----------------------------------------------------------------------------
# Stick-figure character
# ----------------------------------------------------------------------------
L_THIGH, L_SHIN = 0.80, 0.80
L_TORSO = 0.92
L_UARM, L_FARM = 0.58, 0.54
HEAD_R = 0.29


def ik(a, b, l1, l2, forward=1.0):
    """Two-bone IK: joint between a and b, bending towards +x*forward."""
    d = b - a
    dist = float(np.hypot(*d))
    dist = min(max(dist, 1e-4), l1 + l2 - 1e-4)
    u = d / max(float(np.hypot(*d)), 1e-4)
    x = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist)
    h = math.sqrt(max(l1 * l1 - x * x, 0))
    n = np.array([-u[1], u[0]])
    if n[0] * forward < 0:
        n = -n
    return a + u * x + n * h


def dirv(theta):
    """Unit vector at angle theta from vertical-up, positive = forward (+x)."""
    return np.array([math.sin(theta), math.cos(theta)])


def build_pose(hip, foot1, foot2, lean, arm1, arm2, bend1, bend2, head_tilt=0.0):
    """Returns joint dict. arm angles are measured from straight down, + = forward."""
    j = {"hip": hip, "foot1": foot1, "foot2": foot2}
    j["knee1"] = ik(hip, foot1, L_THIGH, L_SHIN, 1)
    j["knee2"] = ik(hip, foot2, L_THIGH, L_SHIN, 1)
    j["neck"] = hip + dirv(lean) * L_TORSO
    j["head"] = j["neck"] + dirv(lean + head_tilt) * (HEAD_R + 0.07)
    sh = hip + dirv(lean) * (L_TORSO * 0.86)
    j["shoulder"] = sh
    for i, (a, b) in enumerate(((arm1, bend1), (arm2, bend2)), 1):
        e = sh + np.array([math.sin(a), -math.cos(a)]) * L_UARM
        h = e + np.array([math.sin(a + b), -math.cos(a + b)]) * L_FARM
        j[f"elbow{i}"], j[f"hand{i}"] = e, h
    return j


def blend_pose(a, b, w):
    return {k: a[k] * (1 - w) + b[k] * w for k in a}


def pose_points(j):
    """Points along the skeleton (for particle emission / bounding boxes)."""
    segs = [("hip", "knee1"), ("knee1", "foot1"), ("hip", "knee2"), ("knee2", "foot2"),
            ("hip", "neck"), ("shoulder", "elbow1"), ("elbow1", "hand1"),
            ("shoulder", "elbow2"), ("elbow2", "hand2")]
    return segs


def draw_figure(canvas, j, cam, color, alpha=1.0, back_alpha=0.55, thick=1.0, head_scale=1.0):
    s = cam.s
    lw = 0.19 * s * thick
    tw = 0.23 * s * thick
    P = lambda k: cam.pt(j[k])
    # back limbs (dimmer, for depth)
    pb = paint(color, alpha * back_alpha, lw)
    for a, b in (("hip", "knee2"), ("knee2", "foot2"), ("shoulder", "elbow2"), ("elbow2", "hand2")):
        canvas.drawLine(*P(a), *P(b), pb)
    pf = paint(color, alpha, lw)
    canvas.drawLine(*P("hip"), *P("neck"), paint(color, alpha, tw))
    for a, b in (("hip", "knee1"), ("knee1", "foot1"), ("shoulder", "elbow1"), ("elbow1", "hand1")):
        canvas.drawLine(*P(a), *P(b), pf)
    hx, hy = P("head")
    canvas.drawCircle(hx, hy, HEAD_R * s * head_scale, paint(color, alpha))


class Camera:
    """Maps world (y-up) to screen: world point (wx, wy) -> screen (sx, sy)."""

    def __init__(self):
        self.s, self.wx, self.wy, self.sx, self.sy = 100.0, 0.0, 0.0, W / 2, H / 2
        self.init = False

    def pt(self, p):
        return (self.sx + (p[0] - self.wx) * self.s, self.sy - (p[1] - self.wy) * self.s)

    def fit(self, pts, region, smax, k):
        pts = np.asarray(pts)
        x0, y0 = pts.min(0)
        x1, y1 = pts.max(0)
        rx0, ry0, rx1, ry1 = region
        s = min((rx1 - rx0) / max(x1 - x0, 1e-3), (ry1 - ry0) / max(y1 - y0, 1e-3), smax)
        tgt = (s, (x0 + x1) / 2, (y0 + y1) / 2, (rx0 + rx1) / 2, (ry0 + ry1) / 2)
        if not self.init:
            self.s, self.wx, self.wy, self.sx, self.sy = tgt
            self.init = True
            return
        ls = math.log(self.s) + (math.log(tgt[0]) - math.log(self.s)) * k
        self.s = math.exp(ls)
        self.wx += (tgt[1] - self.wx) * k
        self.wy += (tgt[2] - self.wy) * k
        self.sx += (tgt[3] - self.sx) * k
        self.sy += (tgt[4] - self.sy) * k


class Particles:
    def __init__(self, seed=7):
        self.rng = np.random.default_rng(seed)
        self.p = np.zeros((0, 8), np.float32)  # x y vx vy age life size seed

    def emit(self, pts, vel=(0.3, 0.9), spread=0.6, life=(1.2, 2.6), size=(0.03, 0.07)):
        n = len(pts)
        if n == 0:
            return
        r = self.rng
        v = np.stack([vel[0] + r.normal(0, spread, n), vel[1] + r.normal(0, spread, n)], 1)
        new = np.zeros((n, 8), np.float32)
        new[:, 0:2] = pts
        new[:, 2:4] = v
        new[:, 5] = r.uniform(*life, n)
        new[:, 6] = r.uniform(*size, n)
        new[:, 7] = r.uniform(0, 6.28, n)
        self.p = np.concatenate([self.p, new])

    def step(self, dt):
        if len(self.p) == 0:
            return
        p = self.p
        p[:, 4] += dt
        p[:, 3] += 0.35 * dt          # embers rise
        p[:, 2] *= (1 - 0.6 * dt)
        p[:, 3] *= (1 - 0.4 * dt)
        p[:, 0] += p[:, 2] * dt + np.sin(p[:, 4] * 3 + p[:, 7]) * 0.15 * dt
        p[:, 1] += p[:, 3] * dt
        self.p = p[p[:, 4] < p[:, 5]]

    def draw(self, canvas, cam, c0, c1):
        for x, y, vx, vy, age, life, size, sd in self.p:
            t = age / life
            col = mix(c0, c1, smoothstep(0.0, 0.22, t))
            a = (1 - t) ** 1.5 * (0.6 + 0.4 * math.sin(sd + age * 20))
            sx, sy = cam.pt((x, y))
            canvas.drawCircle(sx, sy, max(1.2, size * cam.s * (1 - 0.5 * t)), paint(col, a))


# ----------------------------------------------------------------------------
# Flat-ground running cycle + misc helpers (EP02+)
# ----------------------------------------------------------------------------
def run_pose(x, phase, inten, ground=0.0, lean_add=0.0, head_tilt=0.0):
    """Procedural run cycle on flat ground. inten 0 = standing, 1 = sprint."""
    feet, hs = [], []
    for i in range(2):
        ph = phase + i * math.pi
        th = 0.1 + 0.8 * inten * math.sin(ph)
        ka = 0.2 + inten * (1.4 * max(0.0, math.cos(ph)) + 0.4 * max(0.0, -math.sin(ph)))
        k = np.array([math.sin(th), -math.cos(th)]) * L_THIGH
        f = k + np.array([math.sin(th - ka), -math.cos(th - ka)]) * L_SHIN
        feet.append(f)
        hs.append(-f[1])
    hip = np.array([x, ground + max(hs) - 0.02])
    f1, f2 = hip + feet[0], hip + feet[1]
    lean = 0.1 + 0.25 * inten + lean_add
    a1 = 0.1 - 0.9 * inten * math.sin(phase + math.pi)
    a2 = 0.1 - 0.9 * inten * math.sin(phase)
    bend = 0.35 + 1.05 * inten
    return build_pose(hip, f1, f2, lean, a1, a2, bend, bend, head_tilt)


def rotate_pose(j, pivot, ang):
    c, s = math.cos(ang), math.sin(ang)
    R = np.array([[c, -s], [s, c]])
    return {k: pivot + R @ (v - pivot) for k, v in j.items()}


def fit_font(text, size, name, spacing, max_w):
    f = font(size, name)
    while spaced_width(text, f, spacing) > max_w and size > 10:
        size -= 2
        f = font(size, name)
    return f


def dashed(color, alpha, width, on, off, phase):
    p = paint(color, alpha, width)
    p.setPathEffect(skia.DashPathEffect.Make([on, off], phase))
    return p
