"""Reusable kit for the concept shorts (poses, bodies, props, title/punchline,
render loop). Episodes from EP09 on are built on top of this file.

Safe zone (TikTok UI): HUD at y 360/470, keep content in x 80..880 and
y 320..1560. CX is the horizontal centre of that zone.
"""
import math
import os
import subprocess

import numpy as np
import skia

from engine import (FPS, H, HEAD_R, L_FARM, L_SHIN, L_THIGH, L_UARM, RED, WHITE, W, Camera,
                    Layer, Post, VideoWriter, bloom, build_pose, clamp, dirv, draw_figure,
                    draw_runs, draw_spaced, ease_out, fit_font, font, ik, mix, mux, paint,
                    smoothstep)

GREY = (0.5, 0.5, 0.53)
CX = 470.0
dt = 1 / FPS


# ------------------------------------------------------------------ poses
def stand(x, lean=0.02, a1=0.12, a2=0.08, b1=0.15, b2=0.1, head=0.0, bob=0.0, hip_h=1.52):
    return build_pose(np.array([x, hip_h + bob]), np.array([x + 0.13, 0.02]), np.array([x - 0.13, 0.02]),
                      lean, a1, a2, b1, b2, head)


def flex(x, t=0.0):
    return stand(x, -0.02, 1.57, 1.42, 1.55, 1.65, -0.12, 0.01 * math.sin(t * 3))


def crossed(x):
    return stand(x, -0.04, 0.5, 0.45, 1.9, 1.95, -0.18)


def curl(x, c):
    a = 0.12 + 0.18 * c
    b = 0.15 + 2.3 * c
    return stand(x, 0.03 - 0.05 * c, a, a - 0.04, b, b - 0.05, 0.05)


def sad(x, t=0.0):
    return stand(x, 0.32, 0.04, 0.0, 0.12, 0.08, 0.9, 0.02 * math.sin(t * 2.2) - 0.04)


def arms_up(x, t=0.0):
    return stand(x, -0.05, 2.75, 2.95, 0.15, 0.1, -0.25, 0.01 * math.sin(t * 3))


def phone_pose(x, t=0.0):
    """Looking at a phone held at chest height."""
    return stand(x, 0.12, 0.9, 0.85, 1.4, 1.45, 0.55)


def clap(x, t):
    c = 0.5 + 0.5 * math.sin(t * 18)
    return stand(x, 0.0, 1.25, 1.2, 0.9 + 0.25 * c, 0.9 + 0.25 * c, 0.0)


def mirror(j, cx):
    return {k: np.array([2 * cx - v[0], v[1]]) for k, v in j.items()}


def shift(j, dx, dy=0.0):
    return {k: v + [dx, dy] for k, v in j.items()}


def scale_pose(j, x, sc):
    return {k: np.array([x + (v[0] - x) * sc, v[1] * sc]) for k, v in j.items()}


def blend(a, b, w):
    return {k: a[k] * (1 - w) + b[k] * w for k in a}


def kneel(x, t, head_down=0.6, reach=0.0):
    hip = np.array([x, 0.95 + 0.015 * math.sin(t * 5)])
    lean = 0.38 - 0.25 * reach
    neck = hip + dirv(lean) * 0.92
    sh = hip + dirv(lean) * 0.79
    k1 = np.array([x + 0.78, 0.83])
    j = {"hip": hip, "neck": neck, "head": neck + dirv(lean + head_down * (1 - reach) - 0.3 * reach) * 0.36,
         "shoulder": sh, "knee1": k1, "foot1": np.array([x + 0.82, 0.03]),
         "knee2": np.array([x - 0.12, 0.1]), "foot2": np.array([x - 0.88, 0.1]),
         "elbow1": sh + [0.32, -0.38], "hand1": k1 + [-0.02, 0.08],
         "elbow2": sh + [0.05, -0.52], "hand2": sh + [0.0, -1.02]}
    if reach > 0:
        j["elbow1"] = j["elbow1"] * (1 - reach) + (sh + [0.5, 0.25]) * reach
        j["hand1"] = j["hand1"] * (1 - reach) + (sh + [1.0, 0.55]) * reach
        j["elbow2"] = j["elbow2"] * (1 - reach) + (sh + [0.45, 0.1]) * reach
        j["hand2"] = j["hand2"] * (1 - reach) + (sh + [0.95, 0.35]) * reach
    return j


