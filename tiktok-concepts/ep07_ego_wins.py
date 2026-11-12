"""EP07 - EGO VS OBSESSION  (the fight - this time EGO wins)

Visual hook: total darkness, a spotlight slams on a boxing ring, two fighters
face to face. Title only: EGO VS OBSESSION.
ROUND 1  OBSESSION is a machine: endless combos, EGO (red gloves) is pushed
         into the ropes.
ROUND 2  Slow-motion uppercut. EGO is down. Big red count 1..9.
         OBSESSION doesn't rest - he keeps punching the air, he never stops,
         and his light starts to flicker (burning out).
         At 6 the crowd laughs (red HA) and films EGO on the floor.
         Pride ignites: red aura, EGO gets up at 9.
ROUND 3  Exhausted OBSESSION throws a slow jab, EGO slips it in slow motion
         and lands ONE counter. K.O. Red spotlight, glove raised.
PUNCH    OBSESSION NEVER STOPS. / EGO NEVER STAYS DOWN.
Safe zone: HUD y 360/470, scene left of x 880, nothing below y 1560.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import (FPS, H, HEAD_R, RED, WHITE, W, Camera, Layer, Particles, Post,
                    VideoWriter, blend_pose, bloom, build_pose, clamp, dirv, draw_figure,
                    draw_runs, draw_spaced, ease_out, fit_font, font, mix, mux, paint,
                    rotate_pose, smoothstep)
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep07_ego_wins"
GREY = (0.5, 0.5, 0.53)
dt = 1 / FPS
CX = 470.0
FLOOR_SY = 1290.0
RING = 3.5

# ------------------------------------------------------------ script (tau)
T_SPOT = 0.25
DING1, DING2, DING3 = 2.55, 6.85, 14.95
O_JABS = [3.2, 3.5, 3.8, 4.5, 4.75, 5.0, 5.25, 5.9, 6.15, 6.4,
          7.2, 7.45, 7.7, 8.2, 8.45]
E_BLOCKS = {3.2, 3.5, 3.8, 4.5, 7.2, 7.45}
UPPER = 8.95                    # the knock-down
COUNT_A, COUNT_STEP = 9.9, 0.56
COUNT = [COUNT_A + i * COUNT_STEP for i in range(9)]      # 1..9
LAUGH_T = COUNT[5]
RISE_A, RISE_B = COUNT[7], COUNT[8] + 0.15
O_LAST_JAB = 15.45
E_DODGE = 15.45
E_COUNTER = 15.95
KO_FLY = 0.75
T_RAISE = E_COUNTER + 1.3
SHADOW = [9.9 + 0.33 * i for i in range(14)]               # Obsession punching the air


def rate(tau):
    r = 1.0
    for a, b, rr in ((UPPER - 0.12, UPPER + 0.6, 0.35), (E_DODGE - 0.05, E_COUNTER + 0.45, 0.3)):
        w = smoothstep(a - 0.12, a, tau) * (1 - smoothstep(b, b + 0.15, tau))
        r -= (1 - rr) * w
    return r


taus = [0.0]
while taus[-1] < T_RAISE:
    taus.append(taus[-1] + rate(taus[-1]) * dt)
T_RAISE_REAL = len(taus) * dt
T_P1 = T_RAISE_REAL + 0.8
T_P2 = T_P1 + 1.1
DUR = T_P2 + 3.2
N = int(DUR * FPS)
while len(taus) < N:
    taus.append(taus[-1] + dt)
TAUS = np.array(taus)


def tau_to_t(tau):
    return int(np.searchsorted(TAUS, tau)) * dt


def keys(tau, kf):
    if tau <= kf[0][0]:
        return kf[0][1]
    for (t0, v0), (t1, v1) in zip(kf, kf[1:]):
        if tau <= t1:
            u = (tau - t0) / (t1 - t0)
            return v0 + (v1 - v0) * u * u * (3 - 2 * u)
    return kf[-1][1]


EX = [(0, -1.55), (3.1, -1.55), (6.6, -2.3), (9.0, -2.35), (E_DODGE, -2.35), (E_DODGE + 0.3, -2.0), (E_COUNTER, -1.55)]
OX = [(0, 1.55), (2.8, 1.55), (3.15, 0.1), (6.6, -0.65), (8.9, -0.75), (9.6, -0.2), (10.2, 0.9), (14.7, 0.9),
      (O_LAST_JAB - 0.05, 0.0)]


def pulse(tau, t0, rise=0.08, hold=0.05, fall=0.16):
    u = tau - t0
    if u < 0 or u > rise + hold + fall:
        return 0.0
    if u < rise:
        return ease_out(u / rise)
    if u < rise + hold:
        return 1.0
    return 1 - smoothstep(0, fall, u - rise - hold)


# ------------------------------------------------------------ boxer poses (facing +x)
def boxer(x, tau, t, jab=0.0, cross=0.0, upper=0.0, hit=0.0, guard=1.0, tired=0.0, lean_extra=0.0, bob_ph=0.0):
    bob = 0.04 * math.sin(t * 7 + bob_ph) * (1 - tired * 0.5)
    hip = np.array([x + 0.05 * jab + 0.12 * cross - 0.18 * hit, 1.36 - 0.1 * tired + bob])
    f_front = np.array([x + 0.45, 0.02])
    f_back = np.array([x - 0.45, 0.02])
    lean = 0.14 + 0.25 * tired + 0.12 * jab + 0.2 * cross - 0.45 * hit + lean_extra
    head = -0.55 * hit + 0.35 * tired
    # front arm (jab)
    ga, gb = 0.75 * guard + 0.35 * (1 - guard), 2.05 * guard + 1.1 * (1 - guard)
    a1 = ga + (1.55 - ga) * jab
    b1 = gb + (0.05 - gb) * jab
    # back arm (cross / uppercut)
    ga2, gb2 = 0.55 * guard + 0.3 * (1 - guard), 2.25 * guard + 1.2 * (1 - guard)
    a2 = ga2 + (1.5 - ga2) * cross
    b2 = gb2 + (0.08 - gb2) * cross
    if upper > 0:
        a2 = 0.25 + 2.15 * upper
        b2 = 2.4 - 1.9 * upper
    return build_pose(hip, f_front, f_back, lean, a1, a2, b1, b2, head)


def mirror(j, cx):
    return {k: np.array([2 * cx - v[0], v[1]]) for k, v in j.items()}


def supine(x):
    hip = np.array([x, 0.24])
    neck = np.array([x - 0.92, 0.3])
    sh = hip + (neck - hip) * 0.86
    return {"hip": hip, "neck": neck, "head": np.array([x - 1.3, 0.31]), "shoulder": sh,
            "knee1": np.array([x + 0.5, 0.66]), "foot1": np.array([x + 1.0, 0.06]),
            "knee2": np.array([x + 0.72, 0.36]), "foot2": np.array([x + 1.4, 0.07]),
            "elbow1": sh + [0.3, -0.18], "hand1": sh + [0.62, -0.22],
            "elbow2": sh + [-0.35, -0.15], "hand2": sh + [-0.75, -0.2]}


def kneel(x, t, head_up=0.0):
    hip = np.array([x, 0.95 + 0.015 * math.sin(t * 5)])
    lean = 0.38
    neck = hip + dirv(lean) * 0.92
    sh = hip + dirv(lean) * 0.79
    k1 = np.array([x + 0.78, 0.83])
    return {"hip": hip, "neck": neck, "head": neck + dirv(lean + 0.5 - 0.9 * head_up) * 0.36, "shoulder": sh,
            "knee1": k1, "foot1": np.array([x + 0.82, 0.03]),
            "knee2": np.array([x - 0.12, 0.1]), "foot2": np.array([x - 0.88, 0.1]),
            "elbow1": sh + [0.32, -0.38], "hand1": k1 + [-0.02, 0.08],
            "elbow2": sh + [0.05, -0.52], "hand2": sh + [0.0, -1.02]}


def victory(x, t):
    return build_pose(np.array([x, 1.5]), np.array([x + 0.3, 0.02]), np.array([x - 0.3, 0.02]),
                      -0.05, 3.0 + 0.05 * math.sin(t * 3), 0.6, 0.15, 2.1, -0.25)


# ------------------------------------------------------------ scene pieces
def draw_ring(c, cam, alpha, red=0.0):
    col = mix(WHITE, RED, red)
    fl, fr = cam.pt((-RING, 0)), cam.pt((RING, 0))
    c.drawLine(*fl, *fr, paint(WHITE, 0.85 * alpha, max(2, 0.06 * cam.s)))
    # apron
    al, ar = cam.pt((-RING, -0.75)), cam.pt((RING, -0.75))
    c.drawLine(*al, *ar, paint(WHITE, 0.35 * alpha, 2))
    for x in (-RING, RING):
        c.drawLine(*cam.pt((x, 0)), *cam.pt((x, -0.75)), paint(WHITE, 0.35 * alpha, 2))
        c.drawLine(*cam.pt((x, 0)), *cam.pt((x, 2.25)), paint(WHITE, 0.8 * alpha, max(2, 0.09 * cam.s)))
    for y in (0.75, 1.3, 1.85):
        c.drawLine(*cam.pt((-RING, y)), *cam.pt((RING, y)), paint(col, 0.32 * alpha, max(1.5, 0.035 * cam.s)))


def draw_spot(c, cam, alpha, red):
    if alpha < 0.01:
        return
    col = mix(WHITE, RED, red)
    top = (cam.pt((0, 0))[0], 300)
    l, r = cam.pt((-RING - 0.6, 0)), cam.pt((RING + 0.6, 0))
    path = skia.Path()
    path.moveTo(top[0] - 40, top[1])
    path.lineTo(top[0] + 40, top[1])
    path.lineTo(*r)
    path.lineTo(*l)
    path.close()
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear(
        [skia.Point(0, top[1]), skia.Point(0, l[1])],
        [skia.Color4f(*col, 0.0), skia.Color4f(*col, 0.10 * alpha)]))
    c.drawPath(path, p)
    # pool of light on the canvas
    cx, cy = cam.pt((0, 0))
    c.drawOval(skia.Rect(cx - (RING + 0.4) * cam.s, cy - 18, cx + (RING + 0.4) * cam.s, cy + 18), paint(col, 0.10 * alpha))


def draw_crowd(c, cam, t, alpha, laugh, film, flashes, tau):
    """A row of heads/shoulders below the ring."""
    xs = np.linspace(-3.4, 3.2, 8)
    for i, x in enumerate(xs):
        sx, sy = cam.pt((x, -1.25))
        bob = 3 * math.sin(t * 12 + i) * laugh
        r = 0.27 * cam.s
        c.drawCircle(sx, sy - r * 0.2 + bob, r, paint(GREY, 0.45 * alpha))
        c.drawRoundRect(skia.Rect(sx - r * 1.5, sy + r * 1.0 + bob, sx + r * 1.5, sy + r * 3.2), r, r, paint(GREY, 0.35 * alpha))
        if film > 0 and i % 2 == 0:
            pw, ph = 0.3 * cam.s, 0.5 * cam.s
            px, py = sx + r * 0.9, sy - r * 1.4 + bob
            rr = skia.Rect(px - pw / 2, py - ph, px + pw / 2, py)
            c.drawRoundRect(rr, 6, 6, paint((0, 0, 0), 1.0))
            c.drawRoundRect(rr, 6, 6, paint(WHITE, 0.9 * film * alpha, 3))
            if (int(t * 2.5) + i) % 2 == 0:
                c.drawCircle(px - pw * 0.25, py - ph * 0.82, 4, paint(RED, film * alpha))
            for ft, k in flashes:
                if k == i and 0 <= tau - ft < 0.25:
                    fa = 1 - (tau - ft) / 0.25
                    c.drawCircle(px + pw * 0.2, py - ph * 0.8, (0.1 + 0.25 * fa) * cam.s, paint(WHITE, 0.95 * fa))


def draw_gloves(c, cam, j, col, alpha):
    for k, a in (("hand2", 0.6), ("hand1", 1.0)):
        x, y = cam.pt(j[k])
        c.drawCircle(x, y, 0.2 * cam.s, paint(col, alpha * a))


def render(stills=None):
    os.makedirs(OUT, exist_ok=True)
    env, fig, txt = Layer(), Layer(), Layer()
    post = Post()
    sparks = Particles(9)
    embers = Particles(10)
    events = []
    rng = np.random.default_rng(5)
    writer = None if stills else VideoWriter(os.path.join(OUT, NAME + "_video.mp4"))
    f_lab = font(28, "Inter-Bold")
    f_cap = font(24, "Inter-SemiBold")
    f_title = fit_font("OBSESSION", 150, "InterDisplay-Black", 6, 760)
    f_p1 = fit_font("OBSESSION NEVER STOPS.", 58, "InterDisplay-Bold", 4, 780)
    f_p2 = fit_font("EGO NEVER STAYS DOWN.", 80, "InterDisplay-Black", 4, 780)

    cam = Camera()
    cam.s, cam.sx, cam.sy, cam.wx, cam.wy = 120.0, CX, FLOOR_SY, 0.0, 0.0
    frozen = {}
    logged = set()
    has = []
    flashes = []
    next_flash = LAUGH_T + 0.2
    prev_tau = 0.0
    for fi in range(N):
        t = fi * dt
        tau = taus[fi]
        dtau = tau - prev_tau
        prev_tau = tau
        draw_now = stills is None or fi in stills

        def log(name, kind, extra=0):
            if name not in logged:
                logged.add(name)
                events.append((t, kind, 0, extra))

        # ================= OBSESSION (faces left -> mirrored)
        ox = keys(tau, OX)
        jab = max([pulse(tau, tj) for tj in O_JABS] + [0.0])
        tired = smoothstep(10.5, 14.0, tau)
        shadow = 0.0
        if 9.9 <= tau < 14.7:
            shadow = max(pulse(tau, ts_, 0.07, 0.03, 0.12) for ts_ in SHADOW)
        up = 0.0
        if UPPER - 0.25 <= tau < UPPER + 0.5:
            up = smoothstep(UPPER - 0.25, UPPER + 0.02, tau) * (1 - smoothstep(UPPER + 0.2, UPPER + 0.5, tau))
        last = pulse(tau, O_LAST_JAB, 0.3, 0.1, 0.3) * 0.85
        o_hit = 0.0
        if tau < E_COUNTER:
            jo = boxer(0.0, tau, t, jab=max(jab, shadow, last), upper=up, tired=tired, bob_ph=1.3)
            jo = {k: v + [ox, 0] for k, v in jo.items()}
            jo = mirror(jo, ox)
        else:
            if "O" not in frozen:
                jf = boxer(0.0, tau, t, hit=1.0, tired=tired)
                jf = {k: v + [ox, 0] for k, v in jf.items()}
                pv = jf["foot2"].copy()
                frozen["O"] = (jf, pv)
            jf, pv = frozen["O"]
            u = (tau - E_COUNTER) / KO_FLY
            slide = 1.3 * ease_out(min(1, u))
            rot = rotate_pose(jf, pv, 1.5 * ease_out(min(1, u * 1.2)))
            rot = {k: v - [slide, 0] for k, v in rot.items()}
            jl = supine(ox - slide)
            jo = blend_pose(rot, jl, smoothstep(0.45, 1.0, u))
            jo = mirror(jo, ox)
            o_hit = 1.0
        o_flick = 1.0
        if tired > 0.2 and (int(t * 30) * 7919) % 9 < 2 * tired:
            o_flick = 0.45
        o_alpha = (1 - 0.35 * tired) * o_flick * (1 - 0.4 * smoothstep(E_COUNTER, E_COUNTER + 1.5, tau))

        # ================= EGO (faces right)
        ex = keys(tau, EX)
        hits = [tj for tj in O_JABS if tj not in E_BLOCKS]
        e_hit = max([pulse(tau, tj + 0.06, 0.06, 0.05, 0.25) for tj in hits] + [0.0])
        e_guard = 1.0
        rage = smoothstep(RISE_A - 0.6, RISE_B, tau)
        if tau < UPPER + 0.02:
            je = boxer(ex, tau, t, hit=e_hit, guard=e_guard)
        elif tau < RISE_A - 0.4:
            if "E" not in frozen:
                jf = boxer(ex, tau, t, hit=1.0)
                frozen["E"] = (jf, jf["foot2"].copy())
            jf, pv = frozen["E"]
            u = (tau - UPPER) / 0.7
            rot = rotate_pose(jf, pv, 1.5 * ease_out(min(1, u * 1.2)))
            je = blend_pose(rot, supine(ex + 0.3), smoothstep(0.45, 1.0, u))
            if tau > LAUGH_T:      # lifts his head when he hears them
                je = {k: v for k, v in je.items()}
                je["head"] = je["head"] + [0.15, 0.25 * smoothstep(LAUGH_T, LAUGH_T + 0.4, tau)]
        elif tau < RISE_B:
            u = smoothstep(RISE_A - 0.4, RISE_A + 0.1, tau)
            je = blend_pose(supine(ex + 0.3), kneel(ex - 0.2, t, 1.0), u)
            je = blend_pose(je, boxer(ex, tau, t), smoothstep(RISE_A + 0.2, RISE_B, tau))
        else:
            dodge = smoothstep(E_DODGE - 0.02, E_DODGE + 0.12, tau) * (1 - smoothstep(E_DODGE + 0.3, E_DODGE + 0.45, tau))
            counter = pulse(tau, E_COUNTER - 0.1, 0.1, 0.25, 0.35)
            je = boxer(ex, tau, t, cross=counter, lean_extra=-0.55 * dodge)
            if tau > T_RAISE - 0.6:
                je = blend_pose(je, victory(ex, t), smoothstep(T_RAISE - 0.6, T_RAISE - 0.1, tau))
        ecol = mix(WHITE, RED, 0.15 + 0.75 * rage)

        # ================= events
        for i, tj in enumerate(O_JABS):
            if tau >= tj:
                if tj in E_BLOCKS:
                    log(f"jab{i}", "block", i)
                else:
                    log(f"jab{i}", "hit", i)
                    if f"spark{i}" not in logged:
                        logged.add(f"spark{i}")
                        sparks.emit(np.tile(je["head"], (14, 1)), vel=(-1.5, 0.6), spread=1.4, life=(0.2, 0.45), size=(0.02, 0.05))
        if tau >= UPPER:
            log("upper", "ko1")
            if "sparkU" not in logged:
                logged.add("sparkU")
                sparks.emit(np.tile(je["head"], (50, 1)), vel=(-2.0, 1.5), spread=2.0, life=(0.3, 0.8), size=(0.02, 0.06))
        for i, tc_ in enumerate(COUNT):
            if tau >= tc_:
                log(f"count{i}", "count", i + 1)
        if tau >= LAUGH_T:
            log("laugh", "laugh")
            while len(has) < 9 and tau >= LAUGH_T + 0.12 * len(has):
                x = rng.uniform(-3.0, 2.8)
                has.append((tau, x, rng.uniform(-0.6, -0.2), rng.uniform(0.85, 1.2)))
            while tau >= next_flash and tau < E_COUNTER + 3:
                flashes.append((next_flash, int(rng.integers(8))))
                events.append((t, "shutter", 0, len(flashes)))
                next_flash += rng.uniform(0.12, 0.35)
        if tau >= RISE_A - 0.6:
            log("rage", "rage")
        if tau >= RISE_B:
            log("risen", "risen")
        for i, s_ in enumerate(SHADOW):
            if tau >= s_ and s_ < 14.7:
                log(f"sh{i}", "swish", i)
        for name, tt in (("d1", DING1), ("d2", DING2), ("d3", DING3)):
            if tau >= tt:
                log(name, "bell")
        if tau >= O_LAST_JAB:
            log("lastjab", "swish", 99)
        if tau >= E_COUNTER:
            log("ko2", "ko2")
            if "sparkK" not in logged:
                logged.add("sparkK")
                sparks.emit(np.tile(jo["head"], (90, 1)),
                            vel=(2.5, 1.0), spread=2.4, life=(0.4, 1.1), size=(0.02, 0.07))
        if tau >= T_RAISE - 0.4:
            log("raise", "raise")
        if rage > 0.05 and tau < RISE_B + 0.6:
            n = int(6 * dtau / 0.033)
            pts = [je[k] for k in ("hip", "neck", "shoulder", "head")]
            embers.emit(np.array([pts[rng.integers(4)] + rng.normal(0, 0.15, 2) for _ in range(n)]),
                        vel=(0.0, 1.2), spread=0.5, life=(0.5, 1.1), size=(0.02, 0.05))
        sparks.step(dtau)
        embers.step(dtau)

        # ================= camera: small zooms on the big moments
        z = 1.0
        z += 0.3 * smoothstep(UPPER - 0.4, UPPER - 0.05, tau) * (1 - smoothstep(UPPER + 0.5, UPPER + 1.0, tau))
        z += 0.35 * smoothstep(E_DODGE - 0.3, E_DODGE, tau) * (1 - smoothstep(E_COUNTER + 0.4, E_COUNTER + 1.0, tau))
        focus_x = (ex + ox) / 2
        z = 1 + (z - 1) * 0.55
        cam.s = 108.0 * z
        cam.wx = focus_x - focus_x * 108.0 / cam.s      # keep the action point fixed on screen
        cam.wy = 0.0
        cam.sy = FLOOR_SY - 1.2 * 108.0 + 1.2 * cam.s
        shake = 0.0
        for tt, a in ((UPPER, 1.0), (E_COUNTER, 1.4), (COUNT[8], 0.5)):
            if tau >= tt:
                shake = max(shake, a * math.exp(-(tau - tt) * 6))
        cam.sx = CX + shake * 14 * math.sin(t * 90)

        if not draw_now:
            continue

        # ================================================= draw
        for L in (env, fig, txt):
            L.clear()
        master = (1 - smoothstep(DUR - 0.35, DUR, t))
        lights = smoothstep(T_SPOT, T_SPOT + 0.06, tau)
        red = smoothstep(E_COUNTER, E_COUNTER + 0.4, tau)
        e, f_, tcv = env.canvas, fig.canvas, txt.canvas
        draw_spot(e, cam, lights, red)
        draw_ring(e, cam, lights, red)
        draw_crowd(e, cam, t, lights, smoothstep(LAUGH_T, LAUGH_T + 0.2, tau) * (1 - smoothstep(RISE_B, RISE_B + 0.5, tau)),
                   smoothstep(LAUGH_T, LAUGH_T + 0.3, tau), flashes, tau)
        draw_figure(f_, jo, cam, WHITE, o_alpha * lights, 0.6)
        draw_gloves(f_, cam, jo, WHITE, o_alpha * lights)
        draw_figure(f_, je, cam, ecol, lights, 0.6)
        draw_gloves(f_, cam, je, RED, lights)
        embers.draw(f_, cam, RED, RED)
        sparks.draw(f_, cam, WHITE, WHITE)
        # rage rings
        for k, tt in enumerate((RISE_A, COUNT[8])):
            age = tau - tt
            if 0 <= age < 0.8:
                cx, cy = cam.pt(je["hip"])
                f_.drawCircle(cx, cy - 0.4 * cam.s, (0.5 + 3.5 * ease_out(age / 0.8)) * cam.s, paint(RED, 0.6 * (1 - age / 0.8), 5 + 3 * k))
        # KO impact ring
        age = tau - E_COUNTER
        if 0 <= age < 0.7:
            cx, cy = cam.pt(jo["head"])
            f_.drawCircle(cx, cy, (0.3 + 3.0 * ease_out(age / 0.7)) * cam.s, paint(WHITE, 0.8 * (1 - age / 0.7), 6))

        # HA bubbles
        for ts0, x, y, size in has:
            age = tau - ts0
            if 0 <= age < 0.8:
                sx, sy = cam.pt((x, y + age * 0.6))
                pop = 1 + 0.5 * math.exp(-age * 18)
                draw_spaced(tcv, "HA", sx, sy, font(44 * size * pop, "InterDisplay-Black"), 2, paint(RED, (1 - age / 0.8) ** 1.2))

        # labels
        la = lights * smoothstep(2.3, 2.7, tau) * (1 - smoothstep(T_P1 - 0.5, T_P1, t))
        for j, name, col in ((je, "EGO", ecol), (jo, "OBSESSION", WHITE)):
            fx = j["hip"][0]
            sx, _ = cam.pt((fx, 0))
            draw_spaced(tcv, name, sx, cam.pt((0, 0))[1] + 46, f_lab, 6, paint(col, la * (1 if name == "EGO" else o_alpha)))

        # HUD round
        rnd = 1 if tau < DING2 else 2 if tau < DING3 else 3
        ha_ = lights * smoothstep(2.4, 2.8, tau) * (1 - 0.6 * smoothstep(T_P1 - 0.3, T_P1 + 0.3, t))
        draw_spaced(tcv, "ROUND", CX, 360, f_cap, 12, paint(WHITE, 0.7 * ha_))
        pop = 1.0
        for tt in (DING2, DING3):
            if 0 <= tau - tt < 0.3:
                pop = 1 + 0.3 * (1 - (tau - tt) / 0.3)
        draw_spaced(tcv, str(rnd), CX, 470, font(104 * pop, "InterDisplay-Bold"), 4, paint(RED if rnd == 3 else WHITE, ha_))

        # count
        for i, tc_ in enumerate(COUNT):
            age = tau - tc_
            if 0 <= age < COUNT_STEP + (0.5 if i == 8 else 0):
                pop = 1 + 0.5 * math.exp(-age * 14)
                a = 1 - smoothstep(COUNT_STEP * 0.7, COUNT_STEP + (0.5 if i == 8 else 0), age)
                draw_spaced(tcv, str(i + 1), CX, 830, font(230 * pop, "InterDisplay-Black"), 0, paint(RED, a))

        # K.O.
        age = tau - (E_COUNTER + 0.35)
        if age >= 0 and t < T_P1 - 0.2:
            pop = 1 + 0.6 * math.exp(-age * 10)
            a = smoothstep(0, 0.08, age) * (1 - smoothstep(T_P1 - 0.6, T_P1 - 0.2, t))
            draw_spaced(tcv, "K.O.", CX, 820, font(210 * pop, "InterDisplay-Black"), 8, paint(RED, a))

        # title
        ta = smoothstep(0.45, 0.65, tau) * (1 - smoothstep(2.2, 2.5, tau))
        if ta > 0.01:
            pop = 1 + 0.08 * (1 - ease_out((tau - 0.45) / 0.35))
            draw_spaced(tcv, "EGO", CX, 620, font(f_title.getSize() * 1.3 * pop, "InterDisplay-Black"), 8, paint(RED, ta))
            draw_spaced(tcv, "VS", CX, 700, font(48, "InterDisplay-Bold"), 10, paint(WHITE, 0.7 * ta))
            draw_spaced(tcv, "OBSESSION", CX, 840, font(f_title.getSize() * pop, "InterDisplay-Black"), 6, paint(WHITE, ta))

        # punchline
        def reveal(t0):
            uu = ease_out((t - t0) / 0.4)
            return uu, (1 - uu) * 30
        if t >= T_P1:
            uu, off = reveal(T_P1)
            draw_spaced(tcv, "OBSESSION NEVER STOPS.", CX, 640 + off, f_p1, 4, paint(WHITE, 0.85 * uu))
        if t >= T_P2:
            uu, off = reveal(T_P2)
            draw_runs(tcv, [("EGO", paint(RED, uu)), (" NEVER STAYS DOWN.", paint(WHITE, uu))], CX, 760 + off, f_p2, 4)

        # composite
        flash = 0.0
        for tt, a in ((UPPER, 0.6), (E_COUNTER, 1.2)):
            if tau >= tt:
                flash = max(flash, a * math.exp(-(tau - tt) * 4))
        eb = bloom(env.rgb(), (0.9, (4, 0.6), (22, 0.35)))
        gb = bloom(fig.rgb(), (1.0, (5, 0.9), (18, 0.8 + 0.3 * rage), (60, 0.5 + 0.3 * rage + flash)))
        xb = bloom(txt.rgb(), (1.0, (6, 0.7), (26, 0.45)))
        img = (eb + gb + xb) * master
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
    m.add_bed(sfx.drone(DUR, rise_at=tau_to_t(E_COUNTER)), gain=0.45, start=0.3, fade_in=0.8, fade_out=2.5, stop=DUR)
    m.add(T_SPOT, sfx.spot_on(), 1.0, 0, 0.4)
    m.add(T_SPOT + 0.3, sfx.text_hit(5), 0.7, 0, 0.4)
    for t, kind, pan, extra in events:
        if kind == "bell":
            m.add(t, sfx.bell(), 0.8, 0, 0.5)
        elif kind == "hit":
            m.add(t - 0.05, sfx.swish(extra), 0.5, 0.2, 0.1)
            m.add(t + 0.04, sfx.punch_hit(extra, 0.8), 0.8, -0.2, 0.25)
        elif kind == "block":
            m.add(t - 0.05, sfx.swish(extra), 0.45, 0.2, 0.1)
            m.add(t + 0.04, sfx.punch_block(extra), 0.7, -0.2, 0.2)
        elif kind == "ko1":
            m.add(t - 0.2, sfx.whoosh(0.4, 300, 6000, 0.8, seed=2), 0.7, 0, 0.3)
            m.add(t, sfx.punch_hit(77, 1.6), 1.0, -0.2, 0.4)
            m.add(t, sfx.boom(2.5), 0.7, 0, 0.4)
            m.add(t + 0.5, sfx.body_fall(), 0.9, -0.2, 0.4)
            m.add(t + 0.3, sfx.power_down(1.5), 0.4, 0, 0.4)
        elif kind == "count":
            m.add(t, sfx.text_hit(extra), 0.55 + 0.04 * extra, 0, 0.35)
            m.add(t, sfx.heartbeat(), 0.45 + 0.05 * extra, 0, 0.3)
        elif kind == "swish":
            m.add(t, sfx.swish(100 + extra), 0.3 if extra != 99 else 0.6, 0.3, 0.1)
        elif kind == "laugh":
            for k in range(5):
                m.add(t + 0.15 * k, sfx.laugh(20 + k, 4, 150 + 20 * k, 0.5), 0.35, -0.5 + 0.25 * k, 0.4)
        elif kind == "shutter":
            m.add(t, sfx.shutter(extra), 0.35, ((extra * 37) % 11) / 11 - 0.5, 0.2)
        elif kind == "rage":
            m.add(t, sfx.riser(1.6), 0.6, 0, 0.3)
            m.add(t + 0.3, sfx.power_up(70), 0.9, 0, 0.4)
        elif kind == "risen":
            m.add(t, sfx.boom(3.0), 0.9, 0, 0.5)
            m.add(t, sfx.power_up(98), 0.6, 0, 0.4)
        elif kind == "ko2":
            m.add(t - 0.35, sfx.whoosh(0.5, 200, 7000, 0.85, seed=21), 0.9, 0, 0.3)
            m.add(t, sfx.punch_hit(99, 2.2), 1.0, 0.2, 0.5)
            m.add(t, sfx.boom(4.5), 1.0, 0, 0.5)
            m.add(t + 0.05, sfx.glitch(9), 0.6, 0.2, 0.2)
            m.add(t + 0.8, sfx.body_fall(), 0.9, 0.3, 0.4)
            m.add(t + 0.9, sfx.bell(780, 3.0), 0.7, 0, 0.5)
            m.add(t + 1.0, sfx.applause(4.5, 55, 4), 0.55, 0, 0.35)
        elif kind == "raise":
            m.add(t, sfx.sparkle(1.8), 0.5, 0, 0.6)
    m.add(T_P1, sfx.text_hit(1), 0.55, 0, 0.4)
    m.add(T_P2, sfx.text_hit(2), 0.95, 0, 0.5)
    m.add(T_P2, sfx.boom(2.0), 0.45, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}s frames {N} KO1 {tau_to_t(UPPER):.2f} rise {tau_to_t(RISE_B):.2f} KO2 {tau_to_t(E_COUNTER):.2f}")
    if "--stills" in sys.argv:
        ts = [0.15, 1.2, 3.9, 6.0, tau_to_t(UPPER) + 0.1, tau_to_t(COUNT[2]) + 0.1, tau_to_t(LAUGH_T) + 0.3,
              tau_to_t(RISE_B) + 0.1, tau_to_t(E_DODGE) + 0.3, tau_to_t(E_COUNTER) + 0.2, tau_to_t(E_COUNTER) + 1.0, T_P2 + 1.2]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
