"""EP14 - DIG  (motivation, talent, ego, obsession)

Visual hook: we open deep underground on a diamond glittering in the dark,
then the camera rushes up to the surface: four tiny figures with shovels.
Their names pop one by one: MOTIVATION / TALENT / EGO / OBSESSION.
They dig. MOTIVATION starts fastest and quits first (OUT). TALENT finds one red
coin and sits admiring it (OUT). EGO finds a pile of coins and lies on it (OUT).
OBSESSION keeps going alone; red doubts appear on the walls, he drops to his
knees, gets back up with a red aura and digs faster and faster... 60 M: he
strikes the diamond. Pull back on the four shafts.
PUNCH  EVERYONE STOPS SOMEWHERE. / OBSESSION / DOESN'T.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import (FPS, HEAD_R, RED, WHITE, W, Camera, Particles, build_pose, clamp, draw_spaced,
                    ease_out, font, mix, paint, smoothstep)
from kit import (CX, GREY, Log, Video, blend, draw_body, hud, kneel, punch, sad, sit, stand)
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep14_dig"
dt = 1 / FPS
S0 = 92.0
XS = {"MOTIVATION": -2.85, "TALENT": -0.95, "EGO": 0.95, "OBSESSION": 2.85}
ORDER = ["MOTIVATION", "TALENT", "EGO", "OBSESSION"]
DIAMOND = 30.6
M_PER_U = 2.0

HOOK_PAN = (1.1, 2.3)
NAMES_T = [2.6, 2.95, 3.3, 3.65]
GO = 4.1
STOP = {"MOTIVATION": (5.3, 2.4), "TALENT": (6.8, 4.6), "EGO": (8.6, 8.2)}
DOUBT = (10.6, 13.6)
DOUBTS = [(10.8, "I CAN'T."), (11.5, "NOT BUILT FOR THIS."), (12.2, "WHAT'S THE POINT?")]
KNEEL = (12.2, 12.8)
RISE = 13.6
HIT = 17.6
PULL = HIT + 0.9
P1, P2, P3 = HIT + 2.3, HIT + 3.1, HIT + 3.6
DUR = P3 + 3.0


def depth(name, t):
    if t < GO:
        return 0.0
    u = t - GO
    if name in STOP:
        ts, d = STOP[name]
        T = ts - GO
        return d * (1 - (1 - min(1.0, u / T)) ** 1.6)
    # obsession
    d1 = 1.05 * min(u, DOUBT[0] - GO)                         # steady
    if t < DOUBT[0]:
        return d1
    d2 = d1 + 0.18 * (min(t, RISE) - DOUBT[0])                 # doubts: almost stops
    if t < RISE:
        return d2
    v = 1.5 + 4.0 * smoothstep(RISE, RISE + 2.0, t)
    acc = 0.0
    tt = RISE
    while tt < min(t, HIT):
        acc += (1.5 + 4.0 * smoothstep(RISE, RISE + 2.0, tt)) * 0.02
        tt += 0.02
    return min(DIAMOND - 1.0, d2 + acc)


def dig_pose(x, y, t, speed, ph=0.0):
    """Facing right, shovel strokes. Returns joints + shovel tip."""
    c = 0.5 + 0.5 * math.sin(t * (6 + 6 * speed) + ph)
    j = build_pose(np.array([x - 0.05, y + 1.42 - 0.12 * c]), np.array([x + 0.25, y + 0.02]), np.array([x - 0.25, y + 0.02]),
                   0.35 + 0.3 * c, 0.9 - 0.5 * c, 0.75 - 0.5 * c, 0.6, 0.7, 0.3 + 0.2 * c)
    hand = (j["hand1"] + j["hand2"]) / 2
    tip = hand + np.array([0.25 + 0.1 * c, -1.0 + 0.3 * (1 - c)])
    return j, hand, tip, c


def lie_relax(x, y):
    hip = np.array([x, y + 0.45])
    neck = np.array([x + 0.88, y + 0.62])
    sh = hip + (neck - hip) * 0.86
    return {"hip": hip, "neck": neck, "head": np.array([x + 1.2, y + 0.75]), "shoulder": sh,
            "knee1": np.array([x - 0.55, y + 0.85]), "foot1": np.array([x - 1.05, y + 0.45]),
            "knee2": np.array([x - 0.7, y + 0.6]), "foot2": np.array([x - 1.3, y + 0.42]),
            "elbow1": sh + [0.35, 0.45], "hand1": sh + [0.5, 0.2],
            "elbow2": sh + [0.25, 0.5], "hand2": sh + [0.42, 0.25]}


def gem(c, cx, cy, r, alpha, t):
    pts = [(-1, 0), (-0.6, 0.45), (0.6, 0.45), (1, 0), (0, -1.0)]
    p = skia.Path()
    for k, (a, b) in enumerate(pts):
        (p.moveTo if k == 0 else p.lineTo)(cx + a * r, cy - b * r)
    p.close()
    c.drawPath(p, paint(WHITE, 0.25 * alpha))
    c.drawPath(p, paint(WHITE, alpha, 4))
    for a, b in ((-0.6, 0.45), (0.6, 0.45), (0, 0.45)):
        c.drawLine(cx + a * r, cy - b * r, cx, cy + r, paint(WHITE, 0.7 * alpha, 2))
    c.drawLine(cx - r, cy, cx + r, cy, paint(WHITE, 0.7 * alpha, 2))
    for k in range(4):                          # glints
        ang = t * 2 + k * 1.57
        gx, gy = cx + math.cos(ang) * r * 1.4, cy + math.sin(ang * 1.3) * r * 0.9
        L = r * 0.3 * (0.5 + 0.5 * math.sin(t * 7 + k))
        c.drawLine(gx - L, gy, gx + L, gy, paint(WHITE, alpha, 2))
        c.drawLine(gx, gy - L, gx, gy + L, paint(WHITE, alpha, 2))


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    dirt = Particles(3)
    rng = np.random.default_rng(6)
    cam = Camera()
    cam.sx, cam.wx = CX, 0.0
    for fi in range(v.n):
        t = fi * dt
        D = {n: depth(n, t) for n in ORDER}
        dO = D["OBSESSION"]
        if t >= HIT:
            dO = DIAMOND - 1.0
        # ---------------- events
        for k, nt in enumerate(NAMES_T):
            if t >= nt:
                log.once(f"name{k}", t, "name", k)
        if t >= HOOK_PAN[0]:
            log.once("pan", t, "pan")
        for n in ORDER:
            sp_k = int((t - GO) * (2.4 if n != "OBSESSION" or t > RISE else 1.6)) if t >= GO else -1
            active = t >= GO and (n not in STOP or t < STOP[n][0]) and not (n == "OBSESSION" and (DOUBT[0] + 0.6 < t < RISE or t >= HIT))
            if active and sp_k >= 0:
                fast = n == "OBSESSION" and t > RISE
                if fast:
                    sp_k = int((t - RISE) * (2 + 6 * smoothstep(RISE, RISE + 2, t)))
                log.once(f"dig{n}{sp_k}", t, "dig", (ORDER.index(n), fast))
                if rng.random() < 0.5:
                    x = XS[n]
                    dirt.emit(np.array([[x + 0.3, -D[n] + 0.1]]) + rng.normal(0, 0.1, (3, 2)), vel=(0.0, 2.5 if not fast else 4), spread=0.8,
                              life=(0.3, 0.6), size=(0.03, 0.06))
        for n, (ts, d) in STOP.items():
            if t >= ts:
                log.once(f"out{n}", t, "out", ORDER.index(n))
        for k, (tt, s_) in enumerate(DOUBTS):
            if t >= tt:
                log.once(f"doubt{k}", t, "doubt", k)
        if t >= KNEEL[0]:
            log.once("kneel", t, "kneel")
        if t >= RISE - 0.6:
            log.once("rise", t, "rise")
        if t >= HIT:
            log.once("hit", t, "hit")
        if t >= PULL:
            log.once("pull", t, "pull")
        dirt.step(dt)

        # ---------------- camera
        if t < HOOK_PAN[0]:
            wy, s = -DIAMOND + 0.4, S0
        elif t < HOOK_PAN[1]:
            u = smoothstep(*HOOK_PAN, t)
            wy, s = (-DIAMOND + 0.4) * (1 - u) + (-0.6) * u, S0
        elif t < PULL:
            wy, s = min(-0.6, -dO + 1.8), S0
        else:
            u = smoothstep(PULL, PULL + 1.6, t)
            s_full = (1560 - 900) / (DIAMOND + 2.0)
            wy_full = -(DIAMOND + 2.0) / 2 + 0.6
            wy = (-dO + 1.8) * (1 - u) + wy_full * u
            s = math.exp(math.log(S0) * (1 - u) + math.log(s_full) * u)
        cam.wy, cam.s = wy, s
        cam.sy = 1060.0 if t < PULL else 1060 + 170 * smoothstep(PULL, PULL + 1.6, t)
        if not v.wants(fi):
            continue

        # ================================================= draw
        v.clear()
        e, f_, tc, hc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas
        # ground block
        l, top = cam.pt((-4.1, 0))
        r, bot = cam.pt((4.1, -DIAMOND - 3))
        e.drawRect(skia.Rect(max(60, l), top, min(W - 60, r), bot), paint(WHITE, 0.055))
        for k in range(1, 26):
            y = -k * 1.3
            a0 = cam.pt((-4.1, y))
            a1 = cam.pt((4.1, y + 0.08 * math.sin(k)))
            e.drawLine(max(60, a0[0]), a0[1], min(W - 60, a1[0]), a1[1], paint(WHITE, 0.035, 2))
        e.drawLine(max(60, l), top, min(W - 60, r), top, paint(WHITE, 0.7, 3))
        # shafts (black, dug)
        for n in ORDER:
            x = XS[n]
            d = D[n] if n != "OBSESSION" else dO
            sl, st_ = cam.pt((x - 0.55, 0.02))
            sr, sb = cam.pt((x + 0.55, -d - 0.05))
            if sb > st_:
                e.drawRect(skia.Rect(sl, st_, sr, sb), paint((0, 0, 0), 1.0))
                e.drawLine(sl, st_, sl, sb, paint(WHITE, 0.12, 2))
                e.drawLine(sr, st_, sr, sb, paint(WHITE, 0.12, 2))
                if n == "EGO" and d > 7.0:          # a small cave where he found the gold
                    cl, ct = cam.pt((x - 1.45, -d + 1.25))
                    cr, cb = cam.pt((x + 1.45, -d - 0.05))
                    e.drawRoundRect(skia.Rect(cl, ct, cr, cb), 30, 30, paint((0, 0, 0), 1.0))
        # diamond
        gx, gy = cam.pt((XS["OBSESSION"] + 0.1, -DIAMOND + 0.1))
        ga = 1.0
        gem(f_, gx, gy, 0.55 * cam.s * (1 + 0.5 * (t >= HIT) * math.exp(-(t - HIT) * 3)), ga, t)
        f_.drawCircle(gx, gy, 1.2 * cam.s, paint(WHITE, 0.05 + 0.1 * (t >= HIT)))
        dirt.draw(f_, cam, WHITE, GREY)

        # figures
        for i, n in enumerate(ORDER):
            x = XS[n]
            d = D[n] if n != "OBSESSION" else dO
            y = -d
            stopped = n in STOP and t >= STOP[n][0]
            col = WHITE
            alpha = 1.0
            if t < GO:
                j = stand(x - 0.1, 0.0, 0.3, 0.25, 0.4, 0.4, 0.0)
                j = {k: vv + [0, 0.0] for k, vv in j.items()}
                hand = (j["hand1"] + j["hand2"]) / 2
                tip = hand + np.array([0.15, -1.2])
            elif stopped:
                w = smoothstep(STOP[n][0], STOP[n][0] + 0.4, t)
                jd, hand, tip, _ = dig_pose(x, y, t, 0.0)
                if n == "MOTIVATION":
                    js = sit(x - 0.35, 0.05, t, 0.8)
                    js = {k: vv + [0, y] for k, vv in js.items()}
                elif n == "TALENT":
                    js = sit(x - 0.35, 0.05, t, 0.1)
                    js = {k: vv + [0, y] for k, vv in js.items()}
                    js["hand1"] = js["shoulder"] + [0.45, 0.35]
                else:
                    js = lie_relax(x - 0.15, y + 0.15)
                j = blend(jd, js, w)
                col = mix(WHITE, GREY, 0.6 * w)
                alpha = 1 - 0.25 * w
                tip = hand + np.array([0.0, -1.0])
            elif n == "OBSESSION" and t >= DOUBT[0] and t < RISE:
                jd, hand, tip, _ = dig_pose(x, y, t, 0.0)
                w = smoothstep(DOUBT[0], DOUBT[0] + 0.5, t)
                j = blend(jd, {k: vv + [0, y] for k, vv in sad(x, t).items()}, w * (1 - smoothstep(*KNEEL, t)))
                kx = {k: vv + [0, y] for k, vv in kneel(x - 0.35, t, 0.9).items()}
                j = blend(j, kx, smoothstep(*KNEEL, t))
                col = mix(WHITE, RED, 0.6 * w)
            elif n == "OBSESSION" and t >= HIT:
                jd, hand, tip, _ = dig_pose(x, y, t, 1.0)
                j = blend(jd, {k: vv + [0, y] for k, vv in stand(x, -0.05, 2.75, 2.95, 0.15, 0.1, -0.25).items()},
                          smoothstep(HIT + 0.2, HIT + 0.6, t))
                col = mix(WHITE, RED, 0.25)
            else:
                speed = 1.0 if (n == "OBSESSION" and t > RISE) else 0.3
                j, hand, tip, _ = dig_pose(x, y, t, speed, i * 1.7)
                if n == "OBSESSION" and t > RISE:
                    col = mix(WHITE, RED, 0.35)
            draw_body(hc, j, cam, col, alpha)
            # shovel
            if not (n == "EGO" and stopped) and not (n == "OBSESSION" and KNEEL[0] < t < RISE):
                hand = (j["hand1"] + j["hand2"]) / 2
                hc.drawLine(*cam.pt(hand + [0, 0.25]), *cam.pt(tip), paint(col, alpha, max(2, 0.05 * cam.s)))
                bl = tip + np.array([0.0, -0.12])
                hc.drawLine(*cam.pt(tip + [-0.1, 0]), *cam.pt(bl + [0, -0.08]), paint(col, alpha, max(3, 0.12 * cam.s)))
            # loot
            if n == "TALENT" and stopped:
                cx_, cy_ = cam.pt(j["hand1"] + [0.05, 0.1])
                pop = 1 + 0.5 * math.exp(-(t - STOP[n][0]) * 6)
                f_.drawCircle(cx_, cy_, 0.13 * cam.s * pop, paint(RED, 1.0))
                f_.drawCircle(cx_, cy_, 0.07 * cam.s * pop, paint((0, 0, 0), 1.0, 2))
            if n == "EGO" and t >= STOP[n][0] - 0.2:
                pr = np.random.default_rng(9)
                for k in range(26):
                    px = x + pr.uniform(-0.5, 0.5)
                    py = y + 0.08 + abs(pr.normal(0, 0.12)) * (1 - abs(px - x) * 1.6)
                    cx_, cy_ = cam.pt((px, py))
                    f_.drawCircle(cx_, cy_, 0.08 * cam.s, paint(RED, 0.9))
            # labels: name above head; OUT when stopped
            if t >= NAMES_T[i]:
                pop = 1 + 0.5 * math.exp(-(t - NAMES_T[i]) * 8)
                hx, hy = cam.pt(j["head"])
                la = 1 - smoothstep(P1 - 0.5, P1, t)
                if t >= PULL:
                    la *= 0.0
                draw_spaced(tc, n, hx, hy - 0.55 * cam.s, font(22 * pop, "Inter-Bold"), 4,
                            paint(RED if n == "OBSESSION" else WHITE, la))
                if stopped:
                    po = 1 + 0.5 * math.exp(-(t - STOP[n][0]) * 8)
                    draw_spaced(tc, "OUT", hx, hy - 0.55 * cam.s - 30, font(22 * po, "InterDisplay-Black"), 4, paint(RED, la))
        # doubts on the walls
        for k, (tt, s_) in enumerate(DOUBTS):
            age = t - tt
            if 0 <= age and t < RISE + 0.2:
                a = smoothstep(0, 0.1, age) * (1 - smoothstep(RISE - 0.2, RISE + 0.2, t))
                pop = 1 + 0.4 * math.exp(-age * 10)
                wx_, wy_ = cam.pt((XS["OBSESSION"] - 1.2 + 0.4 * (k % 2), -dO + 2.6 - 0.75 * k))
                draw_spaced(tc, s_, max(wx_, 300), wy_, font(30 * pop, "InterDisplay-Black"), 2, paint(RED, a))
        # rise ring
        if RISE - 0.05 <= t < RISE + 0.75:
            age = t - RISE + 0.05
            cx_, cy_ = cam.pt((XS["OBSESSION"], -dO + 1.2))
            f_.drawCircle(cx_, cy_, (0.5 + 3.5 * ease_out(age / 0.8)) * cam.s, paint(RED, 0.6 * (1 - age / 0.8), 6))

        dm = int(round((dO if t < HIT else DIAMOND) * M_PER_U))
        hud(tc, "DEPTH", f"{dm}M", smoothstep(GO - 0.2, GO + 0.2, t) * (1 - 0.6 * smoothstep(P1 - 0.3, P1 + 0.3, t)), t >= HIT)
        punch(tc, t, [(P1, [("EVERYONE STOPS SOMEWHERE.", WHITE)], 620, 52),
                      (P2, [("OBSESSION", RED)], 750, 120),
                      (P3, [("DOESN'T.", WHITE)], 890, 150)])
        flash = math.exp(-(t - HIT) * 2.5) * 1.2 if t >= HIT else 0.0
        pdim = 0.6 * smoothstep(P1 - 0.3, P1, t)
        dark = 0.35 * smoothstep(DOUBT[0], DOUBT[0] + 0.8, t) * (1 - smoothstep(RISE - 0.2, RISE + 0.3, t))
        v.compose(fi, t, flash=flash, glow=0.4 * (t > RISE), dim=max(pdim, dark), white=0.08 * flash)
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=HIT), gain=0.45, fade_in=0.5, fade_out=2.5, stop=DUR)
    m.add(0.1, sfx.sparkle(1.2, 50, 1), 0.6, 0.3, 0.6)
    m.add(0.2, sfx.chime(1320, 0.3), 0.5, 0.3, 0.6)
    for t, kind, _, extra in events:
        if kind == "pan":
            m.add(t, sfx.whoosh(HOOK_PAN[1] - HOOK_PAN[0] + 0.2, 150, 5000, 0.75, seed=2), 0.9, 0, 0.3)
        elif kind == "name":
            m.add(t, sfx.text_hit(extra), 0.55 + 0.1 * (extra == 3), (-0.6 + 0.4 * extra), 0.4)
        elif kind == "dig":
            idx, fast = extra
            if idx == 3:
                m.add(t, sfx.dig(int(t * 100), 1.2 if fast else 0.9), 0.7, 0.45, 0.25)
            else:
                m.add(t, sfx.dig(int(t * 100) + idx, 0.5), 0.35, -0.6 + 0.4 * idx, 0.2)
        elif kind == "out":
            m.add(t, sfx.power_down(1.0), 0.3, -0.6 + 0.4 * extra, 0.3)
            if extra == 1:
                m.add(t, sfx.chime(990, 0.3), 0.6, -0.2, 0.5)
            if extra == 2:
                for k in range(8):
                    m.add(t + k * 0.05, sfx.chime(900 + 70 * k, 0.15), 0.4, 0.2, 0.4)
        elif kind == "doubt":
            m.add(t, sfx.glitch(extra), 0.6, 0.3, 0.2)
            m.add(t, sfx.lock_on(extra), 0.45, 0.3, 0.3)
        elif kind == "kneel":
            m.add(t, sfx.body_fall() * 0.5, 0.6, 0.4, 0.3)
            m.add(t + 0.3, sfx.heartbeat(), 0.8, 0, 0.3)
            m.add(t + 1.0, sfx.heartbeat(), 0.9, 0, 0.3)
        elif kind == "rise":
            m.add(t, sfx.power_up(70), 1.0, 0.3, 0.4)
            m.add(t + 0.55, sfx.boom(2.0), 0.6, 0, 0.4)
        elif kind == "hit":
            m.add(t, sfx.boom(4.5), 1.0, 0, 0.5)
            m.add(t, sfx.shatter(3, 1.2), 0.6, 0.3, 0.5)
            m.add(t, sfx.sparkle(2.4, 120, 4), 0.8, 0.3, 0.6)
            for k, f in enumerate((660, 880, 1320)):
                m.add(t + 0.05 * k, sfx.chime(f, 0.3), 0.6, 0, 0.6)
        elif kind == "pull":
            m.add(t, sfx.whoosh(1.4, 100, 2500, 0.7, seed=13), 0.45, 0, 0.4)
    m.add(HIT - 2.5, sfx.riser(2.5), 0.55, 0, 0.3)
    m.add(P1, sfx.text_hit(1), 0.5, 0, 0.4)
    m.add(P2, sfx.text_hit(2), 0.75, 0, 0.4)
    m.add(P3, sfx.text_hit(3), 0.95, 0, 0.5)
    m.add(P3, sfx.boom(2.0), 0.45, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [0.6, 1.8, 3.8, 5.0, 6.5, 8.0, 9.5, 11.6, 12.8, 14.2, 16.5, HIT + 0.3, PULL + 1.8, P3 + 1.0]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
