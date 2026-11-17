"""EP20 - TALENT VS OBSESSION  (the rematch: this time TALENT wins)

Split screen (EP02/EP19 format), moving from the first frame. 400 M race.
TOP     TALENT runs relaxed, even waves at the camera mid-race, then turns on
        the afterburners in the last 100 m (sparkles, speed lines).
BOTTOM  OBSESSION leads from the start, red, all-in, grimacing.
Last metres in slow motion: TALENT breaks the tape. OBSESSION's legs give
out - he falls one step before the line (his tape is still intact).
TEXT    SOMETIMES TALENT JUST WINS.
Then OBSESSION pushes himself up (red aura), turns around and walks back to
the START line.  TEXT  ...OR DOES IT?
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import (FPS, RED, WHITE, W, Particles, clamp, draw_spaced, ease_out, font, mix, paint,
                    rotate_pose, run_pose, smoothstep)
from kit import CX, GREY, Log, Video, arms_up, blend, caption, draw_body, kneel, lane_cam, mirror, stand
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep20_talent_vs_obsession_rematch"
dt = 1 / FPS
S = 118.0
FINISH = 40.0                 # 1 world unit = 10 m
LANES = {"TALENT": (330, 935, 860), "OBSESSION": (965, 1565, 1475)}
RUN_SX = 400.0
STRIDE = 2.6

T_KF = [(0, 0.0), (4.0, 11.0), (8.0, 22.0), (11.0, 34.5), (13.2, 40.4), (14.0, 41.6)]
O_KF = [(0, 0.0), (4.0, 14.0), (8.0, 26.0), (11.0, 34.6), (13.0, 38.75)]
WAVE = (5.0, 6.6)
BOOST = 8.8
SLOW = (11.0, 13.4)
O_FALL = 13.0
T_WIN = 13.05
TXT1 = 13.8
O_RISE = (15.6, 16.4)
O_TURN = 16.4
TXT2 = 16.6
DUR = 19.6


def keys(t, kf):
    if t <= kf[0][0]:
        return kf[0][1]
    for (t0, v0), (t1, v1) in zip(kf, kf[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * (t - t0) / (t1 - t0)
    return kf[-1][1]


def pos(n, t):
    if n == "TALENT":
        return keys(t, T_KF)
    if t < O_TURN:
        return keys(t, O_KF)
    return 38.75 - 1.4 * (t - O_TURN)          # walking back to the start


def spd(n, t):
    return abs(pos(n, t + 0.02) - pos(n, t - 0.02)) / 0.04


def prone(x):
    """Face down on the track, head towards +x."""
    hip = np.array([x, 0.22])
    neck = np.array([x + 0.92, 0.26])
    sh = hip + (neck - hip) * 0.86
    return {"hip": hip, "neck": neck, "head": np.array([x + 1.3, 0.3]), "shoulder": sh,
            "knee1": np.array([x - 0.78, 0.15]), "foot1": np.array([x - 1.55, 0.12]),
            "knee2": np.array([x - 0.7, 0.3]), "foot2": np.array([x - 1.4, 0.18]),
            "elbow1": sh + [0.35, -0.12], "hand1": sh + [0.75, -0.14],
            "elbow2": sh + [0.2, -0.1], "hand2": sh + [0.6, -0.15]}


def gate(e, f_, cam, label, tape_state, t):
    for px in (FINISH, FINISH + 0.9):
        e.drawLine(*cam.pt((px, 0)), *cam.pt((px, 2.9)), paint(WHITE, 0.7, 4))
    e.drawLine(*cam.pt((FINISH, 2.9)), *cam.pt((FINISH + 0.9, 2.9)), paint(WHITE, 0.7, 4))
    gx, gy = cam.pt((FINISH + 0.45, 2.9))
    draw_spaced(e, label, gx, gy - 12, font(0.22 * cam.s, "InterDisplay-Black"), 3, paint(WHITE, 0.9))
    if label != "FINISH":
        return
    if tape_state is None:
        p = skia.Path()
        p.moveTo(*cam.pt((FINISH, 1.6)))
        for k in range(1, 9):
            p.lineTo(*cam.pt((FINISH + 0.9 * k / 8, 1.6 + 0.04 * math.sin(t * 9 + k))))
        f_.drawPath(p, paint(RED, 1.0, 6))
    else:
        b = ease_out(min(1, tape_state))
        f_.drawLine(*cam.pt((FINISH, 1.6)), *cam.pt((FINISH + 0.15, 1.6 - 1.2 * b)), paint(RED, 1.0, 6))
        f_.drawLine(*cam.pt((FINISH + 0.9, 1.6)), *cam.pt((FINISH + 1.1, 1.6 - 1.1 * b)), paint(RED, 1.0, 6))


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    sparkles = Particles(3)
    aura = Particles(4)
    rng = np.random.default_rng(2)
    ph = {"TALENT": 0.3, "OBSESSION": 0.0}
    contact = {}
    frozen = None
    for fi in range(v.n):
        t = fi * dt
        slow = smoothstep(SLOW[0], SLOW[0] + 0.3, t) * (1 - smoothstep(SLOW[1] - 0.2, SLOW[1], t))
        for n in ("TALENT", "OBSESSION"):
            s = spd(n, t)
            if n == "OBSESSION" and O_FALL <= t < O_TURN:
                s = 0.0
            cad = 1.0 if n == "OBSESSION" else 0.85
            if n == "OBSESSION" and t >= O_TURN:
                cad = 1.2
            ph[n] += (s / STRIDE) * 2 * math.pi * dt * cad * (1 + 1.6 * slow)
            for leg in range(2):
                c = math.floor((ph[n] + leg * math.pi - 1.87) / (2 * math.pi))
                key = n + str(leg)
                if contact.get(key) is not None and c != contact[key] and s > 0.3:
                    log.add(t, "step_" + n, int(t * 100))
                contact[key] = c
        for key, tt, kind in (("go", 0.0, "go"), ("wave", WAVE[0], "wave"), ("boost", BOOST, "boost"),
                              ("slow", SLOW[0], "slow"), ("fall", O_FALL, "fall"), ("win", T_WIN, "win"),
                              ("txt1", TXT1, "txt1"), ("rise", O_RISE[0], "rise"), ("turn", O_TURN, "turn"),
                              ("txt2", TXT2, "txt2")):
            if t >= tt:
                log.once(key, tt, kind)
        if t >= BOOST and t < T_WIN + 1.5 and rng.random() < 0.7:
            x = pos("TALENT", t)
            sparkles.emit(np.array([[x - 0.3 + rng.normal(0, 0.2), rng.uniform(0.4, 2.6)]]), vel=(-2.0, 0.3), spread=0.4,
                          life=(0.3, 0.7), size=(0.02, 0.05))
        if O_RISE[0] - 0.2 <= t < O_TURN + 0.8:
            x = pos("OBSESSION", t)
            aura.emit(np.array([[x + rng.normal(0, 0.4), rng.uniform(0.3, 2.4)] for _ in range(3)]), vel=(0, 1.3), spread=0.4,
                      life=(0.5, 1.0), size=(0.02, 0.05))
        sparkles.step(dt)
        aura.step(dt)
        if not v.wants(fi):
            continue

        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        for n, (y0, y1, gy) in LANES.items():
            x = pos(n, t)
            cam = lane_cam(S, gy, x)
            cam.sx = RUN_SX if not (n == "OBSESSION" and t >= O_TURN) else RUN_SX + 160 * smoothstep(O_TURN, O_TURN + 0.8, t)
            for L in (v.env, v.fig, v.hero, v.txt):
                L.canvas.save()
                L.canvas.clipRect(skia.Rect(0, y0, W, y1))
            e.drawLine(0, gy, W, gy, paint(WHITE, 0.55, 2.5))
            k0 = math.floor(x - 4)
            for k in range(k0, k0 + 10):
                sx, _ = cam.pt((k * 1.0, 0))
                e.drawLine(sx, gy + 10, sx - 18, gy + 26, paint(WHITE, 0.16, 2))
            for mk in range(0, 41, 10):           # 100 m markers
                if abs(mk - x) < 6 and mk not in (0, 40):
                    sx, _ = cam.pt((mk + 1.8, 0))
                    e.drawLine(sx, gy, sx, gy - 0.9 * S, paint(WHITE, 0.4, 3))
                    draw_spaced(tc, f"{mk * 10}M", sx, gy - 0.95 * S, font(24, "InterDisplay-Bold"), 2, paint(WHITE, 0.6))
            if abs(FINISH - x) < 7:
                tape = None
                if n == "TALENT" and t >= T_WIN:
                    tape = (t - T_WIN) / 0.4
                gate(e, f_, cam, "FINISH", tape, t)
            if abs(0 - x) < 7:
                gate(e, f_, cam, "START", None, t)
            # speed lines in the boost / slow-mo
            if n == "TALENT" and BOOST <= t < T_WIN:
                for k in range(6):
                    ly = gy - 60 - 70 * k
                    lx = W - ((t * 2200 + k * 337) % (W + 300))
                    e.drawLine(lx, ly, lx + 160, ly, paint(WHITE, 0.15, 2))
            # runner
            if n == "TALENT":
                inten = 0.75 + 0.25 * smoothstep(BOOST, BOOST + 0.6, t)
                j = run_pose(x, ph[n], inten, 0, 0.05 + 0.15 * smoothstep(BOOST, BOOST + 0.6, t), -0.05)
                if WAVE[0] <= t < WAVE[1]:
                    w = smoothstep(WAVE[0], WAVE[0] + 0.2, t) * (1 - smoothstep(WAVE[1] - 0.2, WAVE[1], t))
                    sh = j["shoulder"]
                    wav = 0.25 * math.sin(t * 14)
                    j["elbow2"] = j["elbow2"] * (1 - w) + (sh + [0.15 + wav * 0.3, 0.55]) * w
                    j["hand2"] = j["hand2"] * (1 - w) + (sh + [0.3 + wav, 1.1]) * w
                if t >= T_WIN + 0.3:
                    j = blend(j, arms_up(x, t), smoothstep(T_WIN + 0.3, T_WIN + 0.8, t))
                draw_body(hc, j, cam, WHITE, 1.0, 0.2)
                sparkles.draw(f_, cam, WHITE, WHITE)
                if WAVE[0] + 0.2 <= t < WAVE[1] - 0.1:
                    hx, hy = cam.pt(j["head"])
                    draw_spaced(oc, "HI MOM.", hx + 10, hy - 70, font(34, "InterDisplay-Black"), 2, paint(WHITE, 1.0))
                col = WHITE
            else:
                if t < O_FALL:
                    strain = smoothstep(9.0, 12.5, t)
                    j = run_pose(x, ph[n], 1.0, 0, 0.25 + 0.15 * strain, 0.15 + 0.25 * strain)
                    if strain > 0.3:
                        j = {kk: vv + [0.015 * math.sin(t * 40) * strain, 0] for kk, vv in j.items()}
                elif t < O_RISE[0]:
                    if frozen is None:
                        jf = run_pose(x, ph[n], 1.0, 0, 0.4, 0.4)
                        pv = jf["foot1"] if jf["foot1"][0] > jf["foot2"][0] else jf["foot2"]
                        frozen = (jf, pv.copy())
                    jf, pv = frozen
                    u = (t - O_FALL) / 0.45
                    rot = rotate_pose(jf, pv, -1.4 * ease_out(min(1, u)))
                    j = blend(rot, prone(x - 0.2), smoothstep(0.5, 1.0, u))
                    if t > O_FALL + 1.6:                       # fist hits the floor
                        hit = smoothstep(O_FALL + 1.6, O_FALL + 1.75, t) * (1 - smoothstep(O_FALL + 1.75, O_FALL + 1.95, t))
                        j["hand1"] = j["hand1"] + [0, 0.35 * hit]
                        j["elbow1"] = j["elbow1"] + [0, 0.2 * hit]
                elif t < O_TURN:
                    u = smoothstep(*O_RISE, t)
                    j = blend(prone(x - 0.2), kneel(x, t, 0.2), smoothstep(0.0, 0.5, u))
                    j = blend(j, stand(x, 0.1, 0.15, 0.1, 0.4, 0.4, 0.0), smoothstep(0.5, 1.0, u))
                else:
                    jw = run_pose(0.0, ph[n], 0.32)
                    jw = {kk: vv + [x, 0] for kk, vv in jw.items()}
                    j = blend(stand(x, 0.1, 0.15, 0.1, 0.4, 0.4, 0.0), mirror(jw, x), smoothstep(O_TURN, O_TURN + 0.3, t))
                col = RED
                draw_body(hc, j, cam, col, 1.0, 0.25)
                aura.draw(f_, cam, RED, RED)
                if O_RISE[0] <= t < O_RISE[0] + 0.8:
                    age = t - O_RISE[0]
                    cx_, cy_ = cam.pt((x, 1.1))
                    f_.drawCircle(cx_, cy_, (0.5 + 3.0 * ease_out(age / 0.8)) * cam.s, paint(RED, 0.6 * (1 - age / 0.8), 6))
            lx, _ = cam.pt((x if not (n == "OBSESSION" and O_FALL <= t < O_RISE[0]) else x + 0.3, 0))
            draw_spaced(tc, n, lx, gy + 44, font(26, "Inter-Bold"), 5, paint(RED if n == "OBSESSION" else WHITE, 1.0))
            meters = int(round(min(400, max(0, x) * 10))) if not (n == "OBSESSION" and t >= O_FALL) else 399
            ka = smoothstep(2.4, 2.7, t)
            draw_spaced(tc, f"{meters} M", 760, y0 + 60, font(40, "InterDisplay-Black"), 2, paint(WHITE, 0.9 * ka))
            if n == "TALENT" and t >= T_WIN:
                pop = 1 + 0.4 * math.exp(-(t - T_WIN) * 8)
                draw_spaced(tc, "1ST", 760, y0 + 125, font(56 * pop, "InterDisplay-Black"), 2, paint(WHITE, 1.0))
            if n == "OBSESSION" and t >= O_FALL + 0.4:
                pop = 1 + 0.4 * math.exp(-(t - O_FALL - 0.4) * 8)
                draw_spaced(tc, "DNF", 760, y0 + 125, font(56 * pop, "InterDisplay-Black"), 2, paint(RED, 1.0))
            for L in (v.env, v.fig, v.hero, v.txt):
                L.canvas.restore()

        # divider + progress bar
        oc.drawRect(skia.Rect(0, 935, W, 965), paint((0, 0, 0), 1.0))
        oc.drawLine(120, 950, 840, 950, paint(WHITE, 0.35, 3))
        oc.drawLine(840, 938, 840, 962, paint(WHITE, 0.8, 3))
        for n, col in (("OBSESSION", RED), ("TALENT", WHITE)):
            px = 120 + 720 * clamp(pos(n, t) / FINISH)
            oc.drawCircle(px, 950, 11, paint(col, 1.0))
        # texts
        if t < 2.6:
            ta = 1 - smoothstep(2.2, 2.6, t)
            caption(oc, "TALENT VS OBSESSION", 405, ta, WHITE, 50)
            draw_spaced(oc, "400 M", 760, 1025, font(40, "InterDisplay-Black"), 2, paint(RED, ta * smoothstep(0.2, 0.35, t)))
        if SLOW[0] + 0.2 <= t < SLOW[1]:
            draw_spaced(oc, "SLOW MOTION", CX - 60, 400, font(26, "Inter-Bold"), 6, paint(RED, 0.9 * (0.6 + 0.4 * math.sin(t * 8))))
        if TXT1 <= t < O_RISE[0] + 0.2:
            a = smoothstep(TXT1, TXT1 + 0.3, t) * (1 - smoothstep(O_RISE[0] - 0.1, O_RISE[0] + 0.2, t))
            oc.drawRect(skia.Rect(0, 660, W, 860), paint((0, 0, 0), 0.85 * a))
            caption(oc, "SOMETIMES TALENT", 745, a, WHITE, 60, band=False)
            caption(oc, "JUST WINS.", 830, a, WHITE, 60, band=False)
        if t >= TXT2:
            a = smoothstep(TXT2, TXT2 + 0.3, t)
            oc.drawRect(skia.Rect(0, 680, W, 840), paint((0, 0, 0), 0.85 * a))
            caption(oc, "...OR DOES IT?", 790, a, RED, 72, band=False)
        flash = math.exp(-(t - T_WIN) * 3) if t >= T_WIN else 0.0
        v.compose(fi, t, flash=flash * 0.8, glow=0.3 * slow, dim=0.25 * slow, fade_in=0.0)
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=T_WIN), gain=0.4, fade_in=0.3, fade_out=2.0, stop=DUR)
    last = {"TALENT": -1.0, "OBSESSION": -1.0}
    for t, kind, _, extra in events:
        if kind.startswith("step_"):
            n = kind[5:]
            if t - last[n] < 0.08:
                continue
            last[n] = t
            if n == "TALENT":
                m.add(t, sfx.step_light(extra), 0.25, 0.0, 0.1)
            else:
                m.add(t, sfx.step_heavy(extra), 0.25, 0.0, 0.15)
        elif kind == "go":
            m.add(0.0, sfx.beep(1320, 0.35), 0.6, 0, 0.3)
            m.add(0.02, sfx.text_hit(5), 0.6, 0, 0.4)
        elif kind == "wave":
            m.add(t + 0.2, sfx.chime(880, 0.3), 0.5, 0, 0.4)
        elif kind == "boost":
            m.add(t, sfx.whoosh(0.8, 300, 9000, 0.4, seed=4), 0.7, 0, 0.3)
            m.add(t, sfx.sparkle(1.5, 70, 3), 0.5, 0, 0.5)
        elif kind == "slow":
            m.add(t, sfx.whoosh(0.6, 100, 3000, 0.8, seed=7), 0.6, 0, 0.4)
            for k in range(3):
                m.add(t + 0.3 + 0.75 * k, sfx.heartbeat(), 0.7 + 0.1 * k, 0, 0.3)
            m.add(t, sfx.riser(2.0), 0.45, 0, 0.3)
        elif kind == "fall":
            m.add(t + 0.35, sfx.body_fall(), 0.9, 0, 0.4)
            m.add(t + 0.4, sfx.power_down(1.4), 0.4, 0, 0.4)
            m.add(t + 1.7, sfx.punch_hit(3, 1.0), 0.6, 0, 0.3)
        elif kind == "win":
            m.add(t, sfx.boom(3.5), 0.9, 0, 0.5)
            m.add(t + 0.2, sfx.applause(2.5, 40, 2), 0.45, 0, 0.3)
        elif kind == "txt1":
            m.add(t, sfx.text_hit(1), 0.7, 0, 0.4)
        elif kind == "rise":
            m.add(t - 0.4, sfx.power_up(70), 0.9, 0, 0.4)
        elif kind == "turn":
            for k in range(6):
                m.add(t + 0.2 + k * 0.4, sfx.step_heavy(k), 0.4, 0, 0.2)
        elif kind == "txt2":
            m.add(t, sfx.text_hit(3), 0.95, 0, 0.5)
            m.add(t, sfx.boom(2.0), 0.45, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [0.1, 1.5, 3.0, 5.6, 8.0, 9.5, 11.8, 12.9, 13.3, 14.5, 15.9, 17.5]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