def sit(x, seat_y=0.75, t=0.0, slump=0.0):
    """Sitting on a seat (couch/bench), facing +x."""
    hip = np.array([x, seat_y + 0.12])
    lean = -0.15 + 0.6 * slump
    neck = hip + dirv(lean) * 0.92
    sh = hip + dirv(lean) * 0.79
    k = np.array([x + 0.75, seat_y + 0.2])
    f = np.array([x + 0.85, 0.03])
    j = {"hip": hip, "neck": neck, "head": neck + dirv(lean + 0.5 * slump) * 0.36, "shoulder": sh,
         "knee1": k, "foot1": f, "knee2": k + [-0.05, -0.02], "foot2": f + [-0.12, 0]}
    j["hand1"] = sh + np.array([0.55, -0.15])
    j["hand2"] = sh + np.array([0.5, -0.22])
    j["elbow1"] = ik(sh, j["hand1"], L_UARM, L_FARM, -1)
    j["elbow2"] = ik(sh, j["hand2"], L_UARM, L_FARM, -1)
    return j


def old_pose(x, t=0.0):
    """Hunched old man with a cane (cane drawn separately at hand1)."""
    return stand(x, 0.45, 0.6, 0.2, 0.3, 0.3, 0.5, 0.0, 1.38)


# ------------------------------------------------------------------ bodies
SEGS_M = [("hip", "knee2", 0.38, True), ("knee2", "foot2", 0.26, True),
          ("shoulder", "elbow2", 0.34, True), ("elbow2", "hand2", 0.22, True),
          ("hip", "neck", 0.52, False),
          ("hip", "knee1", 0.38, False), ("knee1", "foot1", 0.26, False),
          ("shoulder", "elbow1", 0.36, False), ("elbow1", "hand1", 0.24, False)]


def draw_body(c, j, cam, col, alpha, g=0.0, fat=0.0, head_scale=1.0):
    """Stick figure that fills out with muscle (g 0..1) and/or a belly (fat 0..1)."""
    s = cam.s
    for a, b, wx, back in SEGS_M:
        pa, pb = np.array(cam.pt(j[a])), np.array(cam.pt(j[b]))
        al = alpha * (0.55 if back else 1.0)
        base = (0.15 if (a, b) == ("hip", "neck") else 0.12) * s
        c.drawLine(*pa, *pb, paint(col, al, base))
        w = (0.04 + wx * g ** 0.9) * s
        if w > base * 1.05:
            d = pb - pa
            L = float(np.hypot(*d))
            mid = pa + d * (0.45 if b not in ("foot1", "foot2") else 0.35)
            c.save()
            c.translate(*mid)
            c.rotate(math.degrees(math.atan2(d[1], d[0])))
            r = skia.Rect(-L * 0.42, -w / 2, L * 0.42, w / 2)
            c.drawOval(r, paint(col, al))
            c.drawOval(r, paint((0, 0, 0), 1.0, max(2.0, 0.05 * s)))
            c.restore()
    if fat > 0.02:
        hip, neck = j["hip"], j["neck"]
        d = neck - hip
        fwd = np.array([d[1], -d[0]]) / (np.hypot(*d) + 1e-6)
        if j["foot1"][0] < hip[0] - 0.2 and j["head"][0] < hip[0]:
            fwd = -fwd
        ctr = hip + d * 0.35 + fwd * (0.08 + 0.2 * fat)
        c.drawCircle(*cam.pt(ctr), (0.12 + 0.36 * fat) * s, paint(col, alpha))
    sx, sy = cam.pt(j["shoulder"])
    c.drawCircle(sx, sy, (0.07 + 0.17 * g) * s, paint(col, alpha))
    if g > 0.1:
        c.drawCircle(sx, sy, (0.07 + 0.17 * g) * s, paint((0, 0, 0), 1.0, max(2.0, 0.05 * s)))
    nx, ny = cam.pt(j["neck"])
    c.drawLine(sx, sy, nx, ny, paint(col, alpha, (0.12 + 0.16 * g) * s))
    hx, hy = cam.pt(j["head"])
    c.drawCircle(hx, hy, HEAD_R * s * (1 - 0.08 * g) * head_scale, paint(col, alpha))


