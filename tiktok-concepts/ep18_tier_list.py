"""EP18 - MINDSET TIER LIST  (debate bait)

A black & white tier list S/A/B/C/D. Mindsets drop into their tier one by one
with an impact and a one-line verdict:
  D  MOTIVATION  "LASTS 3 DAYS."          D  COMFORT  "FEELS GOOD. KILLS SLOWLY."
  C  TALENT      "USELESS WITHOUT WORK."   C  FEAR     "KEEPS YOU SAFE. AND SMALL."
  B  DISCIPLINE  "BORING. WORKS."          (controversial)
  A  EGO         "GOT HIM UP OFF THE FLOOR." (controversial, callback to EP07)
  S  ... a pulsing "?" ... drumroll ... OBSESSION slams in, red.
END  FIGHT ME IN THE COMMENTS.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import FPS, RED, WHITE, W, Camera, clamp, draw_spaced, ease_out, font, mix, paint, smoothstep
from kit import (CX, GREY, Log, Video, arms_up, blend, caption, crossed, curl, draw_body, flex, lane_cam,
                 mirror, sad, scale_pose, sit, stand)
from engine import Particles, run_pose, fit_font
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep18_tier_list"
dt = 1 / FPS
TIERS = ["S", "A", "B", "C", "D"]
TOP, ROW_H = 470, 205
LX0, LX1, X1 = 80, 200, 880
SLOTS = [330, 490, 650, 800]
ITEMS = [  # t, name, tier, verdict
    (1.4, "MOTIVATION", "D", "LASTS 3 DAYS."),
    (3.2, "COMFORT", "D", "FEELS GOOD. KILLS SLOWLY."),
    (5.0, "TALENT", "C", "USELESS WITHOUT WORK."),
    (6.8, "FEAR", "C", "KEEPS YOU SAFE. AND SMALL."),
    (8.6, "DISCIPLINE", "B", "BORING. WORKS."),
    (10.4, "EGO", "A", "GOT HIM UP OFF THE FLOOR."),
]
Q_T = 12.3
S_T = 14.2
FLASH_T = 15.0             # white flash -> fusion room
ROOM = (15.0, 16.1)
MERGE = (16.1, 17.0)
MONSTER_T = 17.0
RUN = (17.9, 19.4)
LIFT = (19.4, 21.0)
LOCK = 20.25
FINAL = 21.1
SPLUS_DROP = 21.6
UNSTOP = 22.1
END_T = 22.9
DUR = 25.4
FALL = 0.32


def row_y(tier):
    return TOP + TIERS.index(tier) * ROW_H


def icon_pose(name, t):
    if name == "MOTIVATION":
        return sit(-0.3, 0.45, t, 1.0)
    if name == "COMFORT":
        return {"hip": np.array([0.0, 0.3]), "neck": np.array([-0.9, 0.38]), "head": np.array([-1.25, 0.42]),
                "shoulder": np.array([-0.78, 0.37]), "knee1": np.array([0.7, 0.35]), "foot1": np.array([1.4, 0.3]),
                "knee2": np.array([0.65, 0.5]), "foot2": np.array([1.3, 0.4]), "elbow1": np.array([-0.5, 0.6]),
                "hand1": np.array([-0.9, 0.75]), "elbow2": np.array([-0.5, 0.5]), "hand2": np.array([-0.95, 0.6])}
    if name == "TALENT":
        return stand(0, 0.0, 2.9, 0.1, 0.4, 0.15, -0.35)
    if name == "FEAR":
        j = stand(0, -0.1, 0.65, 0.6, 2.1, 2.15, 0.3)
        return {k: vv + [0.025 * math.sin(t * 45), 0] for k, vv in j.items()}
    if name == "DISCIPLINE":
        return curl(0, math.sin(math.pi * ((t % 1.1) / 1.1)))
    if name == "EGO":
        return flex(0, t)
    return arms_up(0, t)


def draw_icon(c, name, cx, base_y, s, t, alpha=1.0, col=None):
    cam = Camera()
    cam.s, cam.sx, cam.sy, cam.wx, cam.wy = s, cx, base_y, 0.0, 0.0
    j = icon_pose(name, t)
    if col is None:
        col = RED if name in ("EGO", "OBSESSION") else WHITE
    g = 0.6 if name == "DISCIPLINE" else 0.35 if name == "OBSESSION" else 0.0
    draw_body(c, j, cam, col, alpha, g)
    if name == "DISCIPLINE":
        b = (j["hand1"] + j["hand2"]) / 2
        c.drawCircle(*cam.pt(b), 0.18 * s, paint(WHITE, alpha, 2))


RNG = np.random.default_rng(5)
embers = None


def mon_x(t):
    if t < RUN[0]:
        return 0.0
    if t < RUN[1]:
        return 9.0 * (t - RUN[0])
    return 9.0 * (RUN[1] - RUN[0])


def draw_monster(c, cam, j, t, alpha=1.0):
    """EGO + OBSESSION: huge muscular body, red outline, red eyes."""
    big = scale_pose(j, j["hip"][0], 1.07)
    big = {k: vv - [0, (big["foot1"][1] + big["foot2"][1]) / 2 - (j["foot1"][1] + j["foot2"][1]) / 2] for k, vv in big.items()}
    draw_body(c, big, cam, RED, alpha, 1.45)           # thick red rim
    draw_body(c, j, cam, WHITE, alpha, 1.0)
    hx, hy = cam.pt(j["head"])
    r = 0.29 * cam.s * 0.92
    for sgn in (-1, 1):                                # two small red horns
        hp = skia.Path()
        hp.moveTo(hx + sgn * r * 0.45, hy - r * 0.75)
        hp.lineTo(hx + sgn * r * 0.95, hy - r * 1.55)
        hp.lineTo(hx + sgn * r * 0.15, hy - r * 0.95)
        hp.close()
        c.drawPath(hp, paint(RED, alpha))
    fwd = 1 if j["foot1"][0] >= j["hip"][0] - 0.3 else -1
    for k in (0, 1):
        c.drawCircle(hx + fwd * r * (0.2 + 0.4 * k), hy - r * 0.1, r * 0.17, paint(RED, alpha))
    c.drawLine(hx + fwd * r * 0.1, hy - r * 0.38, hx + fwd * r * 0.8, hy - r * 0.28, paint((0, 0, 0), alpha, 3))


def draw_grid6(e, f_, tc, hc, oc, t, grow, shake):
    tiers = ["S+", "S", "A", "B", "C", "D"]
    rh = 168
    y = TOP
    sx_ = shake * math.sin(t * 90)
    rows = {}
    for tier in tiers:
        h = rh * (grow if tier == "S+" else 1.0)
        if h < 2:
            continue
        rows[tier] = (y, h)
        e.drawRect(skia.Rect(LX0 + sx_, y, X1 + sx_, y + h - 6), paint(WHITE, 0.3, 2, cap=False))
        box = skia.Rect(LX0 + sx_, y, LX1 + sx_, y + h - 6)
        fs = font(min(100, h * 0.62), "InterDisplay-Black")
        if tier in ("S", "S+"):
            f_.drawRect(box, paint(RED, 0.95 if tier == "S+" else 0.9))
            draw_spaced(oc, tier, (LX0 + LX1) / 2 + sx_, y + h * 0.68, fs if tier == "S" else font(min(80, h * 0.5), "InterDisplay-Black"), 0,
                        paint((0, 0, 0), 1.0))
        else:
            e.drawRect(box, paint(WHITE, 0.9, 3, cap=False))
            draw_spaced(tc, tier, (LX0 + LX1) / 2 + sx_, y + h * 0.68, fs, 0, paint(WHITE, 1.0))
        y += h
    counts = {tr: 0 for tr in TIERS}
    for (t0, n, tier, verdict) in ITEMS:
        slot = counts[tier]
        counts[tier] += 1
        ry, h = rows[tier]
        tx = SLOTS[slot] + sx_
        draw_icon(hc, n, tx, ry + h - 40, 42, t)
        draw_spaced(tc, n, tx, ry + h - 14, font(15, "Inter-Bold"), 2, paint(RED if n == "EGO" else WHITE, 0.95))
    ry, h = rows["S"]
    draw_icon(hc, "OBSESSION", (LX1 + X1) / 2 - 150 + sx_, ry + h - 28, 42, t)
    draw_spaced(oc, "OBSESSION", (LX1 + X1) / 2 + 110 + sx_, ry + h * 0.62, font(44, "InterDisplay-Black"), 2, paint(RED, 1.0))
    return rows, sx_


def draw_fusion(v, t, e, f_, tc, hc, oc):
    flash = 0.0
    white = 0.0
    if t < FINAL:
        cam = lane_cam(110, 1350, 0.0)
        if t >= RUN[0]:
            cam.wx = mon_x(t) - (0.0 if t < RUN[1] else 0.0)
        # floor + spotlight
        e.drawLine(80, cam.sy, W - 80, cam.sy, paint(WHITE, 0.5, 2.5))
        if t < RUN[0]:
            sp = skia.Path()
            sp.moveTo(CX - 40, 330)
            sp.lineTo(CX + 40, 330)
            sp.lineTo(CX + 380, cam.sy)
            sp.lineTo(CX - 380, cam.sy)
            sp.close()
            pt = skia.Paint(AntiAlias=True)
            pt.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 330), skia.Point(0, cam.sy)],
                                                        [skia.Color4f(1, 1, 1, 0.0), skia.Color4f(1, 1, 1, 0.09)]))
            e.drawPath(sp, pt)
        if t < MONSTER_T:
            # ego (left) and obsession (right) walk to each other, then merge
            u = smoothstep(ROOM[0] + 0.2, ROOM[1], t)
            xe, xo = -2.4 + 1.9 * u, 2.4 - 1.9 * u
            if t < MERGE[0]:
                je = run_pose(xe, t * 6, 0.3 if u < 1 else 0.0)
                jo = mirror(run_pose(xo, t * 6 + 1, 0.3 if u < 1 else 0.0), xo)
                draw_body(hc, je, cam, RED, 1.0, 0.3)
                draw_body(hc, jo, cam, WHITE, 1.0, 0.3)
                for x, nme, col in ((xe, "EGO", RED), (xo, "OBSESSION", WHITE)):
                    sx, _ = cam.pt((x, 0))
                    draw_spaced(tc, nme, sx, cam.sy + 44, font(26, "Inter-Bold"), 4, paint(col, 1.0))
            else:
                m = (t - MERGE[0]) / (MERGE[1] - MERGE[0])
                ang = 9 * m * m
                rad = 0.5 * (1 - m)
                for k, col in ((0, RED), (1, WHITE)):
                    cx_ = math.cos(ang + k * math.pi) * rad
                    j = stand(0, 0.0, 2.6, 2.4, 0.3, 0.3, -0.2)
                    j = {kk: np.array([cx_ + (vv[0]) * (1 - 0.3 * m), vv[1] * (1 - 0.15 * m)]) for kk, vv in j.items()}
                    draw_body(hc, j, cam, col, 1 - 0.3 * m, 0.3)
                for k in range(26):                      # red / white swirl
                    a = ang * 1.5 + k * 0.6
                    rr = (1.6 - 1.2 * m) + 0.4 * math.sin(k)
                    px, py = cam.pt((math.cos(a) * rr, 1.6 + math.sin(a) * rr * 0.9))
                    f_.drawCircle(px, py, 5 + 3 * (k % 3), paint(RED if k % 2 else WHITE, 0.85))
                white = 0.5 * smoothstep(MERGE[1] - 0.25, MERGE[1], t)
        else:
            x = mon_x(t)
            sc = 1.6
            if t < RUN[0]:
                pop = 1 + 0.15 * math.exp(-(t - MONSTER_T) * 6)
                roar = smoothstep(MONSTER_T + 0.1, MONSTER_T + 0.3, t) * (1 - smoothstep(RUN[0] - 0.3, RUN[0], t))
                j = blend(stand(0), flex(0, t), smoothstep(MONSTER_T + 0.15, MONSTER_T + 0.5, t))
                j = scale_pose(j, 0, sc * pop)
                if roar > 0:
                    j = {kk: vv + [0.02 * math.sin(t * 60), 0] for kk, vv in j.items()}
                caption(oc, "EGO + OBSESSION", 560, smoothstep(MONSTER_T + 0.2, MONSTER_T + 0.4, t), RED, 56)
            elif t < RUN[1]:
                j = scale_pose(run_pose(x, (t - RUN[0]) * 15, 1.0), x, sc)
                for k in range(8):                       # speed lines
                    ly = 500 + 110 * k
                    L = 200 + 120 * math.sin(k * 3.1)
                    lx = (W - ((t * 2600 + k * 337) % (W + 400)))
                    e.drawLine(lx, ly, lx + L, ly, paint(WHITE, 0.18, 2))
                for k in range(-2, 12):                  # ground ticks
                    gx, gy = cam.pt((math.floor(cam.wx / 1.5) * 1.5 + k * 1.5 - 6, 0))
                    e.drawLine(gx, gy + 10, gx - 20, gy + 26, paint(WHITE, 0.2, 2))
                caption(oc, "EGO + OBSESSION", 560, 1.0 - smoothstep(RUN[0] + 0.6, RUN[0] + 0.9, t), RED, 56)
            else:
                lu = smoothstep(LIFT[0] + 0.2, LOCK, t)
                j = scale_pose(stand(x, -0.05, 2.0 + 0.9 * lu, 2.0 + 0.9 * lu, 1.6 - 1.4 * lu, 1.6 - 1.4 * lu, -0.15 - 0.15 * lu), x, sc)
                # giant barbell across the top (stylised front view), bending
                hand = (j["hand1"] + j["hand2"]) / 2
                bx, by = cam.pt(hand + [0, 0.05])
                half = 330
                sag = 30 + 25 * smoothstep(LOCK - 0.1, LOCK + 0.2, t)
                bar = skia.Path()
                bar.moveTo(bx - half, by + sag)
                bar.quadTo(bx, by - sag * 0.6, bx + half, by + sag)
                f_.drawPath(bar, paint(WHITE, 1.0, 9))
                for sgn in (-1, 1):
                    for k in range(3):
                        px = bx + sgn * (half - 18 - 30 * k)
                        r = skia.Rect(px - 15, by + sag - 120 + 16 * k, px + 15, by + sag + 120 - 16 * k)
                        f_.drawRoundRect(r, 6, 6, paint((0, 0, 0), 1.0))
                        f_.drawRoundRect(r, 6, 6, paint(RED if k == 0 else WHITE, 1.0, 5))
                if t >= LOCK:                             # floor cracks
                    cr = smoothstep(LOCK, LOCK + 0.25, t)
                    fx, fy = cam.pt((x, 0))
                    r2 = np.random.default_rng(3)
                    for k in range(7):
                        p = skia.Path()
                        p.moveTo(fx, fy)
                        ang = math.pi * (0.05 + 0.9 * k / 6)
                        px, py = fx, fy
                        for s_ in range(4):
                            px += math.cos(ang + r2.normal(0, 0.3)) * 60 * cr * (1 if k < 4 else -1) * (1 if k % 2 else -1)
                            py += abs(math.sin(ang)) * 14 * cr + r2.uniform(0, 6)
                            p.lineTo(px, py)
                        f_.drawPath(p, paint(RED, 0.95, 4))
                    flash = math.exp(-(t - LOCK) * 4)
            draw_monster(hc, cam, j, t)
            embers.draw(f_, cam, RED, RED)
            white = 0.9 * max(0.0, 1 - (t - MONSTER_T) / 0.25) if t < MONSTER_T + 0.25 else 0.0
        if t < FLASH_T + 0.25:
            white = max(white, 0.9 * (1 - (t - FLASH_T) / 0.25))
        if t >= FINAL - 0.12:
            white = max(white, 0.8 * smoothstep(FINAL - 0.12, FINAL, t))
    else:
        draw_spaced(oc, "MINDSET TIER LIST", CX, 415, font(54, "InterDisplay-Black"), 3, paint(WHITE, 1.0))
        grow = ease_out(clamp((t - FINAL - 0.1) / 0.4))
        shake = 16 * max(0.0, 1 - (t - SPLUS_DROP - FALL) / 0.45) if t >= SPLUS_DROP + FALL else 0.0
        rows, sx_ = draw_grid6(v.env.canvas, f_, tc, hc, oc, t, grow, shake)
        if t >= SPLUS_DROP:
            ry, h = rows["S+"]
            u = clamp((t - SPLUS_DROP) / FALL)
            ty = ry + h - 22
            sy = 300 + (ty - 300) * u * u
            camm = Camera()
            camm.s, camm.sx, camm.sy, camm.wx, camm.wy = 44 * (1.6 - 0.6 * u), (LX1 + X1) / 2 - 170 + sx_, sy, 0.0, 0.0
            draw_monster(hc, camm, flex(0, t), t)
            if t >= UNSTOP:
                a = smoothstep(UNSTOP, UNSTOP + 0.15, t)
                draw_spaced(oc, "EGO + OBSESSION", (LX1 + X1) / 2 + 90 + sx_, ry + h * 0.45,
                            fit_font("EGO + OBSESSION", 34, "InterDisplay-Black", 2, 400), 2, paint(WHITE, a))
                draw_spaced(oc, "UNSTOPPABLE.", (LX1 + X1) / 2 + 90 + sx_, ry + h * 0.85,
                            fit_font("UNSTOPPABLE.", 46, "InterDisplay-Black", 2, 420), 2, paint(RED, a))
            if t >= SPLUS_DROP + FALL:
                flash = math.exp(-(t - SPLUS_DROP - FALL) * 3)
        if t >= END_T:
            caption(oc, "FIGHT ME IN THE COMMENTS.", 1555, smoothstep(END_T, END_T + 0.3, t), RED, 44)
        white = 0.8 * max(0.0, 1 - (t - FINAL) / 0.25) if t < FINAL + 0.25 else 0.0
    v.compose(int(round(t * FPS)), t, flash=flash, white=white, glow=0.4)


def render(stills=None):
    global embers
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    embers = Particles(12)
    for fi in range(v.n):
        t = fi * dt
        for k, (t0, n, tier, verdict) in enumerate(ITEMS):
            if t >= t0:
                log.once(f"in{k}", t0, "whoosh", k)
            if t >= t0 + FALL:
                log.once(f"slam{k}", t0 + FALL, "slam", k)
        if t >= Q_T:
            log.once("q", Q_T, "q")
        if t >= S_T:
            log.once("s", S_T, "s")
        if t >= END_T:
            log.once("end", END_T, "end")
        for key, tt, kind in (("flash", FLASH_T, "flash"), ("merge", MERGE[0], "merge"), ("monster", MONSTER_T, "monster"),
                              ("run", RUN[0], "run"), ("lift", LIFT[0], "lift"), ("lock", LOCK, "lock"),
                              ("final", FINAL, "final"), ("splus", SPLUS_DROP + FALL, "splus"), ("unstop", UNSTOP, "unstop")):
            if t >= tt:
                log.once(key, tt, kind)
        if t >= MERGE[0]:
            embers.step(dt)
            if t < LIFT[1] and t >= MONSTER_T - 0.05:
                embers.emit(np.array([[mon_x(t) + RNG.normal(0, 0.5), RNG.uniform(0.5, 3.8)] for _ in range(3)]),
                            vel=(0, 1.4), spread=0.4, life=(0.5, 1.0), size=(0.02, 0.05))
        if not v.wants(fi):
            continue
        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        if t >= FLASH_T:
            draw_fusion(v, t, e, f_, tc, hc, oc)
            continue
        # title
        draw_spaced(oc, "MINDSET TIER LIST", CX, 415, font(54, "InterDisplay-Black"), 3, paint(WHITE, smoothstep(0, 0.2, t)))
        # grid
        shake = 0.0
        for k, (t0, n, tier, verdict) in enumerate(ITEMS):
            if t0 + FALL <= t < t0 + FALL + 0.2:
                shake = 6 * (1 - (t - t0 - FALL) / 0.2)
        if S_T <= t < S_T + 0.4:
            shake = 14 * (1 - (t - S_T) / 0.4)
        sx_ = shake * math.sin(t * 90)
        for i, tier in enumerate(TIERS):
            y0 = TOP + i * ROW_H
            flash = 0.0
            for (t0, n, tr, verdict) in ITEMS:
                if tr == tier and t0 + FALL <= t < t0 + FALL + 0.35:
                    flash = 1 - (t - t0 - FALL) / 0.35
            if tier == "S" and t >= S_T:
                flash = max(flash, math.exp(-(t - S_T) * 3))
            e.drawRect(skia.Rect(LX0 + sx_, y0, X1 + sx_, y0 + ROW_H - 8), paint(WHITE, 0.3, 2, cap=False))
            if flash > 0:
                f_.drawRect(skia.Rect(LX1 + sx_, y0, X1 + sx_, y0 + ROW_H - 8), paint(RED if tier == "S" else WHITE, 0.12 * flash))
            box = skia.Rect(LX0 + sx_, y0, LX1 + sx_, y0 + ROW_H - 8)
            if tier == "S":
                f_.drawRect(box, paint(RED, 0.9))
                draw_spaced(oc, tier, (LX0 + LX1) / 2 + sx_, y0 + ROW_H * 0.66, font(110, "InterDisplay-Black"), 0, paint((0, 0, 0), 1.0))
            else:
                e.drawRect(box, paint(WHITE, 0.9, 3, cap=False))
                draw_spaced(tc, tier, (LX0 + LX1) / 2 + sx_, y0 + ROW_H * 0.66, font(110, "InterDisplay-Black"), 0, paint(WHITE, 1.0))
        # placed + falling items
        counts = {tr: 0 for tr in TIERS}
        for k, (t0, n, tier, verdict) in enumerate(ITEMS):
            if t < t0:
                continue
            slot = counts[tier]
            counts[tier] += 1
            tx = SLOTS[slot] + sx_
            ty = row_y(tier) + ROW_H - 46
            u = clamp((t - t0) / FALL)
            if u < 1:
                sy = 300 + (ty - 300) * u * u
                s_ = 50 * (1.8 - 0.8 * u)
            else:
                bounce = math.exp(-(t - t0 - FALL) * 10) * math.sin((t - t0 - FALL) * 30) * 6
                sy, s_ = ty - abs(bounce), 50
            draw_icon(hc, n, tx, sy, s_, t)
            if u >= 1:
                draw_spaced(tc, n, tx, ty + 30, font(17, "Inter-Bold"), 2, paint(RED if n == "EGO" else WHITE, 0.95))
        # verdict captions (shown in the empty S row until the end)
        for k, (t0, n, tier, verdict) in enumerate(ITEMS):
            if t0 + FALL <= t < (ITEMS[k + 1][0] if k + 1 < len(ITEMS) else Q_T):
                a = smoothstep(t0 + FALL, t0 + FALL + 0.1, t)
                from engine import fit_font
                rx = (LX1 + X1) / 2
                draw_spaced(oc, n + ":", rx, 545, fit_font(n + ":", 40, "InterDisplay-Black", 2, 640), 2, paint(RED if n == "EGO" else WHITE, a))
                draw_spaced(oc, verdict, rx, 610, fit_font(verdict, 36, "InterDisplay-Black", 2, 640), 2, paint(WHITE, a))
        # the S slot
        sy0 = row_y("S")
        if Q_T <= t < S_T:
            pulse = 1 + 0.12 * math.sin((t - Q_T) * (8 + 10 * (t - Q_T)))
            draw_spaced(oc, "?", (LX1 + X1) / 2, sy0 + ROW_H * 0.7, font(150 * pulse, "InterDisplay-Black"), 0, paint(RED, 1.0))
        if t >= S_T:
            u = clamp((t - S_T + FALL) / FALL)
            tx = (LX1 + X1) / 2 + sx_
            ty = sy0 + ROW_H - 30
            s_ = 50 * (1 + 0.25 * math.exp(-(t - S_T) * 8))
            draw_icon(hc, "OBSESSION", tx - 150, ty, s_, t)
            draw_spaced(oc, "OBSESSION", tx + 110, sy0 + ROW_H * 0.6, font(52, "InterDisplay-Black"), 2, paint(RED, smoothstep(S_T, S_T + 0.15, t)))
        if t >= END_T:
            oc.drawRect(skia.Rect(0, 1530, W, 1530), paint(WHITE, 0))
            caption(oc, "FIGHT ME IN THE COMMENTS.", 1600 - 60, smoothstep(END_T, END_T + 0.3, t), RED, 44)
        flash = math.exp(-(t - S_T) * 3) if t >= S_T else 0.0
        v.compose(fi, t, flash=flash * 0.8)
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=MONSTER_T), gain=0.35, fade_in=0.4, fade_out=2.0, stop=DUR)
    m.add(0.05, sfx.text_hit(5), 0.7, 0, 0.4)
    for t, kind, _, extra in events:
        if kind == "whoosh":
            m.add(t, sfx.whoosh(0.35, 500, 9000, 0.8, seed=extra), 0.5, 0, 0.2)
        elif kind == "slam":
            m.add(t, sfx.punch_hit(extra, 1.2), 0.8, 0, 0.3)
            m.add(t, sfx.boom(1.2) * 0.6, 0.5, 0, 0.3)
            if extra >= 4:
                m.add(t + 0.1, sfx.glitch(extra), 0.4, 0, 0.2)
        elif kind == "q":
            tt = 0.0
            k = 0
            while tt < S_T - Q_T - 0.05:      # drumroll speeding up
                m.add(Q_T + tt, sfx.tick(1200 + 40 * k, 0.6), 0.5, 0.2 * ((-1) ** k), 0.1)
                m.add(Q_T + tt, sfx.step_heavy(k) * 0.5, 0.3, 0, 0.1)
                tt += max(0.045, 0.22 - 0.1 * tt)
                k += 1
            m.add(Q_T, sfx.riser(S_T - Q_T), 0.6, 0, 0.3)
        elif kind == "s":
            m.add(t, sfx.boom(4.0), 1.0, 0, 0.5)
            m.add(t, sfx.punch_hit(77, 2.0), 0.9, 0, 0.4)
            m.add(t, sfx.sparkle(1.6), 0.5, 0, 0.6)
        elif kind == "flash":
            m.add(t, sfx.whoosh(0.4, 300, 9000, 0.4, seed=4), 0.7, 0, 0.3)
            m.add(t, sfx.spot_on(), 0.7, 0, 0.4)
            for k in range(4):
                m.add(t + 0.3 + k * 0.25, sfx.step_heavy(k), 0.35, -0.3 + 0.2 * k, 0.2)
        elif kind == "merge":
            m.add(t, sfx.riser(MERGE[1] - MERGE[0]), 0.7, 0, 0.3)
            m.add(t, sfx.whoosh(MERGE[1] - MERGE[0], 150, 6000, 0.9, seed=6), 0.7, 0, 0.3)
            m.add(t, sfx.power_up(55), 0.8, 0, 0.4)
        elif kind == "monster":
            m.add(t, sfx.boom(4.0), 1.0, 0, 0.5)
            m.add(t, sfx.thunder(3), 0.6, 0, 0.3)
            m.add(t + 0.1, sfx.power_down(1.2) * 0.8, 0.6, 0, 0.4)
        elif kind == "run":
            for k in range(10):
                m.add(t + k * 0.15, sfx.step_heavy(k), 0.7, 0, 0.2)
            m.add(t, sfx.whoosh(1.5, 200, 7000, 0.5, seed=9), 0.5, 0, 0.3)
        elif kind == "lift":
            m.add(t + 0.2, sfx.rattle(0.8, 4), 0.6, 0, 0.2)
            m.add(t + 0.1, sfx.breath(9, 0.6), 0.6, 0, 0.2)
        elif kind == "lock":
            m.add(t, sfx.boom(3.5), 1.0, 0, 0.5)
            m.add(t, sfx.shatter(2, 1.5), 0.7, 0, 0.4)
            m.add(t, sfx.plate_clank(9, 2.0), 0.7, 0, 0.4)
        elif kind == "final":
            m.add(t, sfx.whoosh(0.4, 300, 9000, 0.4, seed=10), 0.6, 0, 0.3)
            m.add(t + 0.1, sfx.riser(0.5), 0.5, 0, 0.3)
        elif kind == "splus":
            m.add(t, sfx.boom(4.0), 1.0, 0, 0.5)
            m.add(t, sfx.punch_hit(78, 2.2), 1.0, 0, 0.4)
        elif kind == "unstop":
            m.add(t, sfx.text_hit(2), 0.8, 0, 0.4)
        elif kind == "end":
            m.add(t, sfx.text_hit(3), 0.8, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [14.6, 15.6, 16.6, 17.3, 18.6, 19.9, 20.5, 21.4, 22.4, 24.0]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
