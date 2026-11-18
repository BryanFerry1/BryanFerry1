"""EP27 - EGO VS OBSESSION  (triathlon: swim, bike, run)

Zooms format, several phases, setback + comeback + surprise.
SWIM  Ego starts fast, then stops to wave at the camera: Obsession passes him.
BIKE  Obsession leads... flat tyre (PSSSH). He kneels and repairs. Ego rides past
      laughing (HAHA). Obsession gets back on, far behind.
RUN   A sign "5 KM LOOP". Ego looks around and ducks under the red NO ENTRY rope:
      shortcut straight to the finish, celebrates... the judge raises a red card:
      DISQUALIFIED. Obsession runs the whole loop (KM 1..5), comes back exhausted,
      walking, and breaks the tape. Falls to his knees, then raises his arms.
END   (black, centred) EGO TOOK THE SHORTCUT. / OBSESSION TOOK / THE LONG WAY.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import (FPS, H, L_FARM, L_UARM, RED, WHITE, W, Camera, Particles, build_pose, clamp, draw_spaced,
                    ease_out, font, ik, mix, paint, run_pose, smoothstep)
from kit import CX, GREY, Log, Video, arms_up, blend, caption, draw_body, ending, kneel, stand
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep27_triathlon"
dt = 1 / FPS
SWIM_END, BIKE_END, FINISH = 20.0, 45.0, 70.0
LOOP_X = 52.0
WATER_Y = 0.45
FLAT = (6.4, 8.2)
WAVE = (2.0, 3.4)
DUCK = (11.15, 11.5)
EGO_FIN = 12.4
DQ = 13.4
LOOP = (11.6, 14.4)
OBS_FIN = 16.2
END_T = 17.8
DUR = 21.8

E_KF = [(0, 0.0), (2.0, 9.5), (3.4, 10.2), (5.2, 20.0), (7.6, 30.0), (9.8, 45.0), (11.15, 52.0), (11.5, 52.4),
        (EGO_FIN, 71.7), (99, 71.7)]
O_KF = [(0, 0.0), (4.6, 20.0), (6.4, 30.0), (8.2, 30.0), (10.6, 45.0), (11.6, LOOP_X), (14.4, LOOP_X),
        (OBS_FIN, 70.0), (16.8, 70.6), (99, 70.6)]
SHOTS = [(0.0, "pair", 175), (2.1, "EGO", 210), (3.5, "pair", 110), (5.4, "OBS", 190), (6.4, "OBS", 235),
         (7.3, "EGO", 190), (8.4, "pair", 110), (10.9, "SIGN", 175), (12.4, "FIN", 150), (13.3, "EGO", 220),
         (14.3, "OBS", 175), (15.4, "FIN", 140)]


def lin(t, kf):
    if t <= kf[0][0]:
        return kf[0][1]
    for (t0, v0), (t1, v1) in zip(kf, kf[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * (t - t0) / (t1 - t0)
    return kf[-1][1]


def xpos(n, t):
    return lin(t, E_KF if n == "EGO" else O_KF)


def phase_of(x):
    return "swim" if x < SWIM_END else "bike" if x < BIKE_END else "run"


# ------------------------------------------------------------------ poses
def swim_pose(x, t, ph):
    hip = np.array([x, 0.38])
    neck = np.array([x + 0.9, 0.45])
    sh = hip + (neck - hip) * 0.86
    j = {"hip": hip, "neck": neck, "head": np.array([x + 1.25, 0.52]), "shoulder": sh}
    for i, off in ((1, 0.0), (2, math.pi)):
        a = t * 7 + ph + off
        hand = sh + np.array([0.55 + 0.4 * math.cos(a), 0.55 * math.sin(a)])
        j[f"hand{i}"] = hand
        j[f"elbow{i}"] = (sh + hand) / 2 + np.array([0.0, 0.12])
    k = math.sin(t * 14 + ph)
    j["knee1"], j["foot1"] = np.array([x - 0.75, 0.38 + 0.06 * k]), np.array([x - 1.5, 0.4 + 0.14 * k])
    j["knee2"], j["foot2"] = np.array([x - 0.75, 0.38 - 0.06 * k]), np.array([x - 1.5, 0.4 - 0.14 * k])
    return j


def tread_wave(x, t):
    j = stand(x, 0.0, 0.5, 2.8 + 0.25 * math.sin(t * 14), 0.4, 0.3, -0.15)
    return {k: v + [0, -1.05] for k, v in j.items()}


def bike_pose(x, t, ph):
    c = np.array([x, 0.38])
    p = t * 9 + ph
    f1 = c + 0.2 * np.array([math.cos(p), math.sin(p)])
    f2 = c - 0.2 * np.array([math.cos(p), math.sin(p)])
    j = build_pose(np.array([x - 0.28, 1.1]), f1, f2, 0.55, 1.0, 0.9, 0.3, 0.3, 0.1)
    sh = j["shoulder"]
    for i, off in ((1, 0.0), (2, -0.04)):
        hand = np.array([x + 0.5 + off, 1.18])
        j[f"hand{i}"] = hand
        j[f"elbow{i}"] = ik(sh, hand, L_UARM, L_FARM, -1)
    return j


def draw_bike(c, cam, x, col, alpha, flat=0.0):
    rh, fh = np.array([x - 0.62, 0.35]), np.array([x + 0.62, 0.35])
    seat, crank, handle = np.array([x - 0.25, 1.0]), np.array([x, 0.38]), np.array([x + 0.5, 1.15])
    lw = max(2, 0.045 * cam.s)
    for a, b in ((rh, crank), (crank, seat), (seat, rh), (seat, handle), (handle, fh), (crank, handle)):
        c.drawLine(*cam.pt(a), *cam.pt(b), paint(col, alpha, lw))
    fx, fy = cam.pt(fh)
    c.drawCircle(fx, fy, 0.35 * cam.s, paint(col, alpha, lw))
    rx, ry = cam.pt(rh)
    if flat > 0:
        r = skia.Rect(rx - 0.38 * cam.s, ry - 0.35 * cam.s * (1 - 0.45 * flat), rx + 0.38 * cam.s, ry + 0.35 * cam.s)
        c.drawOval(r, paint(mix(col, RED, flat), alpha, lw))
    else:
        c.drawCircle(rx, ry, 0.35 * cam.s, paint(col, alpha, lw))


def exhausted_run(x, ph):
    return run_pose(x, ph, 0.35, 0, 0.5, 0.6)


def scaled_about(j, foot, sc, dy):
    return {k: foot + (v - foot) * sc + np.array([0, dy]) for k, v in j.items()}


# ------------------------------------------------------------------ camera
def target(t):
    xe, xo = xpos("EGO", t), xpos("OBSESSION", t)
    cur = SHOTS[0]
    for s in SHOTS:
        if t >= s[0]:
            cur = s
    _, who, s = cur
    if who == "pair":
        mid = (xe + xo) / 2
        s = min(s, 800 / (abs(xe - xo) + 4.0))
        return mid + 0.3, 1.2, s
    if who == "EGO":
        return xe + 0.3, (0.6 if xe < SWIM_END else 1.4), s
    if who == "OBS":
        return xo - (0.4 if FLAT[0] <= t < FLAT[1] + 0.3 else -0.3), (0.7 if xo < SWIM_END else 1.2), s
    if who == "SIGN":
        return LOOP_X + 0.6, 1.4, s
    if who == "FIN":
        return FINISH + 0.4, 1.5, s
    return xe, 1.2, s


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    splash = Particles(2)
    dust = Particles(3)
    rng = np.random.default_rng(4)
    cam = Camera()
    cam.sx, cam.sy = CX, 1150.0
    cam.wx, cam.wy, cam.s = target(0.0)
    ph = {"EGO": 0.0, "OBSESSION": 1.3}
    for fi in range(v.n):
        t = fi * dt
        xe, xo = xpos("EGO", t), xpos("OBSESSION", t)
        for n in ph:
            vx = abs(xpos(n, t + 0.03) - xpos(n, t - 0.03)) / 0.06
            ph[n] += dt * (2 + vx * 1.2)
        for k, (ts, who, s) in enumerate(SHOTS[1:], 1):
            if t >= ts:
                log.once(f"cut{k}", ts, "cut", k)
        for key, tt, kind in (("go", 0.0, "go"), ("wave", WAVE[0], "wave"), ("bikeO", 4.6, "bike"),
                              ("bikeE", 5.2, "bike"), ("flat", FLAT[0], "flat"), ("laugh", 7.4, "laugh"),
                              ("fix", FLAT[1], "fix"), ("run", 10.6, "run"), ("duck", DUCK[0], "duck"),
                              ("efin", EGO_FIN, "efin"), ("dq", DQ, "dq"), ("loop", LOOP[0], "loop"),
                              ("back", LOOP[1], "back"), ("ofin", OBS_FIN, "ofin"), ("end", END_T, "end"),
                              ("end2", END_T + 1.0, "end2")):
            if t >= tt:
                log.once(key, tt, kind)
        for n, x in (("EGO", xe), ("OBSESSION", xo)):
            if x < SWIM_END and not (n == "EGO" and WAVE[0] <= t < WAVE[1]) and rng.random() < 0.5:
                splash.emit(np.array([[x + 0.5 + rng.normal(0, 0.4), WATER_Y]]), vel=(0, 1.5), spread=0.6,
                            life=(0.2, 0.5), size=(0.02, 0.05))
            if x >= BIKE_END and rng.random() < 0.25:
                dust.emit(np.array([[x - 0.3, 0.05]]), vel=(-0.6, 0.4), spread=0.3, life=(0.3, 0.5), size=(0.02, 0.04))
        splash.step(dt)
        dust.step(dt)
        if FLAT[0] <= t < FLAT[0] + 0.05:
            dust.emit(np.array([[30 - 0.62, 0.35]] * 16), vel=(0, 0.5), spread=1.4, life=(0.3, 0.7), size=(0.02, 0.05))
        wx, wy, s = target(t)
        snap = any(abs(t - ts) < dt * 0.6 for ts, _, _ in SHOTS[1:])
        k_ = 0.5 if snap else 0.18
        cam.wx += (wx - cam.wx) * k_
        cam.wy += (wy - cam.wy) * k_
        cam.s = math.exp(math.log(cam.s) + (math.log(s) - math.log(cam.s)) * k_)
        shake = 0.0
        for tt, a in ((DQ, 14.0), (OBS_FIN, 12.0)):
            if t >= tt:
                shake = max(shake, a * math.exp(-(t - tt) * 5))
        cam.sx = CX + shake * math.sin(t * 85)
        if not v.wants(fi):
            continue

        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        # ---------- world
        gy = cam.pt((0, 0))[1]
        wl, wyy = cam.pt((-10, WATER_Y))
        wr, _ = cam.pt((SWIM_END + 0.3, WATER_Y))
        if wr > 0:
            e.drawLine(wl, wyy, wr, wyy, paint(WHITE, 0.6, 3))
            for k in range(int(SWIM_END) + 12):
                xx = -10 + k + 0.3 * math.sin(t * 2 + k)
                p1 = cam.pt((xx, WATER_Y - 0.25))
                e.drawLine(p1[0], p1[1], p1[0] + 0.3 * cam.s, p1[1], paint(WHITE, 0.15, 2))
        gl, _ = cam.pt((SWIM_END + 0.3, 0))
        e.drawLine(max(gl, -10), gy, W + 10, gy, paint(WHITE, 0.55, 3))
        if gl < W:
            e.drawLine(gl, gy, gl, wyy, paint(WHITE, 0.55, 3))
        # zone markers
        for zx, lab in ((SWIM_END + 0.6, "T1  BIKE"), (BIKE_END, "T2  RUN")):
            px, py = cam.pt((zx, 0))
            if -100 < px < W + 100:
                e.drawLine(px, py, px, py - 1.8 * cam.s, paint(WHITE, 0.5, 3))
                draw_spaced(tc, lab, px, py - 1.95 * cam.s, font(max(20, 0.2 * cam.s), "Inter-Bold"), 3, paint(WHITE, 0.7))
        # loop sign + loop road + NO ENTRY rope
        sx_, sy_ = cam.pt((LOOP_X + 0.4, 0))
        if -300 < sx_ < W + 300:
            e.drawLine(sx_, sy_, sx_, sy_ - 2.0 * cam.s, paint(WHITE, 0.7, 4))
            br = skia.Rect(sx_ - 0.75 * cam.s, sy_ - 2.55 * cam.s, sx_ + 0.75 * cam.s, sy_ - 1.9 * cam.s)
            e.drawRect(br, paint((0, 0, 0), 1.0))
            e.drawRect(br, paint(WHITE, 0.9, 3, cap=False))
            draw_spaced(tc, "5 KM LOOP", sx_, sy_ - 2.12 * cam.s, font(max(18, 0.2 * cam.s), "InterDisplay-Black"), 2, paint(WHITE, 1))
            road = skia.Path()
            road.moveTo(*cam.pt((LOOP_X + 0.6, 0.0)))
            road.cubicTo(*cam.pt((LOOP_X + 2.0, 0.6)), *cam.pt((LOOP_X + 3.5, 1.6)), *cam.pt((LOOP_X + 1.5, 2.2)))
            e.drawPath(road, paint(WHITE, 0.25, max(2, 0.04 * cam.s)))
        for k in range(17):
            px0, py0 = cam.pt((LOOP_X + 1.0 + k, 0.0))
            if -50 < px0 < W + 50:
                e.drawLine(px0, py0, px0, py0 - 0.9 * cam.s, paint(WHITE, 0.4, 3))
        r0, r1 = cam.pt((LOOP_X + 1.0, 0.9)), cam.pt((LOOP_X + 17.0, 0.9))
        f_.drawLine(*r0, *r1, paint(RED, 0.9, max(3, 0.05 * cam.s)))
        nx_, ny_ = cam.pt((LOOP_X + 2.3, 0.9))
        if -200 < nx_ < W + 200:
            draw_spaced(tc, "NO ENTRY", nx_, ny_ - 12, font(max(16, 0.17 * cam.s), "InterDisplay-Black"), 2, paint(RED, 1.0))
        # finish gate + crowd + judge
        fx_, fy_ = cam.pt((FINISH, 0))
        if -400 < fx_ < W + 400:
            for k in range(9):
                hx, hy = cam.pt((FINISH - 4 + k * 1.0, 1.45 + 0.06 * abs(math.sin(t * 9 + k))))
                e.drawCircle(hx, hy, 0.2 * cam.s, paint(GREY, 0.3))
            for px in (FINISH, FINISH + 0.9):
                e.drawLine(*cam.pt((px, 0)), *cam.pt((px, 2.9)), paint(WHITE, 0.7, 4))
            e.drawLine(*cam.pt((FINISH, 2.9)), *cam.pt((FINISH + 0.9, 2.9)), paint(WHITE, 0.7, 4))
            gx, gyy = cam.pt((FINISH + 0.45, 2.9))
            draw_spaced(tc, "FINISH", gx, gyy - 12, font(max(18, 0.22 * cam.s), "InterDisplay-Black"), 3, paint(WHITE, 0.9))
            if t < OBS_FIN:
                f_.drawLine(*cam.pt((FINISH, 1.55)), *cam.pt((FINISH + 0.9, 1.55)), paint(RED, 1.0, max(3, 0.06 * cam.s)))
            else:
                b = ease_out(min(1, (t - OBS_FIN) / 0.4))
                f_.drawLine(*cam.pt((FINISH, 1.55)), *cam.pt((FINISH + 0.15, 1.55 - 1.2 * b)), paint(RED, 1, max(3, 0.06 * cam.s)))
                f_.drawLine(*cam.pt((FINISH + 0.9, 1.55)), *cam.pt((FINISH + 1.1, 1.55 - 1.1 * b)), paint(RED, 1, max(3, 0.06 * cam.s)))
            card = smoothstep(DQ - 0.2, DQ, t)
            jj = stand(FINISH + 2.9, 0.0, 0.2 + 2.7 * card, 0.1, 0.2, 0.1, 0.0)
            draw_body(hc, jj, cam, GREY, 0.8)
            if card > 0.05:
                hx, hy = cam.pt(jj["hand1"])
                hc.drawRect(skia.Rect(hx - 0.13 * cam.s, hy - 0.4 * cam.s, hx + 0.13 * cam.s, hy), paint(RED, card))
            draw_spaced(tc, "JUDGE", cam.pt((FINISH + 2.9, 0))[0], gy + 36, font(20, "Inter-Bold"), 3, paint(GREY, 0.8))
        splash.draw(f_, cam, WHITE, WHITE)
        dust.draw(f_, cam, WHITE, GREY)
        # ---------- racers
        joints = {}
        for n, x in (("OBSESSION", xo), ("EGO", xe)):
            col = RED if n == "EGO" else WHITE
            p = phase_of(x)
            alpha = 1.0
            if p == "swim":
                if n == "EGO" and WAVE[0] <= t < WAVE[1]:
                    j = tread_wave(x, t)
                else:
                    j = swim_pose(x, t, ph[n])
            elif p == "bike":
                if n == "OBSESSION" and FLAT[0] <= t < FLAT[1]:
                    draw_bike(hc, cam, 30.0, col, 1.0, smoothstep(FLAT[0], FLAT[0] + 0.2, t))
                    j = blend(bike_pose(30.0, t, 0), kneel(30.0 - 1.55, t, 0.3, 0.6), smoothstep(FLAT[0] + 0.2, FLAT[0] + 0.6, t))
                    if t > FLAT[0] + 0.6:
                        j["hand1"] = np.array([30 - 0.75, 0.45 + 0.05 * math.sin(t * 20)])
                        j["hand2"] = np.array([30 - 0.65, 0.3])
                else:
                    draw_bike(hc, cam, x, col, 1.0)
                    j = bike_pose(x, t, ph[n])
                    if n == "EGO" and 7.1 <= t < 8.3:
                        j["head"] = j["head"] + [-0.15, 0.05]
            else:
                if n == "EGO":
                    if t < DUCK[0]:
                        j = run_pose(x, ph[n], 0.9)
                    elif t < DUCK[1]:
                        j = run_pose(x, ph[n], 0.6, 0, 0.9, 0.5)
                        j = {k: v_ - [0, 0.35] if k not in ("foot1", "foot2") else v_ for k, v_ in j.items()}
                    elif t < EGO_FIN:
                        j = run_pose(x, ph[n], 0.95, 0, 0.3)
                    elif t < DQ + 0.3:
                        j = arms_up(x, t)
                    else:
                        j = blend(arms_up(x, t), kneel(x - 0.4, t, 1.0), smoothstep(DQ + 0.3, DQ + 0.8, t))
                        col = mix(RED, GREY, 0.4 * smoothstep(DQ + 0.3, DQ + 1.2, t))
                else:
                    if t < LOOP[0]:
                        j = run_pose(x, ph[n], 0.85)
                    elif t < LOOP[1]:
                        u = (t - LOOP[0]) / (LOOP[1] - LOOP[0])
                        d = math.sin(math.pi * u)
                        base = run_pose(0.0, ph[n], 0.8)
                        foot = np.array([0.0, 0.0])
                        j = scaled_about(base, foot, 1 - 0.65 * d, 1.9 * d)
                        j = {k: v_ + [x + 1.2 * d, 0] for k, v_ in j.items()}
                        alpha = 1 - 0.4 * d
                    elif t < OBS_FIN:
                        j = exhausted_run(x, ph[n])
                        col = mix(WHITE, RED, 0.35)
                    elif t < 16.8:
                        j = kneel(x - 0.3, t, 0.8)
                    else:
                        j = blend(kneel(x - 0.3, t, 0.8), arms_up(x, t), smoothstep(16.8, 17.2, t))
            draw_body(hc, j, cam, col, alpha, 0.1 if n == "EGO" else 0.3)
            joints[n] = (j, p)
        # water covers submerged parts
        if wr > 0:
            hc.drawRect(skia.Rect(-10, wyy, wr, H), paint((0.02, 0.02, 0.03), 0.55))
        # ---------- callouts
        je, _ = joints["EGO"]
        jo, _ = joints["OBSESSION"]
        if WAVE[0] + 0.15 <= t < WAVE[1]:
            hx, hy = cam.pt(je["head"])
            draw_spaced(oc, "HI CAMERA!", min(hx + 60, 780), hy - 0.7 * cam.s, font(44, "InterDisplay-Black"), 2, paint(RED, 1.0))
        if FLAT[0] <= t < FLAT[0] + 1.0:
            hx, hy = cam.pt((30 - 0.62, 0.9))
            pop = 1 + 0.4 * math.exp(-(t - FLAT[0]) * 8)
            draw_spaced(oc, "PSSSHH", hx, hy - 0.4 * cam.s, font(56 * pop, "InterDisplay-Black"), 2,
                        paint(RED, 1 - smoothstep(FLAT[0] + 0.7, FLAT[0] + 1.0, t)))
        if 7.4 <= t < 8.4:
            hx, hy = cam.pt(je["head"])
            draw_spaced(oc, "HAHA", hx - 0.2 * cam.s, hy - 0.55 * cam.s, font(50, "InterDisplay-Black"), 2, paint(RED, 1.0))
        if LOOP[0] + 0.2 <= t < LOOP[1]:
            u = (t - LOOP[0]) / (LOOP[1] - LOOP[0])
            hx, hy = cam.pt(jo["head"])
            draw_spaced(oc, f"KM {1 + min(4, int(u * 5))}", hx, hy - 50, font(40, "InterDisplay-Black"), 2, paint(WHITE, 1.0))
        if t >= DQ and 40 < cam.pt(je["head"])[0] < W - 40:
            hx, hy = cam.pt(je["head"])
            pop = 1 + 0.5 * math.exp(-(t - DQ) * 9)
            oc.save()
            oc.translate(min(max(hx, 300), 660), hy - 0.9 * cam.s * 0 - 160)
            oc.rotate(-12)
            oc.scale(pop, pop)
            f = font(64, "InterDisplay-Black")
            r = skia.Rect(-270, -62, 270, 22)
            a = 1 - smoothstep(END_T - 0.6, END_T - 0.3, t)
            oc.drawRect(r, paint((0, 0, 0), 0.85 * a))
            oc.drawRect(r, paint(RED, a, 6, cap=False))
            draw_spaced(oc, "DISQUALIFIED", 0, 0, f, 2, paint(RED, a))
            oc.restore()
        # labels on wide shots
        la = 1 - smoothstep(150, 190, cam.s)
        for n, col in (("EGO", RED), ("OBSESSION", WHITE)):
            j, p = joints[n]
            fx = j["hip"][0]
            yy = WATER_Y if p == "swim" else 0
            sx, sy = cam.pt((fx, yy))
            draw_spaced(tc, n, sx, sy + 40, font(24, "Inter-Bold"), 4, paint(col, la))
        # HUD: discipline of the shot
        seg = phase_of(cam.wx)
        hud_a = 1 - smoothstep(END_T - 0.6, END_T - 0.3, t)
        if t >= 1.8:
            draw_spaced(oc, "TRIATHLON", CX, 360, font(24, "Inter-SemiBold"), 10, paint(WHITE, 0.7 * hud_a))
            draw_spaced(oc, seg.upper(), CX, 455, font(88, "InterDisplay-Black"), 6, paint(WHITE, hud_a))
        else:
            caption(oc, "EGO VS OBSESSION", 520, 1 - smoothstep(1.4, 1.8, t), WHITE, 64)
        ending(oc, t, END_T - 0.3, [(END_T, "EGO TOOK", RED, 96), (END_T + 0.25, "THE SHORTCUT.", RED, 96),
                                    (END_T + 1.0, "OBSESSION TOOK", WHITE, 86), (END_T + 1.25, "THE LONG WAY.", WHITE, 86)],
               gap=118)
        flash = math.exp(-(t - OBS_FIN) * 3) if t >= OBS_FIN else 0.0
        white = 0.08 * max(0.0, 1 - min(abs(t - ts) for ts, _, _ in SHOTS[1:]) / 0.05)
        v.compose(fi, t, flash=flash * 0.8, white=white, fade_in=0.0)
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=OBS_FIN), gain=0.4, fade_in=0.3, fade_out=2.0, stop=DUR)
    t_ = 0.1
    while t_ < 5.0:                                                      # swim strokes
        m.add(t_, sfx.bandnoise(0.15, 800, 7000, int(t_ * 50)) * np.exp(-np.linspace(0, 6, int(0.15 * sfx.SR))) * 0.5,
              0.35, -0.2 + 0.4 * ((int(t_ * 3)) % 2), 0.3)
        t_ += 0.32
    m.add(4.6, sfx.rattle(5.2, 3) * 0.6, 0.35, 0, 0.2)                    # bike chains
    t_ = 10.6
    k = 0
    while t_ < OBS_FIN:                                                  # running steps
        m.add(t_, sfx.step_light(k), 0.25, 0, 0.1)
        t_ += 0.21 if t_ < LOOP[1] else 0.4
        k += 1
    for t, kind, _, extra in events:
        if kind == "go":
            m.add(0.0, sfx.beep(1320, 0.35), 0.6, 0, 0.3)
            m.add(0.05, sfx.bandnoise(1.0, 300, 8000, 2) * np.exp(-np.linspace(0, 4, sfx.SR)) * 0.8, 0.6, 0, 0.3)
        elif kind == "cut":
            m.add(t - 0.05, sfx.whoosh(0.25, 500, 9000, 0.6, seed=extra), 0.4, 0, 0.2)
        elif kind == "wave":
            m.add(t + 0.1, sfx.chime(880, 0.3), 0.5, -0.3, 0.4)
        elif kind == "bike":
            m.add(t, sfx.tick(2400, 0.4), 0.4, 0, 0.1)
        elif kind == "flat":
            m.add(t, sfx.bandnoise(1.0, 2000, 9000, 6) * np.linspace(1, 0, sfx.SR) * 0.9, 0.7, 0.3, 0.3)
            m.add(t, sfx.punch_block(2), 0.6, 0.3, 0.3)
            m.add(t + 0.3, sfx.power_down(1.0), 0.4, 0.3, 0.4)
        elif kind == "laugh":
            m.add(t, sfx.laugh(7, 5, 160, 0.6), 0.6, -0.3, 0.4)
        elif kind == "fix":
            m.add(t - 0.6, sfx.plate_clank(3, 0.3), 0.4, 0.3, 0.3)
            m.add(t, sfx.power_up(80), 0.7, 0.3, 0.4)
        elif kind == "run":
            m.add(t, sfx.tick(2400, 0.4), 0.4, 0, 0.1)
        elif kind == "duck":
            m.add(t, sfx.whoosh(0.4, 300, 6000, 0.5, seed=4), 0.6, -0.3, 0.3)
            m.add(t + 0.05, sfx.glitch(2), 0.4, -0.3, 0.2)
        elif kind == "loop":
            m.add(t, sfx.chime(520, 0.3), 0.5, 0.3, 0.5)
            m.add(t + 0.3, sfx.heartbeat(), 0.6, 0.3, 0.3)
        elif kind == "efin":
            m.add(t, sfx.applause(1.2, 40, 2), 0.5, 0, 0.3)
            m.add(t, sfx.text_hit(2), 0.6, 0, 0.4)
        elif kind == "dq":
            m.add(t - 0.15, sfx.beep(2800, 0.25), 0.8, 0, 0.3)
            m.add(t + 0.15, sfx.beep(2800, 0.6), 0.8, 0, 0.3)
            m.add(t + 0.1, sfx.text_hit(4), 0.9, 0, 0.4)
            m.add(t + 0.1, sfx.boom(2.5), 0.7, 0, 0.4)
            m.add(t + 0.4, sfx.power_down(1.4), 0.5, -0.3, 0.4)
        elif kind == "back":
            m.add(t, sfx.breath(5, 1.2), 0.7, 0.3, 0.2)
            m.add(t + 0.4, sfx.riser(OBS_FIN - t - 0.4), 0.5, 0, 0.3)
            m.add(t + 0.3, sfx.heartbeat(), 0.8, 0, 0.3)
            m.add(t + 1.1, sfx.heartbeat(), 0.85, 0, 0.3)
        elif kind == "ofin":
            m.add(t, sfx.boom(4.0), 1.0, 0, 0.5)
            m.add(t + 0.2, sfx.applause(3.2, 60, 5), 0.6, 0, 0.3)
            m.add(t, sfx.sparkle(1.6), 0.5, 0, 0.5)
        elif kind == "end":
            m.add(t, sfx.text_hit(1), 0.7, 0, 0.4)
        elif kind == "end2":
            m.add(t, sfx.text_hit(3), 0.95, 0, 0.5)
            m.add(t, sfx.boom(2.0), 0.45, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [0.5, 1.5, 2.6, 4.2, 5.8, 6.8, 7.7, 9.2, 11.3, 12.0, 12.8, 13.7, 14.0, 15.0, 16.0, 16.9, 19.5]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