def body_scale(g):
    return 0.9 + 0.38 * g


# ------------------------------------------------------------------ props
def heart_path(cx, cy, r):
    p = skia.Path()
    p.moveTo(cx, cy + r)
    p.cubicTo(cx - r * 1.6, cy - r * 0.2, cx - r * 0.8, cy - r * 1.4, cx, cy - r * 0.55)
    p.cubicTo(cx + r * 0.8, cy - r * 1.4, cx + r * 1.6, cy - r * 0.2, cx, cy + r)
    p.close()
    return p


def draw_heart(c, cx, cy, r, alpha, col=RED):
    if alpha > 0.01:
        c.drawPath(heart_path(cx, cy, r), paint(col, alpha))


def draw_crown(c, cx, cy, w, alpha, col=RED):
    """Crown centred at (cx, cy) in screen px, width w."""
    if alpha < 0.01:
        return
    h = w * 0.62
    p = skia.Path()
    p.moveTo(cx - w / 2, cy + h / 2)
    p.lineTo(cx - w / 2, cy - h / 2)
    p.lineTo(cx - w / 4, cy)
    p.lineTo(cx, cy - h / 2 - h * 0.15)
    p.lineTo(cx + w / 4, cy)
    p.lineTo(cx + w / 2, cy - h / 2)
    p.lineTo(cx + w / 2, cy + h / 2)
    p.close()
    c.drawPath(p, paint(col, alpha))
    for k in (-0.5, 0.0, 0.5):
        c.drawCircle(cx + k * w, cy - h / 2 - (h * 0.15 if k == 0 else 0) - w * 0.06, w * 0.07, paint(col, alpha))


def draw_trophy(c, cx, cy, w, alpha, col=WHITE):
    """Cup trophy; (cx, cy) = bottom centre."""
    if alpha < 0.01:
        return
    h = w * 1.3
    c.drawRect(skia.Rect(cx - w * 0.35, cy - h * 0.12, cx + w * 0.35, cy), paint(col, alpha))
    c.drawLine(cx, cy - h * 0.12, cx, cy - h * 0.42, paint(col, alpha, w * 0.12))
    cup = skia.Path()
    cup.moveTo(cx - w * 0.5, cy - h)
    cup.lineTo(cx + w * 0.5, cy - h)
    cup.cubicTo(cx + w * 0.5, cy - h * 0.55, cx + w * 0.2, cy - h * 0.42, cx, cy - h * 0.42)
    cup.cubicTo(cx - w * 0.2, cy - h * 0.42, cx - w * 0.5, cy - h * 0.55, cx - w * 0.5, cy - h)
    cup.close()
    c.drawPath(cup, paint(col, alpha))
    for sgn in (-1, 1):
        c.drawCircle(cx + sgn * w * 0.55, cy - h * 0.82, w * 0.16, paint(col, alpha, w * 0.07))


def draw_car(c, cam, x, alpha, col=WHITE, scale=1.0):
    """Side-view sports car outline, rear at x, on the ground."""
    if alpha < 0.01:
        return
    s = scale
    pts = [(0, 0.35), (0.1, 0.8), (1.0, 0.95), (1.6, 1.45), (2.6, 1.45), (3.3, 0.95), (3.9, 0.85), (4.0, 0.35)]
    p = skia.Path()
    p.moveTo(*cam.pt((x + pts[0][0] * s, pts[0][1] * s)))
    for px, py in pts[1:]:
        p.lineTo(*cam.pt((x + px * s, py * s)))
    p.close()
    c.drawPath(p, paint(col, alpha, max(2, 0.06 * cam.s)))
    win = skia.Path()
    win.moveTo(*cam.pt((x + 1.25 * s, 1.0 * s)))
    win.lineTo(*cam.pt((x + 1.7 * s, 1.35 * s)))
    win.lineTo(*cam.pt((x + 2.5 * s, 1.35 * s)))
    win.lineTo(*cam.pt((x + 3.0 * s, 1.0 * s)))
    win.close()
    c.drawPath(win, paint(col, 0.6 * alpha, max(1.5, 0.04 * cam.s)))
    for wx in (0.85, 3.15):
        cx, cy = cam.pt((x + wx * s, 0.35 * s))
        c.drawCircle(cx, cy, 0.38 * s * cam.s, paint((0, 0, 0), 1.0))
        c.drawCircle(cx, cy, 0.38 * s * cam.s, paint(col, alpha, max(2, 0.07 * cam.s)))
        c.drawCircle(cx, cy, 0.12 * s * cam.s, paint(col, alpha))


