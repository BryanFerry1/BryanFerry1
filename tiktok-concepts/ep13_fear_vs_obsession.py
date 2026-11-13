"""EP13 - FEAR VS OBSESSION  (the jump)

Visual hook: a pebble falls off a cliff edge into a black void... and never
lands. Across the gap, a red crown glows on the other cliff.
OBSESSION stares at the crown, backs up, sprints and jumps into the void:
a plank of light appears under every step. He crosses, takes the crown.
The bridge vanishes behind him.
FEAR walks to the edge; red voices pop: WHAT IF YOU FAIL? / WHAT IF THEY
LAUGH? / WHAT IF IT'S TOO LATE? Every time he steps back. Years pass. He grows
old at the edge, still asking.
PUNCH  FEAR ASKS WHAT IF. / OBSESSION ASKS / WHEN.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import FPS, RED, WHITE, W, clamp, dashed, draw_spaced, ease_out, font, mix, paint, run_pose, smoothstep
from kit import (CX, GREY, Log, Video, arms_up, blend, draw_body, draw_cane, draw_crown, hud, label,
                 lane_cam, old_pose, punch, stand, title)
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep13_fear_vs_obsession"
dt = 1 / FPS
S = 100.0
GROUND = 1240.0
WX = 0.35
EDGE_L, EDGE_R = -1.0, 2.0
CROWN_X = 3.3
PLANKS = [-0.65, -0.05, 0.55, 1.15, 1.7]

ARRIVE = (2.6, 3.6)
BACKUP = (4.3, 4.8)
RUN = (5.0, 7.0)
TAKE = 7.4
FEAR_TRIES = [8.0, 9.6, 11.2]
VOICES = ["WHAT IF YOU FAIL?", "WHAT IF THEY LAUGH?", "WHAT IF IT'S TOO LATE?"]
AGE_A, AGE_B = 9.0, 13.2
P1, P2, P3 = 14.4, 15.3, 15.8
DUR = P3 + 3.0
FX0 = -3.45


def rate(t):
    a = RUN[0] + 0.35
    w = smoothstep(a - 0.1, a, t) * (1 - smoothstep(a + 0.5, a + 0.7, t))
    return 1 - 0.6 * w


TAUS = [0.0]
while len(TAUS) < int(DUR * FPS) + 2:
    TAUS.append(TAUS[-1] + rate(TAUS[-1]) * dt)
TAUS = np.array(TAUS)


def obs_x(tau):
    if tau < ARRIVE[0]:
        return -2.25
    if tau < ARRIVE[1]:
        return -2.25 + 0.9 * smoothstep(ARRIVE[0], ARRIVE[1], tau)
    if tau < BACKUP[1]:
        return -1.35 - 0.85 * smoothstep(BACKUP[0], BACKUP[1], tau)
    if tau < RUN[0]:
        return -2.2
    if tau < RUN[1]:
        u = (tau - RUN[0]) / (RUN[1] - RUN[0])
        return -2.2 + (CROWN_X - 0.75 + 2.2) * (u ** 0.9)
    return CROWN_X - 0.75


def fear_x(tau):
    x = FX0
    if tau >= ARRIVE[0]:
        x = FX0 + 0.1 * smoothstep(ARRIVE[0], ARRIVE[1], tau)
    for k, tt in enumerate(FEAR_TRIES):
        fw = smoothstep(tt - 0.6, tt, tau) * (1 - smoothstep(tt + 0.25, tt + 0.9, tau))
        x += (-1.45 - (FX0 + 0.1)) * fw
    return x


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    ph = 0.0
    prev = 0.0
    for fi in range(v.n):
        t = fi * dt
        tau = TAUS[fi]
        dtau = tau - prev
        prev = tau
        ox = obs_x(tau)
        fx = fear_x(tau)
        age = smoothstep(AGE_A, AGE_B, tau)
        year = 1 + int(round(29 * age)) if tau >= AGE_A else 1
        # events
        if tau >= 0.25:
            log.once("pebble", t, "pebble")
        for k, px in enumerate(PLANKS):
            if ox >= px - 0.45 and tau >= RUN[0]:
                log.once(f"plank{k}", t, "plank", k)
        if tau >= RUN[0] + 0.3:
            log.once("jump", t, "jump")
        if tau >= TAKE:
            log.once("take", t, "take")
        for k, tt in enumerate(FEAR_TRIES):
            if tau >= tt:
                log.once(f"voice{k}", t, "voice", k)
        if tau >= ARRIVE[0]:
            log.once("arrive", t, "arrive")
        if not v.wants(fi):
            continue
        v.clear()
        e, f_, tc, hc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas
        cam = lane_cam(S, GROUND, WX)
        # cliffs
        for x0, x1, edge in ((-6.0, EDGE_L, EDGE_L), (EDGE_R, 6.0, EDGE_R)):
            e.drawLine(*cam.pt((x0, 0)), *cam.pt((x1, 0)), paint(WHITE, 0.7, 3))
            for k in range(8):
                y0, y1 = -k * 0.45, -(k + 1) * 0.45
                e.drawLine(*cam.pt((edge, y0)), *cam.pt((edge + (0.05 if edge > 0 else -0.05) * (k % 2), y1)),
                           paint(WHITE, 0.7 * (1 - k / 8), 3))
        # void mist
        for k in range(5):
            y = -1.0 - k * 0.5
            a0 = cam.pt((EDGE_L + 0.2, y))
            a1 = cam.pt((EDGE_R - 0.2, y + 0.1 * math.sin(t + k)))
            e.drawLine(*a0, *a1, paint(WHITE, 0.03, 2))
        # pebble (hook)
        if 0.25 <= tau < 2.6:
            u = tau - 0.25
            py = -2.2 * u * u
            sx, sy = cam.pt((EDGE_L + 0.15 + 0.3 * u, py + 0.08))
            if sy < 1560:
                f_.drawCircle(sx, sy, 7, paint(WHITE, max(0, 1 - u / 2.2)))
        # crown on pedestal / on his head
        if tau < TAKE:
            px, py = cam.pt((CROWN_X, 0))
            e.drawRect(skia.Rect(px - 0.3 * S, py - 0.9 * S, px + 0.3 * S, py), paint(WHITE, 0.6, 3, cap=False))
            draw_crown(f_, px, py - 1.25 * S + 6 * math.sin(t * 2.5), 64, 1.0)
            f_.drawCircle(px, py - 1.25 * S, 0.8 * S, paint(RED, 0.06))
        # planks of light
        for k, pxw in enumerate(PLANKS):
            if tau >= RUN[0] and ox >= pxw - 0.45:
                ap = ease_out(clamp((ox - (pxw - 0.45)) / 0.3))
                fade = 1 - smoothstep(RUN[1] + 0.2 + 0.15 * k, RUN[1] + 0.8 + 0.15 * k, tau)
                l, top = cam.pt((pxw - 0.27 * ap, 0.0))
                r, bot = cam.pt((pxw + 0.27 * ap, -0.1))
                f_.drawRect(skia.Rect(l, top, r, bot), paint(WHITE, 0.95 * fade))
        # ---------- OBSESSION
        moving = (ARRIVE[0] <= tau < ARRIVE[1]) or (RUN[0] <= tau < RUN[1]) or (BACKUP[0] <= tau < BACKUP[1])
        speed = 2.0 if tau < RUN[0] else 4.5
        if moving:
            ph += speed / 2.6 * 2 * math.pi * dtau * (1 if tau >= RUN[0] or tau < BACKUP[0] else -1)
        jo = run_pose(ox, ph, 0.95 if RUN[0] <= tau < RUN[1] else 0.4 if moving else 0.0)
        if RUN[0] + 0.25 <= tau < RUN[0] + 0.75:      # the leap
            jump = math.sin(math.pi * (tau - RUN[0] - 0.25) / 0.5) * 0.55
            jo = {k: vv + [0, jump] for k, vv in jo.items()}
        if tau >= RUN[1]:
            reach = smoothstep(RUN[1], TAKE, tau)
            jo = blend(jo, stand(ox, 0.1, 1.5 * reach, 0.2, 0.3, 0.2, 0.0), reach)
            if tau >= TAKE:
                jo = blend(jo, arms_up(ox, t), smoothstep(TAKE, TAKE + 0.4, tau))
        draw_body(hc, jo, cam, WHITE, 1.0, 0.25)
        if tau >= TAKE:
            hx, hy = cam.pt(jo["head"] + [0, 0.42])
            pop = 1 + 0.4 * math.exp(-(tau - TAKE) * 8)
            draw_crown(f_, hx, hy, 52 * pop, 1.0)
        if ARRIVE[1] - 0.2 < tau < RUN[0] + 0.3:     # stare at the crown
            la = smoothstep(ARRIVE[1] - 0.2, ARRIVE[1] + 0.2, tau)
            a = cam.pt(jo["head"])
            b = cam.pt((CROWN_X, 1.25))
            f_.drawLine(*a, *b, dashed(WHITE, 0.6 * la, 3, 14, 12, t * 90))
        label(tc, cam, ox, "OBSESSION", smoothstep(2.6, 3.0, t) * (1 - smoothstep(P1 - 0.5, P1, t)), WHITE, 46, 24)
        # ---------- FEAR
        shiver = 0.025 * math.sin(t * 47) if tau > ARRIVE[0] else 0.0
        jf = stand(fx + shiver, -0.12, 0.65, 0.6, 2.1, 2.15, 0.25)
        jf_old = old_pose(fx)
        jf = blend(jf, jf_old, age)
        fcol = mix(WHITE, GREY, age)
        draw_body(hc, jf, cam, fcol, 0.9, 0.0, 0.35 * age)
        if age > 0.3:
            draw_cane(hc, cam, jf, age)
        label(tc, cam, fx, "FEAR", smoothstep(2.6, 3.0, t) * (1 - smoothstep(P1 - 0.5, P1, t)), RED, 46, 24)
        # red voices
        for k, tt in enumerate(FEAR_TRIES):
            a_ = tau - tt
            if 0 <= a_ < 1.3:
                pop = 1 + 0.4 * math.exp(-a_ * 10)
                al = 1 - smoothstep(0.9, 1.3, a_)
                hx, hy = cam.pt(jf["head"])
                yy = hy - 90 - 60 * (k % 2)
                txt = VOICES[k]
                f = font(34 * pop, "InterDisplay-Black")
                draw_spaced(tc, txt, min(max(hx + 120, 330), 640), yy, f, 2, paint(RED, al))
                for s_ in range(4):
                    ang = s_ * 0.9 + 0.4
                    f_.drawLine(hx + math.cos(ang) * 38, hy - math.sin(ang) * 38, hx + math.cos(ang) * 58, hy - math.sin(ang) * 58,
                                paint(RED, 0.7 * al, 3))

        hud(tc, "YEAR", year, smoothstep(AGE_A - 0.3, AGE_A, tau) * (1 - 0.6 * smoothstep(P1 - 0.3, P1 + 0.3, t)), year >= 30)
        title(tc, t, [([("FEAR", RED)], 170, 80), ([("VS", WHITE)], 48, 130), ([("OBSESSION", WHITE)], 130, 0)], t0=0.9, t1=2.4, y0=600)
        punch(tc, t, [(P1, [("FEAR", RED), (" ASKS WHAT IF.", WHITE)], 600, 62),
                      (P2, [("OBSESSION ASKS", WHITE)], 720, 76),
                      (P3, [("WHEN.", WHITE)], 880, 170)])
        tdim = 0.55 * smoothstep(0.9, 1.15, t) * (1 - smoothstep(2.4, 2.8, t))
        pdim = 0.6 * smoothstep(P1 - 0.3, P1, t)
        flash = math.exp(-(tau - TAKE) * 3) if tau >= TAKE else 0.0
        v.compose(fi, t, flash=flash, glow=0.3 * (tau >= TAKE), dim=max(tdim, pdim))
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=10.0), gain=0.45, fade_in=0.6, fade_out=2.5, stop=DUR)
    m.add(0.6, sfx.text_hit(5), 0.7, 0, 0.4)
    for t, kind, _, extra in events:
        if kind == "pebble":
            m.add(t, sfx.tick(2000, 0.4), 0.5, -0.2, 0.3)
            m.add(t + 0.05, sfx.sweep(2.2, 1800, 300) * np.linspace(1, 0, int(2.2 * sfx.SR)) ** 2 * 0.15, 0.6, -0.1, 0.6)
        elif kind == "arrive":
            for k in range(5):
                m.add(t + k * 0.25, sfx.step_light(k), 0.3, -0.2, 0.1)
        elif kind == "jump":
            m.add(t - 0.2, sfx.whoosh(0.6, 200, 6000, 0.7, seed=4), 0.8, 0.1, 0.3)
            m.add(t, sfx.heartbeat(), 0.8, 0, 0.3)
        elif kind == "plank":
            m.add(t, sfx.chime(520 * 2 ** (extra * 2 / 12), 0.35), 0.7, -0.1 + 0.1 * extra, 0.5)
            m.add(t, sfx.step_heavy(extra), 0.4, 0, 0.2)
        elif kind == "take":
            m.add(t - 0.55, sfx.power_up(110), 0.9, 0.4, 0.4)
            m.add(t, sfx.boom(3.5), 1.0, 0, 0.5)
            m.add(t, sfx.sparkle(1.8), 0.6, 0.4, 0.6)
        elif kind == "voice":
            m.add(t, sfx.glitch(extra), 0.6, -0.4, 0.2)
            m.add(t, sfx.lock_on(extra), 0.5, -0.4, 0.3)
            m.add(t + 0.1, sfx.laugh(40 + extra, 3, 120, 0.4) if extra == 1 else sfx.heart_break() * 0.4, 0.4, -0.4, 0.4)
    # time passing
    tt_ = AGE_A
    while tt_ < AGE_B:
        m.add(tt_, sfx.tick(2400, 0.3), 0.35, 0, 0.05)
        tt_ += 0.14
    m.add(AGE_A, sfx.power_down(AGE_B - AGE_A), 0.35, -0.3, 0.4)
    m.add(P1, sfx.text_hit(1), 0.55, 0, 0.4)
    m.add(P2, sfx.text_hit(2), 0.65, 0, 0.4)
    m.add(P3, sfx.text_hit(3), 0.95, 0, 0.5)
    m.add(P3, sfx.boom(2.0), 0.45, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [0.6, 1.4, 3.8, 4.6, 5.6, 6.3, 7.8, 8.2, 10.0, 13.0, P3 + 1.0]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
