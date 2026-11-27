"""EP40 - YOU VS PRESSURE  (edit-friendly: big drop at 10.0 s)

  0.0  dark. A guy alone. THUD: two giant red walls slam in from both sides.
  2.0  the walls advance step by step (THUD... THUD...), he looks left, right.
  4.0  they reach him: he pushes them back with both arms... his arms bend.
  6.0  setback: the walls crush him down to his knees, the gap keeps shrinking.
  7.8  dark, heartbeat... a tiny white diamond pulses in his chest.
  8.4  he pushes back, stands up, the walls move back, the light grows.
  9.65 black. silence.
 10.0  DROP: the walls EXPLODE into red shards, a giant glowing diamond behind
       him, aura, shockwave. 12.0: second hit, the diamond flashes.
 END   PRESSURE / MAKES / DIAMONDS.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import (FPS, H, L_FARM, L_UARM, RED, WHITE, W, Camera, Particles, clamp, draw_spaced, ease_out, font,
                    ik, paint, smoothstep)
from kit import Log, Shards, Video, blend, caption, draw_body, ending, kneel, stand
from ep34_courage_vs_fear import aura, ring
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep40_you_vs_pressure"
dt = 1 / FPS
SCX, SCY = 450.0, 960.0
THUDS = [0.5, 2.2, 2.9, 3.6, 4.3]
CONTACT = 4.3
CRUSH = (6.0, 7.6)
GLOW = 7.8
PUSH = (8.4, 9.5)
BLACK = (9.65, 10.0)
DROP = 10.0
HIT2 = 12.0
END_T = 16.8
DUR = 20.8
WALL_H = 6.0
D_KF = [(0, 6.0), (0.5, 3.0), (2.2, 2.6), (2.9, 2.2), (3.6, 1.7), (4.3, 1.3), (CRUSH[0], 1.22), (CRUSH[1], 0.8),
        (PUSH[0], 0.8), (PUSH[1], 1.2), (DROP, 1.25)]


def wall_d(t):
    """Half-gap between the walls."""
    kf = D_KF
    if t <= kf[0][0]:
        return kf[0][1]
    for (t0, v0), (t1, v1) in zip(kf, kf[1:]):
        if t <= t1:
            u = (t - t0) / (t1 - t0)
            if t1 in THUDS:                           # slam: fast move then stop
                u = ease_out(min(1.0, u * 3.0)) if t1 - t0 < 1.0 else ease_out(smoothstep(0.7, 1.0, u))
            return v0 + (v1 - v0) * u
    return kf[-1][1]


def push_arms(j, d, t):
    sh = j["shoulder"]
    for i, side in ((1, 1), (2, -1)):
        hand = np.array([side * (d - 0.04), sh[1] + 0.05])
        reach = abs(hand[0] - sh[0])
        if reach > L_UARM + L_FARM - 0.02:
            hand[0] = sh[0] + side * (L_UARM + L_FARM - 0.02)
        j[f"hand{i}"] = hand
        j[f"elbow{i}"] = ik(sh, hand, L_UARM, L_FARM, -1 if side > 0 else 1) + np.array([0, -0.08])
    return j


def you_pose(t):
    d = wall_d(t)
    if t < 2.0:
        return stand(0.0, 0.0, 0.15, 0.1, 0.2, 0.15, 0.0, 0.006 * math.sin(t * 3))
    if t < CONTACT - 0.3:
        j = stand(0.0, 0.05, 0.5, 0.4, 1.2, 1.1, 0.2)
        if int(t * 2.5) % 2:
            j["head"] = j["head"] + [-0.12, 0]
        return j
    if t < CRUSH[0]:
        j = stand(0.0, 0.0, 1.5, -1.5, 0.2, 0.2, 0.1)
        j = push_arms(j, d, t)
        return {k: v + [0.008 * math.sin(t * 50), 0] for k, v in j.items()}
    if t < PUSH[0]:
        k = stand(0.0, 0.25, 1.5, -1.5, 0.2, 0.2, 0.5, 0.0, 0.95)
        w = smoothstep(CRUSH[0], CRUSH[0] + 0.6, t)
        j = blend(push_arms(stand(0.0, 0.0, 1.5, -1.5, 0.2, 0.2, 0.1), d, t), k, w)
        j = push_arms(j, d, t)
        return {kk: v + [0.006 * math.sin(t * 50), 0] for kk, v in j.items()}
    if t < DROP:
        k = stand(0.0, 0.25, 1.5, -1.5, 0.2, 0.2, 0.5, 0.0, 0.95)
        j = blend(k, stand(0.0, 0.0, 1.5, -1.5, 0.2, 0.2, -0.1), smoothstep(PUSH[0], PUSH[1], t))
        j = push_arms(j, d, t)
        return {kk: v + [0.01 * math.sin(t * 55), 0] for kk, v in j.items()}
    if t < HIT2 - 0.2:
        a = smoothstep(DROP, DROP + 0.35, t)
        return blend(stand(0.0, 0.0, 1.5, -1.5, 0.2, 0.2, -0.1), stand(0.0, -0.04, 0.35, 0.3, 1.2, 1.2, -0.08), a)
    up = smoothstep(HIT2 - 0.2, HIT2, t)
    j = stand(0.0, -0.04, 0.35 + 2.5 * up, 0.3, 1.2 - 0.9 * up, 1.2, -0.08 - 0.15 * up)
    return j


# ------------------------------------------------------------------ drawing
def draw_wall(c, tc, cam, side, d, t, alpha=1.0):
    x_in = side * d
    x_out = side * 12.0
    r = skia.Rect(*cam.pt((min(x_in, x_out), WALL_H)), *cam.pt((max(x_in, x_out), 0)))
    c.drawRect(r, paint((0.16, 0.02, 0.03), alpha))
    sw = max(3, 0.05 * cam.s)
    for q in range(1, 12):                        # bricks
        yy = q * 0.5
        c.drawLine(*cam.pt((x_in, yy)), *cam.pt((x_out, yy)), paint(RED, 0.25 * alpha, 2))
        for k in range(0, 12):
            bx = x_in + side * (0.6 * k + (0.3 if q % 2 else 0))
            c.drawLine(*cam.pt((bx, yy - 0.5)), *cam.pt((bx, yy)), paint(RED, 0.18 * alpha, 2))
    c.drawLine(*cam.pt((x_in, 0)), *cam.pt((x_in, WALL_H)), paint(RED, alpha, sw * 1.6))
    c.drawLine(*cam.pt((x_in, WALL_H)), *cam.pt((x_out, WALL_H)), paint(RED, alpha, sw))
    # label written vertically on the face
    cx, cy = cam.pt((x_in + side * 0.45, 2.6))
    tc.save()
    tc.translate(cx, cy)
    tc.rotate(-90 if side < 0 else 90)
    draw_spaced(tc, "PRESSURE", 0, 0.12 * cam.s, font(max(14, 0.42 * cam.s), "InterDisplay-Black"), 6,
                paint(RED, 0.9 * alpha))
    tc.restore()


def diamond_path(cam, cx, cy, w, rot=0.0):
    h1, h2 = w * 0.32, w * 0.62
    sq = math.cos(rot)
    pts = [(-w / 2, 0), (-w / 3, h1), (w / 3, h1), (w / 2, 0), (0, -h2)]
    p = skia.Path()
    for k, (px, py) in enumerate(pts):
        (p.moveTo if k == 0 else p.lineTo)(*cam.pt((cx + px * (0.75 + 0.25 * sq), cy + py)))
    p.close()
    facets = []
    for fx in (-1 / 3, 0, 1 / 3):
        a = cam.pt((cx + fx * w * 0.5 * (0.75 + 0.25 * sq) + 0.08 * w * math.sin(rot), cy + h1))
        facets.append((a, cam.pt((cx + fx * w * 0.6 * (0.75 + 0.25 * sq), cy))))
        facets.append((cam.pt((cx + fx * w * 0.6 * (0.75 + 0.25 * sq), cy)), cam.pt((cx, cy - h2))))
    return p, facets


def draw_diamond(c, cam, cx, cy, w, alpha, rot, fill=0.12):
    if alpha <= 0.01:
        return
    p, facets = diamond_path(cam, cx, cy, w, rot)
    c.drawPath(p, paint(WHITE, fill * alpha))
    c.drawPath(p, paint(WHITE, alpha, max(3, 0.05 * cam.s)))
    c.drawLine(*cam.pt((cx - w / 2 * (0.75 + 0.25 * math.cos(rot)), cy)),
               *cam.pt((cx + w / 2 * (0.75 + 0.25 * math.cos(rot)), cy)), paint(WHITE, 0.8 * alpha, max(2, 0.03 * cam.s)))
    for a, b in facets:
        c.drawLine(*a, *b, paint(WHITE, 0.55 * alpha, max(2, 0.025 * cam.s)))


def camera(t):
    if t < 2.0:
        u = ease_out(smoothstep(0.0, 2.0, t))
        a, b = (120.0, 0.0, 2.6), (115.0, 0.0, 2.5)
    elif t < CONTACT:
        u = (t - 2.0) / (CONTACT - 2.0)
        a, b = (115.0, 0.0, 2.5), (150.0, 0.0, 2.0)
    elif t < CRUSH[0]:
        u = (t - CONTACT) / (CRUSH[0] - CONTACT)
        a, b = (230.0, 0.0, 1.6), (260.0, 0.0, 1.5)
    elif t < GLOW:
        u = (t - CRUSH[0]) / (GLOW - CRUSH[0])
        a, b = (165.0, 0.0, 1.9), (185.0, 0.0, 1.7)
    elif t < PUSH[0]:
        u = (t - GLOW) / (PUSH[0] - GLOW)
        a, b = (330.0, -0.1, 1.3), (360.0, -0.1, 1.3)
    elif t < DROP:
        u = ease_out((t - PUSH[0]) / (DROP - PUSH[0]))
        a, b = (180.0, 0.0, 1.8), (240.0, 0.0, 1.6)
    elif t < HIT2:
        u = (t - DROP) / (HIT2 - DROP)
        a, b = (105.0, 0.0, 2.8), (125.0, 0.0, 2.6)
    elif t < 14.0:
        u = (t - HIT2) / 2.0
        a, b = (210.0, 0.0, 1.9), (230.0, 0.0, 1.9)
    else:
        u = ease_out(clamp((t - 14.0) / 2.8))
        a, b = (200.0, 0.0, 2.0), (120.0, 0.0, 2.8)
    return tuple(a[i] + (b[i] - a[i]) * clamp(u) for i in range(3))


CUTS = [2.0, CONTACT, CRUSH[0], GLOW, PUSH[0], DROP, HIT2, 14.0]


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    embers = Particles(5)
    shards = Shards(9)
    rng = np.random.default_rng(3)
    for fi in range(v.n):
        t = fi * dt
        for k, tt in enumerate(THUDS):
            if t >= tt:
                log.once(f"thud{k}", tt, "thud", k)
        for key, tt, kind in (("contact", CONTACT, "contact"), ("crush", CRUSH[0], "crush"), ("glow", GLOW, "glow"),
                              ("push", PUSH[0], "push"), ("drop", DROP, "drop"), ("hit2", HIT2, "hit2"),
                              ("end", END_T, "end"), ("end2", END_T + 1.3, "end2")):
            if t >= tt:
                log.once(key, tt, kind)
        j = you_pose(t)
        if abs(t - DROP) < dt / 2:
            for side in (-1, 1):
                xa, xb = sorted((side * 1.3, side * 4.5))
                va, vb = sorted((side * 2, side * 11))
                shards.burst(xa, xb, 0.2, 5.5, 90, vx=(va, vb), vy=(1, 8),
                             size=(0.15, 0.45), life=(1.0, 2.2))
            embers.emit(np.tile(j["neck"], (90, 1)) + rng.normal(0, 0.3, (90, 2)), vel=(0, 2.0), spread=3.0,
                        life=(0.5, 1.4), size=(0.03, 0.08))
        aura_a = 0.0
        if PUSH[0] < t < DROP:
            aura_a = 0.35 * smoothstep(PUSH[0], BLACK[0], t)
        elif t >= DROP:
            aura_a = 1.0
        if aura_a > 0.05 and rng.random() < 0.55:
            pts = np.array([j["hip"], j["neck"], j["foot1"]]) + rng.normal(0, 0.15, (3, 2))
            embers.emit(pts, vel=(0, 1.2 + 1.5 * aura_a), spread=0.35, life=(0.6, 1.3), size=(0.03, 0.06))
        embers.step(dt)
        shards.step(dt, gravity=7.0)
        if not v.wants(fi):
            continue
        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        s, wx, wy = camera(t)
        cam = Camera()
        cam.s, cam.wx, cam.wy, cam.sx, cam.sy = s, wx, wy, SCX, SCY
        shake = 0.0
        for t0 in THUDS:
            if t0 <= t < t0 + 0.4:
                shake = max(shake, 16 * (1 - (t - t0) / 0.4))
        for t0, amp in ((DROP, 34), (HIT2, 22), (CONTACT, 10)):
            if t0 <= t < t0 + 0.5:
                shake = max(shake, amp * (1 - (t - t0) / 0.5))
        if CRUSH[0] < t < PUSH[1]:
            shake = max(shake, 3.5)
        if shake:
            cam.sx += shake * math.sin(t * 97)
            cam.sy += shake * math.cos(t * 83)
        gy = cam.pt((0, 0))[1]
        e.drawLine(0, gy, W, gy, paint(WHITE, 0.45, 2.5))
        d = wall_d(t)
        if t < DROP:
            for side in (-1, 1):
                draw_wall(e, tc, cam, side, d, t)
        shards.draw(hc, cam, RED)
        # diamond
        rot = t * 1.6
        if GLOW <= t < DROP:
            pulse = 0.5 + 0.5 * math.sin((t - GLOW) * math.pi * 2 / 0.6)
            grow = smoothstep(GLOW, BLACK[0], t)
            cx, cy = (j["neck"] * 0.55 + j["hip"] * 0.45)
            draw_diamond(f_, cam, cx, cy + 0.05, 0.22 + 0.35 * grow, 0.6 + 0.4 * pulse, rot, 0.6)
        if t >= DROP:
            g = ease_out(clamp((t - DROP) / 0.5))
            big = 1.0 + 0.25 * math.exp(-(t - HIT2) * 5) * (t >= HIT2)
            draw_diamond(e, cam, 0.0, 1.55, 3.4 * g * big, 0.9, rot * 0.6, 0.06)
        aura(f_, cam, j, aura_a, t)
        embers.draw(f_, cam, WHITE, WHITE)
        draw_body(hc, j, cam, WHITE, 1.0)
        if 2.0 < t < DROP and not (GLOW <= t < PUSH[0]):
            lx, _ = cam.pt((j["hip"][0], 0))
            draw_spaced(tc, "YOU", lx, gy + 54, font(34, "Inter-Bold"), 6, paint(WHITE, smoothstep(2.0, 2.3, t)))
        ring(f_, cam, (0.0, 1.4), t, DROP, 5.5, WHITE, 0.8, 0.12)
        ring(f_, cam, (0.0, 1.4), t, DROP + 0.15, 3.5, WHITE, 0.7, 0.06)
        ring(f_, cam, (0.0, 1.6), t, HIT2, 4.0, WHITE, 0.7, 0.1)
        if 0.6 < t < 2.0:
            caption(oc, "YOU VS PRESSURE", 1500, smoothstep(0.6, 0.9, t) * (1 - smoothstep(1.7, 2.0, t)), WHITE, 60,
                    band=False)
        ending(oc, t, END_T - 0.3, [(END_T, "PRESSURE", RED, 120), (END_T + 0.4, "MAKES", WHITE, 110),
                                    (END_T + 1.1, "DIAMONDS.", WHITE, 130)], gap=140)
        white = 0.0
        for t0, a in ((DROP, 0.85), (HIT2, 0.5)):
            if t0 <= t < t0 + 0.35:
                white = max(white, a * (1 - (t - t0) / 0.35) ** 2)
        for c_ in CUTS:
            if c_ <= t < c_ + 0.1 and c_ not in (DROP, HIT2):
                white = max(white, 0.07)
        dim = 0.0
        if BLACK[0] <= t < BLACK[1]:
            dim, white = 1.0, 0.0
        elif CRUSH[1] - 0.3 < t < PUSH[0]:
            dim = 0.35
        flash = 0.5 * math.exp(-(t - DROP) * 3) if t >= DROP else 0.0
        if t >= HIT2:
            flash += 0.35 * math.exp(-(t - HIT2) * 3)
        v.compose(fi, t, flash=flash, glow=0.15 * aura_a, white=white, dim=dim, fade_in=0.0)
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DROP, rise_at=7.0), gain=0.3, fade_in=0.3, fade_out=0.4, stop=BLACK[0])
    for t, kind, _, extra in events:
        if kind == "thud":
            m.add(t, sfx.boom(1.6), 0.9, 0, 0.4)
            m.add(t, sfx.punch_block(extra), 0.8, 0, 0.3)
        elif kind == "contact":
            m.add(t, sfx.breath(1, 0.7), 0.6, 0, 0.3)
        elif kind == "crush":
            r = sfx.bandnoise(1.6, 50, 400, 3) * sfx.env_ad(int(1.6 * sfx.SR), 0.2, 1.4, 1.2)
            m.add(t, r, 0.7, 0, 0.4)
            m.add(t + 0.4, sfx.body_fall(), 0.6, 0, 0.3)
        elif kind == "glow":
            for q in range(3):
                m.add(t + q * 0.6, sfx.heartbeat(), 0.7, 0, 0.3)
            m.add(t + 0.2, sfx.chime(1760, 0.2), 0.4, 0, 0.6)
        elif kind == "push":
            m.add(t, sfx.breath(3, 0.9), 0.6, 0, 0.3)
            m.add(t, sfx.riser(BLACK[0] - t), 0.6, 0, 0.4)
        elif kind == "drop":
            m.add(t, sfx.boom(3.5), 1.0, 0, 0.6)
            m.add(t, sfx.shatter(1, 1.5), 0.9, 0, 0.5)
            m.add(t + 0.1, sfx.sparkle(2.0), 0.5, 0, 0.6)
        elif kind == "hit2":
            m.add(t, sfx.boom(2.5), 0.9, 0, 0.5)
            m.add(t, sfx.chime(1320, 0.35), 0.6, 0, 0.6)
        elif kind == "end":
            m.add(t, sfx.text_hit(1), 0.7, 0, 0.4)
        elif kind == "end2":
            m.add(t, sfx.text_hit(3), 0.9, 0, 0.5)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [0.3, 0.8, 2.5, 3.8, 5.0, 6.8, 8.0, 9.0, 9.5, 10.1, 10.8, 12.1, 13.0, 15.5, 18.5]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
