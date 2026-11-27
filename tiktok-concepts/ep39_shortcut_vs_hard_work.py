"""EP39 - SHORTCUT VS HARD WORK  (elevator vs stairs, 100 floors)

Split screen + zooms, FLOOR counters, progress bar on the divider.
TOP     SHORTCUT takes the elevator: floors fly by, phone in hand (STAIRS? LOL).
        FLOOR 87: jolt, lights flicker, red alarm. STUCK. Bangs on the doors.
        Sits in the dark. OUT OF ORDER.
BOTTOM  HARD WORK takes the stairs: slow, step by step, sweat. Floor 50: sits
        down, out of breath (HALFWAY...). Gets up. Floor 87: walks past the
        elevator door... HELP! from inside. Keeps climbing.
        Floor 100: the rooftop, sunrise, arms up.
END     THE ELEVATOR WAS FASTER. / THE STAIRS NEVER BROKE.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import (FPS, H, L_SHIN, L_THIGH, RED, WHITE, W, Camera, clamp, draw_spaced, ease_out, fit_font, font,
                    ik, paint, run_pose, smoothstep)
from kit import GREY, Log, Video, arms_up, caption, draw_body, ending, sit, stand
from ep37_motivation_vs_discipline_30days import stamp
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep39_shortcut_vs_hard_work"
dt = 1 / FPS
S = 120.0
LANES = {"SHORTCUT": (330, 935, 860), "HARD WORK": (965, 1565, 1475)}
RUN, RISE, PER = 0.42, 0.3, 10            # stair step, steps per floor
FLOOR_H = RISE * PER
STUCK = 7.0
HALF = (12.0, 13.6)
DOOR = (17.0, 18.7)
TOP = 19.4
END_T = 21.2
DUR = 25.2
E_FL = [(0, 0), (1.0, 0), (STUCK, 87)]
H_FL = [(0, 0), (1.0, 0), (9.4, 8), (12.0, 50), (HALF[1], 50), (16.5, 85), (17.3, 86.9), (18.7, 88.0), (TOP, 100)]
FULL = [(4.4, 6.3, "SHORTCUT", 175, 190), (7.0, 9.4, "SHORTCUT", 175, 195), (HALF[0], HALF[1], "HARD WORK", 215, 240),
        (DOOR[0], DOOR[1], "HARD WORK", 175, 195), (TOP, 21.4, "HARD WORK", 220, 170)]


def keys(t, kf):
    if t <= kf[0][0]:
        return kf[0][1]
    for (t0, v0), (t1, v1) in zip(kf, kf[1:]):
        if t <= t1:
            u = (t - t0) / (t1 - t0)
            if kf is E_FL:
                u = u * u * (3 - 2 * u)
            return v0 + (v1 - v0) * u
    return kf[-1][1]


def floor_of(n, t):
    return keys(t, E_FL if n == "SHORTCUT" else H_FL)


def full_at(t):
    for f in FULL:
        if f[0] <= t < f[1]:
            return f
    return None


# ------------------------------------------------------------------ stairs
def stair_h(x):
    k = math.floor(x / RUN)
    return min(max(k, 0), 100 * PER) * RISE


def climber_xy(fl):
    s = fl * PER
    return s * RUN + 0.25, s * RISE


def climb_pose(fl, t, tired=0.0):
    x, y = climber_xy(fl)
    ph = fl * PER * math.pi * 0.95
    j = run_pose(x, ph, 0.42, y, 0.25 + 0.3 * tired, 0.1 + 0.4 * tired)
    for f, k in (("foot1", "knee1"), ("foot2", "knee2")):
        fx = j[f][0]
        lift = j[f][1] - y
        j[f] = np.array([fx, stair_h(fx) + lift])
        j[k] = ik(j["hip"], j[f], L_THIGH, L_SHIN, 1)
    return j


def draw_stairs(c, cam, x0, x1, top_floor=100):
    p = skia.Path()
    k0 = max(0, math.floor(x0 / RUN))
    k1 = min(top_floor * PER, math.ceil(x1 / RUN))
    first = True
    for k in range(k0, k1 + 1):
        a = cam.pt((k * RUN, k * RISE))
        b = cam.pt(((k + 1) * RUN, k * RISE))
        if first:
            p.moveTo(*a)
            first = False
        else:
            p.lineTo(*a)
        p.lineTo(*b)
        if k < top_floor * PER:
            p.lineTo(*cam.pt(((k + 1) * RUN, (k + 1) * RISE)))
    c.drawPath(p, paint(WHITE, 0.7, max(2.5, 0.035 * cam.s)))
    # floor signs every PER steps
    for fl in range(max(0, k0 // PER), min(100, k1 // PER) + 1):
        sx, sy = cam.pt((fl * PER * RUN + 0.2, fl * PER * RISE + 2.6))
        draw_spaced(c, str(fl), sx, sy, font(max(14, 0.3 * cam.s), "InterDisplay-Black"), 2, paint(WHITE, 0.45))
    if k1 >= top_floor * PER:                       # roof
        rx, ry = top_floor * PER * RUN, top_floor * PER * RISE
        c.drawLine(*cam.pt((rx, ry)), *cam.pt((rx + 8, ry)), paint(WHITE, 0.7, max(2.5, 0.035 * cam.s)))


def elevator_door(c, cam, x, y, alpha=1.0):
    r = skia.Rect(*cam.pt((x - 0.55, y + 2.2)), *cam.pt((x + 0.55, y)))
    c.drawRect(r, paint((0, 0, 0), alpha))
    c.drawRect(r, paint(WHITE, 0.8 * alpha, 3, cap=False))
    c.drawLine(*cam.pt((x, y + 2.2)), *cam.pt((x, y)), paint(WHITE, 0.6 * alpha, 2))
    sx, sy = cam.pt((x, y + 2.55))
    draw_spaced(c, "87", sx, sy, font(max(14, 0.28 * cam.s), "InterDisplay-Black"), 2, paint(RED, alpha))


# ------------------------------------------------------------------ elevator
def cabin_y(t):
    return floor_of("SHORTCUT", t) * FLOOR_H + (0.0 if t < STUCK else -0.12 * math.exp(-(t - STUCK) * 6))


def draw_shaft(c, cam, ycen, span):
    w = max(2.5, 0.035 * cam.s)
    for sx_ in (-1.25, 1.25):
        c.drawLine(*cam.pt((sx_, ycen - span)), *cam.pt((sx_, ycen + span)), paint(WHITE, 0.35, w))
    f0 = math.floor((ycen - span) / FLOOR_H)
    for fl in range(max(0, f0), f0 + int(2 * span / FLOOR_H) + 2):
        yy = fl * FLOOR_H
        c.drawLine(*cam.pt((-1.25, yy)), *cam.pt((-1.7, yy)), paint(WHITE, 0.35, w))
        sx, sy = cam.pt((-1.85, yy + 0.25))
        draw_spaced(c, str(fl), sx - 0.15 * cam.s, sy, font(max(14, 0.3 * cam.s), "InterDisplay-Black"), 2,
                    paint(WHITE, 0.5))


def draw_cabin(c, f_, cam, y, t, light=1.0, alarm=False):
    r = skia.Rect(*cam.pt((-1.1, y + 3.3)), *cam.pt((1.1, y)))
    c.drawRect(r, paint(WHITE, 0.06 * light))
    c.drawRect(r, paint(WHITE, 0.85, max(3, 0.045 * cam.s), cap=False))
    c.drawLine(*cam.pt((0.0, y + 3.3)), *cam.pt((0.0, y + 3.7)), paint(WHITE, 0.6, 3))
    if alarm and int(t * 4) % 2 == 0:
        ax, ay = cam.pt((0.8, y + 3.05))
        f_.drawCircle(ax, ay, 0.12 * cam.s, paint(RED, 1.0))


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    last_fl = {"SHORTCUT": 0, "HARD WORK": 0}
    for fi in range(v.n):
        t = fi * dt
        for n in last_fl:
            fl = int(floor_of(n, t))
            if fl != last_fl[n]:
                log.add(t, "floor_" + ("e" if n == "SHORTCUT" else "h"), fl)
                last_fl[n] = fl
        for key, tt, kind in (("ding", 0.6, "ding"), ("stuck", STUCK, "stuck"), ("bang", 8.0, "bang"),
                              ("half", HALF[0], "half"), ("door", DOOR[0] + 0.5, "help"), ("top", TOP, "top"),
                              ("end", END_T, "end"), ("end2", END_T + 1.3, "end2")):
            if t >= tt:
                log.once(key, tt, kind)
        for k, f in enumerate(FULL):
            if t >= f[0]:
                log.once(f"full{k}", f[0], "zoom")
        if not v.wants(fi):
            continue

        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        fz = full_at(t)
        panes = []
        if fz is None:
            for n, (y0, y1, gy) in LANES.items():
                cam = Camera()
                cam.s = S
                if n == "SHORTCUT":
                    cam.wx, cam.wy = 0.0, cabin_y(t) + 1.7
                    cam.sx, cam.sy = 470, (y0 + y1) / 2 + 20
                else:
                    x, y = climber_xy(floor_of(n, t))
                    cam.wx, cam.wy = x, y + 1.3
                    cam.sx, cam.sy = 430, (y0 + y1) / 2 + 30
                panes.append((n, y0, y1, cam, False))
        else:
            t0, t1, n, s0, s1 = fz
            u = (t - t0) / (t1 - t0)
            cam = Camera()
            cam.s = s0 + (s1 - s0) * ease_out(u)
            if n == "SHORTCUT":
                cam.wx, cam.wy = 0.0, cabin_y(t) + 1.4
            else:
                x, y = climber_xy(floor_of(n, t))
                cam.wx, cam.wy = x + (0.9 if (DOOR[0] <= t < DOOR[1]) else 0.3), y + 1.4
            cam.sx, cam.sy = 450, 1000
            panes = [(n, 0, H, cam, True)]
        flash = 0.0
        for n, y0, y1, cam, full in panes:
            for L in (v.env, v.fig, v.hero, v.txt):
                L.canvas.save()
                L.canvas.clipRect(skia.Rect(0, y0, W, y1))
            span = (y1 - y0) / cam.s
            txt = None
            if n == "SHORTCUT":
                col = RED
                y = cabin_y(t)
                draw_shaft(e, cam, y + 1.2, span)
                stuck = t >= STUCK
                light = 1.0 if not stuck else (0.2 if int(t * 7) % 3 else 1.0)
                draw_cabin(e, f_, cam, y, t, light, stuck)
                if not stuck:
                    j = stand(0.0, 0.1, 0.9, 0.85, 1.4, 1.45, 0.55)
                    j = {k: vv + [0, y] for k, vv in j.items()}
                    hx, hy = cam.pt(j["hand1"])
                    hc.drawRoundRect(skia.Rect(hx - 0.08 * cam.s, hy - 0.22 * cam.s, hx + 0.08 * cam.s, hy), 3, 3,
                                     paint(WHITE, 1.0, 3))
                    if 4.4 < t < STUCK:
                        txt = "STAIRS? LOL"
                elif t < 9.6:
                    bang = 0.5 + 0.5 * math.sin(t * 14)
                    j = stand(0.25, -0.05, 1.6 + 0.6 * bang, 1.4, 0.5, 0.5, -0.1)
                    j = {k: vv + [0, y] for k, vv in j.items()}
                    txt = "STUCK!" if t < 8.2 else "HELLO?!"
                else:
                    j = sit(-0.4, 0.05, t, 0.8)
                    j = {k: vv + [0, y] for k, vv in j.items()}
                draw_body(hc, j, cam, col, 1.0 if light > 0.5 else 0.55, 0.15)
                if stuck and t > 9.6:
                    sx, sy = cam.pt((0.0, y + 4.0))
                    draw_spaced(tc, "OUT OF ORDER", sx, sy, font(max(16, 0.32 * cam.s), "InterDisplay-Black"), 3,
                                paint(RED, 0.9))
            else:
                col = WHITE
                fl = floor_of(n, t)
                x, y = climber_xy(fl)
                draw_stairs(e, cam, x - 700 / cam.s, x + 700 / cam.s)
                dx_door = 368.4
                dy_door = stair_h(dx_door)
                if abs(x - dx_door) < 8:
                    elevator_door(e, cam, dx_door, dy_door)
                    if DOOR[0] + 0.3 < t < DOOR[0] + 1.25:
                        sx, sy = cam.pt((dx_door + 1.5, dy_door + 2.0))
                        if int(t * 5) % 2 == 0:
                            draw_spaced(tc, "HELP!", sx, sy - 0.2 * cam.s, font(max(16, 0.42 * cam.s), "InterDisplay-Black"),
                                        2, paint(RED, 1.0))
                        for q in range(3):
                            bx, by = cam.pt((dx_door + 0.62, dy_door + 1.0 + 0.3 * q))
                            f_.drawLine(bx, by, bx + 0.2 * cam.s, by - 0.05 * cam.s * (q - 1), paint(RED, 0.8, 3))
                if fl >= 99.9:
                    sx, sy = cam.pt((x + 2.3, y + 2.3))
                    e.drawCircle(sx, sy, 0.6 * cam.s, paint(WHITE, 0.9, 4))
                    j = arms_up(x + 0.6 * smoothstep(TOP, TOP + 0.4, t), t)
                    j = {k: vv + [0, y] for k, vv in j.items()}
                    if t < TOP + 0.5:
                        flash = 0.5 * math.exp(-(t - TOP) * 5)
                elif HALF[0] <= t < HALF[1] - 0.3:
                    j = sit(x - 0.2, 0.0, t, 0.9)
                    j = {k: vv + [0, y] for k, vv in j.items()}
                    txt = "HALFWAY..."
                else:
                    tired = smoothstep(4.0, 9.0, t) * (1 - smoothstep(HALF[1], HALF[1] + 1, t)) + 0.4 * smoothstep(16.0, 18.0, t)
                    j = climb_pose(fl, t, tired)
                    if tired > 0.3:
                        hx, hy = cam.pt(j["head"])
                        for q in range(2):
                            f_.drawCircle(hx - 0.35 * cam.s - q * 0.15 * cam.s, hy + 0.1 * cam.s * math.sin(t * 9 + q),
                                          max(3, 0.03 * cam.s), paint(WHITE, 0.8))
                draw_body(hc, j, cam, col, 1.0, 0.15)
            if txt:
                hx, hy = cam.pt(j["head"])
                ty = hy - 0.75 * cam.s
                if full:
                    ty = max(ty, 640)
                else:
                    ty = max(ty, y0 + 70)
                hx = min(max(hx, 260), 640)
                draw_spaced(tc, txt, hx, ty, fit_font(txt, 44 if not full else 64, "InterDisplay-Black", 2, 560), 2,
                            paint(col, 1.0))
            if not full:
                lx, ly = cam.pt((j["hip"][0], j["hip"][1] - 1.0)) if n == "HARD WORK" else cam.pt((0.0, cabin_y(t) - 0.15))
                draw_spaced(tc, n, lx, ly + 52, font(26, "Inter-Bold"), 5, paint(col, 1.0))
                draw_spaced(tc, f"FLOOR {int(floor_of(n, t))}", 760, y0 + 62, font(42, "InterDisplay-Black"), 2,
                            paint(col, 1.0))
            for L in (v.env, v.fig, v.hero, v.txt):
                L.canvas.restore()
            if n == "SHORTCUT" and full and STUCK <= t < STUCK + 1.2:
                stamp(oc, 470, 1400, "STUCK", (t - STUCK) / 1.2)
        if fz is None:
            y = 950
            oc.drawRect(skia.Rect(0, 935, W, 965), paint((0, 0, 0), 1.0))
            oc.drawLine(120, y, 840, y, paint(WHITE, 0.35, 3))
            oc.drawLine(840, y - 12, 840, y + 12, paint(WHITE, 0.8, 3))
            for n, c_ in (("HARD WORK", WHITE), ("SHORTCUT", RED)):
                px = 120 + 720 * clamp(floor_of(n, t) / 100)
                oc.drawCircle(px, y, 11, paint(c_, 1.0))
        else:
            n = fz[2]
            draw_spaced(oc, f"FLOOR {int(floor_of(n, t))}", 470, 470, font(96, "InterDisplay-Black"), 3,
                        paint(RED if n == "SHORTCUT" else WHITE, 1.0))
            draw_spaced(oc, n, 470, 380, font(34, "Inter-Bold"), 8, paint(RED if n == "SHORTCUT" else WHITE, 0.8))
        if t < 2.2:
            caption(oc, "SHORTCUT VS HARD WORK", 420, 1 - smoothstep(1.8, 2.2, t), WHITE, 50)
            draw_spaced(oc, "100 FLOORS", 700, 1035, font(36, "InterDisplay-Black"), 2,
                        paint(RED, (1 - smoothstep(1.8, 2.2, t)) * smoothstep(0.2, 0.4, t)))
        ending(oc, t, END_T - 0.3, [(END_T, "THE ELEVATOR", RED, 100), (END_T + 0.3, "WAS FASTER.", RED, 110),
                                    (END_T + 1.1, "THE STAIRS", WHITE, 110), (END_T + 1.4, "NEVER BROKE.", WHITE, 110)],
               gap=125)
        cut = 0.0
        for tt in [f[0] for f in FULL] + [f[1] for f in FULL]:
            if tt <= t < tt + 0.1:
                cut = 0.07
        if STUCK <= t < STUCK + 0.3:
            flash = max(flash, 0.4 * (1 - (t - STUCK) / 0.3))
        v.compose(fi, t, flash=flash, white=cut + 0.2 * flash, fade_in=0.0)
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=16.0), gain=0.35, fade_in=0.3, fade_out=2.0, stop=DUR)
    lastf = -1.0
    for t, kind, _, extra in events:
        if kind == "floor_e":
            m.add(t, sfx.tick(3400, 0.15), 0.3, 0, 0.1)
        elif kind == "floor_h":
            if t - lastf > 0.09:
                m.add(t, sfx.step_heavy(extra), 0.4, 0, 0.15)
                lastf = t
        elif kind == "ding":
            m.add(t, sfx.chime(1320, 0.3), 0.5, 0, 0.4)
            m.add(t + 0.15, sfx.chime(990, 0.3), 0.5, 0, 0.4)
        elif kind == "zoom":
            m.add(t, sfx.whoosh(0.3, 400, 8000, 0.4, seed=int(t)), 0.35, 0, 0.2)
        elif kind == "stuck":
            m.add(t, sfx.punch_block(2), 0.9, 0, 0.3)
            m.add(t, sfx.power_down(1.2), 0.6, 0, 0.4)
            for q in range(6):
                m.add(t + 0.3 + q * 0.5, sfx.beep(660, 0.25), 0.45, 0, 0.2)
        elif kind == "bang":
            for q in range(5):
                m.add(t + q * 0.22, sfx.punch_hit(q, 0.7), 0.6, 0, 0.3)
        elif kind == "half":
            for q in range(3):
                m.add(t + q * 0.5, sfx.breath(q, 0.45), 0.5, 0, 0.3)
        elif kind == "help":
            for q in range(4):
                m.add(t + q * 0.35, sfx.punch_hit(q + 3, 0.5), 0.5, 0.2, 0.4)
        elif kind == "top":
            m.add(t, sfx.boom(2.5), 0.8, 0, 0.5)
            m.add(t + 0.1, sfx.sparkle(1.5), 0.5, 0, 0.5)
        elif kind == "end":
            m.add(t, sfx.text_hit(1), 0.7, 0, 0.4)
        elif kind == "end2":
            m.add(t, sfx.text_hit(3), 0.9, 0, 0.5)
            m.add(t, sfx.boom(2.0), 0.4, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [0.8, 3.0, 5.2, 7.5, 8.6, 10.5, 12.6, 15.0, 17.2, 18.0, 19.8, 20.8, 23.0]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
