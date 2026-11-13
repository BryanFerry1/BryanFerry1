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
from kit import (CX, GREY, Log, Video, arms_up, caption, crossed, curl, draw_body, flex, sad, sit,
                 stand)
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
END_T = 15.4
DUR = 18.6
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


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
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
        if not v.wants(fi):
            continue
        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
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
    m.add_bed(sfx.drone(DUR, rise_at=S_T), gain=0.35, fade_in=0.4, fade_out=2.0, stop=DUR)
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
        elif kind == "end":
            m.add(t, sfx.text_hit(3), 0.8, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [1.6, 3.6, 5.5, 7.4, 9.2, 11.0, 13.0, 14.4, 17.0]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
