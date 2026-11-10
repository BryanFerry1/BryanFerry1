"""EP05 - DOUBTERS vs CONSISTENCY  (the gym glow-up)

Visual hook (no sentence): we open on the END - a huge glowing lifter flexing
while a crowd films him and flashes pop, DAY 1000 - then a tape REWIND
slams us back to DAY 1.
Title only: "DOUBTERS VS CONSISTENCY".

DAY 1   A skinny figure curls an almost-empty bar, shaking. Three grey
        DOUBTERS point at him and laugh - red "HA" bubbles pop.
MONTAGE Days fly by (1 -> 1000). He grows bigger, thicker, brighter, the plates
        get heavier. The doubters stop laughing, cross their arms, then put
        their hands on their heads.
END     Final heavy rep in slow motion, lockout, he drops the bar - BOOM.
        The same doubters come back with phones up and a paper for an
        autograph, new fans walk in, applause, flashes. He flexes.
PUNCH   "THEY LAUGH AT DAY 1." / "THEY CLAP AT" / "DAY 1000."
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import (FPS, H, HEAD_R, RED, WHITE, W, Camera, Layer, Post, VideoWriter,
                    blend_pose, bloom, build_pose, clamp, draw_figure, draw_runs,
                    draw_spaced, ease_out, fit_font, font, mix, mux, paint, run_pose,
                    smoothstep)
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep05_doubters_vs_consistency"
GREY = (0.55, 0.55, 0.58)
dt = 1 / FPS

T_FF = T_RW = 0.0               # no flash-forward any more: the story starts at t = 0
# Day 1: a shaky rep, a failed rep, he drops the bar, sad, then picks it back up
REP_A = (0.7, 2.2)
REP_B = (2.2, 3.35)
DROP1 = 3.35
SAD_A, SAD_B = 3.6, 5.5
PICK_A, PICK_B = 5.5, 6.9
MONT_REP, MONT_N = 0.5, 16
MONT_A = 7.1
FINAL_A = MONT_A + MONT_REP * MONT_N
FINAL_D = 2.1
LOCK = FINAL_A + 1.55
DROP = FINAL_A + FINAL_D
CROWD = DROP + 0.1
P1, P2, P3 = DROP + 1.7, DROP + 2.5, DROP + 2.95
END_TS = P3 + 2.8
DUR = END_TS
N = int(DUR * FPS)
BAR_GROUND_X = 0.62


def ts_of(t):
    return t


def tts(ts):
    return ts


def rep_state(ts):
    """(day, curl 0..1, shake amplitude, rep id or None)"""
    if ts < REP_A[0]:
        return 1, 0.0, 0.0, None
    if ts < REP_A[1]:
        u = (ts - REP_A[0]) / (REP_A[1] - REP_A[0])
        return 1, 0.85 * math.sin(math.pi * u) ** 1.3, 0.035, ("d1", 0)
    if ts < REP_B[1]:
        u = (ts - REP_B[0]) / (REP_B[1] - REP_B[0])
        c = 0.5 * math.sin(math.pi * min(u, 0.5) / 1.0) if u < 0.75 else 0.5 * (1 - smoothstep(0.75, 1.0, u))
        return 1, c, 0.06, ("d1", 1)
    if ts < MONT_A:
        return 1, 0.0, 0.0, None
    if ts < FINAL_A:
        k = int((ts - MONT_A) // MONT_REP)
        u = (ts - MONT_A - k * MONT_REP) / MONT_REP
        day = int(round(2 * (1000 / 2) ** ((k + 1) / MONT_N)))
        return day, math.sin(math.pi * u), 0.0, ("m", k)
    if ts < DROP:
        u = (ts - FINAL_A) / FINAL_D
        if u < 0.74:
            c = 0.95 * smoothstep(0, 0.74, u) ** 0.8
            sh = 0.03 * smoothstep(0.15, 0.6, u)
        else:
            c = 0.95 - 0.95 * smoothstep(0.74, 1.0, u)
            sh = 0.0
        return 1000, c, sh, ("f", 0)
    return 1000, 0.0, 0.0, None


def growth(day):
    return math.log(day) / math.log(1000)


def plates_for(g):
    kg = 10 + 75 * g
    side = (kg - 10) / 2
    out = []
    for w, r in ((10, 0.30), (5, 0.24), (2.5, 0.18), (1.25, 0.13)):
        while side >= w - 1e-6:
            out.append(r)
            side -= w
    return out or [0.1]


# ------------------------------------------------------------ poses
def scale_pose(j, x, sc):
    return {k: np.array([x + (v[0] - x) * sc, v[1] * sc]) for k, v in j.items()}


def mirror(j, cx):
    return {k: np.array([2 * cx - v[0], v[1]]) for k, v in j.items()}


def stand(x, lean, a1, a2, b1, b2, head, bob=0.0):
    return build_pose(np.array([x, 1.52 + bob]), np.array([x + 0.13, 0.02]), np.array([x - 0.13, 0.02]),
                      lean, a1, a2, b1, b2, head)


def hero_pose(ts, t, x=0.0):
    day, c, sh, _ = rep_state(ts)
    a = 0.12 + 0.18 * c
    b = 0.15 + 2.3 * c
    j = stand(x, 0.03 - 0.05 * c, a, a - 0.04, b, b - 0.05, 0.05)
    # failed rep -> drops the bar -> sad -> looks up -> picks it back up
    if DROP1 <= ts < MONT_A + 0.3:
        br = 0.02 * math.sin(t * 2.2)
        sad = stand(x, 0.32, 0.04, 0.0, 0.12, 0.08, 0.9, br - 0.04)
        look = stand(x, 0.18, 0.06, 0.02, 0.15, 0.1, 0.1, -0.02)
        w = smoothstep(DROP1, SAD_A, ts)
        j = blend_pose(j, sad, w)
        j = blend_pose(j, look, smoothstep(SAD_B - 0.5, SAD_B, ts))
        # bend down, grab, stand up
        bend = build_pose(np.array([x - 0.2, 0.98]), np.array([x + 0.22, 0.02]), np.array([x - 0.1, 0.02]),
                          1.05, 0.3, 0.25, 0.1, 0.1, 0.25)
        bar_g = np.array([BAR_GROUND_X, 0.2])
        for side in ("1", "2"):
            bend["hand" + side] = bar_g + ([0.0, 0] if side == "1" else [0.04, 0])
            bend["elbow" + side] = (bend["shoulder"] + bend["hand" + side]) / 2 + [0.08, 0]
        w_b = smoothstep(PICK_A, PICK_A + 0.45, ts) * (1 - smoothstep(PICK_A + 0.75, PICK_B, ts))
        j = blend_pose(j, bend, w_b)
        rest = stand(x, 0.03, 0.12, 0.08, 0.15, 0.1, 0.0)
        j = blend_pose(j, rest, smoothstep(PICK_A + 0.75, PICK_B, ts))
    if ts >= DROP:
        w = smoothstep(DROP + 0.1, DROP + 0.5, ts)
        flex = stand(x, -0.02, 1.57, 1.42, 1.55, 1.65, -0.12, 0.01 * math.sin(t * 3))
        j = blend_pose(j, flex, w)
    if sh > 0:
        jit = np.array([sh * math.sin(t * 63), sh * 0.7 * math.sin(t * 81)])
        for kk in ("hand1", "hand2", "elbow1", "elbow2"):
            j[kk] = j[kk] + jit * (1 if "hand" in kk else 0.5)
    return j


def bar_pos(ts, t, jh, sc, g):
    """Where the bar is: in the hands, falling, or on the floor."""
    rmax = max(plates_for(g))
    ground = np.array([BAR_GROUND_X * sc, rmax + 0.02])
    hands = (jh["hand1"] + jh["hand2"]) / 2
    if DROP1 <= ts < PICK_A + 0.45:
        b0 = (scale_pose(hero_pose(DROP1 - 0.01, t), 0.0, sc))
        h0 = (b0["hand1"] + b0["hand2"]) / 2
        u = smoothstep(DROP1, DROP1 + 0.22, ts)
        return h0 * (1 - u) + ground * u
    if PICK_A + 0.45 <= ts < PICK_A + 0.75:
        return ground
    if ts >= DROP:
        b0 = scale_pose(hero_pose(DROP - 0.01, t), 0.0, sc)
        h0 = (b0["hand1"] + b0["hand2"]) / 2
        u = smoothstep(DROP - 0.02, DROP + 0.25, ts)
        return h0 * (1 - u) + (ground + [0.0, 0]) * u
    return hands


SEGS_M = [  # (a, b, extra width at full growth, back limb?)
    ("hip", "knee2", 0.38, True), ("knee2", "foot2", 0.26, True),
    ("shoulder", "elbow2", 0.34, True), ("elbow2", "hand2", 0.22, True),
    ("hip", "neck", 0.52, False),
    ("hip", "knee1", 0.38, False), ("knee1", "foot1", 0.26, False),
    ("shoulder", "elbow1", 0.36, False), ("elbow1", "hand1", 0.24, False),
]


def draw_body(c, j, cam, col, alpha, g):
    """Stick figure that fills out with real muscle bellies as g goes 0 -> 1."""
    s = cam.s
    for a, b, wx, back in SEGS_M:
        pa, pb = np.array(cam.pt(j[a])), np.array(cam.pt(j[b]))
        al = alpha * (0.55 if back else 1.0)
        base = (0.12 if a != "hip" or b != "neck" else 0.15) * s
        c.drawLine(*pa, *pb, paint(col, al, base))
        w = (0.04 + wx * g ** 0.9) * s
        if w > base * 1.05:
            d = pb - pa
            L = float(np.hypot(*d))
            ang = math.degrees(math.atan2(d[1], d[0]))
            mid = pa + d * (0.45 if b not in ("foot1", "foot2") else 0.35)
            c.save()
            c.translate(*mid)
            c.rotate(ang)
            r = skia.Rect(-L * 0.42, -w / 2, L * 0.42, w / 2)
            c.drawOval(r, paint(col, al))
            c.drawOval(r, paint((0, 0, 0), 1.0, max(2.0, 0.05 * s)))
            c.restore()
    # delts + traps
    sx, sy = cam.pt(j["shoulder"])
    c.drawCircle(sx, sy, (0.07 + 0.17 * g) * s, paint(col, alpha))
    c.drawCircle(sx, sy, (0.07 + 0.17 * g) * s, paint((0, 0, 0), 1.0, max(2.0, 0.05 * s)))
    nx, ny = cam.pt(j["neck"])
    c.drawLine(sx, sy, nx, ny, paint(col, alpha, (0.12 + 0.16 * g) * s))
    hx, hy = cam.pt(j["head"])
    c.drawCircle(hx, hy, HEAD_R * s * (1 - 0.08 * g), paint(col, alpha))


def doubter_pose(i, x, ts, t):
    bob = 0.03 * abs(math.sin(t * 13 + i * 1.7))
    laugh = stand(x, -0.14 + 0.07 * math.sin(t * 13 + i), 1.5, 0.6, 0.05, 1.6, -0.45, bob)
    crossed = stand(x, 0.0, 0.5, 0.45, 1.9, 1.95, 0.05)
    if i == 1:
        stunned = stand(x, 0.08, 2.7, 2.6, 2.0, 2.05, 0.1)        # hands on head
    else:
        stunned = stand(x, 0.14, 0.08, 0.05, 0.2, 0.15, 0.3)       # jaw drop, arms limp
    if i == 0:
        fan = stand(x, 0.05, 1.42, 0.4, 0.08, 1.2, 0.0)           # hands a paper for an autograph
    else:
        fan = stand(x, 0.02, 1.75 + 0.04 * math.sin(t * 1.5 + i), 1.55, 0.75, 0.95, 0.12)
    j = blend_pose(laugh, crossed, smoothstep(MONT_A + 1.8, MONT_A + 4.0, ts))
    j = blend_pose(j, stunned, smoothstep(MONT_A + 6.0, FINAL_A + 0.5, ts))
    j = blend_pose(j, fan, smoothstep(CROWD, CROWD + 0.5, ts))
    return j


DOUBTERS = [(2.5, 1), (3.5, 2), (4.4, 1)]
FANS = [(-2.1, 1, -6.5), (-2.95, 2, -7.4), (-3.7, 1, -8.2)]
ROWS = {0: (1.0, 0), 1: (0.84, 62), 2: (0.72, 116)}


def draw_phone(c, cam, j, alpha, t, i, flash):
    hx, hy = cam.pt((j["hand1"] + j["hand2"]) / 2)
    pw, ph = 0.44 * cam.s, 0.76 * cam.s
    x0, y0 = hx - pw / 2, hy - ph * 0.62
    r = skia.Rect(x0, y0, x0 + pw, y0 + ph)
    c.drawRoundRect(r, pw * 0.18, pw * 0.18, paint((0, 0, 0), 1.0))
    inner = skia.Rect(x0 + pw * 0.1, y0 + ph * 0.1, x0 + pw * 0.9, y0 + ph * 0.9)
    c.drawRoundRect(inner, pw * 0.08, pw * 0.08, paint(WHITE, 0.18 * alpha))
    cx, cy = (inner.left() + inner.right()) / 2, inner.top() + inner.height() * 0.55
    c.drawCircle(cx, cy - ph * 0.17, pw * 0.1, paint(WHITE, 0.85 * alpha))
    c.drawLine(cx, cy - ph * 0.08, cx, cy + ph * 0.12, paint(WHITE, 0.85 * alpha, max(1.5, pw * 0.07)))
    c.drawLine(cx - pw * 0.2, cy - ph * 0.02, cx + pw * 0.2, cy - ph * 0.02, paint(WHITE, 0.85 * alpha, max(1.5, pw * 0.06)))
    c.drawRoundRect(r, pw * 0.18, pw * 0.18, paint(WHITE, 0.95 * alpha, max(2.0, pw * 0.07)))
    if (int(t * 2.5) + i) % 2 == 0:
        c.drawCircle(inner.left() + pw * 0.13, inner.top() + pw * 0.13, max(2.5, pw * 0.08), paint(RED, alpha))
    if flash > 0:
        c.drawCircle(hx + pw * 0.22, y0 + ph * 0.2, (0.08 + 0.22 * flash) * cam.s, paint(WHITE, 0.95 * flash))


def draw_paper(c, cam, j, alpha):
    hx, hy = cam.pt(j["hand1"])
    w, h = 0.36 * cam.s, 0.48 * cam.s
    r = skia.Rect(hx - w * 0.9, hy - h * 0.6, hx + w * 0.1, hy + h * 0.4)
    c.drawRect(r, paint((0, 0, 0), 1.0))
    c.drawRect(r, paint(WHITE, 0.95 * alpha, max(2, 0.04 * cam.s), cap=False))
    for k in range(3):
        y = r.top() + h * (0.28 + 0.2 * k)
        c.drawLine(r.left() + w * 0.15, y, r.right() - w * 0.15 - k * w * 0.12, y, paint(WHITE, 0.5 * alpha, 2))
    c.drawLine(hx - w * 0.2, hy + h * 0.1, hx + w * 0.35, hy - h * 0.55, paint(RED, alpha, max(2, 0.05 * cam.s)))


def render(stills=None):
    os.makedirs(OUT, exist_ok=True)
    env, fig, txt, hero = Layer(), Layer(), Layer(), Layer()
    post = Post()
    events = []
    rng = np.random.default_rng(12)
    writer = None if stills else VideoWriter(os.path.join(OUT, NAME + "_video.mp4"))
    f_lab = font(30, "Inter-Bold")
    f_cap = font(24, "Inter-SemiBold")
    f_title = fit_font("DOUBTERS VS CONSISTENCY", 64, "InterDisplay-Black", 4, 940)
    f_ha = font(46, "InterDisplay-Black")
    f_p1 = fit_font("THEY LAUGH AT DAY 1.", 62, "InterDisplay-Bold", 6, 940)
    f_p2 = fit_font("THEY CLAP AT", 96, "InterDisplay-Black", 6, 960)

    has = []          # HA bubbles: (ts0, x, y, size)
    flashes = []      # (ts0, who)
    last_rep = None
    last_day = 1
    next_ha = 0.0
    next_flash = CROWD + 0.35
    dropped = False
    prev_ts = None
    for fi in range(N):
        t = fi * dt
        ts = ts_of(t)
        main = t >= T_RW
        draw_now = stills is None or fi in stills

        # ---------------- events (main story only)
        day, c, sh, rep = rep_state(ts)
        if main:
            if rep != last_rep and rep is not None:
                events.append((t, "rep", 0, rep))
            last_rep = rep
            if day != last_day:
                events.append((t, "day", 0, day))
                last_day = day
            ha_rate = (4.0 + 6.0 * smoothstep(DROP1, DROP1 + 0.2, ts) * (1 - smoothstep(SAD_A + 0.5, SAD_B, ts))) * (1 - smoothstep(MONT_A + 0.5, MONT_A + 3.0, ts))
            while ha_rate > 0.2 and ts >= next_ha:
                i = int(rng.integers(3))
                x, row = DOUBTERS[i]
                has.append((ts, x + rng.uniform(-0.6, 0.6), rng.uniform(3.1, 3.9), rng.uniform(0.8, 1.25), i))
                events.append((t, "ha", 0, i))
                next_ha = ts + rng.exponential(1.0 / ha_rate) + 0.08
            if ts >= LOCK and not any(e[1] == "lock" for e in events):
                events.append((t, "lock", 0, 0))
            if ts >= DROP1 and not any(e[1] == "drop1" for e in events):
                events.append((t, "drop1", 0, 0))
            if ts >= PICK_A + 0.55 and not any(e[1] == "pick" for e in events):
                events.append((t, "pick", 0, 0))
            if ts >= DROP and not dropped:
                dropped = True
                events.append((t, "drop", 0, 0))
        if ts >= CROWD + 0.3:
            while ts >= next_flash:
                flashes.append((next_flash, int(rng.integers(6))))
                if main:
                    events.append((t, "shutter", 0, len(flashes)))
                next_flash += rng.uniform(0.08, 0.3)
        prev_ts = ts
        if not draw_now:
            continue

        # ================================================= draw
        for L in (env, fig, txt, hero):
            L.clear()
        master = smoothstep(0, 0.25, t) * (1 - smoothstep(DUR - 0.35, DUR, t))
        cam0 = Camera()
        cam0.s, cam0.wx, cam0.wy, cam0.sx, cam0.sy = 122.0, 0.9, 0.0, W / 2, 1430.0
        ff = t < T_RW

        def rcam(row):
            sc, up = ROWS[row]
            cc = Camera()
            cc.s, cc.wx, cc.wy, cc.sx, cc.sy = cam0.s * sc, cam0.wx, 0.0, cam0.sx, cam0.sy - up
            return cc

        g = growth(day)
        for row in (2, 1):
            env.canvas.drawLine(0, rcam(row).sy, W, rcam(row).sy, paint(WHITE, 0.1, 1.5))
        env.canvas.drawLine(0, cam0.sy, W, cam0.sy, paint(WHITE, 0.55, 2.5))

        # crowd: back rows first
        people = []
        for i, (x, row) in enumerate(DOUBTERS):
            people.append(("d", i, x, row))
        for i, (x, row, x0) in enumerate(FANS):
            people.append(("f", i, x, row))
        for kind, i, x, row in sorted(people, key=lambda p: -p[3]):
            cc = rcam(row)
            if kind == "d":
                jd = mirror(doubter_pose(i, x, ts, t), x)
                filming = ts >= CROWD + 0.3 and i != 0
                col = GREY
                a = 0.6
            else:
                x0 = FANS[i][2]
                u = smoothstep(CROWD - 0.2, CROWD + 0.9, ts)
                xx = x0 + (x - x0) * u
                if ts < CROWD - 0.2:
                    continue
                walk = run_pose(xx, ts * 7 + i, 0.4)
                film = stand(xx, 0.02, 1.75 + 0.04 * math.sin(t * 1.5 + i), 1.55, 0.75, 0.95, 0.12)
                jd = blend_pose(walk, film, smoothstep(CROWD + 0.7, CROWD + 1.1, ts))
                filming = ts >= CROWD + 1.0
                col, a = GREY, 0.5 * smoothstep(CROWD - 0.2, CROWD + 0.2, ts)
            draw_figure(env.canvas, jd, cc, col, a, 0.6)
            if filming:
                fl = 0.0
                who = i + (0 if kind == "d" else 3)
                for ft, k in flashes:
                    if k == who and 0 <= ts - ft < 0.3:
                        fl = 1 - (ts - ft) / 0.3
                draw_phone(fig.canvas, cc, jd, 0.9, t, who, fl)
            if kind == "d" and i == 0 and ts >= CROWD + 0.3:
                draw_paper(fig.canvas, cc, jd, smoothstep(CROWD + 0.3, CROWD + 0.6, ts))

        # hero
        sc = 0.84 + 0.44 * g
        jh = scale_pose(hero_pose(ts, t), 0.0, sc)
        sad = smoothstep(DROP1, SAD_A, ts) * (1 - smoothstep(SAD_B - 0.3, PICK_A + 0.6, ts))
        hcol = WHITE
        draw_body(hero.canvas, jh, cam0, hcol, (0.85 + 0.15 * g) * (1 - 0.35 * sad), g)
        # resolve pulse when he grabs the bar again
        age = ts - (PICK_A + 0.55)
        if 0 <= age < 0.8:
            cx, cy = cam0.pt(jh["hip"])
            fig.canvas.drawCircle(cx, cy - 0.3 * cam0.s, (0.5 + 3.5 * ease_out(age / 0.8)) * cam0.s,
                                  paint(WHITE, 0.5 * (1 - age / 0.8), 4))
        # bar + plates
        bar = bar_pos(ts, t, jh, sc, g)
        radii = plates_for(g)
        for k in range(len(radii) - 1, -1, -1):
            off = np.array([0.07, -0.045]) * k
            cx, cy = cam0.pt(bar + off)
            fig.canvas.drawCircle(cx, cy, radii[k] * cam0.s, paint((0, 0, 0), 1.0))
            fig.canvas.drawCircle(cx, cy, radii[k] * cam0.s, paint(WHITE, 0.95, max(2, 0.045 * cam0.s)))
        cx, cy = cam0.pt(bar)
        fig.canvas.drawCircle(cx, cy, 0.06 * cam0.s, paint(WHITE, 1.0))

        # HA bubbles
        for ts0, x, y, size, i in has:
            age = ts - ts0
            if 0 <= age < 0.7:
                pop = 1 + 0.5 * math.exp(-age * 18)
                cc = rcam(DOUBTERS[i][1])
                sx, sy = cc.pt((x, y + age * 0.6))
                draw_spaced(txt.canvas, "HA", sx, sy, font(46 * size * pop, "InterDisplay-Black"), 2,
                            paint(RED, (1 - age / 0.7) ** 1.2))

        # labels
        la = smoothstep(2.5, 3.0, ts) * (1 - smoothstep(P1 - 0.6, P1, ts))
        draw_spaced(txt.canvas, "CONSISTENCY", cam0.pt((0, 0))[0], cam0.sy + 52, f_lab, 6, paint(WHITE, la))
        da = la * (1 - smoothstep(CROWD - 0.5, CROWD, ts))
        draw_spaced(txt.canvas, "DOUBTERS", rcam(1).pt((3.5, 0))[0], cam0.sy + 52, f_lab, 6, paint(RED, da))

        # day HUD
        shown_day = day
        if T_FF <= t < T_RW:
            u = (t - T_FF) / (T_RW - T_FF)
            shown_day = max(1, int(1000 * (1 - u) ** 3))
        dcol = RED if shown_day >= 1000 else WHITE
        ha_ = smoothstep(2.5, 3.0, t) * (1 - 0.55 * smoothstep(P1 - 0.3, P1 + 0.3, ts))
        draw_spaced(txt.canvas, "DAY", W / 2, 236, f_cap, 12, paint(WHITE, 0.7 * ha_))
        pop = 1.0
        draw_spaced(txt.canvas, str(shown_day), W / 2, 350, font(110 * pop, "InterDisplay-Bold"), 4, paint(dcol, ha_))

        # title: big, centred
        ta = smoothstep(0.05, 0.3, t) * (1 - smoothstep(2.4, 2.9, t))
        if ta > 0.01:
            pop = 1 + 0.06 * (1 - ease_out(t / 0.4))
            f1 = fit_font("CONSISTENCY", 150 * pop, "InterDisplay-Black", 6, 980)
            draw_spaced(txt.canvas, "DOUBTERS", W / 2, 760, font(f1.getSize() * 1.12, "InterDisplay-Black"), 6, paint(RED, ta))
            draw_spaced(txt.canvas, "VS", W / 2, 860, font(56, "InterDisplay-Bold"), 10, paint(WHITE, 0.75 * ta))
            draw_spaced(txt.canvas, "CONSISTENCY", W / 2, 1000, f1, 6, paint(WHITE, ta))
        # punchline
        tc = txt.canvas

        def reveal(t0, dd=0.4):
            uu = ease_out((ts - t0) / dd)
            return uu, (1 - uu) * 34
        if main and ts >= P1:
            uu, off = reveal(P1)
            draw_runs(tc, [("THEY", paint(WHITE, uu * 0.85)), (" LAUGH", paint(RED, uu)),
                           (" AT DAY 1.", paint(WHITE, uu * 0.85))], W / 2, 520 + off, f_p1, 6)
        if main and ts >= P2:
            uu, off = reveal(P2)
            draw_spaced(tc, "THEY CLAP AT", W / 2, 660 + off, f_p2, 6, paint(WHITE, uu))
        if main and ts >= P3:
            uu, off = reveal(P3, 0.3)
            s3 = 1 + 0.3 * (1 - uu)
            draw_spaced(tc, "DAY 1000.", W / 2, 830 + off * 0.3, font(150 * s3, "InterDisplay-Black"), 6, paint(WHITE, uu))

        # composite
        lock_t = tts(LOCK)
        flash = math.exp(-(t - lock_t) * 3.0) if t >= lock_t and main else 0.0
        e = bloom(env.rgb(), (0.9, (4, 0.6), (22, 0.3)))
        gl = bloom(fig.rgb(), (1.0, (5, 0.9), (18, 0.75 + 0.2 * g), (60, 0.45 + 0.25 * g + flash)))
        x_ = bloom(txt.rgb(), (1.0, (6, 0.7), (26, 0.45)))
        hb = bloom(hero.rgb(), (1.0, (4, 0.45), (16, 0.3 + 0.1 * g), (50, 0.22 + 0.12 * g + flash)))
        img = (e + gl + x_ + hb) * master
        if ff:
            # memory look for the flash-forward, then a tape-rewind glitch
            img = img * 0.85
            if t >= T_FF:
                u = (t - T_FF) / (T_RW - T_FF)
                for _ in range(10):
                    y0 = int(rng.integers(0, H - 60))
                    hgt = int(rng.integers(8, 70))
                    img[y0:y0 + hgt] = np.roll(img[y0:y0 + hgt], int(rng.integers(-160, 160) * (0.4 + u)), axis=1)
                img[::4] *= 0.6
                img += (rng.random((H, 1, 1)) < 0.02) * 0.5
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
    m.add_bed(sfx.drone(DUR, rise_at=tts(LOCK)), gain=0.45, fade_in=0.5, fade_out=2.5, stop=DUR)
    m.add(0.05, sfx.text_hit(5), 0.8, 0, 0.4)
    n_m = 0
    for t, kind, pan, extra in events:
        if kind == "ha":
            m.add(t, sfx.laugh(int(t * 100) + extra, int(np.random.default_rng(int(t * 7)).integers(3, 6)),
                               150 + 25 * extra, 0.5), 0.35, 0.25 + 0.15 * extra, 0.35)
        elif kind == "rep":
            ph, k = extra
            if ph == "d1":
                m.add(t + 0.2, sfx.breath(k, 0.6), 0.6, -0.1, 0.2)
                m.add(t + 0.2, sfx.rattle(1.0, k), 0.4, -0.1, 0.2)
            elif ph == "m":
                n_m += 1
                f = 330 * 2 ** (min(n_m, 16) * 1.5 / 12)
                m.add(t, sfx.plate_clank(40 + k, 0.5), 0.35, -0.1, 0.25)
                m.add(t + 0.25, sfx.chime(f, 0.25), 0.35, 0, 0.4)
            else:
                m.add(t, sfx.breath(77, 1.4), 0.6, -0.1, 0.2)
                m.add(t + 0.2, sfx.rattle(1.2, 5), 0.5, -0.1, 0.2)
                m.add(t, sfx.heartbeat(), 0.8, 0, 0.3)
                m.add(t + 0.8, sfx.heartbeat(), 0.9, 0, 0.3)
        elif kind == "drop1":
            m.add(t + 0.2, sfx.plate_clank(31, 0.8), 0.9, -0.1, 0.4)
            m.add(t + 0.35, sfx.power_down(2.2), 0.4, 0, 0.5)
        elif kind == "pick":
            m.add(t - 0.55, sfx.power_up(110), 0.9, 0, 0.4)
            m.add(t - 1.0, sfx.heartbeat(), 0.7, 0, 0.3)
        elif kind == "day":
            m.add(t, sfx.tick(2400, 0.35), 0.4, 0, 0.05)
        elif kind == "lock":
            m.add(t, sfx.boom(3.5), 0.9, 0, 0.5)
        elif kind == "drop":
            m.add(t + 0.22, sfx.plate_clank(99, 2.0), 1.0, 0.1, 0.5)
            m.add(t + 0.25, sfx.applause(5.5, 55, 9), 0.6, 0, 0.35)
        elif kind == "shutter":
            m.add(t, sfx.shutter(extra), 0.35, ((extra * 37) % 11) / 11 - 0.5, 0.2)
    m.add(tts(LOCK) - 2.2, sfx.riser(2.2), 0.45, 0, 0.3)
    m.add(tts(P1), sfx.whoosh(0.5, 800, 9000, 0.5, seed=8), 0.3, -0.2, 0.3)
    m.add(tts(P1) + 0.05, sfx.text_hit(1), 0.45, 0, 0.4)
    m.add(tts(P2), sfx.text_hit(2), 0.65, 0, 0.5)
    m.add(tts(P3), sfx.text_hit(3), 0.95, 0, 0.5)
    m.add(tts(P3), sfx.boom(2.0), 0.4, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}s frames {N} lock {tts(LOCK):.2f} drop {tts(DROP):.2f}")
    if "--stills" in sys.argv:
        ts = [1.0, 2.8, 3.3, 4.4, 5.9, 6.3, 8.5, tts(MONT_A + 4.0), tts(MONT_A + 7.0), tts(FINAL_A + 1.2),
              tts(DROP + 0.8), tts(DROP + 1.4), tts(P3 + 1.0)]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
