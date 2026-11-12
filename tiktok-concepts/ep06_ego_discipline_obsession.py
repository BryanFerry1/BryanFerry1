"""EP06 - EGO VS DISCIPLINE VS OBSESSION  (the climb)

Visual hook: camera starts on an empty summit with a glowing red flag, then
whips all the way down three giant ladders to three tiny figures.
Title only: EGO / VS / DISCIPLINE / VS / OBSESSION.

EGO        climbs fastest, but keeps LOOKING DOWN at the others (red dashed
           sight lines), stops to gloat and point. OBSESSION passes him, he
           panics, scrambles, slips and falls all the way down.
NIGHT      time-lapse day/night strobe. DISCIPLINE climbs by day and rests by
           night. OBSESSION never stops and always LOOKS UP (white line to the flag).
END        OBSESSION reaches the summit, DAY 365, boom. Pull back: Discipline
           two thirds up, Ego on the floor in red.
PUNCH      EGO LOOKS DOWN. / DISCIPLINE LOOKS AHEAD. / OBSESSION LOOKS UP.

Layout follows the TikTok safe zone (CLAUDE.md): HUD at y 360/470,
scene centred left of x 880, nothing important below y 1560.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import (FPS, H, HEAD_R, L_FARM, L_THIGH, L_SHIN, L_UARM, RED, WHITE, W, Camera,
                    Layer, Post, VideoWriter, bloom, clamp, dashed, draw_figure, draw_runs,
                    draw_spaced, ease_out, fit_font, font, ik, mix, mux, paint, smoothstep)
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep06_ego_discipline_obsession"
dt = 1 / FPS

R = 0.5                 # rung spacing (world units)
TOP = 50                # summit rung
TOP_Y = TOP * R + 0.6   # summit ledge height
LAD = {"E": -2.3, "O": 0.0, "D": 2.3}
CX = 470.0              # screen x of world x=0 (scene shifted left of the TikTok icons)

# ------------------------------------------------------------ timeline (seconds)
T_WHIP_A, T_WHIP_B = 0.45, 1.25
T_GO = 2.9
T_GLOAT_A, T_GLOAT_B = 6.6, 9.2
T_SLIP = 9.95
NIGHT_A, NIGHT_B = 11.2, 15.2
N_CYC = 4
DAYS_AT = [1, 9, 41, 150, 300]


def obs_speed(t):
    if t < T_GO:
        return 0.0
    v = 3.3 * smoothstep(T_GO, T_GO + 0.3, t)
    if NIGHT_A <= t < NIGHT_B:
        v = 3.6
    return v


def disc_speed(t):
    if t < T_GO + 0.15:
        return 0.0
    v = 2.6 * smoothstep(T_GO + 0.15, T_GO + 0.5, t)
    if NIGHT_A <= t < NIGHT_B:
        u = ((t - NIGHT_A) / (NIGHT_B - NIGHT_A) * N_CYC) % 1
        v = 2.6 if u < 0.5 else 0.0          # day: climb, night: rest
    if t > 17.0:
        v *= 1 - 0.75 * smoothstep(17.0, 18.0, t)   # still climbing, slowly, while the camera pulls back
    return v


def ego_speed(t):
    if t < T_GO:
        return 0.0
    if t < T_GLOAT_A:
        return 5.2 * smoothstep(T_GO, T_GO + 0.2, t)
    if t < T_GLOAT_B:
        return 5.2 * (1 - smoothstep(T_GLOAT_A, T_GLOAT_A + 0.4, t))
    if t < T_SLIP:
        return 5.0
    return 0.0


def night(t):
    """0 day .. 1 night (time-lapse strobe)."""
    if not (NIGHT_A - 0.3 <= t < NIGHT_B + 0.3):
        return 0.0
    u = (t - NIGHT_A) / (NIGHT_B - NIGHT_A) * N_CYC
    return clamp(0.5 - 0.5 * math.cos(2 * math.pi * u)) * smoothstep(NIGHT_A - 0.3, NIGHT_A, t) * (1 - smoothstep(NIGHT_B, NIGHT_B + 0.3, t))


# pre-integrate climber positions (in rungs)
NT = int(40 * FPS)
P = {"E": np.zeros(NT), "O": np.zeros(NT), "D": np.zeros(NT)}
for i in range(1, NT):
    t = i * dt
    P["O"][i] = min(TOP, P["O"][i - 1] + obs_speed(t) * dt)
    P["D"][i] = P["D"][i - 1] + disc_speed(t) * dt
    P["E"][i] = P["E"][i - 1] + ego_speed(t) * dt
T_SUMMIT = float(np.argmax(P["O"] >= TOP - 1e-6)) * dt
T_STAND = T_SUMMIT + 0.7
T_PULL = T_STAND + 0.4
T_P1, T_P2, T_P3 = T_PULL + 1.3, T_PULL + 2.2, T_PULL + 3.1
DUR = T_P3 + 3.0
N = int(DUR * FPS)
E_SLIP_RUNG = P["E"][int(T_SLIP * FPS)]
FALL_D = 1.05


def day_of(t):
    if t < NIGHT_A:
        return 1
    if t < NIGHT_B:
        k = int((t - NIGHT_A) / (NIGHT_B - NIGHT_A) * N_CYC)
        return DAYS_AT[min(k + 1, N_CYC)]
    return int(300 + 65 * smoothstep(NIGHT_B, T_SUMMIT, t))


# ------------------------------------------------------------ front-view climber
def climb_pose(x, p, t, look=0.0, point=0.0):
    """Front view on a ladder. p = rungs climbed (float)."""
    hip_y = p * R + 1.05
    rungs = []
    for g in (0, 1):
        q = p - g
        n = math.floor(q / 2)
        u = clamp(q - 2 * n)
        u = u * u * (3 - 2 * u)
        rungs.append(2 * n + 2 * u + g)
    hl = np.array([x - 0.42, rungs[0] * R + 2.35])
    fr = np.array([x + 0.3, rungs[0] * R - 0.1])
    hr = np.array([x + 0.42, rungs[1] * R + 2.35])
    fl = np.array([x - 0.3, rungs[1] * R - 0.1])
    hip = np.array([x, hip_y])
    neck = hip + [0, 0.92]
    sh = hip + [0, 0.8]
    head = neck + [0.18 * look * 0, 0.36 - 0.18 * look]
    j = {"hip": hip, "neck": neck, "head": head, "shoulder": sh,
         "foot1": fl, "foot2": fr, "hand1": hl, "hand2": hr}
    j["knee1"] = ik(hip, fl, L_THIGH, L_SHIN, -1)
    j["knee2"] = ik(hip, fr, L_THIGH, L_SHIN, 1)
    if point > 0:
        tgt = sh + np.array([0.75, -0.75]) * 1.0
        j["hand2"] = j["hand2"] * (1 - point) + tgt * point
    j["elbow1"] = ik(sh, j["hand1"], L_UARM, L_FARM, -1)
    j["elbow2"] = ik(sh, j["hand2"], L_UARM, L_FARM, 1)
    # keep feet/hands reachable visually
    return j


def rest_pose(x, p, t):
    """Discipline resting at night: hugging the ladder, head down."""
    j = climb_pose(x, math.floor(p), t)
    j["head"] = j["neck"] + [0.12, 0.16]
    return j


def stand_front(x, y, t, arms_up):
    hip = np.array([x, y + 1.5])
    sh = hip + [0, 0.8]
    neck = hip + [0, 0.92]
    j = {"hip": hip, "neck": neck, "head": neck + [0, 0.36], "shoulder": sh,
         "foot1": np.array([x - 0.28, y]), "foot2": np.array([x + 0.28, y])}
    j["knee1"] = ik(hip, j["foot1"], L_THIGH, L_SHIN, -1)
    j["knee2"] = ik(hip, j["foot2"], L_THIGH, L_SHIN, 1)
    up = arms_up
    j["hand1"] = sh + np.array([-0.55 - 0.2 * up, -0.95 + 2.0 * up])
    j["hand2"] = sh + np.array([0.55 + 0.2 * up, -0.95 + 2.0 * up + 0.05 * math.sin(t * 4)])
    j["elbow1"] = ik(sh, j["hand1"], L_UARM, L_FARM, -1)
    j["elbow2"] = ik(sh, j["hand2"], L_UARM, L_FARM, 1)
    return j


def falling_pose(x, y, t, spin):
    c, s = math.cos(spin), math.sin(spin)
    base = {"hip": (0, 0), "neck": (0, 0.92), "head": (0, 1.28), "shoulder": (0, 0.8),
            "knee1": (-0.5, -0.5), "foot1": (-0.6, -1.2), "knee2": (0.55, -0.4), "foot2": (0.9, -1.0),
            "elbow1": (-0.6, 1.2), "hand1": (-1.0, 1.6), "elbow2": (0.6, 1.25), "hand2": (1.05, 1.5)}
    return {k: np.array([x + c * v[0] - s * v[1], y + s * v[0] + c * v[1]]) for k, v in base.items()}


def lying_front(x, t):
    return {"hip": np.array([x, 0.25]), "neck": np.array([x + 0.9, 0.28]), "head": np.array([x + 1.27, 0.3]),
            "shoulder": np.array([x + 0.78, 0.28]), "knee1": np.array([x - 0.75, 0.2]),
            "foot1": np.array([x - 1.5, 0.12]), "knee2": np.array([x - 0.6, 0.5]), "foot2": np.array([x - 1.3, 0.15]),
            "elbow1": np.array([x + 1.0, 0.65]), "hand1": np.array([x + 1.4, 0.95]),
            "elbow2": np.array([x + 0.9, 0.12]), "hand2": np.array([x + 1.4, 0.1])}


def draw_ladder(c, cam, x, top_rung, alpha):
    y0 = max(-1.0, (cam.wy - (H - cam.sy) / cam.s) - 1)
    y1 = min(top_rung * R + 0.6, cam.wy + cam.sy / cam.s + 1)
    if y1 <= y0:
        return
    for dx in (-0.5, 0.5):
        c.drawLine(*cam.pt((x + dx, y0)), *cam.pt((x + dx, y1)), paint(WHITE, 0.55 * alpha, max(1.5, 0.05 * cam.s)))
    k0 = max(1, int(math.floor(y0 / R)))
    k1 = int(math.ceil(y1 / R))
    if cam.s * R > 5:
        for k in range(k0, min(k1, top_rung + 1)):
            c.drawLine(*cam.pt((x - 0.5, k * R)), *cam.pt((x + 0.5, k * R)), paint(WHITE, 0.32 * alpha, max(1.0, 0.035 * cam.s)))


def draw_flag(c, cam, t, alpha):
    base = np.array([0.0, TOP_Y])
    top = base + [0, 2.6]
    c.drawLine(*cam.pt(base), *cam.pt(top), paint(WHITE, 0.9 * alpha, max(1.5, 0.07 * cam.s)))
    path = skia.Path()
    path.moveTo(*cam.pt(top))
    n = 10
    for i in range(1, n + 1):
        u = i / n
        path.lineTo(*cam.pt((top[0] + 1.3 * u, top[1] - 0.04 + math.sin(u * 3.2 - t * 5.5) * 0.1 * u)))
    for i in range(n, -1, -1):
        u = i / n
        path.lineTo(*cam.pt((top[0] + 1.3 * u, top[1] - 0.8 + math.sin(u * 3.2 - t * 5.5 + 0.4) * 0.1 * u)))
    path.close()
    c.drawPath(path, paint(RED, alpha))


def draw_moon(c, alpha):
    if alpha < 0.01:
        return
    cx, cy, r = 200, 640, 46
    c.drawCircle(cx, cy, r, paint(WHITE, 0.9 * alpha))
    c.drawCircle(cx + 20, cy - 12, r * 0.92, paint((0, 0, 0), 1.0))


def render(stills=None):
    os.makedirs(OUT, exist_ok=True)
    env, fig, txt = Layer(), Layer(), Layer()
    post = Post()
    events = []
    writer = None if stills else VideoWriter(os.path.join(OUT, NAME + "_video.mp4"))
    f_lab = font(26, "Inter-Bold")
    f_cap = font(24, "Inter-SemiBold")
    f_vs = font(44, "InterDisplay-Bold")
    f_big = fit_font("OBSESSION", 132, "InterDisplay-Black", 6, 760)
    f_p = fit_font("DISCIPLINE LOOKS AHEAD.", 56, "InterDisplay-Bold", 4, 780)

    cam = Camera()
    cam.s, cam.sx, cam.wx = 120.0, CX, 0.0
    last_r = {"E": 0, "O": 0, "D": 0}
    last_day = 1
    looks_logged = set()
    for fi in range(N):
        t = fi * dt
        draw_now = stills is None or fi in stills
        pi = min(fi, NT - 1)
        pE, pO, pD = P["E"][pi], P["O"][pi], P["D"][pi]
        nt = night(t)

        # ---------------- poses
        xs = LAD
        # EGO
        e_fall = 0.0
        if t < T_SLIP:
            look = smoothstep(T_GLOAT_A - 0.2, T_GLOAT_A + 0.2, t) * (1 - smoothstep(8.5, 8.7, t))
            for a, b in ((4.6, 5.3),):
                look = max(look, smoothstep(a, a + 0.15, t) * (1 - smoothstep(b, b + 0.15, t)))
            point = smoothstep(T_GLOAT_A + 0.2, T_GLOAT_A + 0.5, t) * (1 - smoothstep(8.4, 8.7, t))
            jE = climb_pose(xs["E"], pE, t, look, point)
            eA = 1.0
        else:
            u = (t - T_SLIP) / FALL_D
            y0 = E_SLIP_RUNG * R + 1.05
            if u < 1:
                yy = y0 - (y0 - 0.3) * u * u
                jE = falling_pose(xs["E"] + 0.6 * u, yy, t, 2.4 * u)
                e_fall = 1.0
            else:
                jE = lying_front(xs["E"] - 0.3, t)
            look = 0.0
        e_red = clamp(0.25 * smoothstep(T_GO, T_GLOAT_A, t) + 0.45 * smoothstep(T_GLOAT_B, T_SLIP, t) + 0.3 * (t > T_SLIP))
        ecol = mix(WHITE, RED, e_red)
        # OBSESSION
        if t < T_SUMMIT:
            jO = climb_pose(xs["O"], pO, t, -0.2 * (t > T_GO))
        else:
            w = smoothstep(T_SUMMIT, T_STAND, t)
            jc = climb_pose(xs["O"], TOP, t)
            js = stand_front(xs["O"] - 0.9, TOP_Y, t, smoothstep(T_STAND, T_STAND + 0.35, t))
            jO = {k: jc[k] * (1 - w) + js[k] * w for k in jc}
        # DISCIPLINE
        resting = disc_speed(t) == 0.0 and NIGHT_A <= t < NIGHT_B
        jD = rest_pose(xs["D"], pD, t) if resting else climb_pose(xs["D"], pD, t)

        # ---------------- events
        for k, p in (("E", pE), ("O", pO), ("D", pD)):
            r = int(p)
            if r != last_r[k] and r % 2 == 0 and (k != "E" or t < T_SLIP):
                events.append((t, "rung_" + k, 0, r))
            last_r[k] = r
        if t >= T_SLIP and "slip" not in looks_logged:
            looks_logged.add("slip")
            events.append((t, "slip", 0, 0))
        if t >= T_SLIP + FALL_D and "crash" not in looks_logged:
            looks_logged.add("crash")
            events.append((t, "crash", 0, 0))
        for name, ta in (("look1", 4.6), ("look2", T_GLOAT_A), ("look3", 8.7)):
            if t >= ta and name not in looks_logged:
                looks_logged.add(name)
                events.append((t, "lock", 0, 0))
        d = day_of(t)
        if d != last_day:
            events.append((t, "day", 0, d))
            last_day = d

        # ---------------- camera (world y up, region y 330..1550)
        if t < T_WHIP_A:
            ty, s_t = TOP_Y - 0.5, 120.0
        elif t < T_WHIP_B:
            u = smoothstep(T_WHIP_A, T_WHIP_B, t)
            ty, s_t = (TOP_Y - 0.5) * (1 - u) + 2.6 * u, 120.0
        elif t < T_GO + 0.5:
            ty, s_t = 2.6, 120.0
        elif t < T_PULL:
            # mostly follow Obsession; frame Ego too while he is near
            ty = pO * R + 1.6
            if t < T_SLIP + 0.3:
                ty = (pO * R * 0.55 + pE * R * 0.45) + 1.6
            s_t = 120.0
        else:
            u = smoothstep(T_PULL, T_PULL + 1.6, t)
            s_full = (1540 - 800) / (TOP_Y + 3.5)
            ty_full = (TOP_Y + 3.0 - 0.5) / 2 + (1170 - 1080) / s_full
            ty = (TOP_Y - 0.5) * (1 - u) + ty_full * u
            s_t = math.exp(math.log(120) * (1 - u) + math.log(s_full) * u)
        if fi == 0:
            cam.wy = ty
        k_cam = 1.0 if T_WHIP_A <= t < T_WHIP_B + 0.05 or t >= T_PULL else 0.12
        cam.wy += (ty - cam.wy) * k_cam
        cam.s = s_t
        cam.sy = 1080.0
        cam.wx = 0.0

        if not draw_now:
            continue

        # ================================================= draw
        for L in (env, fig, txt):
            L.clear()
        master = smoothstep(0, 0.3, t) * (1 - smoothstep(DUR - 0.35, DUR, t))
        dim = 1 - 0.55 * nt
        e, f_, tc = env.canvas, fig.canvas, txt.canvas
        # ground
        gx0, gy = cam.pt((-6, 0))
        e.drawLine(0, gy, W, gy, paint(WHITE, 0.5 * dim, 2.5))
        # ledge at summit
        l0 = cam.pt((-3.1, TOP_Y))
        l1 = cam.pt((3.1, TOP_Y))
        e.drawLine(*l0, *l1, paint(WHITE, 0.75 * dim, max(2, 0.08 * cam.s)))
        for k in ("E", "O", "D"):
            draw_ladder(e, cam, LAD[k], TOP, dim)
        draw_flag(f_, cam, t, 1.0)
        draw_moon(e, nt)
        # whip speed lines
        if T_WHIP_A < t < T_WHIP_B:
            sp = math.sin(math.pi * (t - T_WHIP_A) / (T_WHIP_B - T_WHIP_A))
            rr = np.random.default_rng(fi)
            for _ in range(26):
                x = rr.uniform(80, 880)
                y = rr.uniform(0, H)
                e.drawLine(x, y, x, y - 260 * sp, paint(WHITE, 0.25 * sp, 2))

        # sight lines
        if look > 0.02 and t < T_SLIP:
            a = cam.pt(jE["head"])
            for k in ("O", "D"):
                b = cam.pt((jO if k == "O" else jD)["head"])
                f_.drawLine(*a, *b, dashed(RED, 0.85 * look, 4, 16, 12, -t * 120))
                f_.drawCircle(*b, HEAD_R * cam.s * 1.6, paint(RED, 0.75 * look, 3))
        if T_GO + 0.4 < t < T_SUMMIT:
            a = cam.pt(jO["head"])
            b = cam.pt((0.0, TOP_Y + 2.2))
            la = (0.22 + 0.4 * nt) * smoothstep(T_GO + 0.4, T_GO + 1.0, t)
            f_.drawLine(*a, *b, dashed(WHITE, la, 3, 14, 14, t * 80))
        # panic line: Ego stares UP at Obsession before slipping
        if 8.7 < t < T_SLIP:
            w = smoothstep(8.7, 8.9, t)
            a = cam.pt(jE["head"])
            b = cam.pt(jO["head"])
            f_.drawLine(*a, *b, dashed(RED, 0.85 * w, 4, 16, 12, -t * 160))

        # figures
        draw_figure(f_, jD, cam, WHITE, 0.95 * (1 - 0.35 * nt * (1 if resting else 0)), 1.0)
        draw_figure(f_, jO, cam, WHITE, 1.0, 1.0)
        draw_figure(f_, jE, cam, ecol, 1.0, 1.0)
        if e_fall > 0:
            hx, hy = cam.pt(jE["hip"])
            f_.drawLine(hx, hy, hx - 10, hy - 260, paint(RED, 0.35, 10))
        # zz for resting discipline
        if resting:
            hx, hy = cam.pt(jD["head"])
            za = 0.8 * nt
            draw_spaced(tc, "z", hx + 40, hy - 30 - 10 * math.sin(t * 3), font(30, "InterDisplay-Bold"), 0, paint(WHITE, za))
            draw_spaced(tc, "z", hx + 66, hy - 62 - 10 * math.sin(t * 3 + 1), font(40, "InterDisplay-Bold"), 0, paint(WHITE, za * 0.8))
        # crash flash at the bottom of the screen
        if t > T_SLIP + FALL_D - 0.05:
            fa = math.exp(-(t - T_SLIP - FALL_D) * 3.5)
            f_.drawRect(skia.Rect(0, 1250, W, H), paint(RED, 0.22 * fa))

        # labels (follow figures, under feet)
        lab_a = smoothstep(2.2, 2.8, t) * (1 - smoothstep(T_PULL - 0.3, T_PULL, t))
        for j, name, col, a in ((jE, "EGO", ecol, 1.0 if t < T_SLIP else 0.0),
                                (jO, "OBSESSION", WHITE, 1.0), (jD, "DISCIPLINE", WHITE, 1.0)):
            fx = (j["foot1"][0] + j["foot2"][0]) / 2
            fy = min(j["foot1"][1], j["foot2"][1])
            sx, sy = cam.pt((fx, fy))
            if 330 < sy + 40 < 1550:
                draw_spaced(tc, name, sx, sy + 42, f_lab, 5, paint(col, lab_a * a))

        # HUD (safe zone)
        hud_a = smoothstep(2.9, 3.4, t) * (1 - 0.5 * smoothstep(T_P1 - 0.3, T_P1 + 0.3, t))
        d = day_of(t)
        draw_spaced(tc, "DAY", CX, 360, f_cap, 12, paint(WHITE, 0.7 * hud_a))
        pop = 1.0
        draw_spaced(tc, str(d), CX, 470, font(104, "InterDisplay-Bold"), 4, paint(RED if t >= T_SUMMIT else WHITE, hud_a))

        # title (big, centred in the scene area)
        ta = smoothstep(T_WHIP_B - 0.1, T_WHIP_B + 0.15, t) * (1 - smoothstep(T_GO - 0.4, T_GO, t))
        if ta > 0.01:
            pop = 1 + 0.08 * (1 - ease_out((t - T_WHIP_B) / 0.35))
            fb = font(f_big.getSize() * pop, "InterDisplay-Black")
            draw_spaced(tc, "EGO", CX, 500, font(f_big.getSize() * 1.25 * pop, "InterDisplay-Black"), 8, paint(RED, ta))
            draw_spaced(tc, "VS", CX, 565, f_vs, 10, paint(WHITE, 0.7 * ta))
            draw_spaced(tc, "DISCIPLINE", CX, 685, fit_font("DISCIPLINE", 132 * pop, "InterDisplay-Black", 6, 760), 6, paint(WHITE, ta))
            draw_spaced(tc, "VS", CX, 750, f_vs, 10, paint(WHITE, 0.7 * ta))
            draw_spaced(tc, "OBSESSION", CX, 870, fb, 6, paint(WHITE, ta))

        # punchline
        def reveal(t0):
            uu = ease_out((t - t0) / 0.4)
            return uu, (1 - uu) * 30
        for t0, runs, y in ((T_P1, [("EGO", RED), (" LOOKS DOWN.", WHITE)], 560),
                            (T_P2, [("DISCIPLINE", WHITE), (" LOOKS AHEAD.", WHITE)], 635),
                            (T_P3, [("OBSESSION", WHITE), (" LOOKS UP.", WHITE)], 705)):
            if t >= t0:
                uu, off = reveal(t0)
                big = t0 == T_P3
                ff = f_p if not big else fit_font("OBSESSION LOOKS UP.", 70, "InterDisplay-Black", 4, 780)
                draw_runs(tc, [(s, paint(c, uu * (1 if big or c == RED else 0.85))) for s, c in runs], CX, y + off + (14 if big else 0), ff, 4)

        # composite
        flash = math.exp(-(t - T_SUMMIT) * 3.0) if t >= T_SUMMIT else 0.0
        eb = bloom(env.rgb(), (0.9, (4, 0.6), (22, 0.3)))
        gb = bloom(fig.rgb(), (1.0, (5, 0.9), (18, 0.8 + 0.3 * nt), (60, 0.5 + 0.3 * nt + flash)))
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
    m.add_bed(sfx.drone(DUR, rise_at=T_SUMMIT), gain=0.5, fade_in=0.6, fade_out=2.5, stop=DUR)
    m.add(T_WHIP_A - 0.1, sfx.whoosh(T_WHIP_B - T_WHIP_A + 0.3, 150, 4000, 0.75, seed=4), 0.9, 0, 0.3)
    m.add(T_WHIP_B, sfx.text_hit(5), 0.9, 0, 0.4)
    m.add(T_WHIP_B, sfx.boom(2.5), 0.4, 0, 0.4)
    m.add(T_GO - 0.05, sfx.whoosh(0.4, 600, 8000, 0.5, seed=6), 0.3, 0, 0.2)
    for t, kind, pan, extra in events:
        if kind == "rung_E":
            m.add(t, sfx.tick(3000, 0.35), 0.35, -0.45, 0.1)
        elif kind == "rung_O":
            m.add(t, sfx.plate_clank(extra, 0.3) * 0.5, 0.35, 0.0, 0.2)
        elif kind == "rung_D":
            m.add(t, sfx.step_heavy(extra), 0.25, 0.4, 0.2)
        elif kind == "lock":
            m.add(t, sfx.lock_on(int(t)), 0.6, -0.4, 0.3)
        elif kind == "slip":
            m.add(t, sfx.glitch(7), 0.8, -0.4, 0.2)
            m.add(t, sfx.power_down(FALL_D + 0.3), 0.6, -0.4, 0.3)
            m.add(t, sfx.whoosh(FALL_D, 200, 3000, 0.9, seed=11), 0.8, -0.4, 0.3)
        elif kind == "crash":
            m.add(t, sfx.body_fall(), 1.0, -0.4, 0.4)
            m.add(t, sfx.boom(2.5), 0.6, -0.3, 0.4)
        elif kind == "day":
            m.add(t, sfx.tick(1900, 0.5), 0.5, 0, 0.1)
            m.add(t - 0.15, sfx.whoosh(0.4, 300, 4000, 0.6, seed=extra % 50), 0.25, 0, 0.3)
    m.add(T_SUMMIT - 2.6, sfx.riser(2.6), 0.55, 0, 0.3)
    m.add(T_SUMMIT, sfx.boom(4.0), 1.0, 0, 0.5)
    m.add(T_STAND, sfx.sparkle(2.0), 0.55, 0, 0.6)
    m.add(T_PULL, sfx.whoosh(1.4, 100, 2500, 0.7, seed=13), 0.4, 0, 0.4)
    m.add(T_P1, sfx.text_hit(1), 0.55, -0.3, 0.4)
    m.add(T_P2, sfx.text_hit(2), 0.6, 0.3, 0.4)
    m.add(T_P3, sfx.text_hit(3), 0.95, 0, 0.5)
    m.add(T_P3, sfx.boom(2.0), 0.45, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}s frames {N} summit {T_SUMMIT:.2f} ego slips at rung {E_SLIP_RUNG:.1f}, obs {P['O'][int(T_SLIP*FPS)]:.1f}")
    if "--stills" in sys.argv:
        ts = [0.2, 0.8, 1.8, 4.0, 5.0, 7.4, 9.5, T_SLIP + 0.4, 12.0, 13.6, T_SUMMIT + 0.8, T_P3 + 1.0]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
