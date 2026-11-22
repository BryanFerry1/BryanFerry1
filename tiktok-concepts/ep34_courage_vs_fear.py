"""EP34 - COURAGE VS FEAR  (edit-friendly: big drop at 10.0 s)

  0.0  darkness, two eyes open... pull back: FEAR is a red giant, 3x taller.
  2.2  FEAR stomps forward, COURAGE trembles and backs off.
  4.0  FEAR roars: shockwave, COURAGE is blown off his feet.
  5.8  COURAGE on his knees, the giant foot rises over him... slams down...
  7.6  ...he CATCHES it. Struggle, slowly stands up under it, light leaking.
  9.6  black. silence.
 10.0  DROP: white flash, aura explodes, FEAR is thrown back.
 10.8  COURAGE walks forward, one step every second (on the beat): every step
       FEAR SHRINKS (3x -> 0.3x) and backs off. Cuts alternate close / wide.
 16.0  FEAR is tiny, trembling. Last step: it shatters into red shards.
 16.0  hero shot in the aura.
 END   FEAR SHRINKS / EVERY TIME / YOU STEP / FORWARD.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import (FPS, H, HEAD_R, L_FARM, L_UARM, RED, WHITE, W, Camera, Particles, clamp, draw_spaced, ease_out,
                    font, ik, paint, rotate_pose, run_pose, smoothstep)
from kit import Log, Shards, Video, arms_up, blend, caption, draw_body, ending, kneel, mirror, sad, stand
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep34_courage_vs_fear"
dt = 1 / FPS
SCX, SCY = 450.0, 960.0          # screen anchor of the camera target
EYES = 0.45
STOMP1 = 2.7
ROAR = 4.0
BLOWN = 4.35
KNEEL_UP = 6.0
LIFT = (6.2, 7.3)
SLAM = 7.6
STAND = (8.6, 9.5)
BLACK = (9.65, 10.0)
DROP = 10.0
STEPS = [10.8, 11.8, 12.8, 13.8]
LAST = 16.0
END_T = 18.8
DUR = 22.8
XC_STEPS = [-2.2, -1.7, -1.2, -0.7, -0.2]
K_STEPS = [2.4, 1.75, 1.15, 0.7, 0.36]
XF_STEPS = [1.7, 1.55, 1.3, 1.0, 0.65]
HAND_Y = 2.75


def step_interp(t, vals, dur=0.35):
    """Value after each STEP (moves during the dur seconds before the step lands)."""
    v = vals[0]
    for k, ts in enumerate(STEPS):
        u = ease_out(clamp((t - (ts - dur)) / dur))
        v = v + (vals[k + 1] - vals[k]) * u
    return v


def courage_x(t):
    if t < 3.0:
        return -1.0
    if t < BLOWN:
        return -1.0 - 0.45 * smoothstep(3.0, 3.8, t)
    if t < DROP:
        return -1.45 - 0.75 * ease_out(clamp((t - BLOWN) / 0.35))
    x = step_interp(t, XC_STEPS)
    if t > LAST - 0.3:
        x += 0.45 * ease_out(clamp((t - (LAST - 0.3)) / 0.3))
    return x


def fear_xk(t):
    if t < DROP:
        x = 1.6 - 0.7 * ease_out(clamp((t - (STOMP1 - 0.5)) / 0.5))
        return x, 3.0
    u = ease_out(clamp((t - DROP) / 0.45))
    x0 = 0.9 + (XF_STEPS[0] - 0.9) * u
    k0 = 3.0 + (K_STEPS[0] - 3.0) * u
    x = x0 + step_interp(t, XF_STEPS) - XF_STEPS[0]
    k = k0 + step_interp(t, K_STEPS) - K_STEPS[0]
    return x, k


def fcam_of(cam, X, k):
    c = Camera()
    c.s = cam.s * k
    c.sx, c.sy = cam.pt((X, 0.0))
    c.wx = c.wy = 0.0
    return c


# ------------------------------------------------------------------ poses
def fear_pose(t, X, k, xc):
    """Local pose (x=0 at FEAR's feet, unit size), facing left."""
    breathe = 0.02 * math.sin(t * 2.5)
    if t < ROAR:
        j = stand(0, 0.12, 0.45, 0.35, 0.7, 0.6, 0.2, breathe)
        if STOMP1 - 0.5 < t < STOMP1:
            j["foot2"] = j["foot2"] + [0.25, 0.35 * math.sin(math.pi * (t - (STOMP1 - 0.5)) / 0.5)]
            j["knee2"] = ik(j["hip"], j["foot2"], 0.88, 0.86, 1)
    elif t < KNEEL_UP:
        r = smoothstep(ROAR, ROAR + 0.25, t) * (1 - smoothstep(ROAR + 1.3, ROAR + 1.7, t))
        j = blend(stand(0, 0.12, 0.45, 0.35, 0.7, 0.6, 0.2, breathe),
                  stand(0, -0.15, 2.1, 2.2, 0.5, 0.4, -0.45, breathe), r)
    elif t < DROP:
        j = stand(0, 0.05, 0.6, 0.4, 0.6, 0.5, 0.35, breathe)
        foot_x = -(xc - X) / k            # local, before mirroring (faces left -> +x here)
        if t < SLAM:
            lift = ease_out(smoothstep(LIFT[0], LIFT[1], t))
            fy = (4.3 / k) * lift
            if t > LIFT[1]:
                fy = (4.3 / k) + (HAND_Y / k - 4.3 / k) * (ease_out(clamp((t - (SLAM - 0.15)) / 0.15)))
            fx = 0.13 + (foot_x - 0.13) * smoothstep(LIFT[0], LIFT[1] - 0.3, t)
        else:
            push = smoothstep(STAND[0], STAND[1], t)
            sink = 0.12 * math.exp(-(t - SLAM) * 5)
            fx, fy = foot_x, (HAND_Y - sink + 0.25 * push) / k
        j["foot1"] = np.array([fx, fy])
        j["knee1"] = ik(j["hip"], j["foot1"], 0.88, 0.86, 1)
        j = {kk: vv + [0.006 * math.sin(t * 50) * (t > SLAM), 0] for kk, vv in j.items()}
    else:
        tt = t - DROP
        if tt < 0.8:
            j = stand(0, -0.35 * math.exp(-tt * 3), 1.6, 1.8, 0.4, 0.3, -0.4)
        else:
            sh = smoothstep(0.8, 3.0, tt)
            j = blend(stand(0, -0.1, 0.9, 1.0, 1.9, 1.9, 0.2), sad(0, t), sh)
            j = {kk: vv + [0.012 * math.sin(t * 45) * sh, 0] for kk, vv in j.items()}
    return mirror(j, 0.0)


def hold_kneel(x, t):
    j = kneel(x, t, 0.2)
    sh = j["shoulder"]
    for i, dx in ((1, 0.12), (2, -0.05)):
        h = np.array([x + 0.25 + dx, HAND_Y - 0.12 * math.exp(-(t - SLAM) * 5)])
        j[f"hand{i}"] = h
        j[f"elbow{i}"] = ik(sh, h, L_UARM, L_FARM, 1)
    j["head"] = j["neck"] + np.array([0.05, 0.36])
    return j


def hold_stand(x, t):
    j = stand(x, -0.05, 2.9, 3.0, 0.2, 0.2, -0.3)
    sh = j["shoulder"]
    for i, dx in ((1, 0.12), (2, -0.05)):
        h = np.array([x + 0.25 + dx, HAND_Y + 0.25])
        j[f"hand{i}"] = h
        j[f"elbow{i}"] = ik(sh, h, L_UARM, L_FARM, 1)
    return j


def courage_pose(t, xc):
    if t < 3.0:
        return {k: v + [0.008 * math.sin(t * 40) * (t > 2.2), 0] for k, v in stand(xc, -0.05, 0.3, 0.25, 0.9, 0.9, 0.2).items()}
    if t < ROAR:
        j = run_pose(xc, t * 6, 0.15)
        return mirror(j, xc) if False else {k: v + [0.01 * math.sin(t * 40), 0] for k, v in
                                          stand(xc, 0.15, 0.3, 0.25, 1.6, 1.6, 0.4).items()}
    if t < BLOWN:
        return {k: v + [0.01 * math.sin(t * 45), 0] for k, v in stand(xc, 0.2, 0.9, 0.8, 1.9, 1.9, 0.5).items()}
    if t < KNEEL_UP:
        u = ease_out(clamp((t - BLOWN) / 0.35))
        j = rotate_pose(stand(xc, 0.0, 0.4, 0.3, 0.2, 0.2), np.array([xc, 0.0]), 1.45 * u)
        return {k: v + [0, 0.13 * u] for k, v in j.items()}
    if t < SLAM - 0.12:
        lying = {k: v + [0, 0.13] for k, v in rotate_pose(stand(xc, 0, 0.4, 0.3, 0.2, 0.2), np.array([xc, 0.0]), 1.45).items()}
        return blend(lying, kneel(xc, t, 0.9), smoothstep(KNEEL_UP, KNEEL_UP + 0.5, t))
    if t < STAND[0]:
        return blend(kneel(xc, t, 0.9), hold_kneel(xc, t), smoothstep(SLAM - 0.12, SLAM, t))
    if t < DROP:
        j = blend(hold_kneel(xc, t), hold_stand(xc, t), smoothstep(STAND[0], STAND[1], t))
        return {k: v + [0.008 * math.sin(t * 55), 0] for k, v in j.items()}
    hero = stand(xc, -0.04, 0.35, 0.3, 1.2, 1.2, -0.08)
    if t < DROP + 0.5:
        return blend(arms_up(xc, t), hero, smoothstep(DROP + 0.1, DROP + 0.5, t))
    for ts in STEPS + [LAST]:
        if ts - 0.35 <= t < ts:
            return run_pose(xc, (t - ts) * 9 + math.pi, 0.3)
    if LAST - 1.0 < t < LAST - 0.35:
        return stand(xc, 0.05, 0.35, 0.3, 1.2, 1.2, 0.55)
    return hero


# ------------------------------------------------------------------ fx
def aura(c, cam, j, a, t):
    if a <= 0.01:
        return
    cx, cy = cam.pt((j["hip"] + j["neck"]) / 2)
    r = (1.7 + 0.12 * math.sin(t * 9)) * cam.s
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(
        skia.Point(cx, cy), r, [skia.Color4f(1, 1, 1, 0.16 * a), skia.Color4f(1, 1, 1, 0.05 * a),
                                skia.Color4f(1, 1, 1, 0.0)], [0.0, 0.45, 1.0]))
    c.drawCircle(cx, cy, r, p)