def draw_phone_small(c, cam, pos, alpha, glow=True):
    sx, sy = cam.pt(pos)
    w, h = 0.2 * cam.s, 0.34 * cam.s
    r = skia.Rect(sx - w / 2, sy - h / 2, sx + w / 2, sy + h / 2)
    c.drawRoundRect(r, w * 0.2, w * 0.2, paint((0, 0, 0), 1.0))
    c.drawRoundRect(r, w * 0.2, w * 0.2, paint(WHITE, 0.95 * alpha, max(1.5, 0.03 * cam.s)))
    if glow:
        c.drawRoundRect(r, w * 0.2, w * 0.2, paint(WHITE, 0.35 * alpha))


def draw_cane(c, cam, j, alpha, col=GREY):
    h = j["hand1"]
    c.drawLine(*cam.pt(h), *cam.pt((h[0] + 0.1, 0.0)), paint(col, alpha, max(2, 0.06 * cam.s)))


class Shards:
    """Flying fragments (glass, wall, money...)."""

    def __init__(self, seed=1):
        self.f = []
        self.rng = np.random.default_rng(seed)

    def burst(self, x0, x1, y0, y1, n, vx=(-2, 2), vy=(0, 4), size=(0.07, 0.22), life=(0.9, 1.6)):
        r = self.rng
        for _ in range(n):
            self.f.append([r.uniform(x0, x1), r.uniform(y0, y1), r.uniform(*vx), r.uniform(*vy),
                           r.uniform(0, 6), r.uniform(-12, 12), r.uniform(*size), 0.0, r.uniform(*life)])

    def step(self, d, gravity=11.0):
        for p in self.f:
            p[3] -= gravity * d
            p[0] += p[2] * d
            p[1] += p[3] * d
            if p[1] < 0.05:
                p[1], p[3], p[2] = 0.05, -p[3] * 0.25, p[2] * 0.5
            p[4] += p[5] * d
            p[7] += d
        self.f = [p for p in self.f if p[7] < p[8]]

    def draw(self, c, cam, col, tri=True):
        for x, y, vx, vy, ang, av, size, age, life in self.f:
            a = (1 - age / life) ** 1.2
            cx, cy = cam.pt((x, y))
            hs = size * cam.s / 2
            path = skia.Path()
            n = 3 if tri else 4
            for k in range(n):
                th = ang + k * 2 * math.pi / n
                pt = (cx + math.cos(th) * hs * 1.3, cy + math.sin(th) * hs)
                (path.moveTo if k == 0 else path.lineTo)(*pt)
            path.close()
            c.drawPath(path, paint(col, a))


def lane_cam(s, sy, wx=0.0, sx=CX):
    c = Camera()
    c.s, c.sx, c.sy, c.wx, c.wy = s, sx, sy, wx, 0.0
    return c


# ------------------------------------------------------------------ text
def title(tc, t, lines, t0=0.1, t1=2.4, y0=560):
    """lines: list of (runs, size, gap) where runs = [(text, colour)] ; 'VS' lines small."""
    a = smoothstep(t0, t0 + 0.25, t) * (1 - smoothstep(t1, t1 + 0.4, t))
    if a < 0.01:
        return
    pop = 1 + 0.08 * (1 - ease_out((t - t0) / 0.4))
    y = y0
    for runs, size, gap in lines:
        txt = "".join(r[0] for r in runs)
        f = fit_font(txt, size * pop, "InterDisplay-Black" if size > 70 else "InterDisplay-Bold", 6, 780)
        draw_runs(tc, [(s, paint(col, a * (0.7 if size <= 70 else 1))) for s, col in runs], CX, y, f, 6)
        y += gap


