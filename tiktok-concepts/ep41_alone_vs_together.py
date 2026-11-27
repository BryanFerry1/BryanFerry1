"""EP41 - ALONE VS TOGETHER  (ultra 100 km, EP19 split-screen format + zooms)

TOP     ALONE sprints off, way ahead on the progress bar. NIGHT: runs alone in
        the dark. KM 70: twists his ankle, falls. Zoom: sitting on the road,
        holding his ankle (HELP?)... nobody.
BOTTOM  TOGETHER: a pack of three. Zoom: they pass a water bottle. NIGHT: one
        collapses, zoom: another carries him on his back. They keep going.
MERGE   (surprise) the pack arrives on ALONE's road, stops, lifts him up.
        Four of them run to the line and cross it together.
END     ALONE YOU GO FASTER. / TOGETHER YOU GO FURTHER.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import (FPS, H, L_FARM, L_UARM, RED, WHITE, W, Camera, clamp, draw_spaced, ease_out, fit_font, font, ik,
                    paint, run_pose, smoothstep)
from kit import Log, Video, arms_up, blend, caption, draw_body, ending, kneel, lane_cam, sit, stand
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep41_alone_vs_together"
dt = 1 / FPS
S = 118.0
LANES = {"ALONE": (330, 935, 860), "TOGETHER": (965, 1565, 1475)}
RUN_SX = 400.0
STRIDE = 2.6
NIGHT = (6.0, 14.4)
FALL_B = 6.9
CARRY = (7.5, 10.4)
TWIST = 10.8
ARRIVE = (14.4, 15.1)
LIFT = (15.1, 16.1)
FIN = 19.4
END_T = 21.6
DUR = 25.6
PACK = [1.25, 0.0, -1.25]                 # offsets of the three (front -> back)
A_KF = [(0, 0.0), (6.0, 46.0), (TWIST, 70.0), (40, 70.0)]
T_KF = [(0, 0.0), (6.0, 30.0), (FALL_B, 33.0), (CARRY[0], 33.3), (CARRY[1], 46.0), (ARRIVE[0], 65.2),
        (ARRIVE[1], 67.9), (LIFT[1], 67.9), (FIN, 100.4), (FIN + 2.0, 102.0)]
FULL = [(4.3, 6.0, "TOGETHER", 200, 215), (8.2, 10.2, "TOGETHER", 165, 180), (11.0, 13.0, "ALONE", 230, 200),
        (ARRIVE[0], END_T, "MERGE", 190, 190)]


def keys(t, kf):
    if t <= kf[0][0]:
        return kf[0][1]
    for (t0, v0), (t1, v1) in zip(kf, kf[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * (t - t0) / (t1 - t0)
    return kf[-1][1]


def a_km(t):
    if t < LIFT[1]:
        return keys(t, A_KF)
    return keys(t, T_KF) + 2.6                          # runs at the front of the group


def t_km(t):
    return keys(t, T_KF)


def speed(f, t):
    return (f(t + 0.02) - f(t - 0.02)) / 0.04


def full_at(t):
    for f in FULL:
        if f[0] <= t < f[1]:
            return f
    return None


def finish_gate(c, f_, cam, x, broken_u):
    for px in (x, x + 0.9):
        c.drawLine(*cam.pt((px, 0)), *cam.pt((px, 2.9)), paint(WHITE, 0.7, 4))
    c.drawLine(*cam.pt((x, 2.9)), *cam.pt((x + 0.9, 2.9)), paint(WHITE, 0.7, 4))
    gx, gy = cam.pt((x + 0.45, 2.9))
    draw_spaced(c, "FINISH", gx, gy - 12, font(0.22 * cam.s, "InterDisplay-Black"), 3, paint(WHITE, 0.9))
    if broken_u is None:
        f_.drawLine(*cam.pt((x, 1.6)), *cam.pt((x + 0.9, 1.6)), paint(RED, 1.0, 6))
    else:
        b = ease_out(min(1, broken_u))
        for side, x0 in ((-1, x), (1, x + 0.9)):
            f_.drawLine(*cam.pt((x0, 1.6)), *cam.pt((x0 + side * 0.1, 1.6 - 1.1 * b)), paint(RED, 1.0, 6))


def bottle(c, cam, p, ang=0.0):
    bx, by = cam.pt(p)
    c.save()
    c.translate(bx, by)
    c.rotate(ang)
    c.drawRoundRect(skia.Rect(-0.07 * cam.s, -0.34 * cam.s, 0.07 * cam.s, 0), 4, 4, paint(WHITE, 1.0, 3))
    c.restore()


def pack_poses(x, t, ph):
    """Three runners of TOGETHER around x (front, middle, back)."""
    out = []
    for k, off in enumerate(PACK):
        xx = x + off
        p = ph + k * 2.1
        if FALL_B <= t < CARRY[0] and k == 1:
            u = smoothstep(FALL_B, FALL_B + 0.35, t)
            j = blend(run_pose(xx, p, 0.7), kneel(xx, t, 0.9), u)
        elif CARRY[0] <= t < CARRY[1] and k == 1:
            # exhausted: head down, pulled by the front one, pushed by the back one
            j = run_pose(xx, p, 0.4, 0, 0.45, 0.6)
            j["elbow1"] = j["shoulder"] + [0.45, -0.15]
            j["hand1"] = j["shoulder"] + [0.9, -0.05]
        elif CARRY[0] <= t < CARRY[1] and k == 0:
            j = run_pose(xx, p, 0.5, 0, 0.25, 0.0)
            mid = run_pose(x, ph + 2.1, 0.4, 0, 0.45, 0.6)
            hand = mid["shoulder"] + np.array([0.9, -0.05])
            j["hand2"] = hand
            j["elbow2"] = ik(j["shoulder"], hand, L_UARM, L_FARM, -1)
        elif CARRY[0] <= t < CARRY[1] and k == 2:
            j = run_pose(xx, p, 0.5, 0, 0.3, 0.0)
            mid = run_pose(x, ph + 2.1, 0.4, 0, 0.45, 0.6)
            hand = (mid["shoulder"] + mid["hip"]) / 2 + np.array([-0.12, 0.0])
            j["hand1"] = hand
            j["elbow1"] = ik(j["shoulder"], hand, L_UARM, L_FARM, -1)
        elif FALL_B + 0.3 <= t < CARRY[0] and k != 1:
            j = stand(xx, 0.3, 0.5, 0.4, 0.4, 0.3, 0.5)
        else:
            j = run_pose(xx, p, 0.7, 0, 0.15, 0.05)
            if 4.6 <= t < 5.8 and k == 1:                # pass the bottle forward
                j["elbow1"] = j["shoulder"] + [0.42, -0.1]
                j["hand1"] = j["shoulder"] + [0.85, 0.05]
        out.append(j)
    return out


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    ph = {"ALONE": 0.0, "TOGETHER": 0.5}
    for fi in range(v.n):
        t = fi * dt
        sa, st = speed(a_km, t), speed(t_km, t)
        ph["ALONE"] += (min(sa, 9) / STRIDE) * 2 * math.pi * dt * 0.55
        ph["TOGETHER"] += (min(st, 9) / STRIDE) * 2 * math.pi * dt * 0.7
        if int(ph["ALONE"] / math.pi) != int((ph["ALONE"] - 0.01) / math.pi) and sa > 0.5:
            log.add(t, "step_a", int(t * 100))
        for key, tt, kind in (("go", 0.0, "go"), ("water", 4.6, "water"), ("night", NIGHT[0], "night"),
                              ("fallb", FALL_B, "fall"), ("carry", CARRY[0], "carry"), ("twist", TWIST, "twist"),
                              ("alone", 11.4, "alone"), ("arrive", ARRIVE[0], "arrive"), ("lift", LIFT[0], "lift"),
                              ("go2", LIFT[1], "go2"), ("fin", FIN, "fin"), ("end", END_T, "end"),
                              ("end2", END_T + 1.3, "end2")):
            if t >= tt:
                log.once(key, tt, kind)
        for k, f in enumerate(FULL):
            if t >= f[0]:
                log.once(f"full{k}", f[0], "zoom")
        if not v.wants(fi):
            continue

        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        night = smoothstep(NIGHT[0], NIGHT[0] + 0.5, t) * (1 - smoothstep(NIGHT[1] - 0.5, NIGHT[1], t))
        fz = full_at(t)
        panes = []
        if fz is None:
            for n, (y0, y1, gy) in LANES.items():
                x = a_km(t) if n == "ALONE" else t_km(t)
                cam = lane_cam(S, gy, x)
                cam.sx = RUN_SX
                panes.append((n, y0, y1, cam, False))
        else:
            t0, t1, n, s0, s1 = fz
            u = clamp((t - t0) / (t1 - t0))
            cam = Camera()
            cam.s = s0 + (s1 - s0) * ease_out(u)
            if n == "TOGETHER":
                cam.wx = t_km(t) + 0.1
            elif n == "ALONE":
                cam.wx = a_km(t) + 0.4 - 1.5 * ease_out(u)
            else:
                if t < LIFT[1]:
                    cam.wx = (a_km(t) + t_km(t)) / 2 - 0.2
                else:
                    cam.wx = t_km(t) + 0.8
                cam.s = 170 if t < FIN - 1.0 else 170 + 40 * smoothstep(FIN - 1.0, FIN, t)
            cam.wy = 1.4
            cam.sx, cam.sy = 450, 1000
            panes = [(n, 0, H, cam, True)]
        for n, y0, y1, cam, full in panes:
            gy = cam.pt((0, 0))[1]
            for L in (v.env, v.fig, v.hero, v.txt):
                L.canvas.save()
                L.canvas.clipRect(skia.Rect(0, y0, W, y1))
            e.drawLine(0, gy, W, gy, paint(WHITE, 0.55, 2.5))
            k0 = math.floor(cam.wx - 600 / cam.s)
            for k in range(k0, k0 + int(1200 / cam.s) + 2):
                sx, _ = cam.pt((k * 1.0, 0))
                e.drawLine(sx, gy + 10, sx - 18, gy + 26, paint(WHITE, 0.16, 2))
            for mk in range(0, 101, 10):
                if abs(mk - cam.wx) < 6 and mk < 100:
                    sx, _ = cam.pt((mk + 1.8, 0))
                    e.drawLine(sx, gy, sx, gy - 0.9 * cam.s, paint(WHITE, 0.4, 3))
                    draw_spaced(tc, f"{mk}", sx, gy - 0.95 * cam.s, font(max(20, 0.22 * cam.s), "InterDisplay-Bold"), 2,
                                paint(WHITE, 0.6))
            if night > 0.01:
                mx_, my_ = (620, y0 + 80) if not full else (170, 640)
                e.drawCircle(mx_, my_, 36, paint(WHITE, 0.9 * night))
                e.drawCircle(mx_ + 16, my_ - 10, 33, paint((0, 0, 0), night))
            if abs(100 - cam.wx) < 8:
                fin_x = 100.0
                bu = None if t < FIN else (t - FIN) / 0.4
                finish_gate(e, f_, cam, fin_x, bu)
            txt = None
            focus = None
            if n in ("ALONE", "MERGE"):
                x = a_km(t)
                if t < TWIST:
                    j = run_pose(x, ph["ALONE"], 1.0 - 0.3 * night, 0, 0.18 + 0.15 * night, 0.1 + 0.3 * night)
                elif t < LIFT[0]:
                    u = smoothstep(TWIST, TWIST + 0.3, t)
                    j = blend(run_pose(x, ph["ALONE"], 0.8), sit(x - 0.3, 0.0, t, 0.6), u)
                    if t > TWIST + 0.3:
                        j["hand1"] = j["foot1"] + [-0.1, 0.25]
                        j["elbow1"] = ik(j["shoulder"], j["hand1"], L_UARM, L_FARM, -1)
                        if 11.4 < t < 13.0:
                            txt = "HELP?"
                elif t < LIFT[1]:
                    u = smoothstep(LIFT[0] + 0.2, LIFT[1], t)
                    j = blend(sit(x - 0.3, 0.0, t, 0.6), stand(x, 0.05, 0.4, 0.3, 0.3, 0.3, -0.1), u)
                else:
                    j = run_pose(x, ph["TOGETHER"] + 1.0, 0.7, 0, 0.15, 0.05)
                    if t >= FIN + 0.1:
                        j = blend(j, arms_up(x, t), smoothstep(FIN + 0.1, FIN + 0.5, t))
                draw_body(hc, j, cam, RED, 1.0 if t < TWIST or t > LIFT[1] else 0.8, 0.15)
                focus = j
                if t >= TWIST and t < LIFT[0] and full:
                    hx, hy = cam.pt(j["foot1"])
                    for q in range(3):
                        a = q * 2.1 + t * 3
                        f_.drawLine(hx + 20 * math.cos(a), hy - 0.3 * cam.s + 20 * math.sin(a),
                                    hx + 38 * math.cos(a), hy - 0.3 * cam.s + 38 * math.sin(a), paint(RED, 0.9, 4))
            if n in ("TOGETHER", "MERGE") and (n == "TOGETHER" or t >= ARRIVE[0]):
                x = t_km(t)
                if n == "MERGE" and ARRIVE[1] <= t < LIFT[1]:
                    js = [stand(x + off, 0.1, 0.6, 0.5, 0.4, 0.3, 0.2) for off in PACK]
                    if t >= LIFT[0]:
                        for jj in js[:2]:
                            jj["hand1"] = np.array([a_km(t) - 0.3, 1.2 + 0.5 * smoothstep(LIFT[0], LIFT[1], t)])
                            jj["elbow1"] = ik(jj["shoulder"], jj["hand1"], L_UARM, L_FARM, -1)
                else:
                    js = pack_poses(x, t, ph["TOGETHER"])
                    if t >= FIN + 0.1:
                        js = [blend(jj, arms_up(x + off, t), smoothstep(FIN + 0.1, FIN + 0.5, t))
                              for jj, off in zip(js, PACK)]
                for jj in js:
                    draw_body(hc, jj, cam, WHITE, 1.0, 0.15)
                if n == "TOGETHER" and 4.6 <= t < 5.8:
                    bottle(hc, cam, js[1]["hand1"] + [0.05, 0.2], -20)
                    txt = None
                if n == "TOGETHER" and CARRY[0] <= t < CARRY[1] and full:
                    hx, hy = cam.pt(js[0]["head"])
                    draw_spaced(tc, "I GOT YOU.", min(max(hx, 260), 640), max(640, hy - 0.8 * cam.s),
                                fit_font("I GOT YOU.", 60, "InterDisplay-Black", 2, 560), 2, paint(WHITE, 1.0))
                if focus is None:
                    focus = js[1]
            if txt and focus is not None:
                hx, hy = cam.pt(focus["head"])
                ty = hy - 0.8 * cam.s
                ty = max(ty, 640) if full else max(ty, y0 + 70)
                draw_spaced(tc, txt, min(max(hx, 260), 640), ty,
                            fit_font(txt, 60 if full else 40, "InterDisplay-Black", 2, 560), 2, paint(RED, 1.0))
            if not full:
                lx, _ = cam.pt(((a_km(t) if n == "ALONE" else t_km(t)), 0))
                draw_spaced(tc, n, lx, gy + 44, font(26, "Inter-Bold"), 5, paint(RED if n == "ALONE" else WHITE, 1.0))
                kmv = int(min(100, a_km(t) if n == "ALONE" else t_km(t)))
                draw_spaced(tc, f"KM {kmv}", 760, y0 + 60, font(40, "InterDisplay-Black"), 2,
                            paint(WHITE, 0.9 * smoothstep(2.4, 2.7, t)))
            for L in (v.env, v.fig, v.hero, v.txt):
                L.canvas.restore()
        if fz is None:
            y = 950
            oc.drawRect(skia.Rect(0, 935, W, 965), paint((0, 0, 0), 1.0))
            oc.drawLine(120, y, 840, y, paint(WHITE, 0.35, 3))
            oc.drawLine(840, y - 12, 840, y + 12, paint(WHITE, 0.8, 3))
            for f, c_ in ((t_km, WHITE), (a_km, RED)):
                px = 120 + 720 * clamp(f(t) / 100)
                oc.drawCircle(px, y, 11, paint(c_, 1.0))
        else:
            n = fz[2]
            kmv = int(min(100, t_km(t) if n != "ALONE" else a_km(t)))
            lab = {"ALONE": "ALONE", "TOGETHER": "TOGETHER", "MERGE": "TOGETHER"}[n]
            draw_spaced(oc, lab, 470, 380, font(34, "Inter-Bold"), 8,
                        paint(RED if n == "ALONE" else WHITE, 0.85))
            draw_spaced(oc, f"KM {kmv}", 470, 470, font(90, "InterDisplay-Black"), 3,
                        paint(RED if n == "ALONE" else WHITE, 1.0))
        if t < 2.5:
            ta = 1 - smoothstep(2.1, 2.5, t)
            caption(oc, "ALONE VS TOGETHER", 405, ta, WHITE, 52)
            draw_spaced(oc, "100 KM", 760, 1025, font(40, "InterDisplay-Black"), 2, paint(RED, ta * smoothstep(0.2, 0.35, t)))
        if fz is None and NIGHT[0] - 0.1 <= t < NIGHT[0] + 1.5:
            caption(oc, "NIGHT.", 962, smoothstep(NIGHT[0] - 0.1, NIGHT[0] + 0.1, t) *
                    (1 - smoothstep(NIGHT[0] + 1.2, NIGHT[0] + 1.5, t)), WHITE, 40)
        ending(oc, t, END_T - 0.3, [(END_T, "ALONE YOU GO", RED, 100), (END_T + 0.3, "FASTER.", RED, 110),
                                    (END_T + 1.1, "TOGETHER YOU", WHITE, 100), (END_T + 1.4, "GO FURTHER.", WHITE, 110)],
               gap=125)
        cut = 0.0
        for tt in [f[0] for f in FULL] + [f[1] for f in FULL]:
            if tt <= t < tt + 0.1:
                cut = 0.07
        flash = 0.7 * math.exp(-(t - FIN) * 3) if t >= FIN else 0.0
        v.compose(fi, t, flash=flash, white=cut, dim=0.4 * night, fade_in=0.0)
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=LIFT[1]), gain=0.4, fade_in=0.3, fade_out=2.0, stop=DUR)
    last = -1.0
    for t, kind, _, extra in events:
        if kind == "step_a":
            if t - last > 0.1 and t < TWIST:
                m.add(t, sfx.step_light(extra), 0.25, 0, 0.1)
                last = t
        elif kind == "go":
            m.add(0.0, sfx.beep(1320, 0.35), 0.6, 0, 0.3)
            m.add(0.02, sfx.text_hit(5), 0.6, 0, 0.4)
        elif kind == "zoom":
            m.add(t, sfx.whoosh(0.3, 400, 8000, 0.4, seed=int(t)), 0.35, 0, 0.2)
        elif kind == "water":
            m.add(t + 0.3, sfx.chime(700, 0.25), 0.4, 0, 0.3)
        elif kind == "night":
            m.add(t, sfx.whoosh(0.8, 100, 2000, 0.6, seed=5), 0.5, 0, 0.4)
            m.add(t + 0.2, sfx.power_down(1.2), 0.35, 0, 0.4)
        elif kind == "fall":
            m.add(t, sfx.body_fall(), 0.7, 0, 0.3)
        elif kind == "carry":
            m.add(t, sfx.breath(2, 0.7), 0.5, 0, 0.3)
        elif kind == "twist":
            m.add(t, sfx.punch_hit(3, 0.8), 0.8, 0, 0.3)
            m.add(t + 0.15, sfx.body_fall(), 0.8, 0, 0.3)
        elif kind == "alone":
            for q in range(4):
                m.add(t + q * 0.75, sfx.heartbeat(), 0.6, 0, 0.3)
        elif kind == "arrive":
            for q in range(6):
                m.add(t + q * 0.12, sfx.step_heavy(q), 0.4, 0, 0.15)
        elif kind == "lift":
            m.add(t, sfx.chime(880, 0.3), 0.5, 0, 0.5)
            m.add(t + 0.3, sfx.power_up(220), 0.4, 0, 0.4)
        elif kind == "go2":
            m.add(t, sfx.riser(FIN - t), 0.5, 0, 0.3)
        elif kind == "fin":
            m.add(t, sfx.boom(3.0), 0.9, 0, 0.5)
            m.add(t, sfx.applause(2.5, 45, 4), 0.45, 0, 0.3)
            m.add(t + 0.1, sfx.sparkle(1.5), 0.4, 0, 0.5)
        elif kind == "end":
            m.add(t, sfx.text_hit(1), 0.7, 0, 0.4)
        elif kind == "end2":
            m.add(t, sfx.text_hit(3), 0.9, 0, 0.5)
            m.add(t, sfx.boom(2.0), 0.4, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [1.0, 3.5, 5.0, 6.5, 7.2, 9.0, 10.6, 11.8, 13.6, 14.8, 15.6, 17.0, 18.8, 19.6, 20.6, 23.5]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