def ring(c, cam, center, t, t0, rmax, col=WHITE, dur=0.6, width=0.08):
    u = (t - t0) / dur
    if 0 <= u < 1:
        x, y = cam.pt(center)
        c.drawCircle(x, y, rmax * ease_out(u) * cam.s, paint(col, (1 - u) ** 1.5, max(3, width * cam.s * (1 - u))))


def eyes(c, fcam, j, a, t):
    if a <= 0.01:
        return
    hx, hy = fcam.pt(j["head"])
    r = HEAD_R * fcam.s
    blink = 1.0
    for dx in (-0.55, -0.05):
        c.save()
        c.translate(hx + dx * r, hy - 0.1 * r)
        c.rotate(-12 if dx < -0.3 else 12)
        c.drawOval(skia.Rect(-0.2 * r, -0.07 * r * blink, 0.2 * r, 0.07 * r * blink), paint(WHITE, a))
        c.restore()


# ------------------------------------------------------------------ camera
def camera(t, xc, X, k, head=None):
    """(s, world target x, world target y); hard cuts between segments."""
    if t < 2.2:
        u = ease_out(smoothstep(0.9, 2.2, t))
        a = (300.0, head[0], head[1])
        b = (112.0, 0.0, 3.4)
    elif t < ROAR + 0.9:
        u = (t - 2.2) / (ROAR + 0.9 - 2.2)
        a, b = (112.0, 0.0, 3.4), (122.0, -0.1, 3.3)
    elif t < KNEEL_UP:
        u = (t - (ROAR + 0.9)) / (KNEEL_UP - ROAR - 0.9)
        a, b = (230.0, xc - 0.6, 0.8), (245.0, xc - 0.6, 0.8)
    elif t < SLAM:
        u = (t - KNEEL_UP) / (SLAM - KNEEL_UP)
        a, b = (150.0, xc + 1.1, 2.6), (158.0, xc + 1.1, 2.7)
    elif t < DROP:
        u = ease_out((t - SLAM) / (DROP - SLAM))
        a, b = (215.0, xc + 0.3, 1.9), (265.0, xc + 0.3, 2.0)
    elif t < STEPS[0]:
        u = (t - DROP) / 0.8
        a, b = (112.0, 0.0, 3.4), (118.0, 0.0, 3.3)
    elif t < LAST:
        n = sum(1 for s in STEPS if t >= s) - 1
        ts = STEPS[n]
        u = (t - ts) / 1.0
        if n == 0:
            a, b = (230.0, xc + 0.2, 1.4), (250.0, xc + 0.2, 1.4)
        elif n == 1:
            a, b = (125.0, (xc + X) / 2, 2.6), (132.0, (xc + X) / 2, 2.6)
        elif n == 2:
            a, b = (210.0, X - 0.2, 1.4), (230.0, X - 0.2, 1.4)
        else:
            a, b = (170.0, (xc + X) / 2, 1.5), (190.0, (xc + X) / 2, 1.4)
    else:
        u = ease_out(clamp((t - LAST) / 2.6))
        a, b = (215.0, xc + 0.2, 1.4), (150.0, xc + 0.2, 1.9)
    return tuple(a[i] + (b[i] - a[i]) * clamp(u) for i in range(3))


