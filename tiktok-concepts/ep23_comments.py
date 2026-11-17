"""EP23 - EGO VS OBSESSION  (the comments)

Split screen, moving from the first frame. Both train on a heavy bag.
A grey crowd throws hate comments at both of them.
EGO        stops, sits down, pulls out his phone and replies to every single one
           (red reply bubbles). REPLIES counter explodes.
OBSESSION  puts his (red) headphones on: comments bounce off and pop.
           He keeps punching. PUNCHES counter explodes, he grows.
DAY 365    Bottom: spotlight, crowd cheers, Obsession raises a championship belt.
           Top: dark, Ego still typing "ACTUALLY..." in his phone glow.
END        EGO REPLIED TO 4,312 COMMENTS. / OBSESSION REPLIED WITH RESULTS.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import (FPS, L_FARM, L_UARM, RED, WHITE, W, build_pose, clamp, draw_spaced, ease_out, font, ik,
                    mix, paint, smoothstep, spaced_width)
from kit import CX, GREY, Log, Video, arms_up, blend, caption, draw_body, draw_phone_small, lane_cam, sit, stand
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep23_comments"
dt = 1 / FPS
S = 138.0
LANES = {"EGO": (330, 935, 860), "OBSESSION": (965, 1565, 1475)}
FX = 0.9               # fighter x (world)
BAG_X = 2.15
CROWD_X = 170          # screen x of the crowd (left)

HATE = ["YOU'LL NEVER MAKE IT.", "CRINGE.", "LOL", "WHO DO YOU THINK YOU ARE?", "QUIT.", "NOBODY CARES.",
        "TOO LATE FOR YOU.", "FAKE.", "RATIO.", "STAY IN YOUR LANE."]
REPLIES = ["WATCH ME.", "U DON'T KNOW ME.", "ACTUALLY...", "SAYS WHO?", "BLOCKED.", "COPE.", "ACTUALLY..."]
FIRST = 2.6
REACT = 2.95
CHAMP = 11.4
P1, P2 = 13.6, 14.4
DUR = 17.6


def comment_times():
    ts, t, gap = [], FIRST, 0.9
    while t < CHAMP - 0.6:
        ts.append(t)
        t += gap
        gap = max(0.26, gap * 0.86)
    return ts


CT = comment_times()


def day(t):
    if t < FIRST:
        return 1
    return min(364, int(1 + 363 * clamp((t - FIRST) / (CHAMP - 0.3 - FIRST)) ** 1.4)) if t < CHAMP else 365


def counter(n, t):
    u = clamp((t - REACT) / (CHAMP - REACT))
    return int(4312 * u ** 1.5) if n == "EGO" else int(98000 * u ** 1.3)


def fight_pose(x, t, punch):
    """Orthodox guard facing +x, right hand jab 'punch' 0..1."""
    bob = 0.03 * math.sin(t * 8)
    j = build_pose(np.array([x, 1.42 + bob]), np.array([x + 0.4, 0.02]), np.array([x - 0.4, 0.02]),
                   0.15 + 0.1 * punch, 0.8, 0.55, 2.0, 2.2, 0.0)
    sh = j["shoulder"]
    tgt = sh + np.array([0.25 + 0.85 * punch, 0.25 - 0.1 * punch])
    j["hand1"] = tgt
    j["elbow1"] = ik(sh, tgt, L_UARM, L_FARM, -1)
    return j


def bag(c, cam, swing, alpha=1.0):
    top = np.array([BAG_X, 3.4])
    ang = 0.12 * swing
    ax = math.sin(ang)
    c.drawLine(*cam.pt(top + [0, 0.4]), *cam.pt(top), paint(WHITE, 0.6 * alpha, 3))
    c.save()
    px, py = cam.pt(top)
    c.translate(px, py)
    c.rotate(-math.degrees(ang))
    w, h = 0.55 * cam.s, 1.9 * cam.s
    r = skia.Rect(-w / 2, 0, w / 2, h)
    c.drawRoundRect(r, w * 0.35, w * 0.35, paint((0, 0, 0), alpha))
    c.drawRoundRect(r, w * 0.35, w * 0.35, paint(WHITE, alpha, 4))
    c.drawLine(-w / 2, h * 0.3, w / 2, h * 0.3, paint(WHITE, 0.4 * alpha, 2))
    c.drawLine(-w / 2, h * 0.7, w / 2, h * 0.7, paint(WHITE, 0.4 * alpha, 2))
    c.restore()


def chat(c, x, y, text, alpha, col=WHITE, size=24, tail_left=True):
    if alpha < 0.01:
        return
    f = font(size, "InterDisplay-Black")
    w = spaced_width(text, f, 1) + 30
    h = size + 22
    x = min(max(x, 80 + w / 2), 880 - w / 2)
    r = skia.Rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2)
    c.drawRoundRect(r, 12, 12, paint((0, 0, 0), 0.95 * alpha))
    c.drawRoundRect(r, 12, 12, paint(col, alpha, 3))
    draw_spaced(c, text, x, y + size * 0.36, f, 1, paint(col, alpha))


def headphones(c, cam, j, alpha):
    hx, hy = cam.pt(j["head"])
    r = 0.29 * cam.s
    arc = skia.Path()
    arc.addArc(skia.Rect(hx - r * 1.15, hy - r * 1.25, hx + r * 1.15, hy + r * 1.05), 180, 180)
    c.drawPath(arc, paint(RED, alpha, 6))
    for sgn in (-1, 1):
        c.drawRoundRect(skia.Rect(hx + sgn * r * 1.05 - 9, hy - 14, hx + sgn * r * 1.05 + 9, hy + 18), 6, 6, paint(RED, alpha))


def belt(c, cam, j, alpha):
    a, b = cam.pt(j["hand1"]), cam.pt(j["hand2"])
    mx, my = (a[0] + b[0]) / 2, min(a[1], b[1]) - 10
    c.drawLine(a[0], a[1], b[0], b[1], paint(RED, alpha, 14))
    r = skia.Rect(mx - 46, my - 30, mx + 46, my + 30)
    c.drawRoundRect(r, 12, 12, paint((0, 0, 0), alpha))
    c.drawRoundRect(r, 12, 12, paint(WHITE, alpha, 5))
    c.drawCircle(mx, my, 14, paint(RED, alpha))


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    ph = 0.0
    for fi in range(v.n):
        t = fi * dt
        # ---------- events
        for k, tc_ in enumerate(CT):
            if t >= tc_:
                log.once(f"c{k}", tc_, "comment", k)
            if t >= tc_ + 0.55 and tc_ + 0.55 < CHAMP:
                log.once(f"r{k}", tc_ + 0.55, "reply", k)
        for key, tt, kind in (("go", 0.0, "go"), ("react", REACT, "react"), ("champ", CHAMP, "champ"),
                              ("p1", P1, "p1"), ("p2", P2, "p2")):
            if t >= tt:
                log.once(key, tt, kind)
        rate = 1.6 + 2.2 * smoothstep(4.0, 9.0, t)
        old = ph
        ph += dt * rate
        if t < CHAMP and int(old) != int(ph):
            log.add(t, "punch_O")
            if t < REACT:
                log.add(t + 0.03, "punch_E")
        if not v.wants(fi):
            continue

        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        champ = t >= CHAMP
        punch = max(0.0, math.sin(math.pi * (ph % 1.0))) ** 2
        g_o = 0.9 * smoothstep(REACT, CHAMP, t)
        for n, (y0, y1, gy) in LANES.items():
            cam = lane_cam(S, gy, 0.0)
            cam.sx = CX + 10
            for L in (v.env, v.fig, v.hero, v.txt):
                L.canvas.save()
                L.canvas.clipRect(skia.Rect(0, y0, W, y1))
            e.drawLine(60, gy, W - 60, gy, paint(WHITE, 0.5, 2.5))
            lit = 1.0
            if champ and n == "EGO":
                lit = 1 - 0.65 * smoothstep(CHAMP, CHAMP + 0.4, t)
            # crowd (left)
            for k in range(3):
                hx, hy = CROWD_X - 40 + 45 * k, gy - 70 - 30 * (k % 2)
                ca = (0.55 if not (champ and n == "OBSESSION") else 0.9) * lit
                ccol = GREY if not (champ and n == "OBSESSION") else WHITE
                bob = 6 * abs(math.sin(t * 10 + k)) if (champ and n == "OBSESSION") else 0
                e.drawCircle(hx, hy - 60 - bob, 22, paint(ccol, ca))
                e.drawRoundRect(skia.Rect(hx - 28, hy - 34 - bob, hx + 28, gy - 4), 18, 18, paint(ccol, 0.7 * ca))
            if champ and n == "OBSESSION":
                sp = skia.Path()
                sx_, _ = cam.pt((FX, 0))
                sp.moveTo(sx_ - 30, y0 + 5)
                sp.lineTo(sx_ + 30, y0 + 5)
                sp.lineTo(sx_ + 250, gy)
                sp.lineTo(sx_ - 250, gy)
                sp.close()
                pt = skia.Paint(AntiAlias=True)
                pt.setShader(skia.GradientShader.MakeLinear([skia.Point(0, y0), skia.Point(0, gy)],
                                                            [skia.Color4f(1, 1, 1, 0), skia.Color4f(1, 1, 1, 0.12)]))
                e.drawPath(sp, pt)
            # bag
            swing = 0.0
            if n == "OBSESSION" and not champ:
                swing = punch
            elif n == "EGO" and t < REACT:
                swing = punch
            bag(e, cam, swing, lit if not champ else 0.4)
            # fighter
            if n == "EGO":
                if t < REACT:
                    j = fight_pose(FX, t, punch)
                else:
                    js = sit(FX - 0.6, 0.0, t, 0.6)
                    js = {k: vv + [0, -0.05] for k, vv in js.items()}
                    js["hand1"] = js["shoulder"] + np.array([0.5, 0.05])
                    js["hand2"] = js["shoulder"] + np.array([0.45, 0.0])
                    js["elbow1"] = ik(js["shoulder"], js["hand1"], L_UARM, L_FARM, -1)
                    js["elbow2"] = ik(js["shoulder"], js["hand2"], L_UARM, L_FARM, -1)
                    j = blend(fight_pose(FX, t, 0), js, smoothstep(REACT, REACT + 0.35, t))
                    j = {k: vv + [0.01 * math.sin(t * 30), 0] for k, vv in j.items()}       # typing jitter
                col = mix(RED, mix(RED, GREY, 0.5), smoothstep(CHAMP, CHAMP + 1, t))
                draw_body(hc, j, cam, col, lit, 0.15)
                if t >= REACT:
                    draw_phone_small(f_, cam, j["hand1"] + [0.05, 0.12], 1.0)
                    hx, hy = cam.pt(j["head"])
                    f_.drawCircle(hx + 20, hy + 20, 0.6 * S, paint(WHITE, 0.05 + 0.05 * (champ)))
            else:
                if not champ:
                    j = fight_pose(FX, t, punch)
                else:
                    j = blend(fight_pose(FX, t, 0), stand(FX, -0.05, 2.35, 2.5, 0.9, 0.95, -0.2), smoothstep(CHAMP + 0.1, CHAMP + 0.5, t))
                draw_body(hc, j, cam, WHITE, 1.0, g_o)
                if t >= REACT:
                    headphones(hc, cam, j, smoothstep(REACT, REACT + 0.2, t))
                if champ:
                    belt(hc, cam, j, smoothstep(CHAMP + 0.3, CHAMP + 0.5, t))
            # comments flying in
            for k, tc_ in enumerate(CT):
                age = t - tc_
                if age < 0 or age > 1.1:
                    continue
                txt = HATE[k % len(HATE)]
                hx, hy = cam.pt(j["head"])
                u = ease_out(min(1, age / 0.35))
                sx = CROWD_X + 60 + (hx - 40 - CROWD_X - 60) * u
                sy = y0 + 175 + 60 * (k % 3) + (hy - 60 - (y0 + 150 + 70 * (k % 3))) * u * 0.3
                if n == "OBSESSION" and t >= REACT:
                    a = 1 - smoothstep(0.35, 0.5, age)
                    chat(tc, sx, sy, txt, a, GREY, 24)
                    if 0.35 <= age < 0.6:                 # pop on the headphones
                        pa = 1 - (age - 0.35) / 0.25
                        for s_ in range(6):
                            ang = s_ * 1.05
                            f_.drawLine(sx + math.cos(ang) * 20, sy + math.sin(ang) * 20,
                                        sx + math.cos(ang) * (30 + 40 * (1 - pa)), sy + math.sin(ang) * (30 + 40 * (1 - pa)),
                                        paint(WHITE, pa, 3))
                else:
                    a = 1 - smoothstep(0.9, 1.1, age)
                    chat(tc, sx, sy, txt, a, GREY, 24)
                    if n == "EGO" and age >= 0.55 and tc_ + 0.55 < CHAMP:
                        rr = REPLIES[k % len(REPLIES)]
                        chat(tc, hx + 60, hy - 110, rr, 1 - smoothstep(0.95, 1.1, age), RED, 26)
            if champ and n == "EGO":
                hx, hy = cam.pt(j["head"])
                dots = "." * (1 + int(t * 3) % 3)
                chat(tc, hx + 80, hy - 110, "ACTUALLY" + dots, 1.0, RED, 28)
            # labels + counters
            lx, _ = cam.pt((FX, 0))
            draw_spaced(tc, n, lx, gy + 38, font(24, "Inter-Bold"), 5, paint(RED if n == "EGO" else WHITE, 1.0))
            ca = smoothstep(2.2, 2.5, t)
            lab = "REPLIES" if n == "EGO" else "PUNCHES"
            draw_spaced(tc, lab, 260, y0 + 55, font(20, "Inter-Bold"), 3, paint(WHITE, 0.6 * ca))
            draw_spaced(tc, f"{counter(n, t):,}", 260, y0 + 110, font(52, "InterDisplay-Black"), 2,
                        paint(RED if n == "EGO" else WHITE, ca))
            for L in (v.env, v.fig, v.hero, v.txt):
                L.canvas.restore()

        oc.drawRect(skia.Rect(0, 935, W, 965), paint((0, 0, 0), 1.0))
        d = day(t)
        dtxt = f"DAY {d}" if not champ else "DAY 365 — CHAMPIONSHIP"
        draw_spaced(oc, dtxt, CX, 962, font(34, "InterDisplay-Black"), 3, paint(RED if champ else WHITE, smoothstep(2.2, 2.5, t)))
        if t < 2.4:
            caption(oc, "EGO VS OBSESSION", 405, 1 - smoothstep(2.0, 2.4, t), WHITE, 54)
        if t >= P1:
            a = smoothstep(P1 - 0.2, P1 + 0.2, t)
            oc.drawRect(skia.Rect(0, 640, W, 900), paint((0, 0, 0), 0.86 * a))
            caption(oc, "EGO REPLIED TO 4,312 COMMENTS.", 740, smoothstep(P1, P1 + 0.3, t), WHITE, 44, band=False)
        if t >= P2:
            caption(oc, "OBSESSION REPLIED WITH RESULTS.", 840, smoothstep(P2, P2 + 0.3, t), RED, 44, band=False)
        flash = math.exp(-(t - CHAMP - 0.4) * 3) if t >= CHAMP + 0.4 else 0.0
        white = 0.35 * max(0.0, 1 - (t - CHAMP) / 0.2) if CHAMP <= t < CHAMP + 0.2 else 0.0
        v.compose(fi, t, flash=flash * 0.8, white=white, fade_in=0.0)
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=CHAMP), gain=0.4, fade_in=0.3, fade_out=2.0, stop=DUR)
    last = {}
    for t, kind, _, extra in events:
        if kind == "go":
            m.add(0.02, sfx.text_hit(5), 0.6, 0, 0.4)
        elif kind in ("punch_O", "punch_E"):
            if t - last.get(kind, -1) < 0.18:
                continue
            last[kind] = t
            m.add(t + 0.12, sfx.punch_hit(int(t * 50), 0.7), 0.35, 0.25 if kind == "punch_O" else -0.25, 0.2)
        elif kind == "comment":
            m.add(t, sfx.beep(1100 + 90 * (extra % 4), 0.06, 0.4), 0.45, -0.5, 0.2)
        elif kind == "reply":
            for k in range(4):
                m.add(t - 0.25 + 0.05 * k, sfx.tick(3200 + 200 * (k % 2), 0.25), 0.3, -0.3, 0.05)
            m.add(t, sfx.chime(700, 0.15), 0.3, -0.3, 0.3)
        elif kind == "react":
            m.add(t, sfx.power_down(0.6), 0.4, -0.3, 0.3)
            m.add(t + 0.1, sfx.chime(330, 0.3), 0.5, 0.3, 0.5)
        elif kind == "champ":
            m.add(t, sfx.spot_on(), 0.7, 0.3, 0.4)
            m.add(t + 0.4, sfx.boom(4.0), 1.0, 0, 0.5)
            m.add(t + 0.4, sfx.bell(), 0.6, 0.3, 0.5)
            m.add(t + 0.5, sfx.applause(3.5, 60, 5), 0.6, 0.3, 0.3)
        elif kind == "p1":
            m.add(t, sfx.text_hit(1), 0.6, 0, 0.4)
        elif kind == "p2":
            m.add(t, sfx.text_hit(3), 0.95, 0, 0.5)
            m.add(t, sfx.boom(2.0), 0.4, 0, 0.4)
    m.add(CHAMP - 2.0, sfx.riser(2.4), 0.45, 0, 0.3)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}, comments {len(CT)}")
    if "--stills" in sys.argv:
        ts = [0.2, 1.5, 3.0, 3.6, 5.0, 7.0, 9.0, 10.8, 11.9, 12.8, 14.8, 16.5]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
