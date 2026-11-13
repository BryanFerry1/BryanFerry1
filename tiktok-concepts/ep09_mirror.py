"""EP09 - EGO VS OBSESSION  (the mirror)

Split screen, each one in front of a mirror.
Visual hook: the reflections don't match. EGO's reflection is a glowing
bodybuilder flexing; OBSESSION's is small, dim and the glass is cracked.
EGO keeps admiring (flex, selfies). Days pass: the real EGO gets a belly,
greys and slumps - the reflection stays perfect.
OBSESSION trains in front of his cracked mirror: he grows, the cracks heal,
the reflection grows with him until it matches -> the mirror shines.
EGO's mirror cracks red, glitches between lie and truth, shatters.
PUNCH  EGO LOVES THE MIRROR. / OBSESSION BECOMES / THE REFLECTION.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import FPS, RED, WHITE, W, clamp, ease_out, mix, paint, smoothstep
from kit import (CX, GREY, Log, Shards, Video, blend, body_scale, crossed, curl, draw_body,
                 draw_phone_small, flex, hud, kneel, label, lane_cam, mirror, phone_pose, punch,
                 sad, scale_pose, shift, stand, title)
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep09_mirror"
dt = 1 / FPS
S = 108.0
TOP_G, BOT_G = 905.0, 1525.0
DIV = 945.0
FX, MX = -1.5, 1.35           # figure x, mirror centre x
MW, MH = 0.82, 3.55           # mirror half width, height

INTRO = 2.6
MONT_A, MONT_N, MONT_REP = 5.0, 14, 0.58
MONT_END = MONT_A + MONT_N * MONT_REP
MATCH = MONT_END + 0.3
CRACK = MATCH + 0.9
SHATTER = CRACK + 0.9
KNEEL_T = SHATTER + 0.2
P1, P2, P3 = SHATTER + 1.4, SHATTER + 2.2, SHATTER + 2.7
DUR = P3 + 3.0


def day_of(t):
    if t < MONT_A:
        return 1
    u = clamp((t - MONT_A) / (MONT_END - MONT_A))
    return max(1, int(round(365 ** u)))


def ego_pose(t):
    """Ego keeps posing in front of the mirror."""
    if t < INTRO:
        return stand(FX)
    k = int((t - INTRO) / 1.3) % 3
    poses = [flex(FX, t), phone_pose(FX, t), stand(FX, -0.08, 0.3, 0.25, 1.9, 1.95, -0.25)]
    u = ((t - INTRO) % 1.3) / 1.3
    a = poses[k]
    b = poses[(k + 1) % 3]
    return blend(a, b, smoothstep(0.8, 1.0, u))


def obs_pose(t):
    if t < INTRO + 0.4:
        return stand(FX)
    if t < MONT_A:
        return blend(stand(FX), sad(FX, t), smoothstep(INTRO + 0.4, INTRO + 0.9, t) * (1 - smoothstep(MONT_A - 0.5, MONT_A, t)))
    if t < MONT_END:
        u = ((t - MONT_A) % MONT_REP) / MONT_REP
        return curl(FX, math.sin(math.pi * u))
    return blend(curl(FX, 0), flex(FX, t), smoothstep(MONT_END, MATCH, t))


def draw_mirror(c, cam, alpha, glow=0.0, col=WHITE):
    l, tp = cam.pt((MX - MW, MH))
    r, b = cam.pt((MX + MW, 0.15))
    rect = skia.Rect(l, tp, r, b)
    c.drawRoundRect(rect, 18, 18, paint(col, 0.05 + 0.1 * glow))
    c.drawRoundRect(rect, 18, 18, paint(col, 0.9 * alpha, 5))
    c.drawLine(*cam.pt((MX, 0.15)), *cam.pt((MX, 0.0)), paint(col, 0.7 * alpha, 5))
    c.drawLine(*cam.pt((MX - 0.4, 0.0)), *cam.pt((MX + 0.4, 0.0)), paint(col, 0.7 * alpha, 5))
    return rect


CRACKS_O = [[(-0.6, 3.2), (-0.1, 2.4), (0.25, 2.6), (0.6, 1.6)], [(0.7, 3.3), (0.2, 2.2), (-0.3, 1.4), (-0.7, 0.9)],
            [(-0.1, 2.4), (-0.5, 1.9)], [(0.2, 2.2), (0.55, 0.5)]]
CRACKS_E = [[(0.0, 2.0), (-0.4, 2.9), (-0.7, 3.4)], [(0.0, 2.0), (0.5, 2.8), (0.75, 3.1)], [(0.0, 2.0), (-0.6, 1.4)],
            [(0.0, 2.0), (0.35, 1.0), (0.6, 0.4)], [(0.0, 2.0), (-0.2, 0.6)], [(0.0, 2.0), (0.8, 2.1)]]


def draw_cracks(c, cam, cracks, alpha, col, grow=1.0):
    for line in cracks:
        n = max(2, int(math.ceil(len(line) * grow)))
        p = skia.Path()
        for k, (x, y) in enumerate(line[:n]):
            (p.moveTo if k == 0 else p.lineTo)(*cam.pt((MX + x, y)))
        c.drawPath(p, paint(col, alpha, 3))


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    shards = Shards(4)
    rng = np.random.default_rng(3)
    for fi in range(v.n):
        t = fi * dt
        day = day_of(t)
        u_m = clamp((t - MONT_A) / (MONT_END - MONT_A))
        # --- events
        if t >= INTRO:
            log.once("shine", t, "shine")
        if t >= INTRO + 0.5:
            log.once("sad", t, "sad")
        if MONT_A <= t < MONT_END:
            k = int((t - MONT_A) / MONT_REP)
            log.once(f"rep{k}", t, "rep", k)
            if int((t - INTRO) / 1.3) % 3 == 1:
                log.once(f"selfie{int((t - INTRO) / 1.3)}", t + 0.3, "selfie")
        if t >= MATCH:
            log.once("match", t, "match")
        if t >= CRACK:
            log.once("crack", t, "crack")
        if t >= SHATTER:
            log.once("shatter", t, "shatter")
            if "shards" not in log.seen:
                log.seen.add("shards")
                shards.burst(MX - MW, MX + MW, 0.3, MH, 70, vx=(-4, 1.5), vy=(-1, 5))
        if t >= KNEEL_T + 0.3:
            log.once("kneel", t, "kneel")
        shards.step(dt)
        if not v.wants(fi):
            continue

        v.clear()
        e, f_, tc, hc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas
        end_dim = 0.55 * smoothstep(P1 - 0.4, P1, t)
        # ============ TOP: EGO
        cam = lane_cam(S, TOP_G)
        for L in (v.env, v.fig, v.hero):
            L.canvas.save()
            L.canvas.clipRect(skia.Rect(0, 0, W, DIV))
        e.drawLine(80, TOP_G, W - 80, TOP_G, paint(WHITE, 0.5, 2.5))
        fat = u_m * (1 - 0.0)
        ego_col = mix(WHITE, GREY, 0.75 * u_m)
        broken = t >= SHATTER
        rect = draw_mirror(e, cam, 1.0 if not broken else 0.6, 0.5 * (1 - u_m) if not broken else 0, WHITE if not broken else RED)
        jE = ego_pose(t)
        if t >= KNEEL_T:
            jE = blend(jE, kneel(FX, t, 0.9), smoothstep(KNEEL_T, KNEEL_T + 0.5, t))
        slump = 0.25 * u_m
        jE_real = {k: v_ for k, v_ in jE.items()}
        if slump > 0 and t < KNEEL_T:
            jE_real = stand(FX, 0.02 + slump, 0, 0, 0, 0, 0.2 * u_m)
            jE_real = blend(jE, jE_real, 0.0)  # keep arms of the pose
            jE_real["neck"] = jE["neck"] + [0.12 * u_m, -0.06 * u_m]
            jE_real["head"] = jE["head"] + [0.18 * u_m, -0.1 * u_m]
            jE_real["shoulder"] = jE["shoulder"] + [0.1 * u_m, -0.05 * u_m]
        # reflection
        if not broken:
            hc.save()
            hc.clipRect(rect)
            ideal = shift(jE, MX - FX)
            ideal = mirror(scale_pose(ideal, MX, 1.04), MX)
            if t >= CRACK and rng.random() < 0.45:     # glitch: the truth leaks through
                truth = mirror(shift(jE_real, MX - FX), MX)
                draw_body(hc, truth, cam, GREY, 0.8, 0.0, fat)
            else:
                draw_body(hc, ideal, cam, WHITE, 0.95, 1.0)
                if t > INTRO and rng.random() < 0.5:
                    p = ideal["head"] + rng.normal(0, 0.6, 2)
                    hc.drawCircle(*cam.pt(p), 3, paint(WHITE, 0.8))
            hc.restore()
            if t >= CRACK:
                draw_cracks(f_, cam, CRACKS_E, 0.95, RED, smoothstep(CRACK, CRACK + 0.5, t))
        shards.draw(f_, cam, RED)
        draw_body(hc, jE_real, cam, ego_col, 1.0, 0.0, fat)
        if int((t - INTRO) / 1.3) % 3 == 1 and t > INTRO and t < KNEEL_T:
            draw_phone_small(f_, cam, jE["hand1"] + [0.05, 0.1], 0.9)
        label(tc, cam, FX, "EGO", smoothstep(0.3, 0.8, t) * (1 - smoothstep(P1 - 0.5, P1, t)), RED, 34, 26)
        for L in (v.env, v.fig, v.hero):
            L.canvas.restore()
        e.drawLine(0, DIV, W, DIV, paint(WHITE, 0.2, 2))

        # ============ BOTTOM: OBSESSION
        camb = lane_cam(S, BOT_G)
        for L in (v.env, v.fig, v.hero):
            L.canvas.save()
            L.canvas.clipRect(skia.Rect(0, DIV, W, 1700))
        e.drawLine(80, BOT_G, W - 80, BOT_G, paint(WHITE, 0.5, 2.5))
        g = u_m if t < MONT_END else 1.0
        match = smoothstep(MONT_END, MATCH, t)
        rectb = draw_mirror(e, camb, 1.0, 1.5 * math.exp(-max(0, t - MATCH) * 2.5) if t >= MATCH else 0.0)
        jO = obs_pose(t)
        sc = body_scale(g)
        jO = scale_pose(jO, FX, sc)
        hc.save()
        hc.clipRect(rectb)
        refl_sc = 0.62 + 0.38 * smoothstep(0, 1, u_m if t < MONT_END else 1)
        refl = mirror(scale_pose(shift(jO, MX - FX), MX, refl_sc / sc * sc), MX)
        draw_body(hc, refl, camb, WHITE, 0.45 + 0.5 * u_m + 0.05 * match, g * 0.9 + 0.1 * match)
        hc.restore()
        crack_a = 0.85 * (1 - smoothstep(MONT_A, MONT_END - 1.5, t))
        draw_cracks(f_, camb, CRACKS_O, crack_a, WHITE)
        bar = (jO["hand1"] + jO["hand2"]) / 2
        if MONT_A <= t < MONT_END + 0.2:
            for kk, rr in enumerate([0.12] + [0.2] * int(g * 3)):
                cx, cy = camb.pt(bar + np.array([0.06, -0.04]) * kk)
                hc.drawCircle(cx, cy, rr * S, paint((0, 0, 0), 1.0))
                hc.drawCircle(cx, cy, rr * S, paint(WHITE, 0.95, 3))
        draw_body(hc, jO, camb, WHITE, 1.0, g)
        label(tc, camb, FX, "OBSESSION", smoothstep(0.3, 0.8, t) * (1 - smoothstep(P1 - 0.5, P1, t)), WHITE, 40, 26)
        for L in (v.env, v.fig, v.hero):
            L.canvas.restore()

        # HUD / title / punch
        hud(tc, "DAY", day, smoothstep(MONT_A - 0.3, MONT_A, t) * (1 - 0.6 * smoothstep(P1 - 0.3, P1 + 0.3, t)), day >= 365)
        title(tc, t, [([("EGO", RED)], 160, 75), ([("VS", WHITE)], 48, 130), ([("OBSESSION", WHITE)], 130, 0)], y0=600)
        if t >= P1 - 0.4:
            a = smoothstep(P1 - 0.4, P1, t) * 0.8
            tc.drawRect(skia.Rect(0, 520, W, 900), paint((0, 0, 0), a))
        punch(tc, t, [(P1, [("EGO", RED), (" LOVES THE MIRROR.", WHITE)], 620, 56),
                      (P2, [("OBSESSION BECOMES", WHITE)], 720, 64),
                      (P3, [("THE REFLECTION.", WHITE)], 840, 92)])
        flash = math.exp(-(t - MATCH) * 3) if t >= MATCH else 0.0
        flash = max(flash, math.exp(-(t - SHATTER) * 4) if t >= SHATTER else 0.0)
        title_dim = 0.65 * smoothstep(0.1, 0.35, t) * (1 - smoothstep(2.4, 2.8, t))
        v.compose(fi, t, flash=flash * 0.8, glow=0.4 * match, dim=max(end_dim * 0.6, title_dim))
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=SHATTER), gain=0.45, fade_in=0.6, fade_out=2.5, stop=DUR)
    m.add(0.1, sfx.text_hit(5), 0.8, 0, 0.4)
    n = 0
    for t, kind, _, extra in events:
        if kind == "shine":
            m.add(t, sfx.sparkle(1.6, 70, 4), 0.6, -0.3, 0.5)
            m.add(t, sfx.chime(880, 0.3), 0.5, -0.3, 0.5)
        elif kind == "sad":
            m.add(t, sfx.power_down(1.6), 0.35, 0.3, 0.5)
        elif kind == "rep":
            n += 1
            m.add(t + 0.25, sfx.plate_clank(30 + extra, 0.45), 0.3, 0.3, 0.25)
            m.add(t + 0.3, sfx.chime(300 * 2 ** (n * 1.3 / 12), 0.22), 0.35, 0.3, 0.4)
            m.add(t, sfx.tick(2400, 0.3), 0.35, 0, 0.05)
        elif kind == "selfie":
            m.add(t, sfx.shutter(int(t * 10)), 0.55, -0.4, 0.2)
        elif kind == "match":
            m.add(t - 0.55, sfx.power_up(110), 0.9, 0.3, 0.4)
            m.add(t, sfx.sparkle(1.8, 90, 6), 0.6, 0.3, 0.6)
        elif kind == "crack":
            m.add(t, sfx.heart_break(), 0.8, -0.3, 0.4)
            for k in range(4):
                m.add(t + 0.18 * k, sfx.glitch(k), 0.45, -0.3, 0.2)
        elif kind == "shatter":
            m.add(t, sfx.shatter(5, 2.0), 1.0, -0.3, 0.5)
            m.add(t, sfx.boom(3.0), 0.8, 0, 0.5)
        elif kind == "kneel":
            m.add(t, sfx.body_fall() * 0.6, 0.6, -0.3, 0.3)
    m.add(SHATTER - 2.0, sfx.riser(2.0), 0.45, 0, 0.3)
    m.add(P1, sfx.text_hit(1), 0.5, 0, 0.4)
    m.add(P2, sfx.text_hit(2), 0.6, 0, 0.4)
    m.add(P3, sfx.text_hit(3), 0.95, 0, 0.5)
    m.add(P3, sfx.boom(2.0), 0.4, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [1.0, 3.5, 4.5, 7.0, 10.0, MONT_END - 0.3, MATCH + 0.3, CRACK + 0.4, SHATTER + 0.4, P3 + 1.0]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
