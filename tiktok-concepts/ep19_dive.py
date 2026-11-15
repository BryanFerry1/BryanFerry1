"""EP19 - DIVE!  (inspired by the user's reference; all images redrawn in our DA)

Sunset pier (red sky), "DIVE!". MOTIVATION, TALENT, EGO, OBSESSION jump.
Camera zooms on each character in turn:
  MOTIVATION turns around and swims back up (OUT).
  TALENT finds a glowing red coin and floats with it (OUT).
  OBSESSION: doubt tags pop (I CAN'T / NO AIR LEFT / NOT BUILT FOR THIS), he turns red.
Pop cards: our own close-up of a diver's mask "HOLD ON..." -> dictionary
"obstinate" -> ONE / MORE / METER -> a tiny diver going down a trench.
EGO finds a treasure chest and lies on it. OBSESSION dives into the dark.
Pull back: everyone else is back on the pier. "THEY ALL WENT BACK UP. / HE KEPT GOING DOWN."
At the bottom a giant shell opens: the pearl, light rays. "THE PEARL IS EARNED."
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import (FPS, H, RED, WHITE, W, Camera, Particles, build_pose, clamp, draw_spaced, ease_out,
                    font, mix, paint, rotate_pose, smoothstep, spaced_width)
from kit import CX, GREY, Log, Video, blend, caption, draw_body, draw_heart, stand
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep19_dive"
dt = 1 / FPS
NAMES = ["MOTIVATION", "TALENT", "EGO", "OBSESSION"]
XS = {"MOTIVATION": -2.4, "TALENT": -0.8, "EGO": 0.8, "OBSESSION": 2.4}
PIER_Y = 0.6
PEARL = (2.4, -31.6)
M_PER_U = 4

JUMP = 1.6
CARDS = (10.2, 13.2)
CHEST_T = 13.6
PULL = (17.0, 19.3)
RAYS = 20.4
P_A, P_B, P_C = 17.6, 18.3, 21.0
DUR = 24.0
DOUBTS = [(7.9, "I CAN'T", -1), (8.5, "NO AIR LEFT", 1), (9.1, "NOT BUILT FOR THIS", -1)]

SERIF = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf")
SERIF_BI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf")
SERIF_I = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf")
MONO = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf")


def tf(size, face):
    f = skia.Font(face, size)
    f.setSubpixel(True)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


def keys(t, kf):
    if t <= kf[0][0]:
        return kf[0][1]
    for (t0, v0), (t1, v1) in zip(kf, kf[1:]):
        if t <= t1:
            u = (t - t0) / (t1 - t0)
            return v0 + (v1 - v0) * u * u * (3 - 2 * u)
    return kf[-1][1]


DEPTH = {   # hip world y (negative = under water)
    "MOTIVATION": [(0, 2.1), (JUMP, 2.1), (JUMP + 0.5, -1.0), (3.8, -4.0), (6.0, 0.2), (99, 0.2)],
    "TALENT": [(0, 2.1), (JUMP, 2.1), (JUMP + 0.5, -1.0), (4.6, -6.0), (14.5, -6.2), (16.5, 0.2), (99, 0.2)],
    "EGO": [(0, 2.1), (JUMP, 2.1), (JUMP + 0.5, -1.0), (7.4, -9.0), (CHEST_T, -13.0), (15.0, -13.0), (17.0, 0.2), (99, 0.2)],
    "OBSESSION": [(0, 2.1), (JUMP, 2.1), (JUMP + 0.5, -1.0), (7.4, -10.0), (CARDS[1], -10.8), (19.8, -30.4), (99, -30.4)],
}


def depth_y(n, t):
    return keys(t, DEPTH[n])


def upright_dive(t, kick=1.0, ph=0.0):
    k = math.sin(t * 9 + ph) * kick
    return build_pose(np.array([0.0, 1.5]), np.array([0.14 + 0.18 * k, 0.05 + 0.1 * abs(k)]),
                      np.array([-0.14 - 0.18 * k, 0.05 + 0.1 * abs(k)]), 0.0,
                      math.pi - 0.12, math.pi + 0.12, 0.0, 0.0, 0.0)


def diver(n, t):
    """Joints + 'state' for each character."""
    x = XS[n]
    y = depth_y(n, t)
    ph = NAMES.index(n) * 1.3
    if t < JUMP:
        j = stand(0, 0.0, 0.2, 0.15, 0.2, 0.2, 0.0)
        j = {k: v + [x, PIER_Y - 0.02] for k, v in j.items()}
        return j, "pier"
    if n in ("MOTIVATION", "TALENT", "EGO") and y > -0.05 and t > 5:
        j = stand(0, 0.05, 0.25, 0.2, 0.3, 0.3, 0.2)
        return {k: v + [x, PIER_Y - 0.02] for k, v in j.items()}, "pier"
    rot = math.pi * smoothstep(JUMP, JUMP + 0.45, t)
    up = (n == "MOTIVATION" and 3.8 <= t) or (n == "TALENT" and t >= 14.5) or (n == "EGO" and t >= 15.0)
    if up:
        rot = math.pi * (1 - smoothstep(3.8 if n == "MOTIVATION" else (14.5 if n == "TALENT" else 15.0),
                                        (4.3 if n == "MOTIVATION" else (15.0 if n == "TALENT" else 15.5)), t))
    base = upright_dive(t, 1.0, ph)
    if n == "TALENT" and 4.6 <= t < 14.5:
        base = build_pose(np.array([0.0, 1.5]), np.array([0.25, 0.1]), np.array([-0.2, 0.15]), 0.25,
                          1.35, 1.2, 1.0, 1.1, 0.5)
        rot = 0.25 + 0.05 * math.sin(t * 1.5)
    if n == "EGO" and CHEST_T <= t < 15.0:
        w = smoothstep(CHEST_T, CHEST_T + 0.5, t)
        rot = math.pi * (1 - w) + (math.pi / 2 + 0.15) * w
        base = blend(base, build_pose(np.array([0.0, 1.5]), np.array([0.5, 0.4]), np.array([0.3, 0.2]), 0.0,
                                      2.6, 2.7, 1.6, 1.7, -0.2), w)
    j = rotate_pose(base, np.array([0.0, 1.5]), rot)
    j = {k: v + [x, y - 1.5] for k, v in j.items()}
    return j, "water"


def draw_mask(c, cam, j, col, alpha):
    hx, hy = cam.pt(j["head"])
    r = 0.29 * cam.s
    rr = skia.Rect(hx - r * 0.85, hy - r * 0.35, hx + r * 0.85, hy + r * 0.35)
    c.drawRoundRect(rr, r * 0.25, r * 0.25, paint((0, 0, 0), alpha))
    c.drawRoundRect(rr, r * 0.25, r * 0.25, paint(col, alpha, max(2, r * 0.12)))
    c.drawLine(hx, hy - r * 0.35, hx, hy + r * 0.35, paint(col, alpha, max(1.5, r * 0.08)))


def fins(c, cam, j, col, alpha):
    for k in ("foot1", "foot2"):
        fx, fy = cam.pt(j[k])
        kx, ky = cam.pt(j["knee1" if k == "foot1" else "knee2"])
        d = np.array([fx - kx, fy - ky])
        d = d / (np.hypot(*d) + 1e-6)
        n = np.array([-d[1], d[0]])
        L = 0.38 * cam.s
        p = skia.Path()
        p.moveTo(fx, fy)
        p.lineTo(fx + d[0] * L + n[0] * L * 0.4, fy + d[1] * L + n[1] * L * 0.4)
        p.lineTo(fx + d[0] * L - n[0] * L * 0.4, fy + d[1] * L - n[1] * L * 0.4)
        p.close()
        c.drawPath(p, paint(col, alpha))


def background(e, f_, cam, t):
    sy0 = cam.pt((0, 0))[1]
    sy_deep = cam.pt((0, -32))[1]
    # sky (red sunset band) above the surface
    if sy0 > 0:
        sk = skia.Paint(AntiAlias=True)
        sk.setShader(skia.GradientShader.MakeLinear([skia.Point(0, sy0 - 900), skia.Point(0, sy0)],
                                                    [skia.Color4f(0, 0, 0, 1), skia.Color4f(0.2, 0.025, 0.03, 1)]))
        e.drawRect(skia.Rect(0, 0, W, sy0), sk)
        sx, _ = cam.pt((3.6, 0))
        e.drawCircle(sx, sy0, 0.9 * cam.s, paint(RED, 0.6))
    # water
    wp = skia.Paint(AntiAlias=True)
    wp.setShader(skia.GradientShader.MakeLinear([skia.Point(0, sy0), skia.Point(0, sy_deep)],
                                                [skia.Color4f(0.09, 0.095, 0.11, 1), skia.Color4f(0.0, 0.0, 0.0, 1)]))
    e.drawRect(skia.Rect(0, max(0, sy0), W, H), wp)
    # surface + light rays
    e.drawLine(0, sy0, W, sy0, paint(WHITE, 0.55, 3))
    for k in range(6):
        x0 = -4.5 + 1.8 * k + 0.3 * math.sin(t * 0.4 + k)
        p = skia.Path()
        p.moveTo(*cam.pt((x0, 0)))
        p.lineTo(*cam.pt((x0 + 0.5, 0)))
        p.lineTo(*cam.pt((x0 + 3.5, -18)))
        p.lineTo(*cam.pt((x0 + 2.2, -18)))
        p.close()
        e.drawPath(p, paint(WHITE, 0.025))
    # pier
    l, top = cam.pt((-3.4, PIER_Y))
    r, _ = cam.pt((3.4, PIER_Y))
    e.drawRect(skia.Rect(l, top - 0.12 * cam.s, r, top), paint(WHITE, 0.6))
    for px in (-3.1, -1.6, 0.0, 1.6, 3.1):
        e.drawLine(*cam.pt((px, PIER_Y)), *cam.pt((px, -1.4)), paint(WHITE, 0.45, max(2, 0.1 * cam.s)))
    # seaweed + shell at the bottom
    for k in range(9):
        x = -3.5 + 0.9 * k
        p = skia.Path()
        p.moveTo(*cam.pt((x, -32.4)))
        for s_ in range(1, 7):
            p.lineTo(*cam.pt((x + 0.15 * math.sin(t * 1.5 + s_ + k), -32.4 + 0.45 * s_)))
        e.drawPath(p, paint(WHITE, 0.18, max(1.5, 0.04 * cam.s)))
    e.drawLine(*cam.pt((-5, -32.4)), *cam.pt((5, -32.4)), paint(WHITE, 0.3, 2))


def draw_shell(c, cam, t, open_):
    px, py = PEARL
    cx, cy = cam.pt((px, py - 0.55))
    w, h = 1.6 * cam.s, 0.55 * cam.s
    c.drawOval(skia.Rect(cx - w / 2, cy - h * 0.3, cx + w / 2, cy + h * 0.7), paint((0, 0, 0), 1.0))
    c.drawOval(skia.Rect(cx - w / 2, cy - h * 0.3, cx + w / 2, cy + h * 0.7), paint(WHITE, 0.7, 3))
    c.save()
    c.translate(cx + w / 2, cy)
    c.rotate(-35 * open_)
    c.drawOval(skia.Rect(-w, -h * 0.6, 0, h * 0.3), paint((0, 0, 0), 1.0))
    c.drawOval(skia.Rect(-w, -h * 0.6, 0, h * 0.3), paint(WHITE, 0.7, 3))
    c.restore()
    if open_ > 0.05:
        pr = 0.28 * cam.s * (0.8 + 0.2 * open_)
        c.drawCircle(cx, cy, pr * 3.5, paint(WHITE, 0.07 * open_))
        c.drawCircle(cx, cy, pr, paint(WHITE, open_))


def tag(c, x, y, text, alpha, size=30):
    f = tf(size, MONO)
    w = spaced_width(text, f, 1) + 32
    x = min(max(x, 80 + w / 2), 880 - w / 2)
    r = skia.Rect(x - w / 2, y - size - 10, x + w / 2, y + 12)
    c.drawRect(r, paint((0, 0, 0), 0.92 * alpha))
    c.drawRect(r, paint(WHITE, alpha, 3, cap=False))
    draw_spaced(c, text, x, y, f, 1, paint(WHITE, alpha))


# ------------------------------------------------------------------ pop cards (all our own drawings)
CARD = (130, 560, 810, 1260)


def card_face(c, w, h, u, t):
    """Close-up of a diver behind his mask, ink style, 'HOLD ON...'."""
    z = 1 + 0.08 * u
    c.save()
    c.translate(w * 0.58, h * 0.62)
    c.scale(z, z)
    R = 260
    c.drawCircle(0, 0, R, paint((0.13, 0.13, 0.14), 1.0))
    c.drawCircle(0, 0, R, paint(WHITE, 0.85, 4))
    # mask
    m = skia.Rect(-R * 0.95, -R * 0.55, R * 0.95, R * 0.25)
    c.drawRoundRect(m, 40, 40, paint((0, 0, 0), 1.0))
    c.drawRoundRect(m, 40, 40, paint(WHITE, 1.0, 10))
    c.drawLine(0, -R * 0.55, 0, R * 0.25, paint(WHITE, 1.0, 10))
    for sgn in (-1, 1):
        ex, ey = sgn * R * 0.45, -R * 0.15
        c.drawOval(skia.Rect(ex - 70, ey - 34, ex + 70, ey + 34), paint(WHITE, 0.92))
        c.drawCircle(ex + 10, ey, 24, paint(RED, 1.0))
        c.drawCircle(ex + 10, ey, 10, paint((0, 0, 0), 1.0))
        c.drawLine(ex - 80, ey - 62, ex + 70, ey - 40 - 18 * sgn * 0, paint(WHITE, 1.0, 12))   # angry brow
    # reflections on the glass
    for sgn in (-1, 1):
        c.drawLine(sgn * R * 0.45 - 40, -R * 0.45, sgn * R * 0.45 - 10, -R * 0.5, paint(WHITE, 0.6, 5))
    # gritted mouth
    c.drawLine(-80, R * 0.55, 80, R * 0.5, paint(WHITE, 0.9, 8))
    # ink hatching
    for k in range(18):
        a = 2.2 + k * 0.09
        c.drawLine(math.cos(a) * R * 0.75, math.sin(a) * R * 0.75, math.cos(a) * R * 0.98, math.sin(a) * R * 0.98, paint(WHITE, 0.35, 3))
    c.restore()
    # bubbles
    r = np.random.default_rng(3)
    for k in range(16):
        bx = w * 0.15 + r.uniform(0, w * 0.75)
        by = h - ((t * 260 + r.uniform(0, h)) % h)
        c.drawCircle(bx, by, r.uniform(5, 16), paint(WHITE, 0.7, 3))
    c.drawString("HOLD", 34, 120, tf(92, SERIF_BI), paint(WHITE, 1.0))
    c.drawString("ON...", 34, 205, tf(92, SERIF_BI), paint(WHITE, 1.0))


def card_dict(c, w, h, u):
    z = 1 + 0.1 * u + 1.4 * smoothstep(0.75, 1.0, u) ** 2
    c.save()
    c.translate(170, 230)
    c.scale(z, z)
    c.translate(-170, -230)
    c.drawString("obstinate", 46, 230, tf(84, SERIF), paint(WHITE, 1.0))
    c.drawString("[ˈɒbstɪnət]  adjective • English", 48, 275, tf(26, SERIF_I), paint(WHITE, 0.75))
    c.drawLine(48, 305, 330, 305, paint(WHITE, 0.6, 2))
    for k, ln in enumerate(["refusing to come back up", "when everything says stop.", "",
                            "what separates the dreamers", "from the legends."]):
        c.drawString(ln, 48, 360 + 40 * k, tf(28, SERIF), paint(WHITE, 0.88))
    c.restore()


def card_word(c, w, h, word, u):
    z = 1.25 - 0.25 * ease_out(u)
    c.save()
    c.translate(w / 2, h / 2)
    c.scale(z, z)
    draw_spaced(c, word, 0, 50, tf(170, SERIF_BI), 2, paint(WHITE, 1.0))
    c.restore()


def card_trench(c, w, h, u, t):
    draw_spaced(c, "ONE MORE METER", w / 2, 80, tf(48, SERIF), 2, paint(WHITE, 1.0))
    for sgn in (-1, 1):
        for k in range(14):
            y0 = 120 + 40 * k
            x0 = w / 2 + sgn * (w * 0.48 - k * 18)
            c.drawLine(x0, y0, x0 - sgn * 30, y0 + 40, paint(WHITE, 0.35, 3))
    c.drawCircle(w / 2, h - 90, 60, paint(WHITE, 0.12))
    c.drawCircle(w / 2, h - 90, 18, paint(WHITE, 0.9))
    yy = 170 + (h - 330) * u
    cam = Camera()
    cam.s, cam.sx, cam.sy, cam.wx, cam.wy = 34, w / 2, yy, 0.0, 0.0
    j = rotate_pose(upright_dive(t), np.array([0.0, 1.5]), math.pi)
    draw_body(c, j, cam, RED, 1.0)


def draw_cards(oc, t):
    u0 = t - CARDS[0]
    x0, y0, x1, y1 = CARD
    w, h = x1 - x0, y1 - y0
    pop = 1 + 0.07 * (1 - ease_out(min(1, (u0 % 10) / 0.15)))
    oc.save()
    oc.translate((x0 + x1) / 2, (y0 + y1) / 2)
    oc.scale(pop, pop)
    oc.translate(-w / 2, -h / 2)
    rect = skia.Rect(0, 0, w, h)
    oc.drawRoundRect(rect, 18, 18, paint((0, 0, 0), 0.97))
    oc.drawRoundRect(rect, 18, 18, paint(WHITE, 0.85, 3))
    oc.save()
    oc.clipRect(rect)
    segs = [(0.0, 0.85, "face"), (0.85, 1.6, "dict"), (1.6, 1.87, "ONE"), (1.87, 2.14, "MORE"), (2.14, 2.41, "METER"),
            (2.41, 3.0, "trench")]
    for a, b, kind in segs:
        if a <= u0 < b:
            u = (u0 - a) / (b - a)
            if kind == "face":
                card_face(oc, w, h, u, t)
            elif kind == "dict":
                card_dict(oc, w, h, u)
            elif kind == "trench":
                card_trench(oc, w, h, u, t)
            else:
                card_word(oc, w, h, kind, u)
            if u0 - a < 0.06 and a > 0:
                oc.drawRect(rect, paint(WHITE, 0.5 * (1 - (u0 - a) / 0.06)))
    oc.restore()
    oc.restore()


# ------------------------------------------------------------------ camera shots
def target(t):
    """(wx, wy, scale) for the camera."""
    dy = {n: depth_y(n, t) for n in NAMES}
    if t < JUMP + 0.3:
        return 0.3, 1.0, 105
    if t < 2.2:
        return 0.3, (dy["OBSESSION"] + dy["EGO"]) / 2 - 1.0, 105
    shots = [(2.2, "TALENT", 175), (3.0, "EGO", 175), (3.8, "MOTIVATION", 170), (4.6, "TALENT", 170),
             (6.2, None, 105), (7.4, "OBSESSION", 165), (CARDS[0], "OBSESSION", 150), (CARDS[1], None, 105),
             (14.4, "OBSESSION", 135), (PULL[0], "PULL", 0), (PULL[1], "OBSESSION", 175)]
    cur = shots[0]
    for s in shots:
        if t >= s[0]:
            cur = s
    t0, who, s = cur
    if who == "PULL":
        s_full = (1560 - 420) / (PIER_Y + 2.0 + 32.0)
        return 0.4, (PIER_Y + 2.0 - 32.0) / 2, s_full
    if who is None:
        if t < CARDS[1] + 0.01:
            return 1.6, (dy["EGO"] + dy["OBSESSION"]) / 2 - 1.0, s
        return 1.6, (dy["EGO"] + dy["OBSESSION"]) / 2 - 1.0, s
    y = dy[who] - 0.4
    if who == "OBSESSION" and t >= PULL[1]:
        y = PEARL[1] + 1.4
    return XS[who], y, s


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    bubbles = Particles(4)
    sparks = Particles(7)
    rng = np.random.default_rng(1)
    cam = Camera()
    cam.sx, cam.sy = CX, 1000.0
    cam.wx, cam.wy, cam.s = target(0.0)
    for fi in range(v.n):
        t = fi * dt
        # ---------- events
        for key, tt, kind in (("dive", 0.05, "dive"), ("jump", JUMP, "jump"), ("splash", JUMP + 0.45, "splash"),
                              ("mot", 3.8, "turn"), ("coin", 4.6, "coin"), ("cards", CARDS[0], "cards"),
                              ("back", CARDS[1], "back"), ("chest", CHEST_T, "chest"), ("pull", PULL[0], "pull"),
                              ("pA", P_A, "pA"), ("pB", P_B, "pB"), ("open", 19.9, "open"), ("rays", RAYS, "rays"),
                              ("pC", P_C, "pC")):
            if t >= tt:
                log.once(key, tt, kind)
        for k, (tt, s_, side) in enumerate(DOUBTS):
            if t >= tt:
                log.once(f"doubt{k}", tt, "doubt", k)
        for name, tt in (("cut1", 2.2), ("cut2", 3.0), ("cut3", 3.8), ("cut4", 4.6), ("cut5", 6.2), ("cut6", 7.4),
                         ("cut7", 14.4), ("cut8", PULL[1])):
            if t >= tt:
                log.once(name, tt, "cut")
        # bubbles from divers
        if t > JUMP + 0.4:
            for n in NAMES:
                j, st = diver(n, t)
                if st == "water" and rng.random() < (0.5 if n == "OBSESSION" else 0.25):
                    bubbles.emit(np.array([j["head"] + rng.normal(0, 0.1, 2)]), vel=(0, 1.6), spread=0.3,
                                 life=(0.8, 1.6), size=(0.03, 0.07))
        if t >= RAYS and t < RAYS + 0.05:
            sparks.emit(np.tile(np.array([PEARL[0], PEARL[1] - 0.5]), (60, 1)), vel=(0, 1.5), spread=2.2,
                        life=(0.8, 1.8), size=(0.03, 0.07))
        bubbles.step(dt)
        sparks.step(dt)
        # ---------- camera
        wx, wy, s = target(t)
        snap = any(abs(t - c) < dt * 0.6 for c in (JUMP + 0.3, 2.2, 3.0, 3.8, 4.6, 6.2, 7.4, 14.4))
        k = 0.22 if not snap else 0.55
        if PULL[0] <= t < PULL[1]:
            k = 0.08
        cam.wx += (wx - cam.wx) * k
        cam.wy += (wy - cam.wy) * k
        cam.s = math.exp(math.log(cam.s) + (math.log(s) - math.log(cam.s)) * k)
        if not v.wants(fi):
            continue
        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        background(e, f_, cam, t)
        draw_shell(f_, cam, t, smoothstep(19.9, 20.5, t))
        # coin + chest
        cx_, cy_ = cam.pt((XS["TALENT"] + 0.35, -6.2 + 0.2))
        if t >= 4.3:
            gl = 0.6 + 0.4 * math.sin(t * 5)
            f_.drawCircle(cx_, cy_, 0.5 * cam.s, paint(RED, 0.12 * gl))
            if t < 14.5:
                f_.drawCircle(cx_, cy_, 0.13 * cam.s, paint(RED, 1.0))
        chx, chy = cam.pt((XS["EGO"] + 0.2, -14.55))
        cw, chh = 1.3 * cam.s, 0.75 * cam.s
        f_.drawRect(skia.Rect(chx - cw / 2, chy - chh, chx + cw / 2, chy), paint((0, 0, 0), 1.0))
        f_.drawRect(skia.Rect(chx - cw / 2, chy - chh, chx + cw / 2, chy), paint(WHITE, 0.75, 3, cap=False))
        f_.drawLine(chx - cw / 2, chy - chh * 0.55, chx + cw / 2, chy - chh * 0.55, paint(WHITE, 0.6, 3))
        pr = np.random.default_rng(9)
        for kk in range(26):
            gx = chx + pr.uniform(-cw * 0.45, cw * 0.45)
            gy = chy - chh - abs(pr.normal(0, 0.18)) * cam.s * (1 - abs(gx - chx) / cw)
            f_.drawCircle(gx, gy, 0.07 * cam.s, paint(RED, 0.95))
        bubbles.draw(f_, cam, WHITE, WHITE)
        sparks.draw(f_, cam, WHITE, RED)
        # divers
        for n in NAMES:
            j, st = diver(n, t)
            col = WHITE
            if n == "OBSESSION":
                col = mix(WHITE, RED, smoothstep(9.3, 9.9, t))
            out = (n == "MOTIVATION" and t >= 3.8) or (n == "TALENT" and t >= 4.6) or (n == "EGO" and t >= CHEST_T)
            a = 1.0
            if out and st == "pier":
                col = GREY
            draw_body(hc, j, cam, col, a, 0.25 if n == "OBSESSION" and t > CARDS[1] else 0.0)
            if st == "water":
                draw_mask(hc, cam, j, col, a)
                fins(hc, cam, j, col, a)
            # labels
            if t < PULL[0] - 0.2 or st == "pier":
                hx, hy = cam.pt(j["head"])
                fs = min(40, max(18, 22 * cam.s / 105))
                below = st == "water" and j["head"][1] < j["hip"][1]
                ly = hy + (0.75 * cam.s if below else -0.55 * cam.s)
                draw_spaced(tc, n, hx, ly, tf(fs, MONO), 2, paint(RED if n == "OBSESSION" else WHITE, 0.95))
                if out and t < PULL[0] - 0.2:
                    po = 1 + 0.5 * math.exp(-(t - (3.8 if n == "MOTIVATION" else 4.6 if n == "TALENT" else CHEST_T)) * 8)
                    draw_spaced(tc, "OUT", hx, ly - fs * 1.3, tf(fs * po, MONO), 2, paint(RED, 0.95))
            if n == "EGO" and t >= CHEST_T + 0.4 and t < 15.0:
                hx, hy = cam.pt(j["head"] + [0.2, 0.6])
                draw_heart(f_, hx, hy, 16 * (1 + 0.5 * math.exp(-(t - CHEST_T - 0.4) * 8)), 0.95)
        # doubts
        if 7.4 <= t < CARDS[0]:
            j, _ = diver("OBSESSION", t)
            hx, hy = cam.pt(j["hip"])
            for k, (tt, s_, side) in enumerate(DOUBTS):
                if t >= tt:
                    pop = 1 + 0.25 * math.exp(-(t - tt) * 10)
                    tag(oc, hx + side * 200, hy - 300 + 110 * k, s_, 1.0, int(36 * pop))
        # cards
        if CARDS[0] <= t < CARDS[1]:
            draw_cards(oc, t)
        # end texts
        if P_A <= t < PULL[1] + 0.3:
            caption(oc, "THEY ALL WENT BACK UP.", 470, smoothstep(P_A, P_A + 0.3, t) * (1 - smoothstep(PULL[1], PULL[1] + 0.3, t)), WHITE, 44)
        if P_B <= t < PULL[1] + 0.3:
            caption(oc, "HE KEPT GOING DOWN.", 545, smoothstep(P_B, P_B + 0.3, t) * (1 - smoothstep(PULL[1], PULL[1] + 0.3, t)), RED, 44)
        if t >= RAYS:
            ra = smoothstep(RAYS, RAYS + 0.3, t)
            px, py = cam.pt((PEARL[0], PEARL[1] - 0.55))
            for k in range(14):
                a = -math.pi / 2 + (k - 6.5) * 0.17 + 0.02 * math.sin(t + k)
                p = skia.Path()
                p.moveTo(px, py)
                p.lineTo(px + math.cos(a - 0.03) * 1400, py + math.sin(a - 0.03) * 1400)
                p.lineTo(px + math.cos(a + 0.03) * 1400, py + math.sin(a + 0.03) * 1400)
                p.close()
                f_.drawPath(p, paint(WHITE, 0.07 * ra))
        if t >= P_C:
            caption(oc, "THE PEARL IS EARNED.", 1480, smoothstep(P_C, P_C + 0.4, t), RED, 50)
        # HUD (depth of obsession)
        if JUMP + 0.3 < t < P_C:
            d = int(round(-min(0.0, depth_y("OBSESSION", t)) * M_PER_U))
            a = smoothstep(JUMP + 0.3, JUMP + 0.6, t) * (1 - smoothstep(PULL[0] - 0.2, PULL[0], t) if t < PULL[1] else 1)
            if not (CARDS[0] <= t < CARDS[1]) and not (PULL[0] <= t < PULL[1]):
                draw_spaced(oc, "DEPTH", CX, 350, tf(24, MONO), 6, paint(WHITE, 0.7 * a))
                draw_spaced(oc, f"{d}M", CX, 430, tf(66, MONO), 2, paint(RED if t > CARDS[1] else WHITE, a))
        if t < JUMP + 0.2:
            a = smoothstep(0.0, 0.15, t) * (1 - smoothstep(JUMP, JUMP + 0.2, t))
            draw_spaced(oc, "DIVE!", CX, 520, tf(120 * (1 + 0.12 * math.exp(-t * 8)), MONO), 10, paint(WHITE, a))
        flash = math.exp(-(t - RAYS) * 2.5) * 1.2 if t >= RAYS else 0.0
        dim = 0.65 if CARDS[0] <= t < CARDS[1] else 0.0
        cut_white = 0.0
        for c_ in (2.2, 3.0, 3.8, 4.6, 6.2, 7.4, 14.4, PULL[1]):
            if c_ <= t < c_ + 0.07:
                cut_white = 0.18 * (1 - (t - c_) / 0.07)
        v.compose(fi, t, flash=flash, glow=0.3, dim=dim, white=cut_white)
    v.finish(build_audio, log.events)


def splash():
    d = 1.4
    tt = sfx.t_axis(d)
    return (sfx.bandnoise(d, 300, 9000, 2) * np.exp(-tt * 4) * 0.8 + np.sin(2 * np.pi * 60 * tt) * np.exp(-tt * 8) * 0.5)


def bubble_pop(seed):
    d = 0.08
    tt = sfx.t_axis(d)
    f0 = np.random.default_rng(seed).uniform(500, 1400)
    return np.sin(2 * np.pi * np.cumsum(f0 * (1 + 3 * tt / d)) / sfx.SR) * np.exp(-tt * 50) * 0.4


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    bed = sfx.drone(DUR, rise_at=RAYS)
    lowpass_air = sfx.bandnoise(DUR, 60, 500, 8) * 0.25          # underwater rumble
    tt = np.arange(len(bed)) / sfx.SR
    under = np.clip((tt - JUMP - 0.4) / 0.4, 0, 1)
    m.add_bed(bed * (0.5 + 0.5 * under) + lowpass_air[:len(bed)] * under, gain=0.45, fade_in=0.4, fade_out=2.0, stop=DUR)
    r = np.random.default_rng(3)
    t_ = JUMP + 0.6
    while t_ < DUR - 1:
        m.add(t_, bubble_pop(int(t_ * 100)), 0.25, r.uniform(-0.6, 0.6), 0.4)
        t_ += r.uniform(0.12, 0.45)
    for t, kind, _, extra in events:
        if kind == "dive":
            m.add(t, sfx.text_hit(5), 0.8, 0, 0.4)
        elif kind == "jump":
            m.add(t, sfx.whoosh(0.5, 300, 7000, 0.7, seed=2), 0.6, 0, 0.3)
        elif kind == "splash":
            for k in range(4):
                m.add(t + 0.05 * k, splash(), 0.55, -0.6 + 0.4 * k, 0.3)
        elif kind == "cut":
            m.add(t, sfx.whoosh(0.25, 500, 8000, 0.4, seed=int(t * 10)), 0.35, 0, 0.2)
        elif kind == "turn":
            m.add(t, sfx.power_down(1.0), 0.4, -0.5, 0.4)
        elif kind == "coin":
            m.add(t, sfx.chime(990, 0.35), 0.6, -0.2, 0.6)
            m.add(t + 0.1, sfx.sparkle(0.8, 50, 3), 0.4, -0.2, 0.5)
        elif kind == "doubt":
            m.add(t, sfx.tick(900, 0.6), 0.6, 0.3, 0.2)
            m.add(t, sfx.punch_block(extra), 0.5, 0.3, 0.3)
            m.add(t + 0.1, sfx.heartbeat(), 0.6 + 0.1 * extra, 0, 0.3)
        elif kind == "cards":
            m.add(t, sfx.text_hit(2), 0.7, 0, 0.5)
            for k, tt2 in enumerate((0.85, 1.6, 1.87, 2.14, 2.41)):
                m.add(t + tt2, sfx.text_hit(k), 0.55 + 0.1 * (k in (2, 3, 4)), 0, 0.4)
            m.add(t + 1.6, sfx.boom(1.4), 0.5, 0, 0.5)
        elif kind == "back":
            m.add(t, sfx.power_up(70), 0.9, 0.3, 0.4)
        elif kind == "chest":
            for k in range(8):
                m.add(t + k * 0.05, sfx.chime(900 + 70 * k, 0.15), 0.4, 0.2, 0.5)
        elif kind == "pull":
            m.add(t, sfx.whoosh(2.0, 80, 2500, 0.6, seed=13), 0.5, 0, 0.4)
        elif kind in ("pA", "pB", "pC"):
            m.add(t, sfx.text_hit({"pA": 1, "pB": 3, "pC": 4}[kind]), 0.6 if kind != "pC" else 0.9, 0, 0.4)
        elif kind == "open":
            m.add(t, sfx.riser(0.5), 0.5, 0, 0.4)
        elif kind == "rays":
            m.add(t, sfx.boom(4.0), 1.0, 0, 0.6)
            m.add(t, sfx.sparkle(2.5, 120, 4), 0.8, 0, 0.6)
            for k, f in enumerate((660, 880, 1320)):
                m.add(t + 0.05 * k, sfx.chime(f, 0.3), 0.6, 0, 0.7)
    m.add(RAYS - 2.6, sfx.riser(2.6), 0.5, 0, 0.3)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [0.8, 2.0, 2.6, 3.4, 4.2, 5.4, 6.8, 9.5, 10.5, 11.3, 12.0, 12.8, 14.0, 15.5, 18.6, 20.0, 20.8, 22.5]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
