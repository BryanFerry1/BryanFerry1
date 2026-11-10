"""EP04 - QUITTER vs RESILIENCE  (the walls)

HOOK   "HE FELL 7 TIMES." / "WATCH WHAT HAPPENED."
       Two figures run into a red wall labelled FAILURE. Both fall.
       QUITTER stays down, sits, hugs his knees and greys out - left behind.
       RESILIENCE gets up - a bit bigger, thicker, brighter - and smashes the
       wall. Next wall (REJECTION, DOUBT, BROKE, ALONE, LOSS...) knocks him
       down again, faster and faster, he grows every time. Wall 7: IMPOSSIBLE.
       Longest, darkest fall. Shockwave rise. Slow-motion break-through. BOOM.
PUNCH  "FALL SEVEN TIMES." / "STAND UP" / "EIGHT."
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import (FPS, H, HEAD_R, RED, WHITE, W, Camera, Layer, Post, VideoWriter,
                    blend_pose, bloom, clamp, dirv, draw_figure, draw_runs, draw_spaced,
                    ease_out, fit_font, font, mix, mux, paint, rotate_pose, run_pose,
                    smoothstep)
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep04_quitter_vs_resilience"
GREY = (0.5, 0.5, 0.53)
dt = 1 / FPS
STRIDE = 2.6

WORDS = ["FAILURE", "REJECTION", "DOUBT", "BROKE", "ALONE", "LOSS", "IMPOSSIBLE"]
HEIGHTS = [2.5, 2.8, 3.0, 3.2, 3.4, 3.6, 4.6]
#            fall  lie   kneel stand speed  gap-to-next
CYC = [(0.50, 1.05, 0.60, 0.45, 6.0, 6.0),
       (0.45, 0.55, 0.45, 0.35, 6.5, 4.6),
       (0.30, 0.12, 0.22, 0.15, 8.0, 4.2),
       (0.28, 0.10, 0.20, 0.14, 8.5, 4.2),
       (0.26, 0.08, 0.18, 0.13, 9.0, 4.2),
       (0.26, 0.08, 0.18, 0.13, 9.0, 5.0),
       (0.60, 1.70, 0.85, 0.45, 7.0, 0.0)]
GROW = 0.08


def sc_after(falls):
    return 1 + GROW * falls


# ------------------------------------------------------------ hero timeline
WALL_X = [10.0]
for c in CYC[:-1]:
    WALL_X.append(WALL_X[-1] + c[5])

SEGS = []          # (kind, t0, t1, data)
t, x = 0.0, 0.0
SEGS.append(("stand", 0.0, 0.6, {"x": 0.0}))
t = 0.6
IMPACTS, BREAKS, RISES = [], [], []
for i, (tf, tl, tk, ts, v, gap) in enumerate(CYC):
    sc = sc_after(i)
    xc = WALL_X[i] - 0.55 * sc
    if i > 0:
        # the charge run from the previous fall already started; it ends at this contact
        pass
    tr = (xc - x) / v
    SEGS.append(("run", t, t + tr, {"x0": x, "x1": xc, "v": v}))
    if i > 0:
        tb = t + (WALL_X[i - 1] - 0.45 * sc - x) / v
        BREAKS.append(tb)
    t += tr
    IMPACTS.append(t)
    xb = xc - 1.0 * sc
    SEGS.append(("fall", t, t + tf, {"x0": xc, "x1": xb, "i": i}))
    t += tf
    SEGS.append(("lie", t, t + tl, {"x": xb, "i": i}))
    t += tl
    SEGS.append(("kneel", t, t + tk, {"x": xb, "i": i}))
    t += tk
    SEGS.append(("rise", t, t + ts, {"x": xb, "i": i}))
    t += ts
    RISES.append(t)
    x = xb
# final charge through IMPOSSIBLE and beyond
v = 7.5
sc = sc_after(len(CYC))
TAU_FBREAK = t + (WALL_X[-1] - 0.45 * sc - x) / v
BREAKS.append(TAU_FBREAK)
SEGS.append(("run", t, t + 40, {"x0": x, "x1": x + v * 40, "v": v}))
TAU_IMP0 = IMPACTS[0]


def rate(tau):
    r = 1.0
    w = smoothstep(TAU_IMP0 - 0.15, TAU_IMP0, tau) * (1 - smoothstep(TAU_IMP0 + 0.35, TAU_IMP0 + 0.55, tau))
    r -= 0.5 * w
    w = smoothstep(TAU_FBREAK - 0.45, TAU_FBREAK - 0.2, tau) * (1 - smoothstep(TAU_FBREAK + 0.35, TAU_FBREAK + 0.6, tau))
    r -= 0.7 * w
    return r


taus = [0.0]
while taus[-1] < TAU_FBREAK:
    taus.append(taus[-1] + rate(taus[-1]) * dt)
T_FBREAK = len(taus) * dt
T_P1 = T_FBREAK + 1.3
T_P2 = T_P1 + 0.9
T_P3 = T_P2 + 0.5
DUR = T_P3 + 2.8
N = int(DUR * FPS)
while len(taus) < N:
    taus.append(taus[-1] + dt)
TAUS = np.array(taus)


def tau_to_t(tau):
    return int(np.searchsorted(TAUS, tau)) * dt


def seg_at(tau):
    for k, s in enumerate(SEGS):
        if s[1] <= tau < s[2]:
            return k, s
    return len(SEGS) - 1, SEGS[-1]


def falls_at(tau):
    return sum(1 for ti in IMPACTS if tau >= ti)


def scale_at(tau):
    """Grows during each rise."""
    sc = 1.0
    for k, s in enumerate(SEGS):
        if s[0] == "rise" and tau >= s[1]:
            sc = sc_after(s[3]["i"]) + GROW * smoothstep(s[1], s[2], tau)
    return sc


# ------------------------------------------------------------ poses
def supine(x):
    hip = np.array([x, 0.24])
    neck = np.array([x - 0.92, 0.3])
    sh = hip + (neck - hip) * 0.86
    return {"hip": hip, "neck": neck, "head": np.array([x - 1.3, 0.31]), "shoulder": sh,
            "knee1": np.array([x + 0.5, 0.66]), "foot1": np.array([x + 1.0, 0.06]),
            "knee2": np.array([x + 0.72, 0.36]), "foot2": np.array([x + 1.4, 0.07]),
            "elbow1": sh + [0.3, -0.18], "hand1": sh + [0.62, -0.22],
            "elbow2": sh + [-0.35, -0.15], "hand2": sh + [-0.75, -0.2]}


def kneel(x, t, head_down=0.35):
    hip = np.array([x, 0.95 + 0.015 * math.sin(t * 5)])
    lean = 0.38
    neck = hip + dirv(lean) * 0.92
    sh = hip + dirv(lean) * 0.79
    k1 = np.array([x + 0.78, 0.83])
    return {"hip": hip, "neck": neck, "head": neck + dirv(lean + head_down) * 0.36, "shoulder": sh,
            "knee1": k1, "foot1": np.array([x + 0.82, 0.03]),
            "knee2": np.array([x - 0.12, 0.1]), "foot2": np.array([x - 0.88, 0.1]),
            "elbow1": sh + [0.32, -0.38], "hand1": k1 + [-0.02, 0.08],
            "elbow2": sh + [0.05, -0.52], "hand2": sh + [0.0, -1.02]}


def sit_hug(x, t):
    hip = np.array([x, 0.2])
    lean = 0.55
    neck = hip + dirv(lean) * 0.92
    sh = hip + dirv(lean) * 0.79
    k1 = np.array([x + 0.5, 0.76])
    return {"hip": hip, "neck": neck, "head": neck + dirv(lean + 1.0) * 0.36, "shoulder": sh,
            "knee1": k1, "foot1": np.array([x + 0.82, 0.04]),
            "knee2": k1 + [-0.06, -0.04], "foot2": np.array([x + 0.74, 0.04]),
            "elbow1": sh + [0.42, -0.25], "hand1": k1 + [0.12, -0.1],
            "elbow2": sh + [0.36, -0.3], "hand2": k1 + [0.08, -0.16]}


def scale_pose(j, x, sc):
    return {k: np.array([x + (v[0] - x) * sc, v[1] * sc]) for k, v in j.items()}


class Fragments:
    def __init__(self):
        self.f = []
        self.rng = np.random.default_rng(3)

    def burst(self, xw, hw, power, n):
        r = self.rng
        for _ in range(n):
            y = r.uniform(0.1, hw)
            self.f.append([xw + r.uniform(-0.25, 0.25), y, r.uniform(2, 7) * power, r.uniform(-1, 4.5) * power,
                           r.uniform(0, 6), r.uniform(-12, 12), r.uniform(0.07, 0.24), 0.0, r.uniform(0.9, 1.6)])

    def step(self, dtau):
        for p in self.f:
            p[3] -= 11 * dtau
            p[0] += p[2] * dtau
            p[1] += p[3] * dtau
            if p[1] < 0.05:
                p[1], p[3], p[2] = 0.05, -p[3] * 0.3, p[2] * 0.6
            p[4] += p[5] * dtau
            p[7] += dtau
        self.f = [p for p in self.f if p[7] < p[8]]

    def draw(self, c, cam):
        for x, y, vx, vy, ang, av, size, age, life in self.f:
            a = (1 - age / life) ** 1.2
            cx, cy = cam.pt((x, y))
            hs = size * cam.s / 2
            path = skia.Path()
            for k in range(4):
                th = ang + k * math.pi / 2 + math.pi / 4
                pt = (cx + math.cos(th) * hs * 1.4, cy + math.sin(th) * hs)
                (path.moveTo if k == 0 else path.lineTo)(*pt)
            path.close()
            c.drawPath(path, paint(RED, a))


def render(stills=None):
    os.makedirs(OUT, exist_ok=True)
    env, fig, txt = Layer(), Layer(), Layer()
    post = Post()
    frags = Fragments()
    events = []
    writer = None if stills else VideoWriter(os.path.join(OUT, NAME + "_video.mp4"))
    f_lab = font(30, "Inter-Bold")
    f_wall = font(30, "Inter-Black")
    f_cap = font(24, "Inter-SemiBold")
    f_num = font(110, "InterDisplay-Bold")
    f_h1 = font(104, "InterDisplay-Black")
    f_h2 = fit_font("WATCH WHAT HAPPENED.", 46, "InterDisplay-Bold", 6, 940)
    f_p1 = fit_font("FALL SEVEN TIMES.", 64, "InterDisplay-Bold", 6, 940)
    f_p2 = fit_font("STAND UP", 150, "InterDisplay-Black", 6, 980)
    f_p3 = font(170, "InterDisplay-Black")

    cam = Camera()
    cam.s, cam.sx, cam.sy, cam.wy = 116.0, W * 0.42, 1450.0, 0.0
    cam.wx = 1.5
    phase = 0.0
    q_phase = 0.4
    prev_tau = 0.0
    frozen = {}
    broken = [False] * len(WORDS)
    done_imp, done_rise = 0, 0
    contact_prev = [None, None]
    shake = 0.0
    rings = []
    q_state = None
    q_x = -1.4
    for fi in range(N):
        t = fi * dt
        tau = taus[fi]
        dtau = tau - prev_tau
        prev_tau = tau
        draw_now = stills is None or fi in stills

        # ---------------- hero
        k, (kind, t0, t1, d) = seg_at(tau)
        u = clamp((tau - t0) / max(t1 - t0, 1e-6))
        sc = scale_at(tau)
        falls = falls_at(tau)
        if kind == "stand":
            hx = d["x"]
            j = run_pose(hx, phase, 0.0, 0, 0.15)
        elif kind == "run":
            hx = d["x0"] + d["v"] * (tau - t0)
            ramp = smoothstep(t0, t0 + 0.25, tau)
            phase += (d["v"] / (STRIDE * sc)) * 2 * math.pi * dtau
            j = run_pose(hx, phase, 0.95 * ramp + 0.0, 0, 0.1 * ramp)
            if kind == "run" and k > 0 and SEGS[k - 1][0] == "rise":
                prev = SEGS[k - 1][3]["x"]
                j = blend_pose(run_pose(hx, phase, 0.0), j, smoothstep(t0, t0 + 0.2, tau))
        elif kind == "fall":
            if k not in frozen:
                jf = run_pose(d["x0"], phase, 0.95)
                pivot = jf["foot1"] if jf["foot1"][0] < jf["foot2"][0] else jf["foot2"]
                frozen[k] = (jf, pivot.copy())
            jf, pivot = frozen[k]
            hx = d["x0"] + (d["x1"] - d["x0"]) * ease_out(u)
            rot = rotate_pose(jf, pivot, 1.45 * ease_out(min(1, u * 1.3)))
            rot = {kk: v + [hx - d["x0"], 0] for kk, v in rot.items()}
            j = blend_pose(rot, supine(hx), smoothstep(0.35, 1.0, u))
        elif kind == "lie":
            hx = d["x"]
            j = supine(hx)
            j = {kk: v + [0, 0.012 * math.sin(t * 6)] for kk, v in j.items()}
        elif kind == "kneel":
            hx = d["x"]
            j = blend_pose(supine(hx), kneel(hx, t), ease_out(u))
        else:  # rise
            hx = d["x"]
            j = blend_pose(kneel(hx, t), run_pose(hx, phase, 0.0, 0, 0.0, -0.15), ease_out(u))
        j = scale_pose(j, hx, sc)

        # events
        while done_imp < len(IMPACTS) and tau >= IMPACTS[done_imp]:
            events.append((t, "impact", 0, done_imp))
            shake = 1.0 if done_imp in (0, len(IMPACTS) - 1) else 0.55
            done_imp += 1
        while done_rise < len(RISES) and tau >= RISES[done_rise]:
            events.append((t, "rise", 0, done_rise))
            rings.append([tau, hx, sc])
            done_rise += 1
        for i, tb in enumerate(BREAKS):
            wi = i  # BREAKS[i] breaks wall i
            if not broken[wi] and tau >= tb:
                broken[wi] = True
                final = wi == len(WORDS) - 1
                frags.burst(WALL_X[wi], HEIGHTS[wi], 1.5 if final else 1.0, 170 if final else 55)
                events.append((t, "break", 0, wi))
                shake = max(shake, 1.2 if final else 0.6)
        frags.step(dtau)
        shake = max(0.0, shake - dtau * 2.5)
        if kind == "run":
            for leg in range(2):
                c = math.floor((phase + leg * math.pi - 1.87) / (2 * math.pi))
                if contact_prev[leg] is not None and c != contact_prev[leg]:
                    events.append((t, "step", 0, sc))
                contact_prev[leg] = c

        # ---------------- quitter
        q_imp = TAU_IMP0 + 0.12
        if tau < 0.6:
            jq = run_pose(q_x, q_phase, 0.0, 0, 0.15)
        elif tau < q_imp:
            q_x = -1.4 + 6.0 * (tau - 0.6)
            q_phase += (6.0 / STRIDE) * 2 * math.pi * dtau
            jq = run_pose(q_x, q_phase, 0.9)
            q_contact = q_x
        else:
            if q_state is None:
                jf = run_pose(q_x, q_phase, 0.9)
                pv = jf["foot1"] if jf["foot1"][0] < jf["foot2"][0] else jf["foot2"]
                q_state = (jf, pv.copy(), q_x)
            jf, pv, qx0 = q_state
            uq = (tau - q_imp) / 0.5
            qx = qx0 - 1.7 * ease_out(min(1, uq))
            rot = rotate_pose(jf, pv, 1.45 * ease_out(min(1, uq * 1.3)))
            rot = {kk: v + [qx - qx0, 0] for kk, v in rot.items()}
            jq = blend_pose(rot, supine(qx), smoothstep(0.35, 1.0, uq))
            jq = blend_pose(jq, sit_hug(qx - 0.4, t), smoothstep(q_imp + 1.3, q_imp + 2.3, tau))
            q_x = qx
        q_give = smoothstep(q_imp + 1.3, q_imp + 3.0, tau)
        qcol = mix(WHITE, GREY, q_give)

        # ---------------- camera
        target = hx * 1.0 + 0.9
        if not cam.init:
            cam.wx, cam.init = target, True
        cam.wx += (target - cam.wx) * 0.12
        if not draw_now:
            continue

        # ================================================= draw
        for L in (env, fig, txt):
            L.clear()
        master = smoothstep(0, 0.35, t) * (1 - smoothstep(DUR - 0.35, DUR, t))
        sxs, sys_ = shake * 16 * math.sin(t * 87), shake * 12 * math.sin(t * 71)
        c0 = Camera()
        c0.s, c0.wx, c0.wy, c0.sx, c0.sy = cam.s, cam.wx, 0.0, cam.sx + sxs, cam.sy + sys_
        # darkness during the last, longest fall
        dark = 0.0
        for kk, s in enumerate(SEGS):
            if s[0] == "lie" and s[3]["i"] == len(WORDS) - 1:
                dark = smoothstep(s[1] - 0.3, s[1] + 0.4, tau) * (1 - smoothstep(s[2] + 0.3, s[2] + 1.2, tau))
        env.canvas.drawLine(0, c0.sy, W, c0.sy, paint(WHITE, 0.6 * (1 - 0.5 * dark), 2.5))
        # scrolling ground ticks
        step = 1.5
        k0 = math.floor((c0.wx - c0.sx / c0.s) / step) - 1
        for kk in range(k0, k0 + int(W / (step * c0.s)) + 3):
            sx, _ = c0.pt((kk * step, 0))
            env.canvas.drawLine(sx, c0.sy + 10, sx - 22, c0.sy + 26, paint(WHITE, 0.16 * (1 - dark), 2))
        # walls
        for i, (xw, hw, word) in enumerate(zip(WALL_X, HEIGHTS, WORDS)):
            if broken[i]:
                continue
            l, tp = c0.pt((xw - 0.27, hw))
            r, b = c0.pt((xw + 0.27, 0))
            if r < -50 or l > W + 50:
                continue
            fig.canvas.drawRect(skia.Rect(l, tp, r, b), paint(RED, 0.14))
            fig.canvas.drawRect(skia.Rect(l, tp, r, b), paint(RED, 0.95, max(2, 0.06 * c0.s), cap=False))
            for yy in np.arange(0.6, hw, 0.6):
                _, y = c0.pt((0, yy))
                fig.canvas.drawLine(l, y, r, y, paint(RED, 0.35, 1.5))
            fw = f_wall if word != "IMPOSSIBLE" else font(40, "Inter-Black")
            draw_spaced(txt.canvas, word, (l + r) / 2, tp - 22, fw, 5, paint(RED, 0.95))
        frags.draw(fig.canvas, c0)
        # quitter
        qa = 1 - 0.45 * q_give
        draw_figure(env.canvas, jq, c0, qcol, qa)
        qhx, _ = c0.pt(jq["hip"])
        draw_spaced(txt.canvas, "QUITTER", qhx, c0.sy + 96, f_lab, 6, paint(qcol, qa * smoothstep(0.2, 0.7, t)))
        # rise shockwaves
        for rt, rx, rsc in rings:
            age = tau - rt
            if age < 0.7:
                big = 2.0 if rsc >= sc_after(len(WORDS) - 1) else 1.0
                cx, cy = c0.pt((rx, 1.3 * rsc))
                rr = (0.6 + 4.0 * ease_out(age / 0.7)) * c0.s * big
                fig.canvas.drawCircle(cx, cy, rr, paint(WHITE, 0.55 * (1 - age / 0.7), 3 + 3 * big))
        # hero
        draw_figure(fig.canvas, j, c0, WHITE, 1.0, 0.6, thick=1 + 0.13 * (sc - 1) / GROW, head_scale=1 + 0.03 * (sc - 1) / GROW)
        hhx, _ = c0.pt(j["hip"])
        la = smoothstep(0.2, 0.7, t) * (1 - smoothstep(T_P1 - 0.6, T_P1, t))
        draw_spaced(txt.canvas, "RESILIENCE", hhx, c0.sy + 52, f_lab, 6, paint(WHITE, la))

        # HUD
        hook_a = smoothstep(0.05, 0.3, t) * (1 - smoothstep(2.0, 2.35, t))
        hud_a = smoothstep(2.2, 2.6, t) * (1 - 0.55 * smoothstep(T_P1 - 0.3, T_P1 + 0.3, t))
        draw_spaced(txt.canvas, "FALLS", W / 2, 236, f_cap, 12, paint(WHITE, 0.7 * hud_a))
        pop = 1.0
        if falls > 0:
            age = tau - IMPACTS[falls - 1]
            pop = 1 + 0.25 * math.exp(-age * 8)
        draw_spaced(txt.canvas, str(falls), W / 2, 350, font(110 * pop, "InterDisplay-Bold"), 4, paint(RED, hud_a))

        # hook
        if hook_a > 0.01:
            for L in (env, fig):
                L.canvas.drawRect(skia.Rect(0, 470, W, 760), paint((0, 0, 0), 0.9 * hook_a))
            env.canvas.drawLine(90, 472, W - 90, 472, paint(RED, 0.6 * hook_a, 2))
            env.canvas.drawLine(90, 758, W - 90, 758, paint(RED, 0.6 * hook_a, 2))
            pop = 1 + 0.08 * (1 - ease_out((t - 0.05) / 0.3))
            draw_runs(txt.canvas, [("HE FELL", paint(WHITE, hook_a)), (" 7", paint(RED, hook_a)),
                                   (" TIMES.", paint(WHITE, hook_a))], W / 2, 630, font(104 * pop, "InterDisplay-Black"), 3)
            draw_spaced(txt.canvas, "WATCH WHAT HAPPENED.", W / 2, 715, f_h2, 6, paint(WHITE, 0.85 * hook_a))

        # punchline
        tc = txt.canvas

        def reveal(t0, dd=0.4):
            uu = ease_out((t - t0) / dd)
            return uu, (1 - uu) * 34
        if t >= T_P1:
            uu, off = reveal(T_P1)
            draw_spaced(tc, "FALL SEVEN TIMES.", W / 2, 450 + off, f_p1, 6, paint(WHITE, uu * 0.85))
        if t >= T_P2:
            uu, off = reveal(T_P2)
            draw_spaced(tc, "STAND UP", W / 2, 610 + off, f_p2, 6, paint(WHITE, uu))
        if t >= T_P3:
            uu, off = reveal(T_P3, 0.3)
            s3 = 1 + 0.3 * (1 - uu)
            draw_spaced(tc, "EIGHT.", W / 2, 775 + off * 0.3, font(170 * s3, "InterDisplay-Black"), 8, paint(RED, uu))

        # composite
        flash = math.exp(-(t - T_FBREAK) * 2.8) if t >= T_FBREAK else 0.0
        power = 0.1 * (sc - 1) / GROW
        e = bloom(env.rgb(), (0.9, (4, 0.6), (22, 0.3)))
        g = bloom(fig.rgb(), (1.0, (5, 0.9 + 0.05 * power), (18, 0.8 + 0.08 * power), (60, 0.5 + 0.08 * power + flash)))
        x_ = bloom(txt.rgb(), (1.0, (6, 0.7), (26, 0.45)))
        img = (e + g * (1 - 0.35 * dark) + x_) * master * (1 - 0.4 * dark)
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
    m.add_bed(sfx.drone(DUR, rise_at=T_FBREAK), gain=0.5, fade_in=0.8, fade_out=2.5, stop=DUR)
    m.add(0.05, sfx.text_hit(5), 0.9, 0, 0.4)
    m.add(1.95, sfx.whoosh(0.5, 300, 7000, 0.6, seed=3), 0.35, 0, 0.3)
    last = len(WORDS) - 1
    for t, kind, pan, extra in events:
        if kind == "step":
            m.add(t, sfx.step_heavy(int(t * 91)), 0.18 + 0.12 * (extra - 1) / (GROW * 7), 0.1, 0.15)
        elif kind == "impact":
            g = 1.0 if extra in (0, last) else 0.7
            m.add(t, sfx.body_fall(), g, 0, 0.4)
            m.add(t, sfx.text_hit(extra), 0.6 * g, 0, 0.4)
            m.add(t + 0.03, sfx.glitch(extra), 0.4, 0, 0.2)
            m.add(t, sfx.tick(1600, 0.5), 0.5, 0, 0.1)
            if extra in (0, 1, last):
                m.add(t + 0.7, sfx.heartbeat(), 0.8, 0, 0.3)
            if extra == last:
                m.add(t + 1.6, sfx.heartbeat(), 0.9, 0, 0.3)
        elif kind == "rise":
            f = 110 * 2 ** (extra * 2 / 12)
            m.add(t - 0.55, sfx.power_up(f), 0.75 if extra != last else 1.0, 0, 0.4)
        elif kind == "break":
            if extra == last:
                m.add(t, sfx.shatter(9, 2.0), 1.0, 0, 0.5)
                m.add(t, sfx.boom(4.0), 1.0, 0, 0.5)
                m.add(t, sfx.sparkle(2.0), 0.5, 0, 0.6)
            else:
                m.add(t, sfx.shatter(extra, 1.0), 0.8, 0.15, 0.35)
    m.add(T_FBREAK - 2.4, sfx.riser(2.4), 0.5, 0, 0.3)
    m.add(T_P1, sfx.whoosh(0.5, 800, 9000, 0.5, seed=8), 0.35, -0.2, 0.3)
    m.add(T_P1 + 0.05, sfx.text_hit(1), 0.45, 0, 0.4)
    m.add(T_P2, sfx.text_hit(2), 0.7, 0, 0.5)
    m.add(T_P3, sfx.text_hit(3), 0.95, 0, 0.5)
    m.add(T_P3, sfx.boom(2.0), 0.4, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}s frames {N} impacts {[round(tau_to_t(x), 2) for x in IMPACTS]} final {T_FBREAK:.2f}")
    if "--stills" in sys.argv:
        ts = [1.0, tau_to_t(TAU_IMP0) + 0.2, tau_to_t(TAU_IMP0) + 1.2, tau_to_t(RISES[0]) + 0.05,
              tau_to_t(BREAKS[0]) + 0.1, tau_to_t(IMPACTS[1]) + 0.4, tau_to_t(IMPACTS[3]) + 0.1,
              tau_to_t(IMPACTS[6]) + 1.0, tau_to_t(RISES[6]) + 0.05, T_FBREAK + 0.1, T_FBREAK + 0.8, T_P3 + 1.2]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