CUTS = [2.2, ROAR + 0.9, KNEEL_UP, SLAM, DROP, STEPS[0], STEPS[1], STEPS[2], STEPS[3], LAST]


# ------------------------------------------------------------------ main
def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    embers = Particles(5)
    shards = Shards(9)
    rng = np.random.default_rng(3)
    for fi in range(v.n):
        t = fi * dt
        for key, tt, kind in (("eyes", EYES, "eyes"), ("stomp", STOMP1, "stomp"), ("roar", ROAR, "roar"),
                              ("blown", BLOWN, "blown"), ("lift", LIFT[0], "lift"), ("slam", SLAM, "slam"),
                              ("stand", STAND[0], "stand"), ("drop", DROP, "drop"), ("last", LAST, "last"),
                              ("end", END_T, "end"), ("end2", END_T + 1.5, "end2")):
            if t >= tt:
                log.once(key, tt, kind)
        for k, ts in enumerate(STEPS):
            if t >= ts:
                log.once(f"step{k}", ts, "step", k)
        xc = courage_x(t)
        X, k = fear_xk(t)
        jc = courage_pose(t, xc)
        # particles
        aura_a = 0.0
        if STAND[0] < t < DROP:
            aura_a = 0.35 * smoothstep(STAND[0], BLACK[0], t)
        elif t >= DROP:
            aura_a = 1.0 if t < LAST else 1.0
        if aura_a > 0.05 and rng.random() < 0.55:
            pts = np.array([jc["hip"], jc["neck"], jc["foot1"], jc["foot2"], jc["hand1"]]) + rng.normal(0, 0.15, (5, 2))
            n = 2 + int(4 * aura_a)
            embers.emit(pts[:n % 5 + 1], vel=(0, 1.2 + 1.5 * aura_a), spread=0.35, life=(0.6, 1.3), size=(0.03, 0.06))
        if abs(t - DROP) < dt / 2:
            embers.emit(np.tile(jc["neck"], (80, 1)) + rng.normal(0, 0.3, (80, 2)), vel=(0, 2.0), spread=3.0,
                        life=(0.5, 1.4), size=(0.03, 0.08))
        if abs(t - LAST) < dt / 2:
            shards.burst(X - 0.4, X + 0.4, 0.1, 0.8, 70, vx=(-6, 6), vy=(1, 9), size=(0.08, 0.25), life=(0.9, 2.0))
        embers.step(dt)
        shards.step(dt)
        if not v.wants(fi):
            continue
        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        hd = np.array([X, 0.0]) + fear_pose(t, X, k, xc)["head"] * k
        s, wx, wy = camera(t, xc, X, k, hd)
        cam = Camera()
        cam.s, cam.wx, cam.wy, cam.sx, cam.sy = s, wx, wy, SCX, SCY
        shake = 0.0
        for t0, amp in ((STOMP1, 14), (ROAR, 10), (BLOWN, 8), (SLAM, 22), (DROP, 30), (LAST, 26)):
            if t0 <= t < t0 + 0.5:
                shake = max(shake, amp * (1 - (t - t0) / 0.5))
        for ts in STEPS:
            if ts <= t < ts + 0.3:
                shake = max(shake, 12 * (1 - (t - ts) / 0.3))
        if ROAR + 0.2 < t < ROAR + 1.4:
            shake = max(shake, 5)
        if shake:
            cam.sx += shake * math.sin(t * 97)
            cam.sy += shake * math.cos(t * 83)
        gy = cam.pt((0, 0))[1]
        e.drawLine(0, gy, W, gy, paint(WHITE, 0.45, 2.5))
        # FEAR
        reveal = smoothstep(0.8, 1.8, t)
        fc = fcam_of(cam, X, k)
        if t < LAST:
            jf = fear_pose(t, X, k, xc)
            if reveal > 0:
                draw_body(hc, jf, fc, RED, reveal)
            eyes(tc, fc, jf, smoothstep(EYES, EYES + 0.15, t), t)
            if reveal > 0.5 and t < DROP:
                lx, _ = fc.pt((0, 0))
                draw_spaced(tc, "FEAR", lx, gy + 50, font(34, "Inter-Bold"), 6, paint(RED, smoothstep(2.1, 2.4, t)))
            if ROAR <= t < ROAR + 1.4:
                for q in range(3):
                    ring(f_, fc, jf["head"], t, ROAR + 0.15 + q * 0.35, 3.0, RED, 0.7, 0.05)
        shards.draw(hc, cam, RED)
        # COURAGE
        aura(f_, cam, jc, aura_a, t)
        embers.draw(f_, cam, WHITE, WHITE)
        dim_c = 1.0
        draw_body(hc, jc, cam, WHITE, dim_c)
        lx, _ = cam.pt((jc["hip"][0], 0))
        draw_spaced(tc, "COURAGE", lx, gy + 50, font(34, "Inter-Bold"), 6, paint(WHITE, smoothstep(2.1, 2.4, t) * (t < BLACK[0])))
        ring(f_, cam, (xc, 1.2), t, DROP, 4.5, WHITE, 0.8, 0.12)
        ring(f_, cam, (xc, 1.2), t, DROP + 0.15, 3.0, WHITE, 0.7, 0.06)
        for ts in STEPS:
            ring(e, cam, (jc["foot1"][0], 0.05), t, ts, 1.6, WHITE, 0.45, 0.06)
        ring(f_, cam, (X, 0.3), t, LAST, 3.5, WHITE, 0.7, 0.1)
        ring(f_, cam, (xc, 0.5), t, SLAM, 1.4, WHITE, 0.35, 0.05)
        # text
        if 0.4 < t < 2.2:
            caption(oc, "COURAGE VS FEAR", 1500, smoothstep(0.4, 0.7, t) * (1 - smoothstep(1.9, 2.2, t)), WHITE, 60, band=False)
        ending(oc, t, END_T - 0.3, [(END_T, "FEAR SHRINKS", WHITE, 100), (END_T + 0.4, "EVERY TIME", WHITE, 100),
                                    (END_T + 1.2, "YOU STEP", RED, 110), (END_T + 1.5, "FORWARD.", RED, 120)], gap=125)
        # grading
        flash = 0.0
        white = 0.0
        for t0, a in ((DROP, 0.8), (LAST, 0.6), (SLAM, 0.2)):
            if t0 <= t < t0 + 0.35:
                white = max(white, a * (1 - (t - t0) / 0.35) ** 2)
        for c_ in CUTS:
            if c_ <= t < c_ + 0.1 and c_ not in (DROP, LAST, SLAM):
                white = max(white, 0.07)
        dim = 0.0
        if BLACK[0] <= t < BLACK[1]:
            dim = 1.0
        if LIFT[0] < t < SLAM:
            dim = 0.25 * smoothstep(LIFT[0], LIFT[1], t)
        glow = 0.15 * aura_a
        if t >= DROP:
            flash = 0.5 * math.exp(-(t - DROP) * 3)
        if BLACK[0] <= t < BLACK[1]:
            white = 0.0
        v.compose(fi, t, flash=flash, glow=glow, white=white, dim=dim, fade_in=0.0)
    v.finish(build_audio, log.events)


