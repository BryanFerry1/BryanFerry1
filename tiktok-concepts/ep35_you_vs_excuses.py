"""EP35 - YOU VS EXCUSES  (edit-friendly: big drop at 10.0 s)

  0.0  dark. A guy on his knees. Red chains snake out of the ground and grab
       his wrists, ankle and waist.
  2.2  he tries to stand: the chains snap tight and yank him back down.
       Each chain gets its name: TOMORROW / I'M TIRED / NO TIME / WHAT IF I FAIL?
  4.6  close: he crawls forward, reaching... YANK. Face down.
  6.6  on the ground. Heartbeat. A small light pulses in his chest.
  8.0  he pushes up, chains straining, sparks on every link. Stands.
  9.65 black. silence.
 10.0  DROP: the chains SNAP into red shards, aura, he launches into the sky,
       camera follows him up, hangs at the top, dives...
 12.8  superhero landing: shockwave, ground cracks, the anchors explode.
 14.8  he rises in his aura, hero shot.
 END   EXCUSES ONLY / HOLD YOU / IF YOU STOP PULLING.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import (FPS, H, RED, WHITE, W, Camera, Particles, clamp, draw_spaced, ease_out, font, paint,
                    rotate_pose, smoothstep)
from kit import GREY, Log, Shards, Video, arms_up, blend, caption, draw_body, ending, kneel, stand
from ep34_courage_vs_fear import aura, ring
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep35_you_vs_excuses"
dt = 1 / FPS
SCX, SCY = 450.0, 960.0
X0 = -0.2
GRAB = [0.5, 0.8, 1.1, 1.4]                     # chains reach their target
TRY = (2.4, 3.3)
YANK1 = 3.35
LABELS = [2.5, 3.05, 3.6, 4.15]
CRAWL = (4.8, 5.8)
YANK2 = 5.9
PRONE = 6.25
PUSH = (8.0, 9.4)
BLACK = (9.65, 10.0)
DROP = 10.0
APEX = 11.6
DIVE = 12.4
LAND = 12.8
RISE = (14.8, 15.8)
END_T = 18.6
DUR = 22.6
JUMP_H = 9.0
# anchor x, body joint, label
CHAINS = [(-2.2, "hand2", "TOMORROW"), (-1.4, "foot2", "I'M TIRED"), (1.3, "hand1", "NO TIME"),
          (2.0, "hip", "WHAT IF I FAIL?")]


def you_y(t):
    if t < DROP:
        return 0.0
    if t < APEX:
        return JUMP_H * ease_out((t - DROP) / (APEX - DROP)) ** 0.8
    if t < DIVE:
        return JUMP_H + 0.3 * math.sin(math.pi * (t - APEX) / (DIVE - APEX))
    if t < LAND:
        u = (t - DIVE) / (LAND - DIVE)
        return JUMP_H * (1 - u * u)
    return 0.0


def land_pose(x, t):
    from engine import L_FARM, L_UARM, dirv, ik
    hip = np.array([x, 0.78 + 0.01 * math.sin(t * 4)])
    lean = 0.8
    j = {"hip": hip, "neck": hip + dirv(lean) * 0.92, "shoulder": hip + dirv(lean) * 0.79,
         "knee1": np.array([x + 0.55, 0.62]), "foot1": np.array([x + 0.62, 0.03]),
         "knee2": np.array([x - 0.25, 0.06]), "foot2": np.array([x - 0.95, 0.08])}
    j["head"] = j["neck"] + dirv(1.15) * 0.36
    j["hand1"] = np.array([x + 0.95, 0.06])
    j["elbow1"] = ik(j["shoulder"], j["hand1"], L_UARM, L_FARM, -1)
    j["hand2"] = j["shoulder"] + np.array([-0.95, 0.25])
    j["elbow2"] = j["shoulder"] + np.array([-0.5, 0.05])
    return j


def prone(x):
    j = rotate_pose(stand(x, 0.0, 2.9, 2.9, 0.1, 0.1, 0.0), np.array([x, 0.0]), -1.5)
    return {k: v + [0, 0.14] for k, v in j.items()}


def you_pose(t):
    x = X0
    if t < TRY[0]:
        return kneel(x, t, 0.8)
    if t < YANK1:
        return blend(kneel(x, t, 0.8), stand(x, 0.1, 0.4, 0.3, 0.3, 0.3, 0.1), smoothstep(TRY[0], TRY[1], t))
    if t < CRAWL[0]:
        j = blend(stand(x, 0.1, 0.4, 0.3, 0.3, 0.3, 0.1), kneel(x, t, 0.8), ease_out(clamp((t - YANK1) / 0.25)))
        return j
    if t < YANK2:
        return kneel(x, t, 0.3, smoothstep(CRAWL[0], CRAWL[1], t))
    if t < PUSH[0]:
        return blend(kneel(x, t, 0.3, 1.0), prone(x - 0.6), ease_out(clamp((t - YANK2) / 0.35)))
    if t < DROP:
        u = smoothstep(PUSH[0], PUSH[1], t)
        a = blend(prone(x - 0.6), kneel(x, t, 0.2), smoothstep(0.0, 0.5, u))
        j = blend(a, stand(x, -0.02, 0.5, 0.4, 0.6, 0.5, -0.1), smoothstep(0.5, 1.0, u))
        return {k: v + [0.008 * math.sin(t * 55) * u, 0] for k, v in j.items()}
    y = you_y(t)
    if t < APEX:
        j = arms_up(x, t)
    elif t < DIVE:
        j = stand(x, 0.0, 1.9, -1.2, 0.2, 0.2, -0.1)
    elif t < LAND:
        j = rotate_pose(arms_up(x, t), np.array([x, 1.2]), math.pi * smoothstep(DIVE, LAND - 0.1, t) * 0.0)
        j = blend(stand(x, 0.0, 1.9, -1.2, 0.2, 0.2, -0.1), stand(x, 0.1, 0.3, 0.2, 2.2, 0.2, 0.3),
                  smoothstep(DIVE, LAND, t))
    elif t < RISE[0]:
        j = land_pose(x, t)
    else:
        j = blend(land_pose(x, t), stand(x, -0.04, 0.35, 0.3, 1.2, 1.2, -0.08), smoothstep(RISE[0], RISE[1], t))
    return {kk: v + [0, y] for kk, v in j.items()}


# ------------------------------------------------------------------ chains
def chain_pts(a, b, sag, n=None):
    a, b = np.array(a, float), np.array(b, float)
    L = float(np.hypot(*(b - a)))
    n = n or max(4, int(L / 0.17))
    mid = (a + b) / 2 + np.array([0, -sag])
    us = np.linspace(0, 1, n)
    return [((1 - u) ** 2) * a + 2 * (1 - u) * u * mid + u * u * b for u in us]


def draw_chain(c, cam, pts, col, alpha, t, vib=0.0):
    w = max(2.0, 0.035 * cam.s)
    for k in range(len(pts) - 1):
        p, q = pts[k], pts[k + 1]
        d = q - p
        ang = math.degrees(math.atan2(-d[1], d[0]))
        cx, cy = cam.pt((p + q) / 2)
        cy += vib * math.sin(t * 70 + k) * cam.s * 0.02
        L = float(np.hypot(*d)) * cam.s
        c.save()
        c.translate(cx, cy)
        c.rotate(ang)
        if k % 2 == 0:
            c.drawOval(skia.Rect(-L * 0.62, -0.07 * cam.s, L * 0.62, 0.07 * cam.s), paint(col, alpha, w))
        else:
            c.drawLine(-L * 0.6, 0, L * 0.6, 0, paint(col, alpha, w * 1.2))
        c.restore()


def anchor(c, cam, x, alpha, col=RED):
    sx, sy = cam.pt((x, 0.0))
    r = 0.16 * cam.s
    c.drawRect(skia.Rect(sx - r * 1.2, sy - r * 0.5, sx + r * 1.2, sy + r * 0.2), paint(col, alpha))
    c.drawCircle(sx, sy - r * 1.0, r * 0.6, paint(col, alpha, max(2, 0.04 * cam.s)))


def tension(t):
    """0 = slack (sagging), 1 = tight."""
    if t < TRY[1] - 0.15:
        return 0.3
    if t < CRAWL[0]:
        return 1.0 - 0.6 * smoothstep(YANK1 + 0.3, YANK1 + 0.9, t)
    if t < YANK2 + 0.3:
        return 0.4 + 0.6 * smoothstep(CRAWL[1] - 0.3, YANK2, t)
    if t < PUSH[0]:
        return 0.6
    return 1.0


# ------------------------------------------------------------------ camera
def camera(t, j):
    yb = you_y(t)
    if t < TRY[0]:
        u = ease_out(smoothstep(0.0, TRY[0], t))
        a, b = (220.0, X0 + 0.2, 1.2), (165.0, X0 + 0.1, 1.9)
    elif t < 4.6:
        u = (t - TRY[0]) / (4.6 - TRY[0])
        a, b = (160.0, X0, 1.9), (172.0, X0, 1.8)
    elif t < 6.6:
        u = (t - 4.6) / 2.0
        a, b = (220.0, X0 + 0.3, 1.2), (240.0, X0 + 0.0, 1.0)
    elif t < PUSH[0]:
        u = (t - 6.6) / (PUSH[0] - 6.6)
        a, b = (300.0, X0 - 0.4, 0.6), (330.0, X0 - 0.4, 0.6)
    elif t < DROP:
        u = ease_out((t - PUSH[0]) / (DROP - PUSH[0]))
        a, b = (150.0, X0, 2.2), (215.0, X0, 1.6)
    elif t < LAND:
        u = clamp((t - DROP) / (LAND - DROP))
        s = 150.0 if t < DIVE else 150.0 - 30 * smoothstep(DIVE, LAND, t)
        return s, X0, yb + 1.1 + (0.4 if t < APEX else 0.0)
    elif t < 13.6:
        u = (t - LAND) / 0.8
        a, b = (118.0, X0, 2.6), (124.0, X0, 2.5)
    elif t < RISE[0]:
        u = (t - 13.6) / (RISE[0] - 13.6)
        a, b = (250.0, X0 + 0.2, 0.8), (275.0, X0 + 0.2, 0.8)
    else:
        u = ease_out(clamp((t - RISE[0]) / 3.2))
        a, b = (230.0, X0, 1.3), (150.0, X0, 2.0)
    return tuple(a[i] + (b[i] - a[i]) * clamp(u) for i in range(3))


CUTS = [TRY[0], 4.6, 6.6, PUSH[0], DROP, LAND, 13.6, RISE[0]]


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    embers = Particles(5)
    streaks = Particles(8)
    shards = Shards(9)
    rng = np.random.default_rng(3)
    for fi in range(v.n):
        t = fi * dt
        for key, tt, kind in (("grab", GRAB[0], "grab"), ("yank1", YANK1, "yank"), ("yank2", YANK2, "yank"),
                              ("prone", PRONE, "prone"), ("beat", 6.8, "beat"), ("push", PUSH[0], "push"),
                              ("drop", DROP, "drop"), ("apex", APEX, "apex"), ("dive", DIVE, "dive"),
                              ("land", LAND, "land"), ("rise", RISE[0], "rise"), ("end", END_T, "end"),
                              ("end2", END_T + 1.2, "end2")):
            if t >= tt:
                log.once(key, tt, kind)
        for k, tl in enumerate(LABELS):
            if t >= tl:
                log.once(f"lab{k}", tl, "label", k)
        for k, tg in enumerate(GRAB[1:]):
            if t >= tg:
                log.once(f"grab{k}", tg, "grab")
        j = you_pose(t)
        if abs(t - DROP) < dt / 2:
            for ax, jn, _ in CHAINS:
                pts = chain_pts((ax, 0.25), j[jn], 0.0)
                for p in pts[1:-1]:
                    shards.burst(p[0] - 0.05, p[0] + 0.05, p[1] - 0.05, p[1] + 0.05, 3, vx=(-5, 5), vy=(1, 7),
                                 size=(0.06, 0.16), life=(0.8, 1.6))
            embers.emit(np.tile(j["neck"], (90, 1)) + rng.normal(0, 0.3, (90, 2)), vel=(0, 2.0), spread=3.0,
                        life=(0.5, 1.4), size=(0.03, 0.08))
        if abs(t - LAND) < dt / 2:
            for ax, _, _ in CHAINS:
                shards.burst(ax - 0.2, ax + 0.2, 0.05, 0.4, 14, vx=(-4, 4), vy=(2, 8), size=(0.08, 0.22))
            embers.emit(np.array([[X0 + q, 0.05] for q in np.linspace(-3, 3, 70)]), vel=(0, 1.0), spread=1.2,
                        life=(0.5, 1.2), size=(0.03, 0.07))
        aura_a = 0.0
        if PUSH[0] < t < DROP:
            aura_a = 0.4 * smoothstep(PUSH[0], BLACK[0], t)
        elif t >= DROP:
            aura_a = 1.0
        if aura_a > 0.05 and rng.random() < 0.55:
            pts = np.array([j["hip"], j["neck"], j["foot1"]]) + rng.normal(0, 0.15, (3, 2))
            embers.emit(pts, vel=(0, 1.2 + 1.5 * aura_a), spread=0.35, life=(0.6, 1.3), size=(0.03, 0.06))
        if DROP < t < LAND and rng.random() < 0.9:
            streaks.emit(np.array([[X0 + rng.uniform(-4, 4), you_y(t) + rng.uniform(-6, 6)]]), vel=(0, 0), spread=0.05,
                         life=(0.3, 0.5), size=(0.02, 0.04))
        embers.step(dt)
        streaks.step(dt)
        shards.step(dt)
        if not v.wants(fi):
            continue
        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        s, wx, wy = camera(t, j)
        cam = Camera()
        cam.s, cam.wx, cam.wy, cam.sx, cam.sy = s, wx, wy, SCX, SCY
        shake = 0.0
        for t0, amp in ((YANK1, 14), (YANK2, 16), (PRONE, 8), (DROP, 30), (LAND, 40)):
            if t0 <= t < t0 + 0.5:
                shake = max(shake, amp * (1 - (t - t0) / 0.5))
        if PUSH[0] < t < BLACK[0]:
            shake = max(shake, 4 * smoothstep(PUSH[0], PUSH[1], t))
        if shake:
            cam.sx += shake * math.sin(t * 97)
            cam.sy += shake * math.cos(t * 83)
        gy = cam.pt((0, 0))[1]
        if gy < H + 50:
            e.drawLine(0, gy, W, gy, paint(WHITE, 0.45, 2.5))
        # speed streaks while flying
        if DROP < t < LAND:
            for x, y, vx, vy, age, life, size, sd in streaks.p:
                sx, sy = cam.pt((x, y))
                ln = (0.8 if t < APEX else 1.6 if t > DIVE else 0.2) * cam.s
                f_.drawLine(sx, sy - ln / 2, sx, sy + ln / 2, paint(WHITE, 0.5 * (1 - age / life), 2))
        # ground cracks after landing
        if t >= LAND:
            ca = 1.0 - 0.6 * smoothstep(LAND + 2.0, LAND + 4.0, t)
            g = ease_out(clamp((t - LAND) / 0.25))
            crng = np.random.default_rng(4)
            for side in (-1, 1):
                for q in range(3):
                    p = np.array([X0 + side * 0.3, 0.0])
                    path = skia.Path()
                    path.moveTo(*cam.pt(p))
                    for st in range(6):
                        p = p + np.array([side * crng.uniform(0.25, 0.55) * g, -crng.uniform(0.05, 0.3) * g * (q + 1) * 0.6])
                        path.lineTo(*cam.pt(p))
                    e.drawPath(path, paint(WHITE, 0.7 * ca, max(2, 0.03 * cam.s)))
        # chains
        if t < DROP:
            ten = tension(t)
            for k, (ax, jn, lab) in enumerate(CHAINS):
                g = ease_out(clamp((t - (GRAB[k] - 0.45)) / 0.45))
                if g <= 0:
                    anchor(e, cam, ax, smoothstep(0.0, 0.3, t))
                    continue
                tgt = np.array([ax, 0.25]) + (j[jn] - np.array([ax, 0.25])) * g
                L = float(np.hypot(*(tgt - np.array([ax, 0.25]))))
                pts = chain_pts((ax, 0.25), tgt, (1 - ten) * 0.25 * L * (1 - 0.5 * (g < 1)))
                vib = 1.0 if (PUSH[0] < t) or (abs(t - YANK1) < 0.3) or (abs(t - YANK2) < 0.3) else 0.0
                hl = LABELS[k] <= t < LABELS[k] + 0.55
                draw_chain(hc, cam, pts, WHITE if (hl and int(t * 16) % 2 == 0) else RED, 1.0, t, vib + hl)
                anchor(e, cam, ax, 1.0)
                if PUSH[0] < t < BLACK[0] and int(t * 12 + k) % 3 == 0:
                    p = pts[int(rng.integers(1, len(pts) - 1))]
                    f_.drawCircle(*cam.pt(p), max(3, 0.05 * cam.s), paint(WHITE, 0.95))
                if LABELS[k] <= t < LABELS[k] + 0.55:
                    u = (t - LABELS[k]) / 0.55
                    pop = 1 + 0.25 * math.exp(-u * 12)
                    caption(oc, lab, 640, 1 - smoothstep(0.85, 1.0, u), RED, int(78 * pop), band=False)
        elif t < LAND:
            for ax, _, _ in CHAINS:
                anchor(e, cam, ax, 1.0)
        shards.draw(hc, cam, RED)
        # chest light while down
        if PRONE + 0.5 < t < DROP:
            pulse = 0.5 + 0.5 * math.sin((t - 6.8) * math.pi * 2 / 0.75)
            grow = smoothstep(6.8, 9.6, t)
            cx, cy = cam.pt((j["neck"] * 0.6 + j["hip"] * 0.4))
            f_.drawCircle(cx, cy, (0.06 + 0.1 * grow) * cam.s * (0.8 + 0.3 * pulse), paint(WHITE, 0.6 + 0.4 * pulse))
        aura(f_, cam, j, aura_a, t)
        embers.draw(f_, cam, WHITE, WHITE)
        draw_body(hc, j, cam, WHITE, 1.0)
        if 2.4 < t < PUSH[0]:
            lx, _ = cam.pt((j["hip"][0], 0))
            draw_spaced(tc, "YOU", lx, gy + 50, font(34, "Inter-Bold"), 6, paint(WHITE, smoothstep(2.4, 2.7, t)))
        ring(f_, cam, (X0, 1.2), t, DROP, 4.5, WHITE, 0.8, 0.12)
        ring(f_, cam, (X0, 0.1), t, LAND, 5.0, WHITE, 0.8, 0.12)
        ring(f_, cam, (X0, 0.1), t, LAND + 0.12, 3.2, WHITE, 0.7, 0.06)
        if 0.2 < t < 2.2:
            caption(oc, "YOU VS EXCUSES", 1500, smoothstep(0.2, 0.5, t) * (1 - smoothstep(1.9, 2.2, t)), WHITE, 60,
                    band=False)
        ending(oc, t, END_T - 0.3, [(END_T, "EXCUSES ONLY", WHITE, 100), (END_T + 0.4, "HOLD YOU", WHITE, 110),
                                    (END_T + 1.2, "IF YOU", RED, 110), (END_T + 1.45, "STOP PULLING.", RED, 100)],
               gap=125)
        white = 0.0
        for t0, a in ((DROP, 0.8), (LAND, 0.7), (YANK1, 0.12), (YANK2, 0.12)):
            if t0 <= t < t0 + 0.35:
                white = max(white, a * (1 - (t - t0) / 0.35) ** 2)
        for c_ in CUTS:
            if c_ <= t < c_ + 0.1 and c_ not in (DROP, LAND):
                white = max(white, 0.07)
        dim = 0.0
        if BLACK[0] <= t < BLACK[1]:
            dim, white = 1.0, 0.0
        if 6.6 <= t < PUSH[0]:
            dim = 0.3
        flash = 0.5 * math.exp(-(t - DROP) * 3) if t >= DROP else 0.0
        if t >= LAND:
            flash += 0.4 * math.exp(-(t - LAND) * 3)
        v.compose(fi, t, flash=flash, glow=0.15 * aura_a, white=white, dim=dim, fade_in=0.0)
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DROP, rise_at=8.0), gain=0.3, fade_in=0.3, fade_out=0.4, stop=BLACK[0])
    for t, kind, _, extra in events:
        if kind == "grab":
            m.add(t, sfx.rattle(0.5, int(t * 10)), 0.6, 0, 0.3)
            m.add(t + 0.1, sfx.plate_clank(int(t * 10), 0.8), 0.6, 0, 0.3)
        elif kind == "yank":
            m.add(t, sfx.rattle(0.6, 3), 0.8, 0, 0.3)
            m.add(t, sfx.punch_hit(2, 1.0), 0.8, 0, 0.3)
            m.add(t + 0.1, sfx.body_fall(), 0.6, 0, 0.3)
        elif kind == "label":
            m.add(t, sfx.text_hit(extra), 0.5, 0, 0.4)
        elif kind == "prone":
            m.add(t, sfx.body_fall(), 0.8, 0, 0.3)
        elif kind == "beat":
            for q in range(4):
                m.add(t + q * 0.75, sfx.heartbeat(), 0.7, 0, 0.3)
        elif kind == "push":
            m.add(t, sfx.breath(3, 0.8), 0.6, 0, 0.3)
            m.add(t, sfx.riser(BLACK[0] - t), 0.6, 0, 0.4)
            m.add(t + 0.3, sfx.rattle(1.2, 5), 0.5, 0, 0.3)
        elif kind == "drop":
            m.add(t, sfx.boom(3.5), 1.0, 0, 0.6)
            m.add(t, sfx.shatter(1, 1.2), 0.8, 0, 0.5)
            m.add(t, sfx.whoosh(1.4, 200, 6000, 0.3, seed=2), 0.8, 0, 0.4)
        elif kind == "apex":
            m.add(t, sfx.sparkle(0.8), 0.4, 0, 0.5)
        elif kind == "dive":
            m.add(t, sfx.whoosh(0.4, 400, 9000, 0.9, seed=5), 0.8, 0, 0.3)
        elif kind == "land":
            m.add(t, sfx.boom(3.5), 1.0, 0, 0.6)
            m.add(t, sfx.punch_hit(4, 1.5), 1.0, 0, 0.4)
            m.add(t + 0.05, sfx.shatter(6, 1.0), 0.7, 0, 0.5)
        elif kind == "rise":
            m.add(t, sfx.power_up(110), 0.5, 0, 0.5)
        elif kind == "end":
            m.add(t, sfx.text_hit(1), 0.7, 0, 0.4)
        elif kind == "end2":
            m.add(t, sfx.text_hit(3), 0.9, 0, 0.5)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [0.4, 1.2, 2.0, 2.9, 3.5, 4.4, 5.3, 6.0, 7.2, 8.6, 9.3, 10.2, 10.9, 11.9, 12.6, 12.9, 13.3, 14.2,
              15.4, 17.5]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
