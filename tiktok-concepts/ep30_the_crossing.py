"""EP30 - DISCIPLINE VS OBSESSION  (the crossing: 30 km open-water swim)

EP19 format (best performer): split screen, endurance, each side wins something,
plus zooms inside each lane.
TOP     OBSESSION sprints far ahead. Night. CRAMP: he sinks, struggles, red
        flash... and swims again, slower. Discipline catches up: tie at KM 19.
        Dawn: he pushes again, reaches the beach FIRST, crawls out and collapses.
BOTTOM  DISCIPLINE swims at his own pace, takes a bottle from the feed boat,
        keeps the same stroke all night, reaches the beach SECOND, standing.
MERGE   the divider opens: same beach. Discipline walks to Obsession and gives
        him his hand. Obsession grabs it.
END (black, centred) OBSESSION / ARRIVED FIRST. / DISCIPLINE / ARRIVED STANDING.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import (FPS, H, RED, WHITE, W, Camera, Particles, clamp, draw_spaced, ease_out, font, mix, paint,
                    run_pose, smoothstep)
from kit import CX, GREY, Log, Video, blend, caption, draw_body, ending, kneel, mirror, stand
import ep27_triathlon as e27
import ep20_talent_vs_obsession_rematch as e20
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep30_the_crossing"
dt = 1 / FPS
LANES = {"OBSESSION": (330, 935, 780), "DISCIPLINE": (965, 1565, 1415)}   # clip y0, y1, water-line y
SX0 = 400.0
WATER_Y = 0.45
BEACH = 30.0
NIGHT = (5.4, 12.2)
FEED = (3.3, 4.3)
CRAMP = (8.2, 10.2)
O_FIN, D_FIN = 14.6, 15.6
MERGE = 16.0
HAND = 17.0
END_T = 18.6
DUR = 22.6

O_KF = [(0, 0.0), (5.0, 13.0), (CRAMP[0], 18.6), (CRAMP[1], 19.0), (13.9, 29.3), (O_FIN, BEACH + 0.6), (99, BEACH + 0.6)]
D_KF = [(0, 0.0), (FEED[0], 6.4), (FEED[1], 6.9), (CRAMP[1], 19.0), (14.4, 27.2), (D_FIN, BEACH + 0.4), (MERGE, BEACH + 1.2),
        (99, BEACH + 1.2)]


def lin(t, kf):
    if t <= kf[0][0]:
        return kf[0][1]
    for (t0, v0), (t1, v1) in zip(kf, kf[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * (t - t0) / (t1 - t0)
    return kf[-1][1]


def km(n, t):
    return lin(t, O_KF if n == "OBSESSION" else D_KF)


def seabed(x):
    """height of the sand: under water before the beach, rising onto it."""
    if x < BEACH - 1.5:
        return -9.0
    return min(0.7, WATER_Y - 0.25 + (x - (BEACH - 0.5)) * 0.45)


def lane_scale(n, t):
    z = 0.0
    if n == "DISCIPLINE":
        z = smoothstep(FEED[0] - 0.3, FEED[0], t) * (1 - smoothstep(FEED[1], FEED[1] + 0.3, t))
    else:
        z = smoothstep(CRAMP[0] - 0.3, CRAMP[0], t) * (1 - smoothstep(CRAMP[1] - 0.2, CRAMP[1] + 0.2, t))
        z = max(z, smoothstep(O_FIN - 0.6, O_FIN - 0.2, t) * 0.7)
    return 140 + 70 * z


def boat(c, cam, x, t):
    bob = 0.05 * math.sin(t * 3)
    hull = skia.Path()
    hull.moveTo(*cam.pt((x - 1.3, WATER_Y + 0.5 + bob)))
    hull.lineTo(*cam.pt((x + 1.3, WATER_Y + 0.5 + bob)))
    hull.lineTo(*cam.pt((x + 0.9, WATER_Y - 0.2 + bob)))
    hull.lineTo(*cam.pt((x - 0.9, WATER_Y - 0.2 + bob)))
    hull.close()
    c.drawPath(hull, paint((0, 0, 0), 1.0))
    c.drawPath(hull, paint(WHITE, 0.8, 3))
    j = stand(x + 0.2, 0.35, 1.6, 0.2, 0.2, 0.2, 0.3)
    j = {k: v + [0, WATER_Y + 0.5 + bob] for k, v in j.items()}
    draw_body(c, j, cam, GREY, 0.7)
    return j["hand1"]


def bottle(c, cam, pos, alpha=1.0):
    x, y = cam.pt(pos)
    w, h = 0.12 * cam.s, 0.34 * cam.s
    c.drawRoundRect(skia.Rect(x - w / 2, y - h, x + w / 2, y), 4, 4, paint(WHITE, alpha, 3))
    c.drawRect(skia.Rect(x - w * 0.3, y - h - 0.08 * cam.s, x + w * 0.3, y - h), paint(RED, alpha))


def draw_lane_world(e, f_, cam, x, t, night):
    wy = cam.pt((0, WATER_Y))[1]
    # water + scrolling ripples
    e.drawLine(-10, wy, W + 10, wy, paint(WHITE, 0.55, 3))
    k0 = math.floor(x - 6)
    for k in range(k0, k0 + 14):
        xx = k + 0.3 * math.sin(t * 2 + k)
        p1 = cam.pt((xx, WATER_Y - 0.3 - 0.25 * (k % 3)))
        e.drawLine(p1[0], p1[1], p1[0] + 0.35 * cam.s, p1[1], paint(WHITE, 0.14, 2))
    # beach
    if x > BEACH - 8:
        p = skia.Path()
        p.moveTo(*cam.pt((BEACH - 1.5, WATER_Y - 0.9)))
        for k in range(12):
            xx = BEACH - 1.5 + k * 0.6
            p.lineTo(*cam.pt((xx, seabed(xx))))
        p.lineTo(*cam.pt((BEACH + 10, seabed(BEACH + 5))))
        p.lineTo(*cam.pt((BEACH + 10, -5)))
        p.lineTo(*cam.pt((BEACH - 1.5, -5)))
        p.close()
        e.drawPath(p, paint((0.1, 0.1, 0.11), 1.0))
        top = skia.Path()
        top.moveTo(*cam.pt((BEACH - 1.5, WATER_Y - 0.9)))
        for k in range(12):
            xx = BEACH - 1.5 + k * 0.6
            top.lineTo(*cam.pt((xx, seabed(xx))))
        top.lineTo(*cam.pt((BEACH + 10, seabed(BEACH + 5))))
        e.drawPath(top, paint(WHITE, 0.6, 3))
        fx, fy = cam.pt((BEACH + 2.6, seabed(BEACH + 2.6)))
        e.drawLine(fx, fy, fx, fy - 2.2 * cam.s, paint(WHITE, 0.7, 4))
        fl = skia.Path()
        fl.moveTo(fx, fy - 2.2 * cam.s)
        fl.lineTo(fx + 0.6 * cam.s, fy - 2.0 * cam.s)
        fl.lineTo(fx, fy - 1.8 * cam.s)
        fl.close()
        f_.drawPath(fl, paint(RED, 1.0))


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    splash = Particles(2)
    bubbles = Particles(3)
    rng = np.random.default_rng(8)
    ph = {"OBSESSION": 0.0, "DISCIPLINE": 1.1}
    for fi in range(v.n):
        t = fi * dt
        for n in ph:
            vx = abs(km(n, t + 0.03) - km(n, t - 0.03)) / 0.06
            ph[n] += dt * (1.2 + vx * 0.9)
        for key, tt, kind in (("go", 0.0, "go"), ("feed", FEED[0] + 0.3, "feed"), ("night", NIGHT[0], "night"),
                              ("cramp", CRAMP[0], "cramp"), ("again", CRAMP[1] - 0.4, "again"), ("tie", CRAMP[1], "tie"),
                              ("dawn", NIGHT[1], "dawn"), ("ofin", O_FIN, "ofin"), ("dfin", D_FIN, "dfin"),
                              ("merge", MERGE, "merge"), ("hand", HAND, "hand"), ("end", END_T, "end"),
                              ("end2", END_T + 1.0, "end2")):
            if t >= tt:
                log.once(key, tt, kind)
        for n in ("OBSESSION", "DISCIPLINE"):
            k = int(ph[n] * 1.2)
            swimming = km(n, t) < BEACH - 0.6 and not (n == "OBSESSION" and CRAMP[0] <= t < CRAMP[1] - 0.4)
            if swimming:
                log.once(f"s{n}{k}", t, "stroke", 0 if n == "OBSESSION" else 1)
        if not v.wants(fi):
            continue

        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        night = smoothstep(NIGHT[0], NIGHT[0] + 0.6, t) * (1 - smoothstep(NIGHT[1] - 0.6, NIGHT[1], t))
        merge = smoothstep(MERGE, MERGE + 0.5, t)
        if t < MERGE + 0.5:
            for n, (y0, y1, wy) in LANES.items():
                x = km(n, t)
                cam = Camera()
                cam.s = lane_scale(n, t)
                cam.wx, cam.wy = min(x, BEACH + 0.3), WATER_Y
                cam.sx, cam.sy = SX0 + (80 if x > BEACH - 1 else 0), wy
                if merge > 0:
                    # lanes slide away as the divider opens
                    off = (-1 if n == "OBSESSION" else 1) * 700 * merge
                    y0, y1 = y0 + off, y1 + off
                    cam.sy += off
                for L in (v.env, v.fig, v.hero, v.txt):
                    L.canvas.save()
                    L.canvas.clipRect(skia.Rect(0, max(0, y0), W, min(H, y1)))
                draw_lane_world(e, f_, cam, x, t, night)
                if night > 0.01:
                    e.drawCircle(640, y0 + 80, 34, paint(WHITE, 0.9 * night))
                    e.drawCircle(655, y0 + 70, 31, paint((0, 0, 0), night))
                col = RED if n == "OBSESSION" else WHITE
                alpha = 1.0
                if n == "DISCIPLINE" and 1.5 < t < 6.0:
                    hand = boat(e, cam, 7.6, t)
                    if t < FEED[0] + 0.4:
                        bottle(f_, cam, hand + [0.05, 0.05])
                # swimmer / pose
                if x >= BEACH - 0.6:
                    if n == "OBSESSION":
                        j = e20.prone(x)
                        j = {k: vv + [0, seabed(x) - 0.12] for k, vv in j.items()}
                    else:
                        u = clamp((t - (D_FIN - 0.5)) / 0.6)
                        j = run_pose(x, ph[n] * 2, 0.35 * u)
                        j = {k: vv + [0, seabed(x)] for k, vv in j.items()}
                elif n == "OBSESSION" and CRAMP[0] <= t < CRAMP[1]:
                    u = (t - CRAMP[0]) / (CRAMP[1] - CRAMP[0])
                    sink = 0.9 * math.sin(math.pi * min(1, u * 1.3))
                    j = e27.tread_wave(x, t * 1.8)
                    j = {k: vv + [0.08 * math.sin(t * 30), -sink] for k, vv in j.items()}
                    alpha = 0.85
                    if rng.random() < 0.8:
                        bubbles.emit(np.array([[x + 0.3, WATER_Y - 0.1]]), vel=(0, 1.0), spread=0.3, life=(0.3, 0.7), size=(0.02, 0.05))
                else:
                    j = e27.swim_pose(x, ph[n] * 3.0, 0)
                    if n == "DISCIPLINE" and FEED[0] <= t < FEED[1]:
                        j = e27.tread_wave(x, 0)
                        j["hand2"] = j["head"] + [0.2, 0.05]
                        bottle(f_, cam, j["hand2"] + [0.05, 0.3])
                    if rng.random() < 0.5:
                        splash.emit(np.array([[x + 0.6 + rng.normal(0, 0.3), WATER_Y]]), vel=(0, 1.2), spread=0.5,
                                    life=(0.2, 0.5), size=(0.02, 0.05))
                if n == "OBSESSION":
                    col = mix(RED, mix(RED, GREY, 0.4), smoothstep(CRAMP[0], CRAMP[0] + 0.5, t) * (1 - smoothstep(CRAMP[1], 12.0, t)))
                draw_body(hc, j, cam, col, alpha, 0.2 if n == "OBSESSION" else 0.3)
                splash.draw(f_, cam, WHITE, WHITE)
                bubbles.draw(f_, cam, WHITE, WHITE)
                # water hides what is under the surface
                wsy = cam.pt((0, WATER_Y))[1]
                bx = cam.pt((BEACH - 1.0, 0))[0]
                hc.drawRect(skia.Rect(-10, wsy, min(W + 10, bx), H), paint((0.02, 0.02, 0.03), 0.6))
                # callouts
                if n == "OBSESSION" and CRAMP[0] + 0.1 <= t < CRAMP[1] - 0.3:
                    pop = 1 + 0.4 * math.exp(-(t - CRAMP[0]) * 8)
                    draw_spaced(tc, "CRAMP", CX, y0 + 210, font(80 * pop, "InterDisplay-Black"), 6, paint(RED, 1.0))
                lab_x = cam.pt((min(x, BEACH + 0.3), 0))[0]
                la = 1 - smoothstep(150, 180, cam.s)
                draw_spaced(tc, n, lab_x, wy + 48 + (0 if merge == 0 else 0), font(24, "Inter-Bold"), 4, paint(col, la))
                kmv = min(30, int(km(n, t)))
                draw_spaced(tc, f"KM {kmv}", 760, y0 + 60, font(40, "InterDisplay-Black"), 2, paint(WHITE, 0.9 * smoothstep(1.8, 2.1, t)))
                pos = "1ST" if (n == "OBSESSION" and t >= O_FIN) else "2ND" if (n == "DISCIPLINE" and t >= D_FIN) else ""
                if pos:
                    pop = 1 + 0.4 * math.exp(-(t - (O_FIN if pos == "1ST" else D_FIN)) * 8)
                    draw_spaced(tc, pos, 760, y0 + 125, font(56 * pop, "InterDisplay-Black"), 2, paint(RED if pos == "1ST" else WHITE, 1.0))
                for L in (v.env, v.fig, v.hero, v.txt):
                    L.canvas.restore()
            # divider + progress bar
            da = 1 - merge
            if da > 0.01:
                oc.drawRect(skia.Rect(0, 935, W, 965), paint((0, 0, 0), da))
                oc.drawLine(120, 950, 840, 950, paint(WHITE, 0.35 * da, 3))
                oc.drawLine(840, 938, 840, 962, paint(WHITE, 0.8 * da, 3))
                for n, col in (("DISCIPLINE", WHITE), ("OBSESSION", RED)):
                    px = 120 + 720 * clamp(km(n, t) / BEACH)
                    oc.drawCircle(px, 950, 11, paint(col, da))
                if CRAMP[1] <= t < CRAMP[1] + 1.0:
                    pop = 1 + 0.4 * math.exp(-(t - CRAMP[1]) * 8)
                    draw_spaced(oc, "TIE.", CX + 60, 1030, font(54 * pop, "InterDisplay-Black"), 4,
                                paint(RED, 1 - smoothstep(CRAMP[1] + 0.7, CRAMP[1] + 1.0, t)))
        if merge > 0:
            # ---------- one beach, both of them
            cam = Camera()
            cam.s, cam.wx, cam.wy, cam.sx, cam.sy = 150, BEACH + 1.5, 1.4, CX, 1150
            a = merge
            draw_lane_world(e, f_, cam, BEACH + 1.0, t, 0.0)
            ox = BEACH + 0.6
            jo = e20.prone(ox)
            jo = {k: vv + [0, seabed(ox) - 0.12] for k, vv in jo.items()}
            rise = smoothstep(HAND + 0.2, HAND + 1.0, t)
            if t >= HAND - 0.3:
                kn = kneel(ox + 0.4, t, 0.2, smoothstep(HAND - 0.3, HAND, t))
                kn = {k: vv + [0, seabed(ox + 0.4)] for k, vv in kn.items()}
                jo = blend(jo, kn, smoothstep(HAND - 0.3, HAND, t))
                up = stand(ox + 0.6, 0.15, 1.2, 0.2, 0.3, 0.2, 0.0)
                up = {k: vv + [0, seabed(ox + 0.6)] for k, vv in up.items()}
                jo = blend(jo, up, rise)
            dx = BEACH + 1.2 + 1.6 * smoothstep(MERGE + 0.2, HAND - 0.4, t)
            if t < HAND - 0.4:
                jd = run_pose(dx, t * 7, 0.3)
            else:
                jd = mirror(stand(dx, 0.3, 1.1, 0.1, 0.15, 0.1, 0.4), dx)
            jd = {k: vv + [0, seabed(dx)] for k, vv in jd.items()}
            if t >= HAND - 0.3:
                grip = (jd["hand1"] + jo["hand1"]) / 2
                jd["hand1"] = grip
                jo["hand1"] = grip
            draw_body(hc, jo, cam, mix(RED, WHITE, 0.0), a, 0.2)
            draw_body(hc, jd, cam, WHITE, a, 0.3)
            if t >= HAND - 0.3:
                hc.drawCircle(*cam.pt(jd["hand1"]), 0.1 * cam.s, paint(WHITE, a))
            for j, nme, col in ((jo, "OBSESSION", RED), (jd, "DISCIPLINE", WHITE)):
                sx, sy = cam.pt((j["hip"][0], seabed(j["hip"][0])))
                draw_spaced(tc, nme, sx, sy + 48, font(24, "Inter-Bold"), 4, paint(col, a * (1 - smoothstep(END_T - 0.6, END_T - 0.3, t))))
        if t < 1.8:
            a = 1 - smoothstep(1.4, 1.8, t)
            caption(oc, "DISCIPLINE VS OBSESSION", 405, a, WHITE, 46)
            draw_spaced(oc, "30 KM", 760, 1025, font(40, "InterDisplay-Black"), 2, paint(RED, a))
        ending(oc, t, END_T - 0.3, [(END_T, "OBSESSION", RED, 96), (END_T + 0.25, "ARRIVED FIRST.", RED, 96),
                                    (END_T + 1.0, "DISCIPLINE", WHITE, 96), (END_T + 1.25, "ARRIVED STANDING.", WHITE, 96)],
               gap=118)
        flash = max(math.exp(-(t - O_FIN) * 3) * 0.6 if t >= O_FIN else 0.0,
                    math.exp(-(t - HAND) * 3) * 0.6 if t >= HAND else 0.0)
        v.compose(fi, t, flash=flash, dim=0.4 * night, fade_in=0.0)
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=O_FIN), gain=0.42, fade_in=0.3, fade_out=2.0, stop=DUR)
    m.add(0.0, sfx.bandnoise(DUR, 80, 600, 4) * 0.12, 0.6, 0, 0.1)          # sea rumble
    last = {0: -1.0, 1: -1.0}
    for t, kind, _, extra in events:
        if kind == "stroke":
            if t - last[extra] < 0.2:
                continue
            last[extra] = t
            n = int(0.14 * sfx.SR)
            m.add(t, sfx.bandnoise(0.14, 700, 6000, int(t * 77)) * np.exp(-np.linspace(0, 6, n)) * 0.5, 0.3,
                  -0.3 if extra == 0 else 0.3, 0.3)
        elif kind == "go":
            m.add(0.0, sfx.beep(1320, 0.35), 0.6, 0, 0.3)
            m.add(0.02, sfx.text_hit(5), 0.6, 0, 0.4)
        elif kind == "feed":
            m.add(t, sfx.chime(700, 0.25), 0.45, 0.3, 0.4)
        elif kind == "night":
            m.add(t, sfx.whoosh(0.8, 100, 2000, 0.6, seed=5), 0.5, 0, 0.4)
        elif kind == "cramp":
            m.add(t, sfx.glitch(3), 0.7, -0.3, 0.2)
            m.add(t, sfx.punch_block(4), 0.7, -0.3, 0.3)
            m.add(t + 0.2, sfx.power_down(1.2), 0.5, -0.3, 0.4)
            for q in range(3):
                m.add(t + 0.3 + 0.6 * q, sfx.heartbeat(), 0.8, 0, 0.3)
        elif kind == "again":
            m.add(t, sfx.power_up(70), 0.9, -0.3, 0.4)
        elif kind == "tie":
            m.add(t, sfx.text_hit(2), 0.8, 0, 0.4)
            m.add(t + 0.2, sfx.riser(O_FIN - t - 0.2), 0.5, 0, 0.3)
        elif kind == "dawn":
            m.add(t, sfx.chime(880, 0.3), 0.4, 0, 0.6)
        elif kind == "ofin":
            m.add(t, sfx.boom(3.5), 0.9, -0.3, 0.5)
            m.add(t + 0.3, sfx.body_fall(), 0.7, -0.3, 0.4)
        elif kind == "dfin":
            m.add(t, sfx.text_hit(1), 0.6, 0.3, 0.4)
            for q in range(3):
                m.add(t + 0.1 + q * 0.35, sfx.step_heavy(q), 0.4, 0.3, 0.2)
        elif kind == "merge":
            m.add(t, sfx.whoosh(0.6, 200, 6000, 0.6, seed=9), 0.6, 0, 0.3)
            for q in range(4):
                m.add(t + 0.3 + q * 0.3, sfx.step_heavy(q + 5), 0.35, 0, 0.2)
        elif kind == "hand":
            m.add(t, sfx.punch_block(8), 0.6, 0, 0.3)
            m.add(t + 0.1, sfx.power_up(110), 0.8, 0, 0.4)
            m.add(t + 0.3, sfx.sparkle(1.6, 70, 3), 0.5, 0, 0.5)
        elif kind == "end":
            m.add(t, sfx.text_hit(1), 0.7, 0, 0.4)
        elif kind == "end2":
            m.add(t, sfx.text_hit(3), 0.95, 0, 0.5)
            m.add(t, sfx.boom(2.0), 0.45, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [0.5, 2.5, 3.8, 6.0, 8.6, 9.6, 10.5, 12.5, 14.2, 15.0, 15.9, 16.5, 17.6, 20.5]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
