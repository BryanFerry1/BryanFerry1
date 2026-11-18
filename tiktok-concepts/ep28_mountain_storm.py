"""EP28 - EGO VS OBSESSION  (the mountain storm)

Zooms format, several phases: sun -> storm -> avalanche -> comeback -> summit.
SUN        EGO climbs fast and plants a little red flag every few steps, posing.
           OBSESSION climbs slower, ice axe in hand.
STORM      snow, wind, the sky goes dark. Ego stops for a selfie on a ledge.
           Obsession hammers his ice axe into the slope.
AVALANCHE  a white wave rolls down from the peak and buries them both.
COMEBACK   a red hand punches out of the snow: Obsession digs himself out and
           climbs again. Ego sits up, stays sitting in the snow.
SUMMIT     Obsession plants a big red flag on the top. Pull back: far below, only
           the tip of one of Ego's flags sticks out of the snow.
END (black, centred) THE STORM BURIED EGO. / IT ONLY SLOWED / OBSESSION DOWN.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import (FPS, H, RED, WHITE, W, Camera, Particles, build_pose, clamp, draw_spaced, ease_out, font, mix,
                    paint, run_pose, smoothstep)
from kit import (CX, GREY, Log, Video, arms_up, blend, caption, draw_body, draw_phone_small, ending, flex, phone_pose,
                 sit, stand)
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep28_mountain_storm"
dt = 1 / FPS
SLOPE = 0.35
PEAK = 24.0
STORM = (4.5, 8.5)
AVA = 8.5
BURIED = (10.0, 10.8)
PUNCH = 10.8
SUMMIT = 14.6
PULL = 15.4
END_T = 16.8
DUR = 20.8
FLAGS = [(1.5, 4.0), (3.0, 8.0), (6.0, 15.0)]   # (time, x) Ego's little flags

E_KF = [(0, 0.0), (1.5, 4.0), (2.0, 4.0), (3.0, 8.0), (3.5, 8.0), (4.5, 12.0), (6.0, 15.0), (9.17, 15.0), (10.0, 9.0),
        (99, 9.0)]
O_KF = [(0, 0.0), (4.5, 7.0), (7.2, 11.0), (8.4, 11.0), (9.5, 12.0), (10.0, 7.0), (11.5, 7.0), (SUMMIT, PEAK),
        (99, PEAK)]
SHOTS = [(0.0, "pair", 130), (1.4, "EGO", 220), (2.6, "OBS", 200), (3.6, "pair", 125), (6.0, "EGO", 220),
         (7.2, "OBS", 215), (AVA, "PEAK", 110), (9.1, "pair", 120), (10.0, "MOUND", 230), (11.6, "EGO", 200),
         (12.4, "OBS", 165), (SUMMIT - 0.2, "PEAK", 180), (PULL, "ALL", 46)]


def ground(x):
    if x <= PEAK:
        return max(0.0, x) * SLOPE
    return PEAK * SLOPE - (x - PEAK) * 0.5


def lin(t, kf):
    if t <= kf[0][0]:
        return kf[0][1]
    for (t0, v0), (t1, v1) in zip(kf, kf[1:]):
        if t <= t1:
            u = (t - t0) / (t1 - t0)
            return v0 + (v1 - v0) * u
    return kf[-1][1]


def xpos(n, t):
    return lin(t, E_KF if n == "EGO" else O_KF)


def wave_x(t):
    return PEAK - 12.0 * (t - AVA)


def altitude(x):
    return int(round((2000 + 6848 * clamp(x / PEAK)) / 10) * 10)


def climb(x, ph, inten=0.45):
    return run_pose(x, ph, inten, ground(x), 0.28)


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
        return mid, ground(mid) + 1.4, s
    if who == "EGO":
        return xe, ground(xe) + 1.2, s
    if who == "OBS":
        return xo, ground(xo) + 1.2, s
    if who == "PEAK":
        return PEAK - 1.0, ground(PEAK) + 0.6, s
    if who == "MOUND":
        return 7.2, ground(7.0) + 0.5, s
    if who == "ALL":
        return 15.0, 4.8, s
    return xe, 1.0, s


def flag(c, cam, x, h, alpha, size=1.0, wave=0.0, col=RED):
    base = np.array([x, ground(x) - 0.1])
    top = base + [0, 1.2 * size * h]
    c.drawLine(*cam.pt(base), *cam.pt(top), paint(WHITE, 0.9 * alpha, max(2, 0.04 * cam.s * size)))
    p = skia.Path()
    p.moveTo(*cam.pt(top))
    p.lineTo(*cam.pt(top + [0.55 * size, -0.12 * size + 0.05 * math.sin(wave)]))
    p.lineTo(*cam.pt(top + [0, -0.38 * size]))
    p.close()
    c.drawPath(p, paint(col, alpha))


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    snow = Particles(2)
    debris = Particles(3)
    aura = Particles(4)
    rng = np.random.default_rng(6)
    cam = Camera()
    cam.sx, cam.sy = CX, 1150.0
    cam.wx, cam.wy, cam.s = target(0.0)
    ph = {"EGO": 0.0, "OBSESSION": 1.3}
    flakes = rng.uniform(0, 1, (110, 3))
    for fi in range(v.n):
        t = fi * dt
        xe, xo = xpos("EGO", t), xpos("OBSESSION", t)
        for n in ph:
            vx = abs(xpos(n, t + 0.03) - xpos(n, t - 0.03)) / 0.06
            ph[n] += dt * (vx * 2.6 if vx > 0.3 else 0)
        for k, (ts, who, s) in enumerate(SHOTS[1:], 1):
            if t >= ts:
                log.once(f"cut{k}", ts, "cut", k)
        for k, (tf, xf) in enumerate(FLAGS):
            if t >= tf:
                log.once(f"flag{k}", tf, "flag", k)
        for key, tt, kind in (("go", 0.0, "go"), ("storm", STORM[0], "storm"), ("selfie", 6.3, "selfie"),
                              ("axe", 7.3, "axe"), ("ava", AVA, "ava"), ("hit", 9.15, "hit"), ("buried", BURIED[0], "buried"),
                              ("punch", PUNCH, "punch"), ("egosit", 11.6, "egosit"), ("climb", 11.5, "climb"),
                              ("summit", SUMMIT, "summit"), ("pull", PULL, "pull"), ("end", END_T, "end"),
                              ("end2", END_T + 1.0, "end2")):
            if t >= tt:
                log.once(key, tt, kind)
        if AVA <= t < 10.2:
            wx_ = wave_x(t)
            debris.emit(np.array([[wx_ + rng.uniform(0, 4), ground(wx_) + rng.uniform(0.3, 2.0)] for _ in range(6)]),
                        vel=(-6, 1.0), spread=1.2, life=(0.4, 1.0), size=(0.04, 0.12))
        if PUNCH <= t < PUNCH + 0.12:
            debris.emit(np.array([[7.0, ground(7.0) + 0.6]] * 10), vel=(0, 2.5), spread=1.4, life=(0.3, 0.7), size=(0.03, 0.08))
        if 10.8 <= t < SUMMIT + 0.5 and rng.random() < 0.6:
            aura.emit(np.array([[xo + rng.normal(0, 0.3), ground(xo) + rng.uniform(0.3, 2.0)]]), vel=(0, 1.2), spread=0.4,
                      life=(0.5, 1.0), size=(0.02, 0.05))
        debris.step(dt)
        aura.step(dt)
        wx, wy, s = target(t)
        snap = any(abs(t - ts) < dt * 0.6 for ts, _, _ in SHOTS[1:])
        k_ = 0.5 if snap else 0.18
        if t >= PULL:
            k_ = 0.08
        cam.wx += (wx - cam.wx) * k_
        cam.wy += (wy - cam.wy) * k_
        cam.s = math.exp(math.log(cam.s) + (math.log(s) - math.log(cam.s)) * k_)
        shake = 14 * smoothstep(AVA, AVA + 0.3, t) * (1 - smoothstep(9.8, 10.2, t))
        shake = max(shake, 10 * math.exp(-(t - PUNCH) * 5) if t >= PUNCH else 0)
        cam.sx = CX + shake * math.sin(t * 83)
        if not v.wants(fi):
            continue

        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        storm = smoothstep(STORM[0], STORM[0] + 0.6, t) * (1 - smoothstep(10.6, 11.6, t))
        sun = 1 - storm
        # sky: sun (screen space) + distant mountains
        if sun > 0.05 and t < PULL:
            sx_, sy_ = 760, 640
            e.drawCircle(sx_, sy_, 70, paint(WHITE, 0.7 * sun))
            for k in range(10):
                a = k * 0.628 + t * 0.2
                e.drawLine(sx_ + math.cos(a) * 95, sy_ + math.sin(a) * 95, sx_ + math.cos(a) * 140, sy_ + math.sin(a) * 140,
                           paint(WHITE, 0.4 * sun, 4))
        for k in range(4):
            bx = -10 + k * 12 + cam.wx * 0.6
            p = skia.Path()
            p.moveTo(*cam.pt((bx - 8, 0)))
            p.lineTo(*cam.pt((bx, 6 + 2 * (k % 2))))
            p.lineTo(*cam.pt((bx + 8, 0)))
            p.close()
            e.drawPath(p, paint(WHITE, 0.03))
        # mountain
        mp = skia.Path()
        mp.moveTo(*cam.pt((-8, -20)))
        mp.lineTo(*cam.pt((-8, 0)))
        mp.lineTo(*cam.pt((0, 0)))
        mp.lineTo(*cam.pt((PEAK, ground(PEAK))))
        mp.lineTo(*cam.pt((PEAK + 40, ground(PEAK + 40))))
        mp.lineTo(*cam.pt((PEAK + 40, -20)))
        mp.close()
        e.drawPath(mp, paint((0.05, 0.05, 0.06), 1.0))
        top = skia.Path()
        top.moveTo(*cam.pt((-8, 0)))
        top.lineTo(*cam.pt((0, 0)))
        top.lineTo(*cam.pt((PEAK, ground(PEAK))))
        top.lineTo(*cam.pt((PEAK + 40, ground(PEAK + 40))))
        e.drawPath(top, paint(WHITE, 0.75, max(3, 0.05 * cam.s)))
        cap = skia.Path()
        cap.moveTo(*cam.pt((PEAK - 4, ground(PEAK - 4))))
        cap.lineTo(*cam.pt((PEAK, ground(PEAK))))
        cap.lineTo(*cam.pt((PEAK + 3, ground(PEAK + 3))))
        cap.lineTo(*cam.pt((PEAK + 2, ground(PEAK + 2) - 0.6)))
        cap.lineTo(*cam.pt((PEAK - 3, ground(PEAK - 3) - 0.5)))
        cap.close()
        e.drawPath(cap, paint(WHITE, 0.1))
        # Ego's flags (swept/buried by the avalanche except the tip of one)
        for k, (tf, xf) in enumerate(FLAGS):
            if t < tf:
                continue
            grow = ease_out(min(1, (t - tf) / 0.25))
            swept = t >= AVA and wave_x(t) < xf + 0.5
            if not swept:
                flag(f_, cam, xf, grow, 1.0, 0.8, t * 6 + k)
            elif xf == 8.0:
                p_ = np.array([xf, ground(xf) + 0.35])
                flag(f_, cam, xf + 0.0, 0.55, 0.9, 0.8, t * 3)
        # ---------- avalanche wave
        if AVA <= t < 10.3:
            wx_ = wave_x(t)
            p = skia.Path()
            p.moveTo(*cam.pt((wx_, ground(wx_))))
            for k in range(13):
                xx = wx_ + k * 0.5
                hh = 1.6 + 0.4 * math.sin(xx * 3 + t * 9) - 0.08 * k
                p.lineTo(*cam.pt((xx, ground(xx) + max(0.2, hh))))
            p.lineTo(*cam.pt((wx_ + 7, ground(wx_ + 7))))
            p.close()
            hc_paint = paint(WHITE, 0.92)
            f_.drawPath(p, hc_paint)
        debris.draw(f_, cam, WHITE, WHITE)
        # ---------- climbers
        joints = {}
        # Obsession
        if t < AVA:
            if 7.2 <= t < 8.4:
                hit = abs(math.sin((t - 7.2) * 9))
                jo = build_pose(np.array([xo - 0.1, ground(xo) + 1.25]), np.array([xo + 0.2, ground(xo + 0.2) + 0.02]),
                                np.array([xo - 0.35, ground(xo - 0.35) + 0.02]), 0.55, 1.2 + 1.2 * hit, 0.6, 1.0 - 0.8 * hit, 0.6, 0.2)
            else:
                jo = climb(xo, ph["OBSESSION"])
        elif t < BURIED[0]:
            jo = climb(xo, t * 8, 0.9)
            jo = {k: vv + [0.2 * math.sin(t * 20 + len(k)), 0.15 * math.cos(t * 17 + len(k))] for k, vv in jo.items()}
        elif t < PUNCH:
            jo = stand(xo, 0.6, 0.3, 0.2, 0.6, 0.6, 0.6)
            jo = {k: vv + [0, ground(xo) - 2.4] for k, vv in jo.items()}
        elif t < 11.5:
            u = smoothstep(PUNCH, 11.4, t) * 0.6 + 0.4
            jo = stand(xo, 0.3 - 0.3 * u, 2.9, 0.4 + 2.0 * u, 0.1, 0.2, -0.2)
            jo = {k: vv + [0, ground(xo) - 1.2 * (1 - u)] for k, vv in jo.items()}
        elif t < SUMMIT:
            jo = climb(xo, ph["OBSESSION"], 0.6)
        else:
            up = {k: vv + [0, ground(xo)] for k, vv in arms_up(xo, t).items()}
            jo = blend(climb(xo, 0, 0.0), up, smoothstep(SUMMIT + 0.2, SUMMIT + 0.6, t))
        col_o = mix(WHITE, RED, 0.3 * smoothstep(PUNCH, PUNCH + 0.5, t))
        draw_body(hc, jo, cam, col_o, 1.0, 0.35)
        if t >= PUNCH:                                         # bloody red hand
            hc.drawCircle(*cam.pt(jo["hand1"]), max(5, 0.1 * cam.s), paint(RED, 1.0))
        if t < BURIED[0] or t >= 11.5:                          # ice axe
            hnd = jo["hand1"]
            hc.drawLine(*cam.pt(hnd), *cam.pt(hnd + [0.25, 0.45]), paint(WHITE, 1.0, max(2, 0.05 * cam.s)))
            hc.drawLine(*cam.pt(hnd + [0.1, 0.5]), *cam.pt(hnd + [0.45, 0.35]), paint(WHITE, 1.0, max(2, 0.05 * cam.s)))
        aura.draw(f_, cam, RED, RED)
        joints["OBSESSION"] = jo
        # Ego
        if t < AVA:
            if 6.0 <= t < 7.4:
                je = phone_pose(xe, t)
                je = {k: vv + [0, ground(xe)] for k, vv in je.items()}
                draw_phone_small(f_, cam, je["hand1"] + [0.05, 0.1], 1.0)
                if (t - 6.3) % 0.4 < 0.07 and t > 6.3:
                    f_.drawCircle(*cam.pt(je["hand1"] + [0.05, 0.2]), 0.35 * cam.s, paint(WHITE, 0.9))
            elif any(tf <= t < tf + 0.5 for tf, _ in FLAGS[:2]):
                je = flex(xe, t)
                je = {k: vv + [0, ground(xe)] for k, vv in je.items()}
            else:
                je = climb(xe, ph["EGO"], 0.75)
        elif t < BURIED[0]:
            je = climb(xe, t * 8, 0.9)
            je = {k: vv + [0.2 * math.sin(t * 19 + len(k)), 0.15 * math.cos(t * 23 + len(k))] for k, vv in je.items()}
        elif t < 11.6:
            je = stand(xe, 0.6, 0.3, 0.2, 0.6, 0.6, 0.6)
            je = {k: vv + [0, ground(xe) - 2.4] for k, vv in je.items()}
        else:
            u = smoothstep(11.6, 12.1, t)
            js = sit(xe - 0.3, 0.0, t, 0.9)
            js = {k: vv + [0, ground(xe) - 0.35] for k, vv in js.items()}
            je = js
        col_e = mix(RED, GREY, 0.45 * smoothstep(11.6, 12.6, t))
        draw_body(hc, je, cam, col_e, 1.0, 0.15)
        joints["EGO"] = je
        # the mountain hides whatever is below the slope (buried bodies)
        hc.drawPath(mp, paint((0.05, 0.05, 0.06), 1.0))
        hc.drawPath(top, paint(WHITE, 0.75, max(3, 0.05 * cam.s)))
        # snow mound covering the buried climbers
        if t >= 9.9:
            grow = smoothstep(9.9, 10.1, t)
            for cx_, w_ in ((7.0, 1.6), (9.0, 1.7)):
                dig = 1.0
                if cx_ == 7.0:
                    dig = 1 - smoothstep(PUNCH, 11.4, t)
                if dig <= 0.01:
                    continue
                p = skia.Path()
                p.moveTo(*cam.pt((cx_ - w_, ground(cx_ - w_))))
                p.quadTo(*cam.pt((cx_, ground(cx_) + 1.3 * grow * dig)), *cam.pt((cx_ + w_, ground(cx_ + w_))))
                p.close()
                hc.drawPath(p, paint((0.6, 0.6, 0.63), 1.0))
            if BURIED[0] + 0.2 <= t < PUNCH:                    # a hand twitching out of the mound
                hx, hy = cam.pt((7.1, ground(7.1) + 1.0 + 0.05 * math.sin(t * 25)))
                hc.drawCircle(hx, hy, max(5, 0.1 * cam.s), paint(WHITE, 1.0))
        # summit flag
        if t >= SUMMIT:
            g = ease_out(min(1, (t - SUMMIT) / 0.3))
            flag(hc, cam, PEAK + 0.6, g, 1.0, 1.6, t * 5)
        # storm overlay (screen space)
        if storm > 0.01:
            for k in range(110):
                fx = (flakes[k, 0] * (W + 400) - t * 600 * (0.5 + flakes[k, 2])) % (W + 400) - 200
                fy = (flakes[k, 1] * H + t * 300 * (0.5 + flakes[k, 2])) % H
                f_.drawLine(fx, fy, fx - 26, fy + 9, paint(WHITE, 0.35 * storm, 2))
        # labels on wide shots
        la = 1 - smoothstep(150, 190, cam.s)
        if t < PULL:
            for n, col in (("EGO", RED), ("OBSESSION", WHITE)):
                j = joints[n]
                sx, sy = cam.pt((j["hip"][0], ground(j["hip"][0])))
                if BURIED[0] <= t < PUNCH:
                    continue
                draw_spaced(tc, n, sx, sy + 40, font(24, "Inter-Bold"), 4, paint(col, la))
        # callouts
        if 6.0 <= t < 7.4:
            hx, hy = cam.pt(joints["EGO"]["head"])
            draw_spaced(oc, "#SUMMITVIBES", min(max(hx, 300), 660), hy - 0.75 * cam.s, font(44, "InterDisplay-Black"), 2, paint(RED, 1.0))
        if AVA <= t < 9.6:
            pop = 1 + 0.3 * math.exp(-(t - AVA) * 6)
            draw_spaced(oc, "AVALANCHE", CX, 640, font(84 * pop, "InterDisplay-Black"), 6, paint(RED, 1 - smoothstep(9.3, 9.6, t)))
        # altitude HUD
        ha = smoothstep(1.8, 2.1, t) * (1 - smoothstep(END_T - 0.6, END_T - 0.3, t))
        if ha > 0.01:
            draw_spaced(oc, "ALTITUDE", CX, 355, font(22, "Inter-SemiBold"), 10, paint(WHITE, 0.7 * ha))
            draw_spaced(oc, f"EGO  {altitude(xe):,} M", CX, 410, font(40, "InterDisplay-Black"), 2, paint(RED, ha))
            draw_spaced(oc, f"OBSESSION  {altitude(xo):,} M", CX, 465, font(40, "InterDisplay-Black"), 2,
                        paint(WHITE if xo < PEAK else RED, ha))
        if t < 1.8:
            caption(oc, "EGO VS OBSESSION", 520, 1 - smoothstep(1.4, 1.8, t), WHITE, 64)
        ending(oc, t, END_T - 0.3, [(END_T, "THE STORM", RED, 96), (END_T + 0.25, "BURIED EGO.", RED, 96),
                                    (END_T + 1.0, "IT ONLY SLOWED", WHITE, 84), (END_T + 1.25, "OBSESSION DOWN.", WHITE, 84)],
               gap=118)
        flash = math.exp(-(t - SUMMIT) * 3) if t >= SUMMIT else 0.0
        white = 0.08 * max(0.0, 1 - min(abs(t - ts) for ts, _, _ in SHOTS[1:]) / 0.05)
        v.compose(fi, t, flash=flash * 0.8, white=white, dim=0.3 * storm, fade_in=0.0)
    v.finish(build_audio, log.events)


def wind(dur, seed=3):
    tt = sfx.t_axis(dur)
    x = sfx.bandnoise(dur, 200, 2500, seed) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.7 * tt))
    return x * np.minimum(1, tt) * np.minimum(1, (dur - tt) * 1.5) * 0.6


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=SUMMIT), gain=0.42, fade_in=0.3, fade_out=2.0, stop=DUR)
    m.add(STORM[0], wind(7.0), 0.55, 0, 0.2)
    t_ = 0.2
    k = 0
    while t_ < AVA:
        m.add(t_, sfx.step_heavy(k) * 0.6, 0.25, 0.2, 0.1)
        t_ += 0.45
        k += 1
    for t, kind, _, extra in events:
        if kind == "go":
            m.add(0.02, sfx.text_hit(5), 0.6, 0, 0.4)
        elif kind == "cut":
            m.add(t - 0.05, sfx.whoosh(0.25, 500, 9000, 0.6, seed=extra), 0.4, 0, 0.2)
        elif kind == "flag":
            m.add(t, sfx.punch_block(extra), 0.6, -0.3, 0.3)
            m.add(t + 0.1, sfx.chime(880, 0.25), 0.4, -0.3, 0.4)
        elif kind == "storm":
            m.add(t, sfx.thunder(2), 0.7, 0, 0.3)
        elif kind == "selfie":
            for q in range(3):
                m.add(t + q * 0.4, sfx.shutter(q), 0.5, -0.3, 0.2)
        elif kind == "axe":
            for q in range(4):
                m.add(t + q * 0.33, sfx.plate_clank(q, 0.3), 0.45, 0.3, 0.3)
        elif kind == "ava":
            m.add(t, sfx.thunder(7), 1.0, 0, 0.3)
            m.add(t, sfx.bandnoise(2.0, 40, 400, 9) * np.linspace(0.3, 1, 2 * sfx.SR), 0.9, 0, 0.3)
            m.add(t + 0.1, sfx.riser(0.9), 0.5, 0, 0.3)
        elif kind == "hit":
            m.add(t, sfx.boom(3.0), 1.0, 0, 0.5)
        elif kind == "buried":
            m.add(t, sfx.power_down(0.8), 0.5, 0, 0.4)
            m.add(t + 0.2, sfx.heartbeat(), 0.8, 0, 0.3)
        elif kind == "punch":
            m.add(t, sfx.punch_hit(5, 1.6), 1.0, 0, 0.4)
            m.add(t, sfx.power_up(70), 0.9, 0, 0.4)
        elif kind == "egosit":
            m.add(t, sfx.power_down(1.0), 0.4, -0.3, 0.4)
        elif kind == "climb":
            m.add(t, sfx.riser(SUMMIT - t), 0.5, 0, 0.3)
            for q in range(8):
                m.add(t + 0.2 + q * 0.38, sfx.step_heavy(q), 0.4, 0.2, 0.15)
        elif kind == "summit":
            m.add(t, sfx.boom(4.0), 1.0, 0, 0.5)
            m.add(t, sfx.sparkle(2.0), 0.6, 0, 0.6)
            for q, f in enumerate((660, 880, 1320)):
                m.add(t + 0.05 * q, sfx.chime(f, 0.3), 0.55, 0, 0.6)
        elif kind == "pull":
            m.add(t, sfx.whoosh(1.4, 100, 2500, 0.7, seed=13), 0.45, 0, 0.4)
        elif kind == "end":
            m.add(t, sfx.text_hit(1), 0.7, 0, 0.4)
        elif kind == "end2":
            m.add(t, sfx.text_hit(3), 0.95, 0, 0.5)
            m.add(t, sfx.boom(2.0), 0.45, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [0.6, 1.7, 3.0, 4.2, 5.4, 6.6, 7.8, 8.8, 9.3, 10.4, 11.0, 12.0, 13.2, 14.9, 15.8, 16.4, 18.6]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
