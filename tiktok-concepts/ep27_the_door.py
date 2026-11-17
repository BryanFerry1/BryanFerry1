"""EP27 - EGO VS OBSESSION  (the door)

One shared scene, zooms format (EP25/EP26). A long stone wall with two giant
sliding stone doors engraved "DREAM". Each one pushes his own door to the right.
An OPEN % counter sits above each door: the outcome builds up step by step.
  zoom EGO: pushes hard, door barely moves (2%).
  zoom OBSESSION's feet: slipping, digging in.
  wide: both doors almost shut.
  zoom EGO: kicks the door, yells "OPEN!", gives up, sits with arms crossed.
          His door slides back shut (0%).
  zoom OBSESSION's face: sweat, red aura.
  wide: his door creeps open, light leaks through (35%...).
  zoom on the gap: light pouring out. Ego turns his head.
  wide: the door bursts open (100%), light floods, Obsession walks into it.
END (black, centred) EGO KNOCKED. / OBSESSION PUSHED / UNTIL IT OPENED.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import (FPS, H, RED, WHITE, W, Camera, Particles, build_pose, clamp, draw_spaced, ease_out, font,
                    mix, paint, run_pose, smoothstep)
from kit import CX, GREY, Log, Video, blend, caption, crossed, draw_body, ending, sit, stand
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep27_the_door"
dt = 1 / FPS
DOOR_W, DOOR_H = 1.6, 3.2
D_E, D_O = -2.4, 1.0            # left edge of each doorway (world x)
GO = 1.6
KICK = 6.9
QUIT = 7.6
BURST = 13.0
END_T = 15.6
DUR = 19.6

E_KF = [(0, 0.0), (GO, 0.0), (3.5, 0.02), (6.6, 0.03), (QUIT, 0.03), (8.6, 0.0)]
O_KF = [(0, 0.0), (GO, 0.0), (5.0, 0.03), (8.2, 0.08), (10.0, 0.35), (12.2, 0.62), (BURST, 0.66), (BURST + 0.4, 1.0)]
SHOTS = [(0.0, "wide", 128), (2.3, "EGO", 210), (3.8, "OBS_FEET", 230), (5.2, "wide", 128), (6.4, "EGO", 200),
         (8.4, "OBS", 215), (9.9, "wide", 128), (11.2, "GAP", 210), (12.4, "wide", 128)]


def keys(t, kf):
    if t <= kf[0][0]:
        return kf[0][1]
    for (t0, v0), (t1, v1) in zip(kf, kf[1:]):
        if t <= t1:
            u = (t - t0) / (t1 - t0)
            return v0 + (v1 - v0) * u * u * (3 - 2 * u)
    return kf[-1][1]


def opened(n, t):
    return keys(t, E_KF if n == "EGO" else O_KF)


def pusher(x, t, strain, ph=0.0):
    """Leaning into the door (door on the right), both hands flat on it."""
    sh = 0.02 * strain * math.sin(t * 41 + ph)
    hip = np.array([x, 1.15 + sh])
    j = build_pose(hip, np.array([x - 0.05, 0.02]), np.array([x - 0.75, 0.02]), 0.72 + 0.1 * strain,
                   1.75, 1.6, 0.15, 0.2, -0.35)
    return j


def target(t):
    cur = SHOTS[0]
    for s in SHOTS:
        if t >= s[0]:
            cur = s
    _, who, s = cur
    if who == "wide":
        return -0.75, 1.7, s
    if who == "EGO":
        return D_E - 0.3, 1.6, s
    if who == "OBS":
        return D_O - 0.3, 1.8, s
    if who == "OBS_FEET":
        return D_O - 0.7, 0.7, s
    if who == "GAP":
        return D_O + 0.5, 1.6, s
    return -0.4, 1.9, s


def draw_door(e, f_, hc, tc, cam, x0, frac, t, tint=WHITE, bright=1.0):
    # doorway light (revealed part)
    if frac > 0.001:
        l, tp = cam.pt((x0, DOOR_H))
        r, b = cam.pt((x0 + DOOR_W * frac, 0))
        f_.drawRect(skia.Rect(l, tp, r, b), paint(WHITE, 0.9 * bright))
        # light spilling on the floor in front
        sp = skia.Path()
        sp.moveTo(l, b)
        sp.lineTo(r, b)
        sp.lineTo(r - (1.6 + 2.5 * frac) * cam.s, b + 0.25 * cam.s)
        sp.lineTo(l - (2.4 + 3.0 * frac) * cam.s, b + 0.25 * cam.s)
        sp.close()
        f_.drawPath(sp, paint(WHITE, 0.12 * bright))
        for k in range(5):
            ang = math.pi + 0.15 + 0.12 * k
            f_.drawLine((l + r) / 2, (tp + b) / 2, (l + r) / 2 + math.cos(ang) * 900 * frac,
                        (tp + b) / 2 + math.sin(ang) * 120 * frac + 60 * k * frac, paint(WHITE, 0.05 * bright * frac, 30))
    # the slab
    sx = x0 + DOOR_W * frac
    l, tp = cam.pt((sx, DOOR_H))
    r, b = cam.pt((sx + DOOR_W, 0))
    rect = skia.Rect(l, tp, r, b)
    hc.drawRect(rect, paint((0.06, 0.06, 0.07), 1.0))
    hc.drawRect(rect, paint(tint, 0.9, max(3, 0.05 * cam.s), cap=False))
    for k in range(1, 4):                                  # stone seams
        y = tp + (b - tp) * k / 4
        hc.drawLine(l + 6, y, r - 6, y + 4 * math.sin(k), paint(tint, 0.25, 2))
    cx_, cy_ = (l + r) / 2, tp + (b - tp) * 0.32
    draw_spaced(hc, "DREAM", cx_, cy_, font(max(18, 0.3 * cam.s), "InterDisplay-Black"), 4, paint(tint, 0.85))


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    dust = Particles(2)
    aura = Particles(3)
    sweat = Particles(4)
    rng = np.random.default_rng(7)
    cam = Camera()
    cam.sx, cam.sy = CX, 1180.0
    cam.wx, cam.wy, cam.s = target(0.0)
    for fi in range(v.n):
        t = fi * dt
        oe, oo = opened("EGO", t), opened("OBSESSION", t)
        for k, (ts, who, s) in enumerate(SHOTS[1:], 1):
            if t >= ts:
                log.once(f"cut{k}", ts, "cut", k)
        for key, tt, kind in (("go", GO, "go"), ("kick", KICK, "kick"), ("quit", QUIT, "quit"), ("aura", 8.4, "aura"),
                              ("crack", 10.0, "crack"), ("burst", BURST, "burst"), ("end", END_T, "end"),
                              ("end2", END_T + 1.0, "end2")):
            if t >= tt:
                log.once(key, tt, kind)
        if GO < t < BURST and rng.random() < 0.5:
            dust.emit(np.array([[D_O - 1.0 + rng.normal(0, 0.1), 0.05]]), vel=(-0.7, 0.5), spread=0.3, life=(0.3, 0.6),
                      size=(0.02, 0.04))
        if GO < t < QUIT and rng.random() < 0.3:
            dust.emit(np.array([[D_E - 1.0 + rng.normal(0, 0.1), 0.05]]), vel=(-0.7, 0.5), spread=0.3, life=(0.3, 0.6),
                      size=(0.02, 0.04))
        if 8.4 <= t < BURST + 0.6 and rng.random() < 0.7:
            aura.emit(np.array([[D_O - 0.6 + rng.normal(0, 0.35), rng.uniform(0.3, 2.3)]]), vel=(0, 1.2), spread=0.4,
                      life=(0.5, 1.0), size=(0.02, 0.05))
        if 7.5 < t < BURST and rng.random() < 0.4:
            sweat.emit(np.array([[D_O - 0.3 + rng.normal(0, 0.05), 2.1]]), vel=(-0.3, -0.5), spread=0.3,
                       life=(0.4, 0.8), size=(0.02, 0.035))
        dust.step(dt)
        aura.step(dt)
        sweat.step(dt)
        wx, wy, s = target(t)
        snap = any(abs(t - ts) < dt * 0.6 for ts, _, _ in SHOTS[1:])
        k_ = 0.5 if snap else 0.2
        cam.wx += (wx - cam.wx) * k_
        cam.wy += (wy - cam.wy) * k_
        cam.s = math.exp(math.log(cam.s) + (math.log(s) - math.log(cam.s)) * k_)
        shake = 0.0
        for tt, a in ((KICK, 10.0), (BURST, 16.0)):
            if t >= tt:
                shake = max(shake, a * math.exp(-(t - tt) * 5))
        cam.sx = CX + shake * math.sin(t * 85)
        if not v.wants(fi):
            continue

        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        gy = cam.pt((0, 0))[1]
        # wall + floor
        wl, wt = cam.pt((-6, DOOR_H + 0.9))
        wr, _ = cam.pt((6, 0))
        e.drawRect(skia.Rect(wl, wt, wr, gy), paint(WHITE, 0.04))
        e.drawLine(wl, wt, wr, wt, paint(WHITE, 0.35, 3))
        for k in range(-6, 7):
            bx, _ = cam.pt((k * 1.1 + 0.3, 0))
            e.drawLine(bx, wt, bx, gy, paint(WHITE, 0.04, 2))
        e.drawLine(0, gy, W, gy, paint(WHITE, 0.55, 3))
        # doors
        flood = smoothstep(BURST, BURST + 0.6, t)
        draw_door(e, f_, hc, tc, cam, D_E, oe, t, RED, 1.0)
        draw_door(e, f_, hc, tc, cam, D_O, oo, t, WHITE, 1.0 + flood)
        # OPEN % counters
        for x0, frac, col in ((D_E, oe, RED), (D_O, oo, WHITE)):
            cx_, cy_ = cam.pt((x0 + DOOR_W / 2, DOOR_H + 0.45))
            pct = int(round(frac * 100))
            draw_spaced(tc, f"{pct}%", cx_, cy_, font(max(30, 0.45 * cam.s), "InterDisplay-Black"), 2,
                        paint(col if pct < 100 else RED, 1.0))
        # ---------- characters
        ex = D_E + DOOR_W * oe - 0.85
        if t < KICK:
            je = pusher(ex, t, 0.7 + 0.3 * smoothstep(3.0, 6.0, t))
        elif t < QUIT:
            u = (t - KICK) / 0.5
            kick = math.sin(math.pi * min(1, u))
            je = build_pose(np.array([ex - 0.3, 1.5]), np.array([ex - 0.3 + 0.9 * kick, 0.1 + 0.8 * kick]),
                            np.array([ex - 0.45, 0.02]), -0.1, 0.9, 0.8, 1.6, 1.6, -0.2)
        else:
            w = smoothstep(QUIT, QUIT + 0.4, t)
            js = sit(ex - 0.6, 0.0, t, 0.15)
            jc = crossed(ex - 0.5)
            js["hand1"], js["hand2"], js["elbow1"], js["elbow2"] = jc["hand1"] - [0, 0.7], jc["hand2"] - [0, 0.7], \
                jc["elbow1"] - [0, 0.7], jc["elbow2"] - [0, 0.7]
            je = blend(pusher(ex, t, 0.5), js, w)
            if t > 11.4:                                     # turns his head to the light
                je["head"] = je["head"] + [0.12 * smoothstep(11.4, 11.8, t), 0]
        draw_body(hc, je, cam, RED, 1.0, 0.15)
        ox = D_O + DOOR_W * oo - 0.85
        if t < BURST:
            jo = pusher(ox, t, 0.6 + 0.4 * smoothstep(3.0, 12.0, t), 1.3)
            if 3.8 <= t < 5.2:                               # feet slipping
                jo["foot2"] = jo["foot2"] - [0.15 * abs(math.sin(t * 6)), 0]
        else:
            u = t - BURST
            walk = run_pose(ox + 0.9 * u, u * 8, 0.35)
            jo = blend(pusher(ox, t, 0.5), walk, smoothstep(BURST + 0.4, BURST + 0.8, t))
        col_o = mix(WHITE, RED, 0.35 * smoothstep(8.4, 9.4, t))
        draw_body(hc, jo, cam, col_o, 1.0 - 0.6 * smoothstep(BURST + 1.6, END_T - 0.3, t), 0.35)
        dust.draw(f_, cam, WHITE, GREY)
        aura.draw(f_, cam, RED, RED)
        sweat.draw(f_, cam, WHITE, WHITE)
        if KICK <= t < QUIT + 0.6:
            hx, hy = cam.pt(je["head"])
            draw_spaced(oc, "OPEN!", hx + 0.2 * cam.s, hy - 0.6 * cam.s, font(min(64, max(30, 0.3 * cam.s)), "InterDisplay-Black"),
                        2, paint(RED, 1 - smoothstep(QUIT + 0.3, QUIT + 0.6, t)))
        # labels (wide shots only)
        la = 1 - smoothstep(140, 180, cam.s)
        for j, nme, col in ((je, "EGO", RED), (jo, "OBSESSION", WHITE)):
            fxx = j["hip"][0]
            sx, sy = cam.pt((fxx, 0))
            draw_spaced(tc, nme, sx, sy + 40, font(26, "Inter-Bold"), 4, paint(col, la))
        if t < GO + 0.4:
            caption(oc, "EGO VS OBSESSION", 520, 1 - smoothstep(GO, GO + 0.4, t), WHITE, 64)
        ending(oc, t, END_T - 0.3, [(END_T, "EGO KNOCKED.", RED, 96), (END_T + 1.0, "OBSESSION PUSHED", WHITE, 76),
                                    (END_T + 1.25, "UNTIL IT OPENED.", WHITE, 76)], gap=115)
        flash = math.exp(-(t - BURST) * 3.0) * 0.7 if t >= BURST else 0.0
        white = 0.08 * max(0.0, 1 - min(abs(t - ts) for ts, _, _ in SHOTS[1:]) / 0.05)
        white = max(white, 0.08 * flood * (1 - smoothstep(BURST + 1.0, END_T - 0.3, t)))
        v.compose(fi, t, flash=flash, white=white, glow=0.25 * smoothstep(8.4, 10, t), fade_in=0.0)
    v.finish(build_audio, log.events)


def grind(dur, seed=0):
    tt = sfx.t_axis(dur)
    x = sfx.bandnoise(dur, 60, 700, seed) * (0.6 + 0.4 * np.sin(2 * np.pi * 7 * tt))
    return x * np.minimum(1, tt * 4) * np.minimum(1, (dur - tt) * 4) * 0.6


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=BURST), gain=0.42, fade_in=0.3, fade_out=2.0, stop=DUR)
    m.add(0.02, sfx.text_hit(5), 0.6, 0, 0.4)
    m.add(GO, sfx.breath(1, 1.0), 0.6, -0.3, 0.2)
    m.add(GO + 0.2, sfx.breath(2, 1.0), 0.6, 0.3, 0.2)
    m.add(GO, grind(1.0, 1), 0.5, -0.4, 0.3)
    m.add(8.2, grind(BURST - 8.2, 2), 0.6, 0.4, 0.3)
    for t, kind, _, extra in events:
        if kind == "cut":
            m.add(t - 0.05, sfx.whoosh(0.25, 500, 9000, 0.6, seed=extra), 0.4, 0, 0.2)
        elif kind == "go":
            m.add(t, sfx.punch_block(1), 0.7, 0, 0.3)
        elif kind == "kick":
            m.add(t + 0.2, sfx.punch_hit(4, 1.6), 0.9, -0.4, 0.4)
            m.add(t + 0.25, sfx.text_hit(2), 0.6, -0.4, 0.4)
        elif kind == "quit":
            m.add(t, sfx.power_down(1.2), 0.5, -0.4, 0.4)
            m.add(t + 0.6, grind(0.8, 5), 0.4, -0.4, 0.3)
            m.add(t + 1.3, sfx.punch_block(3), 0.6, -0.4, 0.3)
        elif kind == "aura":
            m.add(t - 0.3, sfx.power_up(70), 0.9, 0.4, 0.4)
            m.add(t + 0.2, sfx.heartbeat(), 0.8, 0.3, 0.3)
            m.add(t + 1.0, sfx.heartbeat(), 0.85, 0.3, 0.3)
        elif kind == "crack":
            m.add(t, sfx.sparkle(1.4, 50, 3), 0.5, 0.4, 0.5)
            m.add(t + 0.2, sfx.riser(BURST - t - 0.2), 0.55, 0, 0.3)
        elif kind == "burst":
            m.add(t, sfx.boom(4.5), 1.0, 0, 0.6)
            m.add(t, sfx.sparkle(2.5, 120, 4), 0.8, 0.3, 0.6)
            for q, f in enumerate((660, 880, 1320)):
                m.add(t + 0.05 * q, sfx.chime(f, 0.3), 0.6, 0, 0.7)
        elif kind == "end":
            m.add(t, sfx.text_hit(1), 0.7, 0, 0.4)
        elif kind == "end2":
            m.add(t, sfx.text_hit(3), 0.95, 0, 0.5)
            m.add(t, sfx.boom(2.0), 0.45, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [0.5, 2.0, 3.0, 4.5, 5.8, 7.0, 8.0, 9.2, 10.8, 11.8, 12.8, 13.4, 14.5, 17.6]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
