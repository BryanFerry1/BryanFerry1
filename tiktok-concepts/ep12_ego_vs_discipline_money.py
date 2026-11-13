"""EP12 - EGO VS DISCIPLINE  (the money)

Visual hook: red banknotes rain down on two figures; both catch the same stack.
EGO      buys a car, a watch, throws a party: hearts / likes everywhere.
         His curve on the chart shoots up... then crashes. Car breaks, watch
         gone, hearts fall. $0 in red.
DISCIPLINE drops a coin in a box every year, a small tree grows next to him.
         His curve crawls, then explodes. A car rolls in behind him. Arms crossed.
PUNCH    EGO BUYS ATTENTION. / DISCIPLINE BUYS / FREEDOM.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import FPS, RED, WHITE, W, clamp, draw_spaced, ease_out, font, mix, paint, smoothstep
from kit import (CX, GREY, Log, Shards, Video, blend, crossed, draw_body, draw_car, draw_heart,
                 draw_phone_small, flex, hud, label, lane_cam, mirror, phone_pose, punch, sad, stand,
                 title)
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep12_ego_vs_discipline_money"
dt = 1 / FPS
S = 100.0
GROUND = 1345.0
EX, DX = -1.15, 1.25
RAIN = (0.0, 2.7)
START = 2.8
CAR_T, WATCH_T, PARTY_T = 3.4, 4.9, 6.2
CRASH = 9.6
END_CHART = 12.6
CAR2 = 12.0
P1, P2, P3 = 14.2, 15.1, 15.6
DUR = P3 + 3.0


def year_of(t):
    if t < START:
        return 1
    return min(10, 1 + int(9 * clamp((t - START) / (END_CHART - START))))


def ego_curve(u):
    rise = 0.78 * smoothstep(0.0, 0.35, u)
    wob = 0.04 * math.sin(u * 30) * smoothstep(0.3, 0.45, u)
    crash = 0.75 * smoothstep(0.62, 0.72, u)
    return 0.05 + rise + wob - crash


def disc_curve(u):
    return 0.05 + 0.18 * u + 0.75 * u ** 5


def money_e(t):
    m = 100
    for tt, cost in ((CAR_T, 45), (WATCH_T, 25), (PARTY_T, 25)):
        if t >= tt:
            m -= cost
    if t >= CRASH:
        m = 0
    return m


def money_d(t):
    u = clamp((t - START) / (END_CHART - START))
    return 100 + 2300 * u ** 4


def fmt(k):
    return f"${k / 1000:.1f}M" if k >= 1000 else f"${int(k)}K"


def tree(c, cam, base, ang, length, depth, grow, fruits, t):
    if depth == 0 or grow <= 0:
        return
    L = length * min(1.0, grow * 1.6)
    end = base + np.array([math.sin(ang), math.cos(ang)]) * L
    c.drawLine(*cam.pt(base), *cam.pt(end), paint(WHITE, 0.85, max(1.5, 0.05 * cam.s * depth / 5)))
    nxt = grow - 0.2
    if nxt <= 0:
        if fruits > 0:
            c.drawCircle(*cam.pt(end), 0.08 * cam.s * fruits, paint(RED, fruits))
        else:
            c.drawCircle(*cam.pt(end), 0.05 * cam.s, paint(WHITE, 0.8))
        return
    for da in (-0.45, 0.4):
        tree(c, cam, end, ang + da + 0.04 * math.sin(t * 1.5 + depth), length * 0.72, depth - 1, nxt, fruits, t)


def draw_bill(c, x, y, ang, s, alpha):
    c.save()
    c.translate(x, y)
    c.rotate(math.degrees(ang))
    r = skia.Rect(-s, -s * 0.5, s, s * 0.5)
    c.drawRect(r, paint((0, 0, 0), 1.0))
    c.drawRect(r, paint(RED, alpha, 3, cap=False))
    c.drawCircle(0, 0, s * 0.28, paint(RED, alpha, 2))
    c.restore()


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    shards = Shards(5)
    rng = np.random.default_rng(2)
    bills = [(rng.uniform(80, 880), rng.uniform(-1600, 0), rng.uniform(0, 6), rng.uniform(22, 34), rng.uniform(550, 900)) for _ in range(85)]
    hearts = []
    for fi in range(v.n):
        t = fi * dt
        u = clamp((t - START) / (END_CHART - START))
        yr = year_of(t)
        # events
        if t >= 0.1:
            log.once("rain", t, "rain")
        if t >= START - 0.1:
            log.once("catch", t, "catch")
        for name, tt in (("car", CAR_T), ("watch", WATCH_T), ("party", PARTY_T)):
            if t >= tt:
                log.once(name, t, name)
        if PARTY_T <= t < CRASH and rng.random() < 0.25:
            hearts.append((t, EX + rng.uniform(-1.4, 1.4), rng.uniform(3.0, 3.8)))
        if t >= CRASH:
            log.once("crash", t, "crash")
            if "carshards" not in log.seen:
                log.seen.add("carshards")
                shards.burst(-3.7, -1.5, 0.2, 1.3, 60, vx=(-3, 3), vy=(0, 4))
        if START <= t < END_CHART:
            k = int((t - START) / ((END_CHART - START) / 9))
            log.once(f"coin{k}", t, "coin", k)
        if t >= CAR2:
            log.once("car2", t, "car2")
        shards.step(dt)
        if not v.wants(fi):
            continue
        v.clear()
        e, f_, tc, hc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas
        cam = lane_cam(S, GROUND)
        e.drawLine(80, GROUND, W - 80, GROUND, paint(WHITE, 0.5, 2.5))

        # money rain (hook)
        if t < RAIN[1] + 0.4:
            ra = 1 - smoothstep(RAIN[1], RAIN[1] + 0.4, t)
            for x, y0, ang, sz, sp in bills:
                y = y0 + t * sp
                if 250 < y < GROUND:
                    draw_bill(f_, x + 30 * math.sin(t * 2 + ang), y, ang + t * 2.0, sz, ra)

        # chart
        ca = smoothstep(START, START + 0.5, t) * (1 - smoothstep(P1 - 0.5, P1 - 0.1, t))
        if ca > 0.01:
            x0, x1, y0, y1 = 120, 860, 880, 560
            e.drawLine(x0, y0, x1, y0, paint(WHITE, 0.4 * ca, 2))
            e.drawLine(x0, y0, x0, y1, paint(WHITE, 0.4 * ca, 2))
            for curve, col, name in ((ego_curve, RED, "EGO"), (disc_curve, WHITE, "DISCIPLINE")):
                p = skia.Path()
                n = max(2, int(80 * u))
                for k in range(n + 1):
                    uu = u * k / n
                    px, py = x0 + (x1 - x0) * uu, y0 - (y0 - y1) * clamp(curve(uu), 0, 1.05)
                    (p.moveTo if k == 0 else p.lineTo)(px, py)
                f_.drawPath(p, paint(col, ca, 5))
                if u > 0.02:
                    px, py = x0 + (x1 - x0) * u, y0 - (y0 - y1) * clamp(curve(u), 0, 1.05)
                    f_.drawCircle(px, py, 8, paint(col, ca))
                    draw_spaced(tc, name, min(px, 800) - 10, py - 18, font(20, "Inter-Bold"), 4, paint(col, ca * 0.9))

        # ---------------- EGO side
        if t < CAR_T:
            je = stand(EX, 0.0, 0.9, 0.2, 0.9, 0.2, 0.05)
        elif t < PARTY_T:
            je = blend(stand(EX), flex(EX, t), smoothstep(CAR_T, CAR_T + 0.4, t))
        elif t < CRASH:
            je = phone_pose(EX, t)
            je = {k: vv + [0, 0.04 * abs(math.sin(t * 9))] for k, vv in je.items()}
        else:
            je = sad(EX, t)
        ecol = mix(WHITE, RED, 0.3 * smoothstep(CAR_T, CRASH, t) + 0.5 * smoothstep(CRASH, CRASH + 0.5, t))
        # car
        if CAR_T <= t < CRASH:
            ci = ease_out((t - CAR_T) / 0.5)
            draw_car(e, cam, -3.75 - 2.5 * (1 - ci), 0.9, WHITE, 0.6)
        shards.draw(f_, cam, RED)
        draw_body(hc, je, cam, ecol, 1.0)
        if WATCH_T <= t < CRASH + 0.1:
            wx, wy = cam.pt(je["hand1"] + [-0.08, 0.12])
            f_.drawCircle(wx, wy, 7, paint(WHITE, 1.0, 3))
            if t - WATCH_T < 0.6:
                a = 1 - (t - WATCH_T) / 0.6
                for k in range(4):
                    ang = k * math.pi / 2 + t * 3
                    f_.drawLine(wx, wy, wx + math.cos(ang) * 30 * a, wy + math.sin(ang) * 30 * a, paint(WHITE, a, 3))
        if PARTY_T <= t < CRASH:
            draw_phone_small(f_, cam, je["hand1"] + [0.05, 0.1], 1.0)
        for ht, hx_, hy_ in hearts:
            age = t - ht
            if 0 <= age < 1.0:
                sx, sy = cam.pt((hx_, hy_ + age * 0.7))
                draw_heart(f_, sx, sy, 16, (1 - age) * (1 if t < CRASH else 0.4), RED if t < CRASH else GREY)
        # money stacks + counters
        if t >= START - 0.1:
            me = money_e(t)
            hx, hy = cam.pt(je["head"] + [0, 0.75])
            draw_spaced(tc, fmt(me), hx, hy, font(30, "InterDisplay-Bold"), 2, paint(RED if me <= 30 else WHITE, 0.95))
        label(tc, cam, EX, "EGO", smoothstep(2.4, 2.8, t) * (1 - smoothstep(P1 - 0.5, P1, t)), RED, 46, 26)

        # ---------------- DISCIPLINE side
        k = int((t - START) / ((END_CHART - START) / 9)) if t >= START else -1
        uk = ((t - START) % ((END_CHART - START) / 9)) / ((END_CHART - START) / 9) if t >= START else 0.0
        drop = math.sin(math.pi * clamp(uk / 0.35)) if START <= t < END_CHART else 0.0
        jd = stand(DX, 0.05 * drop, 0.15 + 1.1 * drop, 0.1, 0.2, 0.15, 0.1 * drop)
        if t >= END_CHART:
            jd = blend(jd, crossed(DX), smoothstep(END_CHART, END_CHART + 0.5, t))
        # box + coin
        bx0, by0 = cam.pt((DX + 0.55, 0.55))
        bx1, by1 = cam.pt((DX + 1.15, 0.0))
        e.drawRect(skia.Rect(bx0, by0, bx1, by1), paint(WHITE, 0.75, 3, cap=False))
        e.drawLine(bx0 + 15, by0, bx1 - 15, by0, paint((0, 0, 0), 1.0, 4))
        if 0 < uk < 0.6 and START <= t < END_CHART:
            cy = 1.4 - 1.1 * clamp((uk - 0.15) / 0.4)
            f_.drawCircle(*cam.pt((DX + 0.85, cy)), 0.11 * S, paint(WHITE, 1.0, 3))
        # tree (compounding)
        grow = smoothstep(START, END_CHART, t)
        fruits = smoothstep(END_CHART - 1.5, END_CHART, t)
        tree(e, cam, np.array([DX + 1.95, 0.0]), 0.0, 1.0, 6, grow * 1.25, fruits, t)
        # car rolling in behind him
        if t >= CAR2:
            bc = lane_cam(S * 0.7, GROUND - 90)
            ci = ease_out((t - CAR2) / 0.8)
            draw_car(e, bc, 0.6 + 4.0 * (1 - ci), 0.8, WHITE, 0.9)
            e.drawLine(80, bc.sy, W - 80, bc.sy, paint(WHITE, 0.12, 1.5))
        draw_body(hc, jd, cam, WHITE, 1.0)
        if t >= START - 0.1:
            md = money_d(t)
            hx, hy = cam.pt(jd["head"] + [0, 0.75])
            draw_spaced(tc, fmt(md), hx, hy, font(30, "InterDisplay-Bold"), 2, paint(WHITE, 0.95))
        label(tc, cam, DX, "DISCIPLINE", smoothstep(2.4, 2.8, t) * (1 - smoothstep(P1 - 0.5, P1, t)), WHITE, 46, 26)

        hud(tc, "YEAR", yr, smoothstep(START - 0.2, START + 0.2, t) * (1 - 0.6 * smoothstep(P1 - 0.3, P1 + 0.3, t)), yr >= 10)
        title(tc, t, [([("EGO", RED)], 170, 80), ([("VS", WHITE)], 48, 130), ([("DISCIPLINE", WHITE)], 130, 0)], y0=600)
        punch(tc, t, [(P1, [("EGO", RED), (" BUYS ATTENTION.", WHITE)], 620, 58),
                      (P2, [("DISCIPLINE BUYS", WHITE)], 730, 74),
                      (P3, [("FREEDOM.", WHITE)], 880, 150)])
        tdim = 0.55 * smoothstep(0.1, 0.35, t) * (1 - smoothstep(2.4, 2.8, t))
        pdim = 0.6 * smoothstep(P1 - 0.3, P1, t)
        flash = max(math.exp(-(t - CRASH) * 4) * 0.6 if t >= CRASH else 0.0,
                    math.exp(-(t - CAR2 - 0.8) * 3) * 0.6 if t >= CAR2 + 0.8 else 0.0)
        v.compose(fi, t, flash=flash, dim=max(tdim, pdim))
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=CAR2), gain=0.42, fade_in=0.6, fade_out=2.5, stop=DUR)
    m.add(0.1, sfx.text_hit(5), 0.8, 0, 0.4)
    for t, kind, _, extra in events:
        if kind == "rain":
            r = np.random.default_rng(1)
            for k in range(26):
                m.add(t + r.uniform(0, 2.4), sfx.whoosh(0.25, 2000, 9000, 0.5, seed=k) * 0.5, 0.25, r.uniform(-0.6, 0.6), 0.2)
        elif kind == "catch":
            m.add(t, sfx.plate_clank(3, 0.3) * 0.4, 0.4, 0, 0.3)
            m.add(t, sfx.chime(990, 0.3), 0.5, 0, 0.4)
        elif kind == "car":
            m.add(t, sfx.whoosh(0.6, 100, 3000, 0.7, seed=5), 0.7, -0.5, 0.3)
            m.add(t + 0.45, sfx.boom(1.2) * 0.5, 0.5, -0.5, 0.3)
            m.add(t + 0.2, sfx.tick(800, 0.4), 0.5, -0.5, 0.1)
        elif kind == "watch":
            m.add(t, sfx.sparkle(0.8, 60, 2), 0.6, -0.3, 0.4)
        elif kind == "party":
            for k in range(26):
                m.add(t + k * 0.13, sfx.step_heavy(k) * 0.8, 0.45 if k % 2 == 0 else 0.25, -0.3, 0.1)
            for k in range(8):
                m.add(t + 0.2 + k * 0.4, sfx.shutter(k), 0.35, -0.4, 0.2)
        elif kind == "crash":
            m.add(t, sfx.shatter(2, 1.5), 0.9, -0.4, 0.4)
            m.add(t, sfx.power_down(2.2), 0.6, -0.3, 0.4)
            m.add(t, sfx.boom(2.5), 0.6, 0, 0.4)
        elif kind == "coin":
            m.add(t + 0.35, sfx.chime(1300 + 60 * extra, 0.25), 0.4, 0.3, 0.3)
            m.add(t + 0.35, sfx.tick(3500, 0.3), 0.4, 0.3, 0.1)
        elif kind == "car2":
            m.add(t, sfx.whoosh(0.9, 100, 3000, 0.7, seed=9), 0.6, 0.5, 0.3)
            m.add(t + 0.8, sfx.boom(3.5), 0.9, 0, 0.5)
            m.add(t + 0.8, sfx.sparkle(1.5), 0.5, 0.4, 0.5)
    m.add(CAR2 - 1.8, sfx.riser(2.6), 0.45, 0, 0.3)
    m.add(P1, sfx.text_hit(1), 0.55, 0, 0.4)
    m.add(P2, sfx.text_hit(2), 0.65, 0, 0.4)
    m.add(P3, sfx.text_hit(3), 0.95, 0, 0.5)
    m.add(P3, sfx.boom(2.0), 0.45, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [1.2, 3.1, 4.2, 5.4, 7.5, 9.0, 10.0, 11.6, 13.0, P3 + 1.0]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
