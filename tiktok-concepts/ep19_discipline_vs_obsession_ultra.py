"""EP19 - DISCIPLINE VS OBSESSION  (the ultra race, EP02 split-screen format)

Moving from the very first frame. Split screen, 100 KM race.
TOP     OBSESSION sprints, skips the water station, never stops. Night falls:
        he keeps running in the dark, starts flickering red, limps.
        Crosses the line FIRST, breaks the red tape... and collapses on his knees.
BOTTOM  DISCIPLINE runs at his own pace, grabs a bottle, sleeps in a tent at
        night, then keeps the same pace. Crosses SECOND, fresh, and keeps running
        (KM 101, 102...).
A progress bar on the divider shows both runners (red dot / white dot).
END     OBSESSION WINS THE RACE. / DISCIPLINE WINS THE NEXT ONE.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import FPS, RED, WHITE, W, clamp, draw_spaced, ease_out, font, mix, paint, run_pose, smoothstep
from kit import CX, GREY, Log, Video, blend, caption, draw_body, kneel, lane_cam, stand
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep19_discipline_vs_obsession_ultra"
dt = 1 / FPS
S = 118.0
FINISH = 100.0
LANES = {"OBSESSION": (330, 935, 860), "DISCIPLINE": (965, 1565, 1475)}   # clip y0, y1, ground y
RUN_SX = 400.0
STRIDE = 2.6

NIGHT = (8.0, 13.0)
O_FIN = 16.5
D_SLEEP = (8.4, 10.2)
D_FIN = 18.6
P1, P2 = 19.6, 20.5
DUR = 23.5
O_WATER, D_WATER = 25.0, 10.0


def keys(t, kf):
    if t <= kf[0][0]:
        return kf[0][1]
    for (t0, v0), (t1, v1) in zip(kf, kf[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * (t - t0) / (t1 - t0)
    return kf[-1][1] + (t - kf[-1][0]) * (kf[-1][1] - kf[-2][1]) / (kf[-1][0] - kf[-2][0])


O_KF = [(0, 0.0), (8.0, 60.0), (13.0, 85.0), (O_FIN, 100.0)]
D_KF = [(0, 0.0), (D_SLEEP[0], 30.0), (D_SLEEP[1], 30.0), (D_FIN, 100.0)]


def km(name, t):
    if name == "OBSESSION":
        return min(100.0, keys(t, O_KF)) if t < O_FIN else 100.0 + 2.0 * ease_out(min(1, (t - O_FIN) / 0.7))
    return keys(t, D_KF)


def speed(name, t):
    return (km(name, t + 0.02) - km(name, t - 0.02)) / 0.04


def tent(c, cam, x, alpha):
    p = skia.Path()
    p.moveTo(*cam.pt((x - 1.1, 0)))
    p.lineTo(*cam.pt((x, 1.3)))
    p.lineTo(*cam.pt((x + 1.1, 0)))
    p.close()
    c.drawPath(p, paint((0, 0, 0), alpha))
    c.drawPath(p, paint(WHITE, alpha, 4))
    c.drawLine(*cam.pt((x, 1.3)), *cam.pt((x, 0)), paint(WHITE, 0.5 * alpha, 2))


def table(c, cam, x, bottle):
    c.drawLine(*cam.pt((x - 0.6, 0.85)), *cam.pt((x + 0.6, 0.85)), paint(WHITE, 0.8, 4))
    for lx in (x - 0.5, x + 0.5):
        c.drawLine(*cam.pt((lx, 0.85)), *cam.pt((lx, 0.0)), paint(WHITE, 0.6, 3))
    if bottle:
        bx, by = cam.pt((x, 0.85))
        r = skia.Rect(bx - 0.08 * cam.s, by - 0.42 * cam.s, bx + 0.08 * cam.s, by)
        c.drawRoundRect(r, 5, 5, paint(WHITE, 0.95, 3))
        c.drawRect(skia.Rect(bx - 0.05 * cam.s, by - 0.52 * cam.s, bx + 0.05 * cam.s, by - 0.42 * cam.s), paint(WHITE, 0.95))


def finish_gate(c, f_, cam, broken_u):
    for px in (FINISH - 0.05, FINISH + 0.85):
        c.drawLine(*cam.pt((px, 0)), *cam.pt((px, 2.9)), paint(WHITE, 0.7, 4))
    c.drawLine(*cam.pt((FINISH - 0.05, 2.9)), *cam.pt((FINISH + 0.85, 2.9)), paint(WHITE, 0.7, 4))
    gx, gy = cam.pt((FINISH + 0.4, 2.9))
    draw_spaced(c, "FINISH", gx, gy - 12, font(0.22 * cam.s, "InterDisplay-Black"), 3, paint(WHITE, 0.9))
    if broken_u is None:
        f_.drawLine(*cam.pt((FINISH - 0.05, 1.6)), *cam.pt((FINISH + 0.85, 1.6)), paint(RED, 1.0, 6))
    else:
        b = ease_out(min(1, broken_u))
        for side, x0 in ((-1, FINISH - 0.05), (1, FINISH + 0.85)):
            f_.drawLine(*cam.pt((x0, 1.6)), *cam.pt((x0 + side * -0.3 * (1 - b) + side * 0.1, 1.6 - 1.1 * b)), paint(RED, 1.0, 6))


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    ph = {"OBSESSION": 0.0, "DISCIPLINE": 0.7}
    contact = {}
    for fi in range(v.n):
        t = fi * dt
        # ---------- simulation + events
        for n in ("OBSESSION", "DISCIPLINE"):
            spd = speed(n, t)
            ph[n] += (spd / STRIDE) * 2 * math.pi * dt * (1.0 if n == "DISCIPLINE" else 0.55)
            for leg in range(2):
                c = math.floor((ph[n] + leg * math.pi - 1.87) / (2 * math.pi))
                key = n + str(leg)
                if contact.get(key) is not None and c != contact[key] and spd > 0.5:
                    log.add(t, "step_" + n, int(t * 100))
                contact[key] = c
        if t >= 0.0:
            log.once("go", 0.0, "go")
        if km("OBSESSION", t) >= O_WATER:
            log.once("skip", t, "skip")
        if km("DISCIPLINE", t) >= D_WATER - 0.3:
            log.once("drink", t, "drink")
        if t >= NIGHT[0]:
            log.once("night", NIGHT[0], "night")
        if t >= D_SLEEP[0]:
            log.once("sleep", D_SLEEP[0], "sleep")
        if t >= D_SLEEP[1]:
            log.once("wake", D_SLEEP[1], "wake")
        if t >= O_FIN - 0.15:
            log.once("ofin", O_FIN - 0.15, "ofin")
        if t >= O_FIN + 0.6:
            log.once("collapse", O_FIN + 0.6, "collapse")
        if t >= D_FIN - 0.1:
            log.once("dfin", D_FIN - 0.1, "dfin")
        for k_, tt in (("p1", P1), ("p2", P2)):
            if t >= tt:
                log.once(k_, tt, k_)
        if not v.wants(fi):
            continue

        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        night = smoothstep(NIGHT[0], NIGHT[0] + 0.6, t) * (1 - smoothstep(NIGHT[1] - 0.6, NIGHT[1], t))
        for n, (y0, y1, gy) in LANES.items():
            x = km(n, t)
            cam = lane_cam(S, gy, x)
            cam.sx = RUN_SX
            for L in (v.env, v.fig, v.hero, v.txt):
                L.canvas.save()
                L.canvas.clipRect(skia.Rect(0, y0, W, y1))
            # ground + scrolling ticks
            e.drawLine(0, gy, W, gy, paint(WHITE, 0.55, 2.5))
            k0 = math.floor(x - 4)
            for k in range(k0, k0 + 10):
                sx, _ = cam.pt((k * 1.0, 0))
                e.drawLine(sx, gy + 10, sx - 18, gy + 26, paint(WHITE, 0.16, 2))
            # km markers
            for mk in range(0, 101, 10):
                mx = mk + 0.0
                if abs(mx - x) < 6:
                    sx, _ = cam.pt((mx + 1.8, 0))
                    e.drawLine(sx, gy, sx, gy - 0.9 * S, paint(WHITE, 0.4, 3))
                    draw_spaced(tc, f"{mk}", sx, gy - 0.95 * S, font(26, "InterDisplay-Bold"), 2, paint(WHITE, 0.6))
            # moon
            if night > 0.01:
                mx_, my_ = 620, y0 + 80
                e.drawCircle(mx_, my_, 36, paint(WHITE, 0.9 * night))
                e.drawCircle(mx_ + 16, my_ - 10, 33, paint((0, 0, 0), night))
            # water station
            wx = O_WATER if n == "OBSESSION" else D_WATER
            if abs(wx - x) < 6:
                taken = n == "DISCIPLINE" and x >= D_WATER - 0.3
                table(e, cam, wx + 0.9, not taken)
            # finish gate
            if abs(FINISH - x) < 6:
                bu = None
                if n == "OBSESSION" and t >= O_FIN - 0.15:
                    bu = (t - O_FIN + 0.15) / 0.4
                if n == "DISCIPLINE":
                    bu = 1.0                                   # already broken by Obsession
                finish_gate(e, f_, cam, bu)
            # runner
            spd = speed(n, t)
            if n == "OBSESSION":
                tired = smoothstep(8.0, 15.5, t)
                if t < O_FIN:
                    inten = 1.0 - 0.25 * tired
                    j = run_pose(x, ph[n], inten, 0, 0.18 + 0.25 * tired, 0.1 + 0.4 * tired)
                    if tired > 0.5:                              # limp
                        j["foot2"] = j["foot2"] + [0, 0.05 * abs(math.sin(ph[n]))]
                else:
                    jr = run_pose(x, ph[n], 0.4, 0, 0.5, 0.6)
                    j = blend(jr, kneel(x - 0.2, t, 0.95), smoothstep(O_FIN + 0.3, O_FIN + 0.8, t))
                col = mix(WHITE, RED, 0.25 + 0.7 * tired)
                flick = 1.0
                if tired > 0.25 and (int(t * 30) * 7919) % 9 < 3 * tired:
                    flick = 0.45
                if t >= O_FIN + 0.8:
                    flick = 0.55 + 0.1 * math.sin(t * 3)
                draw_body(hc, j, cam, col, flick, 0.15)
                for k in range(3 if tired > 0.3 and t < O_FIN else 0):       # sweat drops
                    sx, sy = cam.pt(j["head"] + [-0.3 - 0.2 * k, 0.1 + 0.15 * math.sin(t * 9 + k)])
                    f_.drawCircle(sx, sy, 4, paint(WHITE, 0.8))
            else:
                sleeping = D_SLEEP[0] <= t < D_SLEEP[1]
                if sleeping:
                    tx = 30.0 + 1.2
                    tent(e, cam, tx, smoothstep(D_SLEEP[0] - 0.3, D_SLEEP[0], t) * (1 - smoothstep(D_SLEEP[1] - 0.2, D_SLEEP[1], t)))
                    j = stand(x, 0.25, 0.2, 0.1, 0.2, 0.1, 0.6)
                    jl = {kk: vv for kk, vv in j.items()}
                    w = smoothstep(D_SLEEP[0], D_SLEEP[0] + 0.3, t) * (1 - smoothstep(D_SLEEP[1] - 0.3, D_SLEEP[1], t))
                    a = 1 - 0.85 * w
                    draw_body(hc, j, cam, WHITE, a, 0.15)
                    hx, hy = cam.pt((tx + 0.4, 1.4))
                    for zk in range(2):
                        draw_spaced(tc, "z", hx + 26 * zk, hy - 30 * zk - 8 * math.sin(t * 3 + zk), font(34 + 10 * zk, "InterDisplay-Bold"), 0,
                                    paint(WHITE, 0.85 * w))
                else:
                    drinking = D_WATER - 0.3 <= x < D_WATER + 6
                    j = run_pose(x, ph[n], 0.8, 0, 0.15, 0.05)
                    if drinking:
                        j["elbow1"] = j["shoulder"] + [0.3, -0.15]
                        j["hand1"] = j["head"] + [0.15, -0.05]
                    draw_body(hc, j, cam, WHITE, 1.0, 0.15)
                    if drinking:
                        bx, by = cam.pt(j["hand1"])
                        hc.save()
                        hc.translate(bx, by)
                        hc.rotate(-50)
                        hc.drawRoundRect(skia.Rect(-0.08 * S, -0.4 * S, 0.08 * S, 0), 5, 5, paint(WHITE, 1.0, 3))
                        hc.restore()
                    if t >= D_FIN + 0.2 and t < D_FIN + 1.4:                 # small "fresh" sparkle
                        sx, sy = cam.pt(j["head"] + [0.4, 0.4])
                        L = 14 * (0.5 + 0.5 * math.sin(t * 8))
                        f_.drawLine(sx - L, sy, sx + L, sy, paint(WHITE, 0.9, 3))
                        f_.drawLine(sx, sy - L, sx, sy + L, paint(WHITE, 0.9, 3))
            # label + per-lane counter
            lx, _ = cam.pt((x if not (n == "DISCIPLINE" and D_SLEEP[0] <= t < D_SLEEP[1]) else x, 0))
            draw_spaced(tc, n, lx, gy + 44, font(26, "Inter-Bold"), 5, paint(RED if n == "OBSESSION" else WHITE, 1.0))
            kmv = int(km(n, t))
            pos = ""
            if n == "OBSESSION" and t >= O_FIN:
                pos = "1ST"
            if n == "DISCIPLINE" and t >= D_FIN:
                pos = "2ND"
            ka = smoothstep(2.4, 2.7, t)
            draw_spaced(tc, f"KM {kmv}", 760, y0 + 60, font(40, "InterDisplay-Black"), 2, paint(WHITE, 0.9 * ka))
            if pos:
                pop = 1 + 0.4 * math.exp(-(t - (O_FIN if pos == "1ST" else D_FIN)) * 8)
                draw_spaced(tc, pos, 760, y0 + 125, font(56 * pop, "InterDisplay-Black"), 2, paint(RED if pos == "1ST" else WHITE, 1.0))
            for L in (v.env, v.fig, v.hero, v.txt):
                L.canvas.restore()

        # ---------- divider: progress bar
        y = 950
        oc.drawRect(skia.Rect(0, 935, W, 965), paint((0, 0, 0), 1.0))
        oc.drawLine(120, y, 840, y, paint(WHITE, 0.35, 3))
        oc.drawLine(840, y - 12, 840, y + 12, paint(WHITE, 0.8, 3))
        for n, col in (("DISCIPLINE", WHITE), ("OBSESSION", RED)):
            px = 120 + 720 * clamp(km(n, t) / 100)
            oc.drawCircle(px, y, 11, paint(col, 1.0))
        # title over the action (no black intro)
        if t < 2.6:
            ta = (1 - smoothstep(2.2, 2.6, t))
            caption(oc, "DISCIPLINE VS OBSESSION", 405, ta, WHITE, 46)
            draw_spaced(oc, "100 KM", 760, 1025, font(40, "InterDisplay-Black"), 2, paint(RED, ta * smoothstep(0.2, 0.35, t)))
        if 7.7 <= t < 9.6:
            caption(oc, "NIGHT.", 950 + 12, smoothstep(7.7, 7.9, t) * (1 - smoothstep(9.3, 9.6, t)), WHITE, 40)
        # end
        if t >= P1:
            oc.drawRect(skia.Rect(0, 640, W, 900), paint((0, 0, 0), 0.85 * smoothstep(P1 - 0.2, P1 + 0.2, t)))
            caption(oc, "OBSESSION WINS THE RACE.", 730, smoothstep(P1, P1 + 0.3, t), RED, 52, band=False)
        if t >= P2:
            caption(oc, "DISCIPLINE WINS THE NEXT ONE.", 830, smoothstep(P2, P2 + 0.3, t), WHITE, 48, band=False)
        flash = math.exp(-(t - O_FIN) * 3) if t >= O_FIN else 0.0
        v.compose(fi, t, flash=flash * 0.8, dim=0.45 * night, fade_in=0.0)
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=O_FIN), gain=0.4, fade_in=0.3, fade_out=2.0, stop=DUR)
    last = {"OBSESSION": -1.0, "DISCIPLINE": -1.0}
    for t, kind, _, extra in events:
        if kind.startswith("step_"):
            n = kind[5:]
            if t - last[n] < 0.08:
                continue
            last[n] = t
            if n == "OBSESSION":
                m.add(t, sfx.step_light(extra), 0.28, 0.0, 0.1)
            else:
                m.add(t, sfx.step_heavy(extra), 0.22, 0.0, 0.15)
        elif kind == "go":
            m.add(0.0, sfx.beep(1320, 0.35), 0.6, 0, 0.3)
            m.add(0.02, sfx.text_hit(5), 0.6, 0, 0.4)
        elif kind == "skip":
            m.add(t, sfx.whoosh(0.35, 600, 8000, 0.5, seed=3), 0.5, 0, 0.2)
        elif kind == "drink":
            m.add(t + 0.2, sfx.chime(700, 0.25), 0.4, 0, 0.3)
            for k in range(3):
                m.add(t + 0.25 + 0.15 * k, sfx.tick(500, 0.5), 0.4, 0, 0.1)
        elif kind == "night":
            m.add(t, sfx.whoosh(0.8, 100, 2000, 0.6, seed=5), 0.5, 0, 0.4)
            m.add(t + 0.2, sfx.power_down(1.2), 0.35, 0, 0.4)
        elif kind == "sleep":
            m.add(t, sfx.chime(440, 0.25), 0.4, 0, 0.6)
        elif kind == "wake":
            m.add(t, sfx.beep(990, 0.2), 0.4, 0, 0.3)
            m.add(t + 0.25, sfx.beep(990, 0.2), 0.4, 0, 0.3)
        elif kind == "ofin":
            m.add(t, sfx.boom(3.5), 0.9, 0, 0.5)
            m.add(t, sfx.sparkle(1.4), 0.5, 0, 0.5)
        elif kind == "collapse":
            m.add(t, sfx.body_fall(), 0.8, 0, 0.4)
            m.add(t + 0.2, sfx.power_down(1.6), 0.5, 0, 0.4)
            m.add(t + 0.5, sfx.heartbeat(), 0.7, 0, 0.3)
        elif kind == "dfin":
            m.add(t, sfx.text_hit(2), 0.6, 0, 0.4)
            m.add(t, sfx.applause(2.0, 30, 4), 0.35, 0, 0.3)
        elif kind == "p1":
            m.add(t, sfx.text_hit(1), 0.7, 0, 0.4)
        elif kind == "p2":
            m.add(t, sfx.text_hit(3), 0.9, 0, 0.5)
            m.add(t, sfx.boom(2.0), 0.4, 0, 0.4)
    m.add(O_FIN - 2.4, sfx.riser(2.4), 0.45, 0, 0.3)
    m.add(O_FIN - 1.2, sfx.heartbeat(), 0.6, 0, 0.3)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [0.1, 1.5, 2.9, 3.4, 6.5, 9.0, 11.5, 15.0, 16.6, 17.6, 18.9, 21.5]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