def punch(tc, t, items):
    """items: list of (t0, runs, y, size) ; last one pops."""
    for k, (t0, runs, y, size) in enumerate(items):
        if t < t0:
            continue
        u = ease_out((t - t0) / 0.4)
        off = (1 - u) * 30
        big = k == len(items) - 1
        txt = "".join(r[0] for r in runs)
        sc = 1 + (0.3 * (1 - u) if big else 0)
        f = fit_font(txt, size * sc, "InterDisplay-Black" if size >= 70 else "InterDisplay-Bold", 4, 800)
        draw_runs(tc, [(s, paint(col, u * (1 if big or col == RED else 0.9))) for s, col in runs], CX, y + off * (0.3 if big else 1), f, 4)


def hud(tc, label, value, alpha, red=False):
    if alpha < 0.01:
        return
    draw_spaced(tc, label, CX, 360, font(24, "Inter-SemiBold"), 12, paint(WHITE, 0.7 * alpha))
    draw_spaced(tc, str(value), CX, 470, font(104, "InterDisplay-Bold"), 4, paint(RED if red else WHITE, alpha))


def label(tc, cam, x, text, alpha, col=WHITE, y_off=46, size=28):
    if alpha < 0.01:
        return
    sx, sy = cam.pt((x, 0))
    draw_spaced(tc, text, sx, sy + y_off, font(size, "Inter-Bold"), 6, paint(col, alpha))


# ------------------------------------------------------------------ render loop
class Video:
    def __init__(self, out_dir, name, dur, stills=None):
        self.out, self.name, self.dur = out_dir, name, dur
        self.n = int(dur * FPS)
        self.stills = stills
        os.makedirs(out_dir, exist_ok=True)
        self.env, self.fig, self.txt, self.hero = Layer(), Layer(), Layer(), Layer()
        self.over = Layer()   # opaque overlay (readable text boxes), composited last, no bloom
        self.post = Post()
        self.writer = None if stills else VideoWriter(os.path.join(out_dir, name + "_video.mp4"))

    def wants(self, fi):
        return self.stills is None or fi in self.stills

    def clear(self):
        for L in (self.env, self.fig, self.txt, self.hero, self.over):
            L.clear()

    def compose(self, fi, t, flash=0.0, glow=0.0, white=0.0, dim=0.0):
        master = smoothstep(0, 0.3, t) * (1 - smoothstep(self.dur - 0.35, self.dur, t))
        e = bloom(self.env.rgb(), (0.9, (4, 0.6), (22, 0.3)))
        g = bloom(self.fig.rgb(), (1.0, (5, 0.9), (18, 0.8 + 0.3 * glow), (60, 0.5 + 0.3 * glow + flash)))
        h = bloom(self.hero.rgb(), (1.0, (4, 0.45), (16, 0.35 + 0.2 * glow), (50, 0.25 + 0.2 * glow + flash * 0.6)))
        x = bloom(self.txt.rgb(), (1.0, (6, 0.7), (26, 0.45)))
        img = ((e + g + h) * (1 - dim) + x) * master + white
        ov = self.over.rgba()
        if ov[..., 3].max() > 0:
            a = ov[..., 3:4] * master
            img = img * (1 - a) + ov[..., :3] * master
        frame = self.post.apply(img, fi)
        if self.stills is not None:
            import PIL.Image
            PIL.Image.fromarray(frame).save(os.path.join(self.out, f"still_{fi:04d}.png"))
        else:
            self.writer.write(frame)
        if fi % 120 == 0:
            print(f"frame {fi}/{self.n}", flush=True)

    def finish(self, build_audio, events):
        if self.stills is not None:
            return
        self.writer.close()
        wav = os.path.join(self.out, self.name + "_sfx.wav")
        build_audio(events, wav)
        vid = os.path.join(self.out, self.name + "_video.mp4")
        mux(vid, wav, os.path.join(self.out, self.name + ".mp4"))
        os.remove(vid)
        os.remove(wav)
        print("done", os.path.join(self.out, self.name + ".mp4"))


class Log:
    def __init__(self):
        self.events, self.seen = [], set()

    def once(self, key, t, kind, extra=0):
        if key not in self.seen:
            self.seen.add(key)
            self.events.append((t, kind, 0, extra))

    def add(self, t, kind, extra=0):
        self.events.append((t, kind, 0, extra))
