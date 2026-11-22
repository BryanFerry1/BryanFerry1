"""EP31 - FEAR VS COURAGE  (the 10 m diving board)

One clear scene: a 10 m diving tower over a pool. A FEAR meter floats above
each head: the hook is that BOTH are terrified.
  Both climb the ladder (camera follows up).
  Look down: the pool is tiny. "10 M".
  Zoom FEAR: shaking, FEAR 95%. He steps back.
  Zoom COURAGE: shaking even more, FEAR 99%.
  FEAR climbs back down and sits by the pool.
  COURAGE closes his eyes... and jumps. Slow fall, huge splash, applause.
  He pops up: FEAR 40%.
  1 YEAR LATER: Courage does a backflip from the top (FEAR 5%). Fear is still
  sitting at the bottom (FEAR 100%).
END (black, centred) COURAGE ISN'T / NO FEAR. / IT'S JUMPING / ANYWAY.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import (FPS, H, RED, WHITE, W, Camera, Particles, clamp, draw_spaced, ease_out, font, mix, paint,
                    rotate_pose, run_pose, smoothstep)
from kit import CX, GREY, Log, Video, arms_up, blend, caption, draw_body, ending, mirror, sit, stand
import ep06_ego_discipline_obsession as e6
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep31_diving_board"
dt = 1 / FPS
TOP = 10.0                    # platform height
LAD_X = -2.6
LAD_F = -3.5
PLAT = (-3.9, -0.3)           # platform x range (edge at the right)
POOL = (-0.3, 4.6)
WATER = -0.3
CLIMB = (0.3, 3.2)
DOWN = (7.4, 9.2)
EYES = 8.6
JUMP = 9.2
SPLASH = 10.7
LATER = 12.0
FLIP = (12.8, 14.0)
PULL = 14.3
END_T = 15.8
DUR = 19.8
FEAR_X, COUR_X = -2.1, -0.65
SHOTS = [(0.0, "bottom", 120), (CLIMB[0] + 0.3, "ladder", 120), (CLIMB[1], "top", 135), (4.0, "down", 58),
         (5.0, "FEAR", 230), (6.2, "COUR", 230), (DOWN[0], "top", 125), (EYES, "COUR", 240), (JUMP, "fall", 120),
         (SPLASH, "pool", 130), (LATER, "top", 125), (FLIP[0] + 0.5, "fall", 115), (PULL, "all", 52)]


def fall_y(t):
    u = clamp((t - JUMP) / (SPLASH - JUMP))
    return TOP - (TOP - WATER + 0.6) * u ** 1.8


def fall_x(t):
    u = clamp((t - JUMP) / (SPLASH - JUMP))
    return COUR_X + 1.4 * ease_out(u)


def flip_state(t):
    u = clamp((t - FLIP[0]) / (FLIP[1] - FLIP[0]))
    y = TOP + 1.2 * math.sin(math.pi * min(1, u * 2.2)) * (u < 0.45) - (TOP - WATER + 0.6) * clamp((u - 0.3) / 0.7) ** 1.7
    x = COUR_X + 1.5 * ease_out(u)
    return x, y, 2 * math.pi * ease_out(min(1, u * 1.15))


def target(t):
    cur = SHOTS[0]
    for s in SHOTS:
        if t >= s[0]:
            cur = s
    _, who, s = cur
    if who == "bottom":
        return -2.0, 1.6, s
    if who == "ladder":
        h = clamp((t - CLIMB[0]) / (CLIMB[1] - CLIMB[0])) * TOP
        return -2.2, h + 1.2, s
    if who == "top":
        return -1.6, TOP + 1.6, s
    if who == "down":
        return 0.4, TOP * 0.5, s
    if who == "FEAR":
        return FEAR_X, TOP + 1.7, s
    if who == "COUR":
        return COUR_X, TOP + 1.7, s
    if who == "fall":
        if t < LATER:
            return 0.4, max(1.5, fall_y(t) + 1.0), s
        return 0.4, max(1.5, flip_state(t)[1] + 1.0), s
    if who == "pool":
        return -0.4, 1.4, s
    return 0.0, (TOP + 1.5) / 2, s


def meter(c, cam, head, val, alpha=1.0, side=0):
    hx, hy = cam.pt(head)
    w = 230
    x0, y0 = min(max(hx - w / 2 + side * 80, 90), 870 - w), hy - 0.75 * cam.s - 40
    c.drawRoundRect(skia.Rect(x0 - 10, y0 - 44, x0 + w + 10, y0 + 24), 10, 10, paint((0, 0, 0), 0.85 * alpha))
    draw_spaced(c, f"FEAR {int(round(val))}%", x0 + w / 2, y0 - 6, font(34, "InterDisplay-Black"), 2, paint(RED, alpha))
    c.drawRect(skia.Rect(x0, y0 + 2, x0 + w, y0 + 14), paint(WHITE, 0.4 * alpha, 2, cap=False))
    c.drawRect(skia.Rect(x0, y0 + 2, x0 + w * clamp(val / 100), y0 + 14), paint(RED, alpha))


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    splash = Particles(2)
    rng = np.random.default_rng(3)
    cam = Camera()
    cam.sx, cam.sy = CX, 1100.0
    cam.wx, cam.wy, cam.s = target(0.0)
    for fi in range(v.n):
        t = fi * dt
        for k, (ts, who, s) in enumerate(SHOTS[1:], 1):
            if t >= ts:
                log.once(f"cut{k}", ts, "cut", k)
        for key, tt, kind in (("go", 0.0, "go"), ("climb", CLIMB[0], "climb"), ("look", 4.0, "look"),
                              ("fear", 5.0, "fear"), ("cour", 6.2, "cour"), ("down", DOWN[0], "down"), ("eyes", EYES, "eyes"),
                              ("jump", JUMP, "jump"), ("splash", SPLASH, "splash"), ("later", LATER, "later"),
                              ("flip", FLIP[0], "flip"), ("splash2", FLIP[1], "splash2"), ("end", END_T, "end"),
                              ("end2", END_T + 1.0, "end2")):
            if t >= tt:
                log.once(key, tt, kind)
        for tt in (SPLASH, FLIP[1]):
            if tt <= t < tt + 0.12:
                x0 = fall_x(t) if tt == SPLASH else COUR_X + 1.5
                splash.emit(np.array([[x0 + rng.normal(0, 0.3), WATER] for _ in range(14)]), vel=(0, 5.0), spread=1.6,
                            life=(0.5, 1.1), size=(0.04, 0.09))
        splash.step(dt)
        wx, wy, s = target(t)
        snap = any(abs(t - ts) < dt * 0.6 for ts, _, _ in SHOTS[1:]) and t < JUMP
        k_ = 0.5 if snap else 0.16
        if t >= PULL:
            k_ = 0.08
        cam.wx += (wx - cam.wx) * k_
        cam.wy += (wy - cam.wy) * k_
        cam.s = math.exp(math.log(cam.s) + (math.log(s) - math.log(cam.s)) * k_)
        shake = max(10 * math.exp(-(t - SPLASH) * 5) if t >= SPLASH else 0.0, 0.0)
        cam.sx = CX + shake * math.sin(t * 85)
        if not v.wants(fi):
            continue

        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        # ---------- scene
        dl, dy_ = cam.pt((-8, 0))
        pl, _ = cam.pt((POOL[0], 0))
        e.drawLine(-10, dy_, pl, dy_, paint(WHITE, 0.6, 3))
        prr, _ = cam.pt((POOL[1], 0))
        e.drawLine(prr, dy_, W + 10, dy_, paint(WHITE, 0.6, 3))
        wl, wyy = cam.pt((POOL[0], WATER))
        wr, wb = cam.pt((POOL[1], -2.4))
        e.drawLine(pl, dy_, pl, wb, paint(WHITE, 0.6, 3))
        e.drawLine(prr, dy_, prr, wb, paint(WHITE, 0.6, 3))
        e.drawLine(pl, wb, prr, wb, paint(WHITE, 0.6, 3))
        for k in range(8):
            xx = POOL[0] + 0.3 + k * 0.6
            p1 = cam.pt((xx + 0.1 * math.sin(t * 2 + k), WATER))
            e.drawLine(p1[0], p1[1], p1[0] + 0.3 * cam.s, p1[1], paint(WHITE, 0.5, 2))
        # tower: posts, platform, ladder
        for px in (PLAT[0], PLAT[0] + 0.5):
            e.drawLine(*cam.pt((px, 0)), *cam.pt((px, TOP)), paint(WHITE, 0.5, max(2, 0.06 * cam.s)))
        e.drawLine(*cam.pt((PLAT[0], TOP)), *cam.pt((PLAT[1], TOP)), paint(WHITE, 0.9, max(3, 0.1 * cam.s)))
        e.drawLine(*cam.pt((PLAT[0], TOP)), *cam.pt((PLAT[0], TOP + 1.0)), paint(WHITE, 0.6, max(2, 0.04 * cam.s)))
        e.drawLine(*cam.pt((PLAT[0], TOP + 1.0)), *cam.pt((PLAT[0] + 0.8, TOP + 1.0)), paint(WHITE, 0.6, max(2, 0.04 * cam.s)))
        for lx in (LAD_X, LAD_F):
            for dx in (-0.4, 0.4):
                e.drawLine(*cam.pt((lx + dx, 0)), *cam.pt((lx + dx, TOP + 0.3)), paint(WHITE, 0.45, max(2, 0.04 * cam.s)))
            for k in range(1, 21):
                e.drawLine(*cam.pt((lx - 0.4, k * 0.5)), *cam.pt((lx + 0.4, k * 0.5)), paint(WHITE, 0.25, max(1.5, 0.03 * cam.s)))
        # "10 M" measure in the look-down shot
        if 4.0 <= t < 5.2:
            a = smoothstep(4.1, 4.3, t) * (1 - smoothstep(4.9, 5.2, t))
            x1, y1 = cam.pt((PLAT[1] + 0.5, TOP))
            x2, y2 = cam.pt((PLAT[1] + 0.5, WATER))
            oc.drawLine(x1, y1, x2, y2, paint(RED, a, 4))
            for yy in (y1, y2):
                oc.drawLine(x1 - 16, yy, x1 + 16, yy, paint(RED, a, 4))
            draw_spaced(oc, "10 M", x1 + 110, (y1 + y2) / 2, font(84, "InterDisplay-Black"), 4, paint(RED, a))
        splash.draw(f_, cam, WHITE, WHITE)
        # ---------- FEAR
        fear_val = 95.0
        if t < CLIMB[0]:
            jf = stand(LAD_F, 0.0, 0.2, 0.2, 0.2, 0.2, 0.0)
        elif t < CLIMB[1] + 0.3:
            p = clamp((t - CLIMB[0] - 0.4) / (CLIMB[1] - CLIMB[0])) * 18.0
            jf = e6.climb_pose(LAD_F, p, t)
        elif t < DOWN[0]:
            back = smoothstep(5.6, 6.0, t)
            x = FEAR_X - 0.4 * back
            jf = stand(x, -0.15 * back + 0.15, 0.6, 0.55, 2.0, 2.1, 0.5)
            jf = {k: vv + [0.025 * math.sin(t * 45), TOP] for k, vv in jf.items()}
            fear_val = 70 + 25 * smoothstep(4.2, 5.0, t)
        elif t < DOWN[1]:
            p = 19.0 * (1 - clamp((t - DOWN[0]) / (DOWN[1] - DOWN[0])))
            jf = e6.climb_pose(LAD_F, p, t)
        else:
            js = sit(-4.9, 0.0, t, 0.6)
            jf = js
            fear_val = 100.0
        draw_body(hc, jf, cam, RED, 1.0, 0.1)
        # ---------- COURAGE
        cour_val = 99.0
        if t < CLIMB[0]:
            jc = stand(LAD_X, 0.0, 0.2, 0.2, 0.2, 0.2, 0.0)
        elif t < CLIMB[1]:
            p = clamp((t - CLIMB[0]) / (CLIMB[1] - CLIMB[0] - 0.2)) * 19.0
            jc = e6.climb_pose(LAD_X, p, t)
            cour_val = 60 + 30 * clamp((t - CLIMB[0]) / 2.5)
        elif t < JUMP:
            shake = 0.035 if t < EYES else 0.02
            jc = stand(COUR_X, 0.05, 0.6, 0.55, 2.0, 2.1, 0.35 if t < EYES else -0.1)
            jc = {k: vv + [shake * math.sin(t * 52), TOP] for k, vv in jc.items()}
            if t >= EYES:
                jc = blend(jc, {k: vv + [0, TOP] for k, vv in arms_up(COUR_X, t).items()}, smoothstep(EYES + 0.3, JUMP, t))
        elif t < SPLASH + 0.2:
            body = arms_up(0.0, t)
            ang = -2.6 * ease_out(clamp((t - JUMP) / (SPLASH - JUMP)))
            jc = rotate_pose(body, np.array([0.0, 1.5]), ang)
            jc = {k: vv + [fall_x(t), fall_y(t) - 1.5] for k, vv in jc.items()}
            cour_val = 99 - 30 * clamp((t - JUMP) / (SPLASH - JUMP))
        elif t < LATER:
            u = smoothstep(SPLASH + 0.3, SPLASH + 0.8, t)
            jc = arms_up(fall_x(SPLASH) + 0.2, t)
            jc = {k: vv + [0, WATER - 1.3 + 0.0 * u] for k, vv in jc.items()}
            jc = {k: vv + [0, -1.2 * (1 - u)] for k, vv in jc.items()}
            cour_val = 99 - 59 * smoothstep(SPLASH + 0.3, SPLASH + 0.9, t)
        elif t < FLIP[0]:
            jc = stand(COUR_X, -0.05, 0.3, 0.25, 0.2, 0.2, -0.2)
            jc = {k: vv + [0, TOP] for k, vv in jc.items()}
            cour_val = 5
        else:
            x, y, ang = flip_state(t)
            body = blend(stand(0.0, 0.0, 2.9, 2.9, 0.1, 0.1, 0.0), arms_up(0.0, t), 0.5)
            jc = rotate_pose(body, np.array([0.0, 1.3]), ang)
            jc = {k: vv + [x, y - (0.0 if t < FLIP[0] + 0.05 else 1.3)] for k, vv in jc.items()}
            if y < WATER:
                jc = {k: vv for k, vv in jc.items()}
            cour_val = 5
        draw_body(hc, jc, cam, WHITE, 1.0, 0.2)
        # water hides what is under the surface
        hc.drawRect(skia.Rect(pl + 2, wyy, prr - 2, wb), paint((0.03, 0.03, 0.04), 0.65))
        # ---------- fear meters (readable, above heads)
        ma = 1 - smoothstep(END_T - 0.6, END_T - 0.3, t)
        if CLIMB[1] - 0.2 <= t < LATER - 0.2 or t >= LATER + 0.4:
            if not (DOWN[0] <= t < DOWN[1]):
                meter(oc, cam, jf["head"], fear_val, ma * (0.0 if cam.s > 200 and t > 6.2 and t < 7.4 else 1.0), -1)
            if not (JUMP + 0.2 <= t < SPLASH + 0.3) and not (FLIP[0] <= t < FLIP[1] + 0.3):
                meter(oc, cam, jc["head"], cour_val, ma * (0.0 if cam.s > 200 and 5.0 <= t < 6.2 else 1.0), 1)
        # labels
        la = 1 - smoothstep(150, 190, cam.s)
        if t < PULL:
            for j, nme, col in ((jf, "FEAR", RED), (jc, "COURAGE", WHITE)):
                fx = (j["foot1"][0] + j["foot2"][0]) / 2
                fy = min(j["foot1"][1], j["foot2"][1])
                sx, sy = cam.pt((fx, fy))
                if 330 < sy < 1550 and not (JUMP <= t < SPLASH + 0.5 and nme == "COURAGE"):
                    draw_spaced(tc, nme, sx, sy + 42, font(26, "Inter-Bold"), 4, paint(col, la))
        if LATER <= t < LATER + 0.9:
            a = smoothstep(LATER, LATER + 0.15, t) * (1 - smoothstep(LATER + 0.6, LATER + 0.9, t))
            oc.drawRect(skia.Rect(0, 0, W, H), paint((0, 0, 0), 0.8 * a))
            draw_spaced(oc, "1 YEAR LATER", CX, 960, font(80, "InterDisplay-Black"), 6, paint(WHITE, a))
        if t < 1.8:
            caption(oc, "FEAR VS COURAGE", 560, 1 - smoothstep(1.4, 1.8, t), WHITE, 64)
        ending(oc, t, END_T - 0.3, [(END_T, "COURAGE ISN'T", WHITE, 100), (END_T + 0.25, "NO FEAR.", WHITE, 100),
                                    (END_T + 1.0, "IT'S JUMPING", RED, 100), (END_T + 1.25, "ANYWAY.", RED, 100)], gap=125)
        flash = max(math.exp(-(t - SPLASH) * 3) * 0.7 if t >= SPLASH else 0.0,
                    math.exp(-(t - FLIP[1]) * 3) * 0.5 if t >= FLIP[1] else 0.0)
        slow = smoothstep(JUMP, JUMP + 0.2, t) * (1 - smoothstep(SPLASH - 0.1, SPLASH, t))
        v.compose(fi, t, flash=flash, glow=0.2 * slow, fade_in=0.0)
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=JUMP), gain=0.42, fade_in=0.3, fade_out=2.0, stop=DUR)
    for t, kind, _, extra in events:
        if kind == "go":
            m.add(0.02, sfx.text_hit(5), 0.6, 0, 0.4)
        elif kind == "cut":
            m.add(t - 0.05, sfx.whoosh(0.25, 500, 9000, 0.6, seed=extra), 0.35, 0, 0.2)
        elif kind == "climb":
            for q in range(12):
                m.add(t + q * 0.24, sfx.plate_clank(q, 0.2) * 0.4, 0.25, -0.3, 0.2)
        elif kind == "look":
            m.add(t, sfx.whoosh(0.8, 80, 2000, 0.8, seed=4), 0.6, 0, 0.4)
            m.add(t + 0.3, sfx.heartbeat(), 0.8, 0, 0.3)
        elif kind == "fear":
            m.add(t, sfx.heartbeat(), 0.85, -0.3, 0.3)
            m.add(t + 0.7, sfx.heartbeat(), 0.9, -0.3, 0.3)
            m.add(t + 0.6, sfx.step_light(2), 0.5, -0.3, 0.2)
        elif kind == "cour":
            for q in range(3):
                m.add(t + q * 0.38, sfx.heartbeat(), 0.85 + 0.05 * q, 0.3, 0.3)
            m.add(t, sfx.breath(3, 1.0), 0.6, 0.3, 0.2)
        elif kind == "down":
            for q in range(7):
                m.add(t + q * 0.24, sfx.plate_clank(20 + q, 0.2) * 0.4, 0.25, -0.4, 0.2)
            m.add(t, sfx.power_down(1.4), 0.4, -0.4, 0.4)
        elif kind == "eyes":
            m.add(t, sfx.breath(6, 0.9), 0.7, 0.2, 0.2)
            m.add(t, sfx.riser(JUMP - t), 0.5, 0, 0.3)
        elif kind == "jump":
            m.add(t, sfx.whoosh(SPLASH - t, 100, 6000, 0.95, seed=9), 0.9, 0, 0.4)
        elif kind == "splash":
            m.add(t, sfx.bandnoise(1.6, 200, 9000, 6) * np.exp(-np.linspace(0, 4, int(1.6 * sfx.SR))) * 1.0, 1.0, 0, 0.4)
            m.add(t, sfx.boom(2.5), 0.7, 0, 0.4)
            m.add(t + 0.4, sfx.applause(2.5, 55, 4), 0.6, 0, 0.3)
        elif kind == "later":
            m.add(t, sfx.text_hit(2), 0.7, 0, 0.4)
        elif kind == "flip":
            m.add(t, sfx.whoosh(1.0, 200, 8000, 0.6, seed=12), 0.7, 0, 0.3)
        elif kind == "splash2":
            m.add(t, sfx.bandnoise(1.2, 200, 9000, 8) * np.exp(-np.linspace(0, 4, int(1.2 * sfx.SR))) * 0.9, 0.9, 0, 0.4)
            m.add(t + 0.2, sfx.applause(2.5, 60, 7), 0.6, 0, 0.3)
        elif kind == "end":
            m.add(t, sfx.text_hit(1), 0.7, 0, 0.4)
        elif kind == "end2":
            m.add(t, sfx.text_hit(3), 0.95, 0, 0.5)
            m.add(t, sfx.boom(2.0), 0.45, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [0.5, 1.6, 2.6, 3.6, 4.5, 5.6, 6.8, 8.0, 8.9, 9.8, 10.4, 11.2, 12.5, 13.3, 13.8, 14.9, 18.0]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