def build_audio(events, path):
    """Light sound design: the user lays an edit sound on top. Big hits on the key beats."""
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DROP, rise_at=7.0), gain=0.3, fade_in=0.3, fade_out=0.4, stop=BLACK[0])
    for t, kind, _, extra in events:
        if kind == "eyes":
            m.add(t, sfx.text_hit(2), 0.5, 0, 0.5)
            m.add(t, sfx.heartbeat(), 0.6, 0, 0.3)
        elif kind == "stomp":
            m.add(t, sfx.boom(2.0), 0.8, 0, 0.4)
            m.add(t, sfx.step_heavy(1), 1.0, 0, 0.3)
        elif kind == "roar":
            r = sfx.bandnoise(1.4, 60, 700, 3) * sfx.env_ad(int(1.4 * sfx.SR), 0.12, 1.2, 1.5)
            m.add(t + 0.1, r, 0.9, 0, 0.5)
            m.add(t + 0.1, sfx.sweep(1.2, 90, 50) * sfx.env_ad(int(1.2 * sfx.SR), 0.1, 1.0, 1.5), 0.6, 0, 0.4)
        elif kind == "blown":
            m.add(t, sfx.whoosh(0.5, 300, 6000, 0.5, seed=4), 0.6, 0, 0.3)
            m.add(t + 0.3, sfx.body_fall(), 0.8, 0, 0.3)
        elif kind == "lift":
            m.add(t, sfx.riser(SLAM - t), 0.5, 0, 0.4)
            for q in range(4):
                m.add(t + q * 0.38, sfx.heartbeat(), 0.6, 0, 0.3)
        elif kind == "slam":
            m.add(t, sfx.boom(2.5), 1.0, 0, 0.5)
            m.add(t, sfx.punch_block(2), 0.9, 0, 0.3)
        elif kind == "stand":
            m.add(t, sfx.breath(3, 0.8), 0.6, 0, 0.3)
            m.add(t, sfx.riser(BLACK[0] - t), 0.6, 0, 0.4)
        elif kind == "drop":
            m.add(t, sfx.boom(3.5), 1.0, 0, 0.6)
            m.add(t, sfx.power_up(110), 0.6, 0, 0.5)
            m.add(t, sfx.shatter(1, 0.8), 0.5, 0, 0.5)
        elif kind == "step":
            m.add(t, sfx.step_heavy(extra), 1.0, 0, 0.3)
            m.add(t, sfx.boom(1.2), 0.45, 0, 0.3)
        elif kind == "last":
            m.add(t, sfx.shatter(7, 1.2), 0.9, 0, 0.6)
            m.add(t, sfx.boom(3.0), 0.9, 0, 0.6)
            m.add(t + 0.2, sfx.sparkle(2.0), 0.5, 0, 0.6)
        elif kind == "end":
            m.add(t, sfx.text_hit(1), 0.7, 0, 0.4)
        elif kind == "end2":
            m.add(t, sfx.text_hit(3), 0.9, 0, 0.5)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [0.6, 1.4, 2.4, 3.6, 4.4, 5.2, 6.4, 7.2, 7.8, 9.0, 9.5, 10.1, 10.5, 11.3, 12.3, 13.3, 14.3, 15.5,
              16.1, 17.5]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
