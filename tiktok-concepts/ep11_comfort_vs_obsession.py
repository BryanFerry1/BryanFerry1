"""EP11 - COMFORT VS OBSESSION  (the couch)

Visual hook: a big clock at the top whose hands start spinning faster and
faster. 5:00 AM alarm.
LEFT   COMFORT sits on his couch with his phone. Every year the couch swallows
       him a bit more, until only a hand holding a glowing phone sticks out.
RIGHT  OBSESSION runs, lifts, works at his desk, over and over; he grows.
YEAR 1 -> 10, then the couch spits COMFORT out: old, grey, belly, cane.
OBSESSION stands tall, a red crown appears above him.
PUNCH  COMFORT IS / A SLOW / DEATH.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import FPS, RED, WHITE, W, clamp, ease_out, mix, paint, run_pose, smoothstep, draw_spaced, font
from kit import (CX, GREY, Log, Video, blend, body_scale, crossed, curl, draw_body, draw_cane,
                 draw_crown, draw_phone_small, hud, label, lane_cam, old_pose, punch, scale_pose,
                 sit, stand, title)
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep11_comfort_vs_obsession"
dt = 1 / FPS
S = 108.0
GROUND = 1330.0
CXW = -2.15            # comfort x (world)
OXW = 2.05             # obsession x
ALARM = 2.7
MONT = (3.2, 14.2)
ACT = 1.05
OUT_T = 14.6
CROWN = OUT_T + 0.6
P1, P2, P3 = OUT_T + 2.0, OUT_T + 2.8, OUT_T + 3.3
DUR = P3 + 3.0


def year_of(t):
    if t < MONT[0]:
        return 1
    return min(10, 1 + int(9 * clamp((t - MONT[0]) / (MONT[1] - MONT[0]))))


def draw_clock(c, cx, cy, r, t, spin, shake):
    cx += shake * 6 * math.sin(t * 80)
    c.drawCircle(cx, cy, r, paint(WHITE, 0.9, 5))
    for k in range(12):
        a = k * math.pi / 6
        r0 = r * (0.82 if k % 3 else 0.72)
        c.drawLine(cx + math.sin(a) * r0, cy - math.cos(a) * r0, cx + math.sin(a) * r * 0.92, cy - math.cos(a) * r * 0.92,
                   paint(WHITE, 0.7, 3 if k % 3 else 5))
    hm = spin * 12.0 + math.pi * 0.0
    hh = spin + math.pi * 5 / 6
    c.drawLine(cx, cy, cx + math.sin(hh) * r * 0.5, cy - math.cos(hh) * r * 0.5, paint(WHITE, 1.0, 7))
    c.drawLine(cx, cy, cx + math.sin(hm) * r * 0.78, cy - math.cos(hm) * r * 0.78, paint(RED, 1.0, 4))
    c.drawCircle(cx, cy, 7, paint(RED, 1.0))
    for sgn in (-1, 1):          # alarm bells
        bx, by = cx + sgn * r * 0.75, cy - r * 0.95
        c.drawCircle(bx, by, r * 0.22, paint(WHITE, 0.85, 4))


def couch(c, cam, x, swallow, alpha=1.0):
    """Side-view couch (back on the left). swallow 0..1 raises the cushions
    over whoever sits there."""
    col = WHITE
    top = 0.78 + 1.9 * swallow
    p = skia.Path()
    pts = [(x - 1.25, 0.12), (x - 1.25, 1.75 + 0.9 * swallow), (x - 0.85, 1.85 + 0.9 * swallow),
           (x - 0.6, top + 0.2 * swallow), (x + 0.3, top + 0.35 * swallow), (x + 1.05, top),
           (x + 1.25, 1.1 + 1.3 * swallow), (x + 1.35, 0.12)]
    p.moveTo(*cam.pt(pts[0]))
    for q in pts[1:]:
        p.lineTo(*cam.pt(q))
    p.close()
    c.drawPath(p, paint((0, 0, 0), 1.0))
    c.drawPath(p, paint(col, 0.85 * alpha, 4))
    for lx in (x - 1.1, x + 1.2):
        c.drawLine(*cam.pt((lx, 0.12)), *cam.pt((lx, 0.0)), paint(col, 0.7 * alpha, 4))
    # cushion seams
    c.drawLine(*cam.pt((x - 0.6, top + 0.2 * swallow)), *cam.pt((x - 0.55, 0.4)), paint(col, 0.35 * alpha, 2))
    c.drawLine(*cam.pt((x + 0.35, top + 0.35 * swallow)), *cam.pt((x + 0.4, 0.4)), paint(col, 0.35 * alpha, 2))


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    ph = 0.0
    for fi in range(v.n):
        t = fi * dt
        yr = year_of(t)
        u = clamp((t - MONT[0]) / (MONT[1] - MONT[0]))
        g = u if t < OUT_T else 1.0
        if t >= ALARM:
            log.once("alarm", t, "alarm")
        if t >= MONT[0]:
            log.once("mont", t, "mont")
        if MONT[0] <= t < MONT[1]:
            k = int((t - MONT[0]) / ACT)
            log.once(f"act{k}", t, "act", k)
        if t >= OUT_T:
            log.once("out", t, "out")
        if t >= CROWN:
            log.once("crown", t, "crown")
        if not v.wants(fi):
            continue
        v.clear()
        e, f_, tc, hc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas
        cam = lane_cam(S, GROUND)
        e.drawLine(80, GROUND, W - 80, GROUND, paint(WHITE, 0.5, 2.5))
        e.drawLine(CX, 770, CX, GROUND - 10, paint(WHITE, 0.14, 2))
        # clock (hook) - spins faster and faster
        spin_speed = 0.0 if t < ALARM else 0.6 + 6.0 * smoothstep(MONT[0], MONT[0] + 3, t) * (1 - smoothstep(MONT[1] - 0.6, MONT[1], t))
        spin = 0.0
        # integrate analytically enough: use cumulative approx
        spin = 0.6 * max(0, t - ALARM) + 6.0 * max(0, min(t, MONT[1]) - (MONT[0] + 1.5)) if t > ALARM else 0.0
        shake = 1.0 if ALARM <= t < ALARM + 0.6 else 0.0
        if 2.3 < t < P1 - 0.2:
            draw_clock(f_, CX, 660, 82, t, spin, shake)

        # ---------- COMFORT
        swallow = smoothstep(MONT[0], MONT[1], t) * (1 - smoothstep(OUT_T, OUT_T + 0.5, t))
        fat = u
        ccol = mix(WHITE, GREY, 0.8 * u)
        if t < OUT_T:
            jc = sit(CXW - 0.35, 0.78, t, 0.3 + 0.4 * u)
            jc["hand1"] = jc["shoulder"] + np.array([0.55, 0.15])
            draw_body(hc, jc, cam, ccol, 1.0, 0.0, fat)
            couch(hc, cam, CXW, swallow)
            # hand + phone sticking out
            hand = jc["hand1"] + [0, 0.25 + 1.5 * swallow]
            hx, hy = cam.pt(hand)
            hc.drawLine(*cam.pt(hand + [0, -0.5]), hx, hy, paint(ccol, 1.0, 0.12 * S))
            draw_phone_small(f_, cam, hand + [0.05, 0.22], 1.0)
            # phone light on the face / couch
            f_.drawCircle(*cam.pt(hand + [0.05, 0.22]), 0.6 * S, paint(WHITE, 0.05))
        else:
            w = smoothstep(OUT_T, OUT_T + 0.8, t)
            jo_ = old_pose(CXW + 1.6 * w)
            couch(e, cam, CXW, swallow, 0.6)
            draw_body(hc, jo_, cam, GREY, 0.85, 0.0, 1.0)
            draw_cane(hc, cam, jo_, 0.85)
        label(tc, cam, CXW, "COMFORT", smoothstep(2.4, 2.8, t) * (1 - smoothstep(P1 - 0.5, P1, t)), RED, 46, 26)

        # ---------- OBSESSION
        if t < ALARM:
            jo = stand(OXW)
        elif t < MONT[0]:
            jo = stand(OXW, 0.0, 0.3, 0.2, 0.2, 0.2, -0.1, 0.05 * math.sin(t * 20))
        elif t < MONT[1]:
            k = int((t - MONT[0]) / ACT) % 3
            uu = ((t - MONT[0]) % ACT) / ACT
            if k == 0:
                ph += 2 * math.pi * 3.0 * dt
                jo = run_pose(OXW, ph, 1.0)
                for kk in range(5):
                    sx, sy = cam.pt((OXW - 0.7, 0.4 + kk * 0.5))
                    L = 50 + 30 * math.sin(t * 9 + kk)
                    e.drawLine(sx - L, sy, sx, sy, paint(WHITE, 0.2, 2))
            elif k == 1:
                jo = curl(OXW, math.sin(math.pi * (uu * 2 % 1)))
            else:
                jo = sit(OXW - 0.3, 0.75, t, 0.2)
                tap = 0.04 * math.sin(t * 40)
                jo["hand1"] = jo["hand1"] + [0.15, 0.1 + tap]
                jo["hand2"] = jo["hand2"] + [0.12, 0.1 - tap]
                dx0, dy0 = cam.pt((OXW + 0.35, 1.05))
                dx1, _ = cam.pt((OXW + 1.25, 1.05))
                e.drawLine(dx0, dy0, dx1, dy0, paint(WHITE, 0.7, 4))
                e.drawLine(*cam.pt((OXW + 1.15, 1.05)), *cam.pt((OXW + 1.15, 0)), paint(WHITE, 0.6, 3))
                lx, ly = cam.pt((OXW + 0.55, 1.05))
                e.drawLine(lx, ly - 2, lx + 0.4 * S, ly - 0.35 * S, paint(WHITE, 0.9, 4))
                f_.drawCircle(lx + 0.2 * S, ly - 0.2 * S, 0.45 * S, paint(WHITE, 0.06))
        else:
            jo = blend(stand(OXW), crossed(OXW), smoothstep(OUT_T, OUT_T + 0.5, t))
        sc = body_scale(g)
        jo = scale_pose(jo, OXW, sc)
        draw_body(hc, jo, cam, WHITE, 1.0, g)
        if MONT[0] <= t < MONT[1] and int((t - MONT[0]) / ACT) % 3 == 1:
            bar = (jo["hand1"] + jo["hand2"]) / 2
            for kk, rr in enumerate([0.12] + [0.2] * int(g * 3)):
                cx, cy = cam.pt(bar + np.array([0.06, -0.04]) * kk)
                hc.drawCircle(cx, cy, rr * S, paint((0, 0, 0), 1.0))
                hc.drawCircle(cx, cy, rr * S, paint(WHITE, 0.95, 3))
        label(tc, cam, OXW, "OBSESSION", smoothstep(2.4, 2.8, t) * (1 - smoothstep(P1 - 0.5, P1, t)), WHITE, 46, 26)
        if t >= CROWN:
            hx, hy = cam.pt(jo["head"] + [0, 0.85])
            pop = 1 + 0.5 * math.exp(-(t - CROWN) * 8)
            draw_crown(f_, hx, hy + 4 * math.sin(t * 3), 70 * pop, smoothstep(CROWN, CROWN + 0.15, t))

        hud(tc, "YEAR", yr, smoothstep(2.7, 3.1, t) * (1 - 0.6 * smoothstep(P1 - 0.3, P1 + 0.3, t)), yr >= 10)
        title(tc, t, [([("COMFORT", RED)], 140, 80), ([("VS", WHITE)], 48, 130), ([("OBSESSION", WHITE)], 130, 0)], y0=600)
        punch(tc, t, [(P1, [("COMFORT", RED), (" IS", WHITE)], 600, 70),
                      (P2, [("A SLOW", WHITE)], 720, 90),
                      (P3, [("DEATH.", RED)], 880, 160)])
        tdim = 0.65 * smoothstep(0.1, 0.35, t) * (1 - smoothstep(2.4, 2.8, t))
        pdim = 0.6 * smoothstep(P1 - 0.3, P1, t)
        flash = math.exp(-(t - CROWN) * 3) if t >= CROWN else 0.0
        v.compose(fi, t, flash=flash, glow=0.3 * g, dim=max(tdim, pdim))
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=CROWN), gain=0.42, fade_in=0.6, fade_out=2.5, stop=DUR)
    m.add(0.1, sfx.text_hit(5), 0.8, 0, 0.4)
    # ticking clock all along, accelerating
    tt_ = 0.4
    while tt_ < OUT_T:
        m.add(tt_, sfx.tick(3200 if int(tt_ * 10) % 2 else 2600, 0.3), 0.4, 0, 0.1)
        sp = 0.5 if tt_ < MONT[0] else max(0.09, 0.5 - 0.4 * (tt_ - MONT[0]) / 3)
        if tt_ > MONT[1] - 0.6:
            sp = 0.5
        tt_ += sp
    for t, kind, _, extra in events:
        if kind == "alarm":
            for k in range(8):
                m.add(t + k * 0.07, sfx.bell(1500 + 300 * (k % 2), 0.25) * 0.6, 0.5, 0, 0.2)
        elif kind == "mont":
            m.add(t - 0.2, sfx.whoosh(0.5, 300, 6000, 0.6, seed=3), 0.5, 0, 0.3)
        elif kind == "act":
            m.add(t, sfx.chime(330 * 2 ** (extra * 1.2 / 12), 0.22), 0.35, 0.35, 0.4)
            if extra % 3 == 0:
                for k in range(5):
                    m.add(t + k * 0.18, sfx.step_heavy(k), 0.25, 0.35, 0.1)
            elif extra % 3 == 1:
                m.add(t + 0.25, sfx.plate_clank(extra, 0.5), 0.3, 0.35, 0.2)
                m.add(t + 0.75, sfx.plate_clank(extra + 50, 0.5), 0.3, 0.35, 0.2)
            else:
                for k in range(10):
                    m.add(t + k * 0.09, sfx.tick(1200 + 200 * (k % 3), 0.2), 0.3, 0.35, 0.05)
        elif kind == "out":
            m.add(t, sfx.power_down(2.0), 0.6, -0.35, 0.4)
            m.add(t + 0.3, sfx.body_fall() * 0.5, 0.5, -0.35, 0.3)
        elif kind == "crown":
            m.add(t - 0.55, sfx.power_up(110), 0.9, 0.35, 0.4)
            m.add(t, sfx.boom(3.5), 0.9, 0, 0.5)
            m.add(t, sfx.sparkle(1.8), 0.5, 0.35, 0.6)
    m.add(P1, sfx.text_hit(1), 0.55, 0, 0.4)
    m.add(P2, sfx.text_hit(2), 0.65, 0, 0.4)
    m.add(P3, sfx.text_hit(3), 0.95, 0, 0.5)
    m.add(P3, sfx.boom(2.0), 0.45, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [1.5, 2.9, 4.0, 5.2, 7.5, 10.5, 13.5, OUT_T + 0.9, CROWN + 0.4, P3 + 1.0]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
