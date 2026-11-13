"""EP08 - LOVE VS TALENT  (heartbreak -> EGO glow-up)

Title only at start: LOVE VS TALENT.
ACT 1  LOVE walks in with a bouquet of red flowers for HER. She takes it, a big
       red heart pops above them.
ACT 2  TALENT walks in, surrounded by sparkles. She turns, drops the bouquet
       (red petals scatter), takes his arm and leaves. The heart cracks in two.
ACT 3  Rain. LOVE falls to his knees. Thunder. His label glitches: LOVE -> EGO
       (red). Red aura, he stands up.
ACT 4  Training montage, DAY 1 -> 365: real muscle growth (EP05 body).
ACT 5  He comes back in slow motion, huge. Girls surround him with hearts,
       his EX on her knees reaching out, TALENT alone and dimmed in the back.
       He crosses his arms and doesn't look.
PUNCH  SHE LEFT FOR TALENT. / HE CAME BACK AS / EGO.
Safe zone: HUD y 360/470, scene in x 80..880, nothing below y 1560.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import (FPS, H, HEAD_R, RED, WHITE, W, Camera, Layer, Particles, Post,
                    VideoWriter, blend_pose, bloom, build_pose, clamp, dirv, draw_figure,
                    draw_runs, draw_spaced, ease_out, fit_font, font, mix, mux, paint,
                    run_pose, smoothstep)
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep08_love_vs_talent"
GREY = (0.5, 0.5, 0.53)
dt = 1 / FPS
CX = 470.0
GROUND = 1330.0
S = 118.0

# ------------------------------------------------------------ timeline (seconds)
WALK_IN = (0.0, 2.6)
OFFER = 2.7
HEART_POP = 3.2
TAL_IN = (4.2, 5.2)
TURN = 5.0
DROP = 5.35
CRACK = 5.7
LEAVE = (6.2, 7.8)
RAIN = (6.4, 10.4)
KNEEL = (7.0, 7.8)
THUNDER = [8.3, 9.0]
GLITCH = (8.3, 9.2)
RISE = (9.2, 9.8)
CUT1 = 10.0
MONT_A, MONT_REP, MONT_N = 10.2, 0.55, 12
MONT_END = MONT_A + MONT_REP * MONT_N
CUT2 = 999.0                      # no second cut any more: everything happens in the gym
EX_RUN = (MONT_END + 0.8, MONT_END + 2.0)
WALK2 = EX_RUN
CROSS = EX_RUN[1] + 0.5
GIRL_AT = [0.22, 0.38, 0.52, 0.66, 0.8]   # growth thresholds where each girl appears
P1, P2, P3 = CROSS + 0.9, CROSS + 1.8, CROSS + 2.3
DUR = P3 + 3.0
N = int(DUR * FPS)

HIM_STOP = -0.55
HER_X = 1.05
TAL_X = 2.5


def keys(t, kf):
    if t <= kf[0][0]:
        return kf[0][1]
    for (t0, v0), (t1, v1) in zip(kf, kf[1:]):
        if t <= t1:
            u = (t - t0) / (t1 - t0)
            return v0 + (v1 - v0) * u
    return kf[-1][1]


# ------------------------------------------------------------ poses / drawing helpers
def stand(x, lean, a1, a2, b1, b2, head, bob=0.0, hip_h=1.52):
    return build_pose(np.array([x, hip_h + bob]), np.array([x + 0.13, 0.02]), np.array([x - 0.13, 0.02]),
                      lean, a1, a2, b1, b2, head)


def mirror(j, cx):
    return {k: np.array([2 * cx - v[0], v[1]]) for k, v in j.items()}


def scale_pose(j, x, sc):
    return {k: np.array([x + (v[0] - x) * sc, v[1] * sc]) for k, v in j.items()}


def kneel(x, t, head_down=0.6, reach=0.0):
    hip = np.array([x, 0.95 + 0.015 * math.sin(t * 5)])
    lean = 0.38 - 0.25 * reach
    neck = hip + dirv(lean) * 0.92
    sh = hip + dirv(lean) * 0.79
    k1 = np.array([x + 0.78, 0.83])
    j = {"hip": hip, "neck": neck, "head": neck + dirv(lean + head_down * (1 - reach) - 0.3 * reach) * 0.36,
         "shoulder": sh, "knee1": k1, "foot1": np.array([x + 0.82, 0.03]),
         "knee2": np.array([x - 0.12, 0.1]), "foot2": np.array([x - 0.88, 0.1]),
         "elbow1": sh + [0.32, -0.38], "hand1": k1 + [-0.02, 0.08],
         "elbow2": sh + [0.05, -0.52], "hand2": sh + [0.0, -1.02]}
    if reach > 0:
        j["elbow1"] = j["elbow1"] * (1 - reach) + (sh + [0.5, 0.25]) * reach
        j["hand1"] = j["hand1"] * (1 - reach) + (sh + [1.0, 0.55]) * reach
        j["elbow2"] = j["elbow2"] * (1 - reach) + (sh + [0.45, 0.1]) * reach
        j["hand2"] = j["hand2"] * (1 - reach) + (sh + [0.95, 0.35]) * reach
    return j


SEGS_M = [("hip", "knee2", 0.38, True), ("knee2", "foot2", 0.26, True),
          ("shoulder", "elbow2", 0.34, True), ("elbow2", "hand2", 0.22, True),
          ("hip", "neck", 0.52, False),
          ("hip", "knee1", 0.38, False), ("knee1", "foot1", 0.26, False),
          ("shoulder", "elbow1", 0.36, False), ("elbow1", "hand1", 0.24, False)]


def draw_body(c, j, cam, col, alpha, g):
    s = cam.s
    for a, b, wx, back in SEGS_M:
        pa, pb = np.array(cam.pt(j[a])), np.array(cam.pt(j[b]))
        al = alpha * (0.55 if back else 1.0)
        base = (0.15 if (a, b) == ("hip", "neck") else 0.12) * s
        c.drawLine(*pa, *pb, paint(col, al, base))
        w = (0.04 + wx * g ** 0.9) * s
        if w > base * 1.05:
            d = pb - pa
            L = float(np.hypot(*d))
            mid = pa + d * (0.45 if b not in ("foot1", "foot2") else 0.35)
            c.save()
            c.translate(*mid)
            c.rotate(math.degrees(math.atan2(d[1], d[0])))
            r = skia.Rect(-L * 0.42, -w / 2, L * 0.42, w / 2)
            c.drawOval(r, paint(col, al))
            c.drawOval(r, paint((0, 0, 0), 1.0, max(2.0, 0.05 * s)))
            c.restore()
    sx, sy = cam.pt(j["shoulder"])
    c.drawCircle(sx, sy, (0.07 + 0.17 * g) * s, paint(col, alpha))
    if g > 0.1:
        c.drawCircle(sx, sy, (0.07 + 0.17 * g) * s, paint((0, 0, 0), 1.0, max(2.0, 0.05 * s)))
    nx, ny = cam.pt(j["neck"])
    c.drawLine(sx, sy, nx, ny, paint(col, alpha, (0.12 + 0.16 * g) * s))
    hx, hy = cam.pt(j["head"])
    c.drawCircle(hx, hy, HEAD_R * s * (1 - 0.08 * g), paint(col, alpha))


def draw_girl(c, cam, j, col, alpha, facing):
    """Pictogram girl: stick figure + dress + ponytail."""
    draw_figure(c, j, cam, col, alpha, 0.6)
    hip, neck = j["hip"], j["neck"]
    waist = hip + (neck - hip) * 0.45
    knee_y = (j["knee1"][1] + j["knee2"][1]) / 2
    path = skia.Path()
    path.moveTo(*cam.pt(waist + [-0.08, 0]))
    path.lineTo(*cam.pt(waist + [0.08, 0]))
    path.lineTo(*cam.pt((hip[0] + 0.42, knee_y + 0.05)))
    path.lineTo(*cam.pt((hip[0] - 0.42, knee_y + 0.05)))
    path.close()
    c.drawPath(path, paint(col, alpha))
    hx, hy = cam.pt(j["head"])
    r = HEAD_R * cam.s
    back = -facing
    c.drawCircle(hx + back * r * 0.35, hy - r * 0.15, r * 1.05, paint(col, alpha * 0.9))
    c.drawLine(hx + back * r * 1.1, hy - r * 0.3, hx + back * r * 1.7, hy + r * 1.3, paint(col, alpha, r * 0.5))


def heart_path(cx, cy, r):
    p = skia.Path()
    p.moveTo(cx, cy + r)
    p.cubicTo(cx - r * 1.6, cy - r * 0.2, cx - r * 0.8, cy - r * 1.4, cx, cy - r * 0.55)
    p.cubicTo(cx + r * 0.8, cy - r * 1.4, cx + r * 1.6, cy - r * 0.2, cx, cy + r)
    p.close()
    return p


def draw_heart(c, cx, cy, r, alpha, split=0.0, t=0.0):
    if alpha < 0.01:
        return
    if split <= 0:
        c.drawPath(heart_path(cx, cy, r), paint(RED, alpha))
        return
    for side in (-1, 1):
        c.save()
        dx = side * 40 * split
        dy = 220 * split * split
        c.translate(cx + dx, cy + dy)
        c.rotate(side * 25 * split)
        c.clipRect(skia.Rect(-r * 2 if side < 0 else 0, -r * 2, 0 if side < 0 else r * 2, r * 2))
        c.drawPath(heart_path(0, 0, r), paint(RED, alpha * (1 - split * 0.6)))
        c.restore()
    # crack zig-zag
    if split < 0.3:
        z = skia.Path()
        z.moveTo(cx, cy - r * 0.55)
        for k, (ox, oy) in enumerate(((-0.15, -0.2), (0.15, 0.15), (-0.12, 0.5), (0.0, 1.0))):
            z.lineTo(cx + ox * r, cy + oy * r)
        c.drawPath(z, paint((0, 0, 0), 1.0, 5))


def draw_bouquet(c, cam, hand, alpha, fall=0.0, ground_pos=None):
    if alpha < 0.01:
        return
    base = np.array(hand) if ground_pos is None else hand * (1 - fall) + ground_pos * fall
    ang = 0.35 + 1.2 * fall
    for k, (dx, h) in enumerate(((-0.12, 0.55), (0.0, 0.65), (0.12, 0.52))):
        tip = base + np.array([math.sin(ang) * h + dx * math.cos(ang), math.cos(ang) * h - dx * math.sin(ang)])
        c.drawLine(*cam.pt(base), *cam.pt(tip), paint(WHITE, 0.8 * alpha, max(1.5, 0.03 * cam.s)))
        c.drawCircle(*cam.pt(tip), 0.1 * cam.s, paint(RED, alpha))


class Rain:
    def __init__(self, n=90, seed=3):
        r = np.random.default_rng(seed)
        self.x, self.y, self.l = r.uniform(0, W + 200, n), r.uniform(0, H, n), r.uniform(40, 110, n)

    def draw(self, c, t, a):
        if a < 0.01:
            return
        for x, y, l in zip(self.x, self.y, self.l):
            yy = (y + t * 1700) % (H + 200) - 100
            xx = (x - t * 300) % (W + 200) - 100
            c.drawLine(xx, yy, xx - l * 0.18, yy + l, paint(WHITE, 0.16 * a, 2))


GIRLS = [(-3.0, 1), (-2.1, 1), (1.4, -1), (2.4, -1), (3.2, -1)]     # x, facing (back row)
EX_X = 1.65


def render(stills=None):
    os.makedirs(OUT, exist_ok=True)
    env, fig, txt, hero = Layer(), Layer(), Layer(), Layer()
    post = Post()
    sparkles = Particles(3)
    petals = Particles(4)
    aura = Particles(5)
    rain = Rain()
    events = []
    rng = np.random.default_rng(8)
    writer = None if stills else VideoWriter(os.path.join(OUT, NAME + "_video.mp4"))
    f_lab = font(28, "Inter-Bold")
    f_cap = font(24, "Inter-SemiBold")
    f_t = fit_font("TALENT", 150, "InterDisplay-Black", 8, 760)
    f_p1 = fit_font("SHE LEFT FOR TALENT.", 60, "InterDisplay-Bold", 4, 780)
    f_p2 = fit_font("HE CAME BACK AS", 76, "InterDisplay-Black", 4, 780)

    cam = Camera()
    cam.s, cam.sx, cam.sy, cam.wx, cam.wy = S, CX, GROUND, 0.0, 0.0
    logged = set()
    ph_him, ph_her, ph_tal = 0.0, 0.0, 0.0
    prev_t = 0.0
    last_day = 1
    walk_ph = 0.0
    hearts_pop = {}
    for fi in range(N):
        t = fi * dt
        dtt = t - prev_t
        prev_t = t
        draw_now = stills is None or fi in stills

        def log(name, kind, extra=0, at=None):
            if name not in logged:
                logged.add(name)
                events.append((t if at is None else at, kind, 0, extra))

        act = 1 if t < CUT1 else 2 if t < CUT2 else 3

        # ================= HIM
        g = 0.0
        day = 1
        bar = None
        if act == 1:
            hx = keys(t, [(WALK_IN[0], -4.2), (WALK_IN[1], HIM_STOP)])
            walking = t < WALK_IN[1]
            if walking:
                ph_him += 2 * math.pi * (3.6 / 2.6) / 2.6 * dtt * 1.4
            jw = run_pose(hx, ph_him, 0.38 if walking else 0.0, 0, 0.0, 0.0)
            # holding the bouquet forward, offer
            off = smoothstep(OFFER - 0.3, OFFER + 0.2, t) * (1 - smoothstep(DROP - 0.2, DROP + 0.1, t))
            hold = stand(hx, 0.05, 0.9 + 0.5 * off, 0.15, 1.2 - 1.0 * off, 0.2, 0.05 + 0.1 * off)
            j = blend_pose(jw, hold, 0.45 if walking else 1.0)
            if walking:
                j = {k: (jw[k] if k not in ("elbow1", "hand1", "shoulder") else hold[k] * 0.6 + jw[k] * 0.4) for k in jw}
            sad = smoothstep(LEAVE[0], LEAVE[0] + 0.6, t)
            j = blend_pose(j, stand(hx, 0.3, 0.05, 0.0, 0.12, 0.08, 0.85, -0.04), sad * (1 - smoothstep(KNEEL[0], KNEEL[1], t)))
            if t >= KNEEL[0]:
                kn = kneel(hx, t, 0.9)
                j = blend_pose(j, kn, smoothstep(KNEEL[0], KNEEL[1], t))
            if t >= RISE[0]:
                up = stand(hx, -0.02, 0.15, 0.1, 0.2, 0.15, -0.15)
                j = blend_pose(j, up, smoothstep(RISE[0], RISE[1], t))
        elif act == 2:
            hx = 0.0
            if t < MONT_END:
                k = int((t - MONT_A) // MONT_REP) if t >= MONT_A else -1
                u = ((t - MONT_A) % MONT_REP) / MONT_REP if t >= MONT_A else 0.0
                c_ = math.sin(math.pi * u) if k >= 0 else 0.0
                day = int(round(365 ** ((k + 1) / MONT_N))) if k >= 0 else 1
                g = clamp((k + u) / MONT_N) if k >= 0 else 0.0
            else:
                k, u, c_, day, g = MONT_N - 1, 1.0, 0.0, 365, 1.0
            a = 0.12 + 0.18 * c_
            b = 0.15 + 2.3 * c_
            j = stand(hx, 0.03 - 0.05 * c_, a, a - 0.04, b, b - 0.05, 0.05)
            if t >= MONT_END:
                cross = stand(hx, -0.04, 0.5, 0.45, 1.9, 1.95, -0.18)
                j = blend_pose(j, cross, smoothstep(MONT_END + 0.15, MONT_END + 0.55, t))
                log("bardrop", "bardrop")
            if k >= 0 and t < MONT_END:
                log(f"rep{k}", "rep", k)
            for i, thr in enumerate(GIRL_AT):
                if g >= thr:
                    log(f"girl{i}", "girl", i)
        else:
            day = 365
            g = 1.0
            hx = keys(t, [(WALK2[0], -4.4), (WALK2[1], -0.9)])
            walking = WALK2[0] <= t < WALK2[1]
            if walking:
                walk_ph += 2 * math.pi * 0.62 * dtt
            jw = run_pose(hx, walk_ph, 0.32 if walking or t < WALK2[0] else 0.0)
            cross = stand(hx, -0.04, 0.5, 0.45, 1.9, 1.95, -0.18)
            j = blend_pose(jw, cross, smoothstep(WALK2[1] - 0.1, CROSS, t))
        sc = 0.9 + 0.38 * g
        j = scale_pose(j, hx, sc)
        ego = smoothstep(GLITCH[0], GLITCH[1], t)
        hcol = mix(WHITE, RED, 0.3 * ego)
        if act == 2:
            bar = (j["hand1"] + j["hand2"]) / 2
            if t >= MONT_END:
                u = smoothstep(MONT_END, MONT_END + 0.25, t)
                b0 = (j["hand1"] + j["hand2"]) / 2
                bar = np.array([-0.75, 0.26]) * u + b0 * (1 - u)

        # ================= HER
        her_vis = act == 1 and t < LEAVE[1] + 0.2
        if act == 1:
            ex_ = keys(t, [(0, HER_X), (DROP + 0.1, HER_X), (LEAVE[0], TAL_X - 0.75), (LEAVE[1], 6.5)])
            moving = DROP + 0.1 < t < LEAVE[1]
            if moving:
                ph_her += 2 * math.pi * 1.2 * dtt
            jh = run_pose(0.0, ph_her, 0.33 if moving else 0.0, 0, 0.0, 0.0)
            hold = smoothstep(OFFER + 0.1, OFFER + 0.5, t) * (1 - smoothstep(DROP - 0.1, DROP + 0.05, t))
            if hold > 0:
                hb = stand(0.0, 0.05, 0.9, 0.15, 1.2, 0.2, 0.1)
                jh = blend_pose(jh, hb, hold)
            if t >= LEAVE[0]:   # takes Talent's arm
                arm = stand(0.0, 0.0, 0.9, 0.2, 0.3, 0.2, -0.05)
                jh = {kk: (arm[kk] if kk in ("elbow1", "hand1") else v) for kk, v in jh.items()}
            jh = {kk: v + [ex_, 0] for kk, v in jh.items()}
            facing_her = -1 if t < TURN else 1
            if facing_her < 0:
                jh = mirror(jh, ex_)
        # ================= TALENT
        tal_vis = act == 1 and TAL_IN[0] <= t < LEAVE[1] + 0.2
        if tal_vis:
            tx = keys(t, [(TAL_IN[0], 5.4), (TAL_IN[1], TAL_X), (LEAVE[0], TAL_X), (LEAVE[1], 7.4)])
            moving = t < TAL_IN[1] or t >= LEAVE[0]
            if moving:
                ph_tal += 2 * math.pi * 1.2 * dtt
            jt = run_pose(0.0, ph_tal, 0.35 if moving else 0.0, 0, -0.05, -0.12)
            jt = {kk: v + [tx, 0] for kk, v in jt.items()}
            if t < LEAVE[0]:
                jt = mirror(jt, tx)
            if rng.random() < 0.6:
                sparkles.emit(np.array([jt["head"] + rng.normal(0, 0.6, 2)]), vel=(0, 0.3), spread=0.2, life=(0.3, 0.7), size=(0.02, 0.05))

        # ================= events & particles
        if t >= HEART_POP:
            log("heart", "heart")
        if t >= TAL_IN[0]:
            log("talent", "talent")
        if t >= DROP + 0.25:
            log("drop", "drop")
            if "petals" not in logged:
                logged.add("petals")
                petals.emit(np.tile(np.array([HER_X - 0.6, 0.2]), (40, 1)), vel=(0, 1.0), spread=1.2, life=(0.8, 1.6), size=(0.03, 0.06))
        if t >= CRACK:
            log("crack", "crack")
        if t >= RAIN[0]:
            log("rain", "rain")
        for i, tt in enumerate(THUNDER):
            if t >= tt:
                log(f"th{i}", "thunder", i)
        if t >= GLITCH[0]:
            log("glitch", "glitch")
        if t >= RISE[0]:
            log("rise", "rise")
        if GLITCH[0] < t < RISE[1] + 0.4:
            n = 4
            aura.emit(np.array([j["hip"] + rng.normal(0, 0.35, 2) + [0, 0.8] for _ in range(n)]),
                      vel=(0, 1.3), spread=0.4, life=(0.5, 1.0), size=(0.02, 0.05))
        if t >= CUT1:
            log("cut1", "cut")
        if t >= CUT2:
            log("cut2", "cut")
        if t >= WALK2[0]:
            log("walk2", "walk2")
        if act == 3 and t >= WALK2[1] - 0.6:
            log("girls", "girls")
        if t >= CROSS:
            log("cross", "cross")
        if day != last_day:
            events.append((t, "day", 0, day))
            last_day = day
        sparkles.step(dtt)
        petals.step(dtt)
        aura.step(dtt)

        if not draw_now:
            continue

        # ================================================= draw
        for L in (env, fig, txt, hero):
            L.clear()
        master = smoothstep(0, 0.3, t) * (1 - smoothstep(DUR - 0.35, DUR, t))
        e, f_, tc, hc = env.canvas, fig.canvas, txt.canvas, hero.canvas
        e.drawLine(80, GROUND, W - 80, GROUND, paint(WHITE, 0.5, 2.5))
        rain_a = smoothstep(RAIN[0], RAIN[0] + 0.6, t) * (1 - smoothstep(RAIN[1] - 0.6, RAIN[1], t))
        rain.draw(e, t, rain_a)

        if act == 1:
            # flowers
            if t < DROP:
                hand = j["hand1"] if t < OFFER + 0.35 else jh["hand1"]
                draw_bouquet(f_, cam, hand, 1.0)
            else:
                u = smoothstep(DROP, DROP + 0.3, t)
                draw_bouquet(f_, cam, np.array([HER_X - 0.6, 1.2]), 1 - 0.3 * smoothstep(DROP + 1, DROP + 3, t),
                             u, np.array([HER_X - 0.6, 0.08]))
            petals.draw(f_, cam, RED, RED)
            if her_vis:
                facing = -1 if t < TURN else 1
                draw_girl(f_, cam, jh, WHITE, 1.0, facing)
            if tal_vis:
                draw_figure(f_, jt, cam, WHITE, 1.0, 0.6)
                sparkles.draw(f_, cam, WHITE, WHITE)
            # big heart
            if t >= HEART_POP:
                hx_, hy_ = cam.pt(((HIM_STOP + HER_X) / 2, 3.6))
                pop = 1 + 0.4 * math.exp(-(t - HEART_POP) * 10)
                split = smoothstep(CRACK, CRACK + 1.4, t) * 0.8
                fade = 1 - smoothstep(CRACK + 1.1, CRACK + 1.6, t)
                draw_heart(f_, hx_, hy_ + 6 * math.sin(t * 3), 58 * pop, fade, split, t)
            # hearts floating
            if HEART_POP < t < TAL_IN[0] + 0.3:
                for k in range(5):
                    age = (t - HEART_POP - k * 0.35)
                    if 0 < age < 1.4:
                        sx, sy = cam.pt((HIM_STOP + 0.4 + 0.5 * math.sin(k * 2.1), 2.6 + age * 0.9))
                        draw_heart(f_, sx, sy, 14, 0.8 * (1 - age / 1.4))
        if act == 2:
            gc = Camera()
            gc.s, gc.sx, gc.sy, gc.wx, gc.wy = S * 0.8, CX, GROUND - 70, 0.0, 0.0
            e.drawLine(80, gc.sy, W - 80, gc.sy, paint(WHITE, 0.14 * smoothstep(MONT_A, MONT_A + 1, t), 1.5))
            g_now = g
            # Talent alone in the very back, appears with the ex
            ta_ = smoothstep(EX_RUN[0], EX_RUN[0] + 0.6, t)
            if ta_ > 0.01:
                tb = Camera()
                tb.s, tb.sx, tb.sy, tb.wx, tb.wy = S * 0.62, CX, GROUND - 130, 0.0, 0.0
                jt2 = mirror(stand(4.6, 0.15, 0.08, 0.05, 0.2, 0.15, 0.4), 4.6)
                draw_figure(e, jt2, tb, GREY, 0.35 * ta_, 0.6)
                tsx, _ = tb.pt((4.6, 0))
                draw_spaced(tc, "TALENT", tsx, tb.sy + 34, font(22, "Inter-Bold"), 5, paint(GREY, 0.5 * ta_))
            # girls appear one by one behind him while he grows
            for i, ((gx, face), thr) in enumerate(zip(GIRLS, GIRL_AT)):
                if g_now < thr:
                    continue
                at = thr
                ga = clamp((g_now - thr) * 8)
                reach = clamp((g_now - thr) * 4)
                jg = stand(0.0, 0.12 * reach, 0.2 + 1.2 * reach, 0.15 + 0.8 * reach, 0.2, 0.4, 0.1)
                jg = {kk: v + [gx, 0] for kk, v in jg.items()}
                if face < 0:
                    jg = mirror(jg, gx)
                draw_girl(e, gc, jg, GREY, 0.55 * ga, face)
                sx, sy = gc.pt((gx, 3.3))
                pop = 1 + 0.6 * (1 - ga)
                draw_heart(f_, sx, sy + 5 * math.sin(t * 4 + i), 22 * pop, 0.9 * ga)
            # the ex runs in from the right and drops to her knees
            if t >= EX_RUN[0]:
                u = smoothstep(EX_RUN[0], EX_RUN[1] - 0.15, t)
                exx_w = 5.2 + (EX_X - 5.2) * u
                running = run_pose(0.0, (t - EX_RUN[0]) * 11.0, 0.85)
                kn = kneel(0.0, t, 0.4, smoothstep(EX_RUN[1], EX_RUN[1] + 0.4, t))
                w = smoothstep(EX_RUN[1] - 0.3, EX_RUN[1] + 0.05, t)
                jx = blend_pose(running, kn, w)
                jx = {kk: v + [exx_w, 0] for kk, v in jx.items()}
                jx = mirror(jx, exx_w)
                draw_girl(f_, cam, jx, WHITE, 0.95, -1)
                exl, _ = cam.pt((exx_w - 0.1, 0))
                draw_spaced(tc, "EX", exl, GROUND + 46, f_lab, 6, paint(WHITE, 0.95 * (1 - smoothstep(P1 - 0.5, P1, t))))
                if t >= EX_RUN[1]:
                    sx, sy = cam.pt((EX_X - 0.5, 2.6))
                    pop = 1 + 0.5 * math.exp(-(t - EX_RUN[1]) * 10)
                    draw_heart(f_, sx, sy + 5 * math.sin(t * 4), 26 * pop, 0.95)

        # him
        if act == 2:
            draw_body(hc, j, cam, hcol, 1.0, g)
            radii = [0.13] + [0.24] * int(g * 3) + [0.18] * (1 if g > 0.5 else 0)
            for kk in range(len(radii) - 1, -1, -1):
                cx, cy = cam.pt(bar + np.array([0.07, -0.045]) * kk)
                hc.drawCircle(cx, cy, radii[kk] * cam.s, paint((0, 0, 0), 1.0))
                hc.drawCircle(cx, cy, radii[kk] * cam.s, paint(WHITE, 0.95, max(2, 0.045 * cam.s)))
        else:
            draw_body(hc, j, cam, hcol, 1.0, g)
        aura.draw(f_, cam, RED, RED)
        if RISE[0] <= t < RISE[0] + 0.8:
            age = t - RISE[0]
            cx, cy = cam.pt(j["hip"])
            f_.drawCircle(cx, cy - 0.4 * cam.s, (0.5 + 3.5 * ease_out(age / 0.8)) * cam.s, paint(RED, 0.6 * (1 - age / 0.8), 6))

        # his label: LOVE -> glitch -> EGO
        la = smoothstep(0.3, 0.8, t) * (1 - smoothstep(P1 - 0.5, P1, t))
        lx, _ = cam.pt((hx, 0))
        if t < GLITCH[0]:
            draw_spaced(tc, "LOVE", lx, GROUND + 46, f_lab, 6, paint(WHITE, la))
        elif t < GLITCH[1]:
            chars = "LOVEGOX#%&@"
            s_ = "".join(chars[rng.integers(len(chars))] for _ in range(4 if rng.random() < 0.5 else 3))
            col = RED if rng.random() < 0.6 else WHITE
            draw_spaced(tc, s_, lx + rng.normal(0, 6), GROUND + 46, f_lab, 6, paint(col, la))
        else:
            pop = 1 + 0.5 * math.exp(-(t - GLITCH[1]) * 8)
            draw_spaced(tc, "EGO", lx, GROUND + 46, font(28 * pop, "Inter-Black"), 6, paint(RED, la))
        if act == 1 and her_vis:
            hsx, _ = cam.pt((jh["hip"][0], 0))
            draw_spaced(tc, "HER", hsx, GROUND + 46, f_lab, 6, paint(WHITE, la * (1 - smoothstep(LEAVE[0], LEAVE[0] + 0.5, t))))
        if act == 1 and tal_vis:
            tsx, _ = cam.pt((jt["hip"][0], 0))
            draw_spaced(tc, "TALENT", tsx, GROUND + 46, f_lab, 6, paint(WHITE, 1 - smoothstep(LEAVE[0], LEAVE[0] + 0.5, t)))

        # DAY HUD (from the transformation on)
        if t >= RISE[0]:
            ha = smoothstep(RISE[0], RISE[0] + 0.4, t) * (1 - 0.5 * smoothstep(P1 - 0.3, P1 + 0.3, t))
            draw_spaced(tc, "DAY", CX, 360, f_cap, 12, paint(WHITE, 0.7 * ha))
            draw_spaced(tc, str(day), CX, 470, font(104, "InterDisplay-Bold"), 4, paint(RED if day >= 365 else WHITE, ha))

        # title
        ta = smoothstep(0.1, 0.35, t) * (1 - smoothstep(2.2, 2.6, t))
        if ta > 0.01:
            pop = 1 + 0.08 * (1 - ease_out(t / 0.4))
            draw_spaced(tc, "LOVE", CX, 600, font(f_t.getSize() * 1.1 * pop, "InterDisplay-Black"), 8, paint(RED, ta))
            draw_spaced(tc, "VS", CX, 675, font(48, "InterDisplay-Bold"), 10, paint(WHITE, 0.7 * ta))
            draw_spaced(tc, "TALENT", CX, 820, font(f_t.getSize() * pop, "InterDisplay-Black"), 8, paint(WHITE, ta))

        # punchline
        def reveal(t0, d=0.4):
            uu = ease_out((t - t0) / d)
            return uu, (1 - uu) * 30
        if t >= P1:
            uu, off = reveal(P1)
            draw_spaced(tc, "SHE LEFT FOR TALENT.", CX, 590 + off, f_p1, 4, paint(WHITE, 0.85 * uu))
        if t >= P2:
            uu, off = reveal(P2)
            draw_spaced(tc, "HE CAME BACK AS", CX, 700 + off, f_p2, 4, paint(WHITE, uu))
        if t >= P3:
            uu, off = reveal(P3, 0.3)
            s3 = 1 + 0.3 * (1 - uu)
            draw_spaced(tc, "EGO.", CX, 870 + off * 0.3, font(190 * s3, "InterDisplay-Black"), 10, paint(RED, uu))

        # composite
        flash = 0.0
        for tt in THUNDER:
            if t >= tt:
                flash = max(flash, math.exp(-(t - tt) * 7))
        cutf = 0.0
        for tt in (CUT1, CUT2):
            if tt - 0.1 <= t < tt + 0.25:
                cutf = max(cutf, 1 - abs(t - tt) / 0.25)
        eb = bloom(env.rgb(), (0.9, (4, 0.6), (22, 0.3)))
        gb = bloom(fig.rgb(), (1.0, (5, 0.9), (18, 0.8), (60, 0.5)))
        hb = bloom(hero.rgb(), (1.0, (4, 0.45), (16, 0.35 + 0.3 * ego), (50, 0.25 + 0.25 * ego)))
        xb = bloom(txt.rgb(), (1.0, (6, 0.7), (26, 0.45)))
        img = (eb + gb + hb + xb) * master + flash * 0.35 + cutf * 0.6
        frame = post.apply(img, fi)
        if stills:
            import PIL.Image
            PIL.Image.fromarray(frame).save(os.path.join(OUT, f"still_{fi:04d}.png"))
        else:
            writer.write(frame)
        if fi % 90 == 0:
            print(f"frame {fi}/{N}", flush=True)

    if stills:
        return
    writer.close()
    wav = os.path.join(OUT, NAME + "_sfx.wav")
    build_audio(events, wav)
    mux(os.path.join(OUT, NAME + "_video.mp4"), wav, os.path.join(OUT, NAME + ".mp4"))
    os.remove(os.path.join(OUT, NAME + "_video.mp4"))
    os.remove(wav)
    print("done", os.path.join(OUT, NAME + ".mp4"))


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=CROSS), gain=0.42, fade_in=1.0, fade_out=2.5, stop=DUR)
    m.add(0.1, sfx.text_hit(5), 0.7, 0, 0.4)
    # soft footsteps walking in
    for k in range(6):
        m.add(0.3 + k * 0.42, sfx.step_light(k), 0.25, -0.3, 0.1)
    n_rep = 0
    for t, kind, pan, extra in events:
        if kind == "heart":
            m.add(t, sfx.chime(660, 0.35), 0.6, 0, 0.5)
            m.add(t + 0.12, sfx.chime(880, 0.3), 0.5, 0, 0.5)
        elif kind == "talent":
            m.add(t, sfx.sparkle(1.5, 70, 2), 0.6, 0.5, 0.5)
        elif kind == "drop":
            m.add(t, sfx.step_light(9), 0.5, 0.1, 0.2)
            m.add(t, sfx.sparkle(0.8, 40, 3), 0.3, 0.1, 0.4)
        elif kind == "crack":
            m.add(t, sfx.heart_break(), 0.9, 0, 0.5)
            m.add(t, sfx.boom(2.0), 0.4, 0, 0.4)
        elif kind == "rain":
            m.add(t, sfx.rain(RAIN[1] - RAIN[0]), 0.45, 0, 0.1)
        elif kind == "thunder":
            m.add(t, sfx.thunder(extra), 0.9, 0, 0.3)
        elif kind == "glitch":
            for k in range(5):
                m.add(t + 0.15 * k, sfx.glitch(k), 0.45, 0, 0.2)
        elif kind == "rise":
            m.add(t - 0.55, sfx.power_up(65), 1.0, 0, 0.4)
            m.add(t, sfx.boom(2.5), 0.6, 0, 0.4)
        elif kind == "cut":
            m.add(t - 0.15, sfx.whoosh(0.4, 400, 8000, 0.7, seed=int(t)), 0.6, 0, 0.3)
        elif kind == "rep":
            n_rep += 1
            m.add(t, sfx.plate_clank(40 + extra, 0.5), 0.35, -0.1, 0.25)
            m.add(t + 0.2, sfx.chime(330 * 2 ** (n_rep * 1.5 / 12), 0.25), 0.35, 0, 0.4)
        elif kind == "day":
            m.add(t, sfx.tick(2400, 0.35), 0.4, 0, 0.05)
        elif kind == "walk2":
            for k in range(7):
                m.add(t + 0.05 + k * 0.17, sfx.step_light(k), 0.4, 0.4 - 0.08 * k, 0.15)
            m.add(EX_RUN[1] - 0.05, sfx.body_fall() * 0.5, 0.6, 0.1, 0.3)
            m.add(EX_RUN[1] + 0.1, sfx.chime(880, 0.35), 0.6, 0, 0.5)
        elif kind == "girl":
            m.add(t, sfx.chime(620 + 90 * extra, 0.3), 0.5, (-1) ** extra * 0.4, 0.5)
        elif kind == "bardrop":
            m.add(t + 0.22, sfx.plate_clank(91, 1.2), 0.8, -0.2, 0.4)
        elif kind == "cross":
            m.add(t, sfx.boom(3.0), 0.7, 0, 0.5)
    m.add(CROSS - 2.0, sfx.riser(2.0), 0.4, 0, 0.3)
    m.add(P1, sfx.text_hit(1), 0.5, 0, 0.4)
    m.add(P2, sfx.text_hit(2), 0.6, 0, 0.4)
    m.add(P3, sfx.text_hit(3), 0.95, 0, 0.5)
    m.add(P3, sfx.boom(2.0), 0.45, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}s frames {N}")
    if "--stills" in sys.argv:
        ts = [1.0, 12.5, 14.5, 16.0, MONT_END + 1.2, EX_RUN[1] + 0.3, P3 + 1.2]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
