"""EP36 - EGO VS DISCIPLINE  (the marathon, EP19 split-screen format)

Split screen, 42 KM, moving from the first frame, progress bar on the divider.
TOP     EGO sprints off, runs BACKWARDS waving at Discipline (TOO SLOW), takes a
        selfie while running, stops to flex for the crowd (phone flashes).
        KM 35: THE WALL. He slows down, flickers... looks back: Discipline is
        right there. He sprints again, gets ahead, and 1 metre before the line
        he raises his arms and turns to the crowd to celebrate...
BOTTOM  DISCIPLINE: same pace all race, drinks at the station, catches up,
        leans... and breaks the tape.
PHOTO FINISH: freeze frame, red line, Discipline's chest on the line, Ego's
        tape still intact. 1ST / 2ND.
END     EGO RAN FOR THE CROWD. / DISCIPLINE RAN FOR THE LINE.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import FPS, RED, WHITE, W, clamp, draw_spaced, ease_out, font, mix, paint, run_pose, smoothstep
from kit import (GREY, Log, Video, arms_up, blend, caption, draw_body, ending, flex, lane_cam, mirror, stand)
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep36_ego_vs_discipline_marathon"
dt = 1 / FPS
S = 118.0
FINISH = 42.0
LANES = {"EGO": (330, 935, 860), "DISCIPLINE": (965, 1565, 1475)}
RUN_SX = 400.0
STRIDE = 2.6

BACKWARD = (3.0, 4.2)
SELFIE = (4.4, 5.6)
FLEX = (6.0, 7.6)
WALL = (10.5, 12.5)
LOOK = (12.4, 12.9)
CELEB = 14.6
D_FIN = 15.2
FREEZE = (15.3, 17.5)
FZ = FREEZE[1] - FREEZE[0]
END_T = 19.4
DUR = 23.4
D_WATER = 16.0
CAM_LOCK = (13.4, 14.3)
LOCK_X = 41.0

E_KF = [(0, 0.0), (3.0, 13.0), (5.6, 21.6), (FLEX[0], 23.4), (FLEX[1], 23.6), (WALL[0], 33.0), (WALL[1], 35.6),
        (CELEB, 41.35), (CELEB + 0.5, 41.62)]
D_KF = [(0, 0.0), (D_FIN, 42.0), (D_FIN + 3.0, 47.0)]


def keys(t, kf):
    if t <= kf[0][0]:
        return kf[0][1]
    for (t0, v0), (t1, v1) in zip(kf, kf[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * (t - t0) / (t1 - t0)
    return kf[-1][1]


def scene_t(t):
    """Scene time: frozen during the photo finish."""
    if t < FREEZE[0]:
        return t
    if t < FREEZE[1]:
        return FREEZE[0]
    return t - FZ


def km(n, ts):
    if n == "EGO":
        return keys(ts, E_KF)
    x = keys(ts, D_KF)
    if ts > D_FIN:                       # easy jog after the line
        x = 42.0 + 1.1 * (ts - D_FIN)
    return x


def speed(n, ts):
    return (km(n, ts + 0.02) - km(n, ts - 0.02)) / 0.04


def table(c, cam, x, bottle):
    c.drawLine(*cam.pt((x - 0.6, 0.85)), *cam.pt((x + 0.6, 0.85)), paint(WHITE, 0.8, 4))
    for lx in (x - 0.5, x + 0.5):
        c.drawLine(*cam.pt((lx, 0.85)), *cam.pt((lx, 0.0)), paint(WHITE, 0.6, 3))
    if bottle:
        bx, by = cam.pt((x, 0.85))
        r = skia.Rect(bx - 0.08 * cam.s, by - 0.42 * cam.s, bx + 0.08 * cam.s, by)
        c.drawRoundRect(r, 5, 5, paint(WHITE, 0.95, 3))


def finish_gate(c, f_, cam, broken_u):
    for px in (FINISH, FINISH + 0.9):
        c.drawLine(*cam.pt((px, 0)), *cam.pt((px, 2.9)), paint(WHITE, 0.7, 4))
    c.drawLine(*cam.pt((FINISH, 2.9)), *cam.pt((FINISH + 0.9, 2.9)), paint(WHITE, 0.7, 4))
    gx, gy = cam.pt((FINISH + 0.45, 2.9))
    draw_spaced(c, "FINISH", gx, gy - 12, font(0.22 * cam.s, "InterDisplay-Black"), 3, paint(WHITE, 0.9))
    if broken_u is None:
        f_.drawLine(*cam.pt((FINISH, 1.6)), *cam.pt((FINISH + 0.9, 1.6)), paint(RED, 1.0, 6))
    else:
        b = ease_out(min(1, broken_u))
        for side, x0 in ((-1, FINISH), (1, FINISH + 0.9)):
            f_.drawLine(*cam.pt((x0, 1.6)), *cam.pt((x0 + side * -0.3 * (1 - b) + side * 0.1, 1.6 - 1.1 * b)),
                        paint(RED, 1.0, 6))


def crowd(c, cam, x0, t, n=3, phones=True, flash_t=None):
    for k in range(n):
        x = x0 + k * 0.55
        j = stand(x, -0.05, 2.3 + 0.2 * math.sin(t * 7 + k), 0.2, 0.6, 0.1, -0.1)
        j = mirror(j, x)
        draw_body(c, j, cam, GREY, 0.5)
        if phones:
            hx, hy = cam.pt(j["hand1"])
            c.drawRoundRect(skia.Rect(hx - 0.07 * cam.s, hy - 0.22 * cam.s, hx + 0.07 * cam.s, hy), 3, 3,
                            paint(GREY, 0.8, 2))
            if flash_t is not None and int(t * 7 + k * 3) % 4 == 0:
                c.drawCircle(hx, hy - 0.11 * cam.s, 0.18 * cam.s, paint(WHITE, 0.9))


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    ph = {"EGO": 0.0, "DISCIPLINE": 0.7}
    contact = {}
    for fi in range(v.n):
        t = fi * dt
        ts = scene_t(t)
        frozen = FREEZE[0] <= t < FREEZE[1]
        for n in ("EGO", "DISCIPLINE"):
            spd = speed(n, ts)
            if not frozen:
                ph[n] += (spd / STRIDE) * 2 * math.pi * dt * (0.55 if n == "EGO" else 1.0)
                for leg in range(2):
                    c = math.floor((ph[n] + leg * math.pi - 1.87) / (2 * math.pi))
                    key = n + str(leg)
                    if contact.get(key) is not None and c != contact[key] and spd > 0.5:
                        log.add(t, "step_" + n, int(t * 100))
                    contact[key] = c
        for key, tt, kind in (("go", 0.0, "go"), ("back", BACKWARD[0], "back"), ("selfie", SELFIE[0] + 0.4, "shutter"),
                              ("selfie2", SELFIE[0] + 0.8, "shutter"), ("flex", FLEX[0], "flex"),
                              ("drink", 5.6, "drink"), ("wall", WALL[0], "wall"), ("look", LOOK[0], "look"),
                              ("sprint", LOOK[1], "sprint"), ("celeb", CELEB, "celeb"), ("dfin", D_FIN, "dfin"),
                              ("photo", FREEZE[0], "photo"), ("rank", FREEZE[0] + 1.1, "rank"),
                              ("end", END_T, "end"), ("end2", END_T + 1.3, "end2")):
            if t >= tt:
                log.once(key, tt, kind)
        if not v.wants(fi):
            continue

        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        lock = smoothstep(*CAM_LOCK, ts)
        zoom = ease_out(smoothstep(FREEZE[0], FREEZE[0] + 0.8, t)) * (1 - smoothstep(FREEZE[1], FREEZE[1] + 0.4, t))
        for n, (y0, y1, gy) in LANES.items():
            x = km(n, ts)
            s_ = S * (1 + 0.28 * zoom)
            cam = lane_cam(s_, gy - 60 * zoom * 0, mix((x, 0, 0), (LOCK_X, 0, 0), lock)[0] if False else
                           x + (LOCK_X - x) * lock)
            cam.sx = RUN_SX + (180 - RUN_SX) * 0 + (300 - RUN_SX) * zoom
            if zoom > 0:
                cam.wx = cam.wx + (FINISH - 0.3 - cam.wx) * zoom
            for L in (v.env, v.fig, v.hero, v.txt):
                L.canvas.save()
                L.canvas.clipRect(skia.Rect(0, y0, W, y1))
            e.drawLine(0, gy, W, gy, paint(WHITE, 0.55, 2.5))
            k0 = math.floor(cam.wx - 5)
            for k in range(k0, k0 + 12):
                sx, _ = cam.pt((k * 1.0, 0))
                e.drawLine(sx, gy + 10, sx - 18, gy + 26, paint(WHITE, 0.16, 2))
            for mk in range(0, 36, 5):
                if abs(mk - cam.wx) < 6:
                    sx, _ = cam.pt((mk + 1.8, 0))
                    e.drawLine(sx, gy, sx, gy - 0.9 * cam.s, paint(WHITE, 0.4, 3))
                    draw_spaced(tc, f"{mk}", sx, gy - 0.95 * cam.s, font(26, "InterDisplay-Bold"), 2, paint(WHITE, 0.6))
            if n == "DISCIPLINE" and abs(D_WATER - x) < 6:
                table(e, cam, D_WATER + 0.9, x < D_WATER - 0.3)
            if abs(FINISH - cam.wx) < 6:
                if n == "DISCIPLINE":
                    bu = None if ts < D_FIN else (ts - D_FIN) / 0.4
                else:
                    bu = None
                finish_gate(e, f_, cam, bu)
                crowd(e, cam, FINISH - 3.6 if n == "EGO" else FINISH + 2.6, ts, 3, phones=(n == "EGO"),
                      flash_t=ts if (n == "EGO" and ts > CELEB) else None)
            # ---------------- runners
            if n == "EGO":
                if FLEX[0] - 0.6 < ts < FLEX[1] + 0.6:
                    crowd(e, cam, 24.4, ts, 3, True, ts if FLEX[0] < ts < FLEX[1] else None)
                tired = smoothstep(WALL[0], WALL[0] + 0.8, ts) * (1 - smoothstep(LOOK[1], LOOK[1] + 0.3, ts))
                col = RED
                alpha = 1.0
                if tired > 0.3 and (int(t * 30) * 7919) % 9 < 4 * tired:
                    alpha = 0.45
                txt = None
                if BACKWARD[0] <= ts < BACKWARD[1]:
                    j = mirror(run_pose(x, -ph[n], 0.6, 0, -0.1, -0.2), x)
                    j["elbow1"] = j["shoulder"] + [-0.15, 0.4]
                    j["hand1"] = j["shoulder"] + [-0.25 + 0.15 * math.sin(ts * 16), 0.9]
                    txt = "TOO SLOW"
                elif SELFIE[0] <= ts < SELFIE[1]:
                    j = run_pose(x, ph[n], 0.7, 0, 0.0, -0.15)
                    j["elbow1"] = j["shoulder"] + [0.45, 0.2]
                    j["hand1"] = j["head"] + [0.55, 0.15]
                    hx, hy = cam.pt(j["hand1"])
                    hc.drawRoundRect(skia.Rect(hx - 0.08 * cam.s, hy - 0.14 * cam.s, hx + 0.08 * cam.s, hy + 0.14 * cam.s),
                                     4, 4, paint(WHITE, 1.0, 3))
                    for ft in (SELFIE[0] + 0.4, SELFIE[0] + 0.8):
                        if ft <= ts < ft + 0.15:
                            f_.drawCircle(hx, hy, 0.5 * cam.s, paint(WHITE, 0.9))
                elif FLEX[0] <= ts < FLEX[1]:
                    j = blend(run_pose(x, ph[n], 0.3), flex(x, ts), smoothstep(FLEX[0], FLEX[0] + 0.25, ts))
                    txt = "LOOK AT ME"
                elif LOOK[0] <= ts < LOOK[1]:
                    j = stand(x, -0.1, 0.4, 0.3, 0.6, 0.5, -0.6)
                    txt = "!?"
                elif ts >= CELEB:
                    u = smoothstep(CELEB, CELEB + 0.35, ts)
                    j = blend(run_pose(x, ph[n], 0.6), arms_up(x, ts), u)
                    if ts > CELEB + 0.3:
                        j = mirror(j, x)
                    txt = "EASY." if ts < D_FIN + 0.1 else None
                else:
                    inten = 1.0 - 0.6 * tired
                    j = run_pose(x, ph[n], inten, 0, 0.18 + 0.35 * tired, 0.1 + 0.5 * tired)
                draw_body(hc, j, cam, col, alpha, 0.15)
                if txt:
                    hx, hy = cam.pt(j["head"])
                    draw_spaced(tc, txt, hx, hy - 0.6 * cam.s, font(40, "InterDisplay-Black"), 2, paint(RED, 1.0))
                if ts > D_FIN + 0.4 and not frozen:
                    pass
            else:
                drinking = D_WATER - 0.3 <= x < D_WATER + 3
                if ts < D_FIN - 0.25:
                    j = run_pose(x, ph[n], 0.8, 0, 0.15, 0.05)
                elif ts < D_FIN + 0.2:
                    j = run_pose(x, ph[n], 0.9, 0, 0.55, 0.15)        # the lean
                else:
                    j = run_pose(x, ph[n], 0.5, 0, 0.1, 0.0)
                if drinking:
                    j["elbow1"] = j["shoulder"] + [0.3, -0.15]
                    j["hand1"] = j["head"] + [0.15, -0.05]
                draw_body(hc, j, cam, WHITE, 1.0, 0.15)
                if drinking:
                    bx, by = cam.pt(j["hand1"])
                    hc.save()
                    hc.translate(bx, by)
                    hc.rotate(-50)
                    hc.drawRoundRect(skia.Rect(-0.08 * cam.s, -0.4 * cam.s, 0.08 * cam.s, 0), 5, 5, paint(WHITE, 1.0, 3))
                    hc.restore()
            # photo-finish line
            if frozen or zoom > 0:
                fx, _ = cam.pt((FINISH, 0))
                f_.drawLine(fx, y0, fx, y1, paint(RED, 0.9 * zoom, 4))
            lx, _ = cam.pt((x, 0))
            draw_spaced(tc, n, lx, gy + 44, font(26, "Inter-Bold"), 5, paint(RED if n == "EGO" else WHITE, 1.0))
            ka = smoothstep(2.4, 2.7, t)
            draw_spaced(tc, f"KM {min(42, int(km(n, ts)))}", 760, y0 + 60, font(40, "InterDisplay-Black"), 2,
                        paint(WHITE, 0.9 * ka))
            if t >= FREEZE[0] + 1.1:
                pos = "1ST" if n == "DISCIPLINE" else "2ND"
                pop = 1 + 0.4 * math.exp(-(t - FREEZE[0] - 1.1) * 8)
                draw_spaced(tc, pos, 760, y0 + 125, font(56 * pop, "InterDisplay-Black"), 2,
                            paint(WHITE if pos == "1ST" else RED, 1.0))
            for L in (v.env, v.fig, v.hero, v.txt):
                L.canvas.restore()

        # divider: progress bar
        y = 950
        oc.drawRect(skia.Rect(0, 935, W, 965), paint((0, 0, 0), 1.0))
        oc.drawLine(120, y, 840, y, paint(WHITE, 0.35, 3))
        oc.drawLine(840, y - 12, 840, y + 12, paint(WHITE, 0.8, 3))
        for n, col in (("DISCIPLINE", WHITE), ("EGO", RED)):
            px = 120 + 720 * clamp(km(n, ts) / FINISH)
            oc.drawCircle(px, y, 11, paint(col, 1.0))
        if t < 2.6:
            ta = 1 - smoothstep(2.2, 2.6, t)
            caption(oc, "EGO VS DISCIPLINE", 405, ta, WHITE, 52)
            draw_spaced(oc, "42 KM", 760, 1025, font(40, "InterDisplay-Black"), 2, paint(RED, ta * smoothstep(0.2, 0.35, t)))
        if WALL[0] - 0.1 <= ts < WALL[0] + 1.6:
            caption(oc, "KM 33. THE WALL.", 962, smoothstep(WALL[0] - 0.1, WALL[0] + 0.1, ts) *
                    (1 - smoothstep(WALL[0] + 1.3, WALL[0] + 1.6, ts)), WHITE, 40)
        if frozen:
            pa = smoothstep(FREEZE[0], FREEZE[0] + 0.2, t)
            caption(oc, "PHOTO FINISH", 962, pa, RED, 46)
        ending(oc, t, END_T - 0.3, [(END_T, "EGO RAN", RED, 100), (END_T + 0.3, "FOR THE CROWD.", RED, 88),
                                    (END_T + 1.1, "DISCIPLINE RAN", WHITE, 92), (END_T + 1.4, "FOR THE LINE.", WHITE, 100)],
               gap=125)
        white = 0.0
        if FREEZE[0] <= t < FREEZE[0] + 0.25:
            white = 0.6 * (1 - (t - FREEZE[0]) / 0.25)
        dim = 0.25 * smoothstep(FREEZE[0], FREEZE[0] + 0.3, t) * (1 - smoothstep(FREEZE[1] - 0.2, FREEZE[1], t))
        v.compose(fi, t, white=white, dim=dim, fade_in=0.0)
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=LOOK[1]), gain=0.4, fade_in=0.3, fade_out=2.0, stop=DUR)
    last = {"EGO": -1.0, "DISCIPLINE": -1.0}
    for t, kind, _, extra in events:
        if kind.startswith("step_"):
            n = kind[5:]
            if t - last[n] < 0.08:
                continue
            last[n] = t
            if n == "EGO":
                m.add(t, sfx.step_light(extra), 0.26, 0.0, 0.1)
            else:
                m.add(t, sfx.step_heavy(extra), 0.22, 0.0, 0.15)
        elif kind == "go":
            m.add(0.0, sfx.beep(1320, 0.35), 0.6, 0, 0.3)
            m.add(0.02, sfx.text_hit(5), 0.6, 0, 0.4)
        elif kind == "back":
            m.add(t + 0.2, sfx.laugh(3, 5, 190, 0.5), 0.5, 0, 0.3)
        elif kind == "shutter":
            m.add(t, sfx.shutter(int(t * 10)), 0.6, 0, 0.2)
        elif kind == "flex":
            for q in range(6):
                m.add(t + 0.1 + q * 0.25, sfx.shutter(q), 0.45, 0, 0.2)
            m.add(t + 0.2, sfx.applause(1.4, 25, 2), 0.3, 0, 0.3)
        elif kind == "drink":
            m.add(t, sfx.chime(700, 0.25), 0.4, 0, 0.3)
        elif kind == "wall":
            m.add(t, sfx.power_down(1.6), 0.5, 0, 0.4)
            for q in range(3):
                m.add(t + 0.3 + q * 0.75, sfx.heartbeat(), 0.6, 0, 0.3)
        elif kind == "look":
            m.add(t, sfx.text_hit(2), 0.6, 0, 0.4)
        elif kind == "sprint":
            m.add(t, sfx.riser(D_FIN - t), 0.5, 0, 0.3)
        elif kind == "celeb":
            m.add(t, sfx.applause(1.5, 40, 3), 0.4, 0, 0.3)
        elif kind == "dfin":
            m.add(t, sfx.boom(2.5), 0.8, 0, 0.5)
        elif kind == "photo":
            m.add(t, sfx.shutter(9), 0.9, 0, 0.3)
            m.add(t, sfx.text_hit(4), 0.7, 0, 0.4)
        elif kind == "rank":
            m.add(t, sfx.text_hit(1), 0.7, 0, 0.4)
            m.add(t + 0.2, sfx.sparkle(1.2), 0.4, 0, 0.5)
        elif kind == "end":
            m.add(t, sfx.text_hit(1), 0.7, 0, 0.4)
        elif kind == "end2":
            m.add(t, sfx.text_hit(3), 0.9, 0, 0.5)
            m.add(t, sfx.boom(2.0), 0.4, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [0.8, 3.5, 5.0, 5.8, 6.8, 11.2, 12.6, 13.6, 14.4, 14.9, 15.15, 16.0, 17.0, 18.2, 22.0]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
