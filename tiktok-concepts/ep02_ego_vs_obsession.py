"""EP02 - EGO vs OBSESSION  (the race)

Split screen, ~23 s, 1080x1920:
  TOP    EGO races among grey rivals. A red dashed sight-line shows who he is
         staring at; a RANK counter flips constantly. He sprints, gloats,
         looks back... and trips. The rivals run off. His lane goes dark.
  BOTTOM OBSESSION races a faint ghost of himself labelled YESTERDAY. Each time
         he passes it, the ghost dissolves, DAY ticks up and a new ghost
         appears. Faster and faster.
  Then the bottom lane takes the whole screen, final pass in slow motion,
  BOOM, punchline:
         "EGO COMPETES WITH OTHERS."  /  "OBSESSION"  /  "COMPETES WITH YESTERDAY."
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import (FPS, H, HEAD_R, RED, WHITE, W, Camera, Layer, Particles, Post,
                    VideoWriter, blend_pose, bloom, build_pose, clamp, dashed, dirv,
                    draw_figure, draw_runs, draw_spaced, ease_out, fit_font, font, mix,
                    mux, paint, pose_points, rotate_pose, run_pose, smoothstep)
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep02_ego_vs_obsession"
GREY = (0.55, 0.55, 0.58)
dt = 1 / FPS

# ------------------------------------------------------------ script (sim time tau)
GO = 1.2
STRIDE = 2.6
V_E = 6.0
TRIP = 8.7


def keys(tau, kf):
    if tau <= kf[0][0]:
        return kf[0][1]
    for (t0, v0), (t1, v1) in zip(kf, kf[1:]):
        if tau <= t1:
            u = (tau - t0) / (t1 - t0)
            u = u * u * (3 - 2 * u)
            return v0 + (v1 - v0) * u
    return kf[-1][1]


RIVALS = [  # keyframes of position relative to Ego, depth row
    ([(0, -1.5), (GO, -1.5), (2.2, 0.3), (3.4, 1.9), (4.9, -1.4), (6.5, -2.2), (8.0, -0.6), (8.7, -1.2)], 1),
    ([(0, -2.9), (GO, -2.9), (3.0, -0.8), (4.9, -2.0), (6.0, 0.4), (7.0, 1.6), (8.0, 0.8), (8.7, -0.6)], 2),
    ([(0, -4.2), (GO, -4.2), (3.0, -1.2), (5.0, -2.6), (6.2, -0.2), (7.2, 2.2), (8.7, 2.6)], 1),
]
ROWS = {1: (0.86, 62), 2: (0.74, 118)}   # scale factor, screen-up offset px
LOOKS = [(0, 2.6, 3.6), (0, 4.6, 5.4), (1, 6.2, 6.9), (2, 7.0, 7.6), (1, 8.1, TRIP + 0.05)]
BURSTS = [(3.3, 4.9), (7.4, 8.6)]


def rival_rel(i, tau):
    kf, _ = RIVALS[i]
    r = keys(tau, kf)
    if tau > TRIP:
        r += 0.5 * (tau - TRIP)
    return r


def ego_x_nominal(tau):
    return V_E * max(0.0, tau - GO)


def ego_x(tau):
    if tau <= TRIP:
        return ego_x_nominal(tau)
    return ego_x_nominal(TRIP) + V_E * 0.32 * (1 - math.exp(-(tau - TRIP) / 0.32))


def burst(tau):
    return max(smoothstep(a - 0.2, a + 0.2, tau) * (1 - smoothstep(b - 0.2, b + 0.2, tau)) for a, b in BURSTS)


def look(tau):
    """(target index, strength) of Ego's current stare."""
    for tgt, a, b in LOOKS:
        if a - 0.1 <= tau <= b + 0.15:
            return tgt, smoothstep(a - 0.1, a + 0.1, tau) * (1 - smoothstep(b, b + 0.15, tau))
    return None, 0.0


# bottom lane: ghost cycles
CYC_D = [2.8, 2.4, 2.1, 1.7] + [0.55] * 8 + [1.9]
CYC_DELTA = [1.0, 1.8, 1.8, 1.8] + [1.4] * 8 + [2.2]
DAYS = [1, 2, 3, 4, 5, 9, 17, 33, 60, 100, 160, 250, 320, 365]
CYC_START = [GO]
for d in CYC_D[:-1]:
    CYC_START.append(CYC_START[-1] + d)
TAU_FINAL_END = CYC_START[-1] + CYC_D[-1]
GHOST_END = -0.9


def ghost_rel(i, tau):
    u = clamp((tau - CYC_START[i]) / CYC_D[i])
    e = u * u * (3 - 2 * u) if i < len(CYC_D) - 1 else u ** 1.4
    return CYC_DELTA[i] + (GHOST_END - CYC_DELTA[i]) * e


def pass_time(i):
    lo, hi = CYC_START[i], CYC_START[i] + CYC_D[i]
    for _ in range(40):
        mid = (lo + hi) / 2
        if ghost_rel(i, mid) > 0:
            lo = mid
        else:
            hi = mid
    return lo


TAU_FPASS = pass_time(len(CYC_D) - 1)
TAU_SPLIT_A, TAU_SPLIT_B = 11.4, 12.6


def v_obs(tau):
    if tau <= GO:
        return 0.0
    return 6.0 + 3.2 * smoothstep(GO + 2, TAU_FPASS, tau)


def rate(tau):
    r = 1.0
    w = smoothstep(TRIP - 0.25, TRIP - 0.05, tau) * (1 - smoothstep(TRIP + 0.4, TRIP + 0.65, tau))
    r -= (1 - 0.45) * w
    w = smoothstep(TAU_FPASS - 0.6, TAU_FPASS - 0.3, tau) * (1 - smoothstep(TAU_FPASS + 0.35, TAU_FPASS + 0.7, tau))
    r -= (1 - 0.28) * w
    return max(r, 0.25)


taus = [0.0]
while taus[-1] < TAU_FINAL_END:
    taus.append(taus[-1] + rate(taus[-1]) * dt)
T_FINAL = len(taus) * dt
T_PUNCH1 = T_FINAL + 0.9
T_PUNCH2 = T_PUNCH1 + 1.3
DUR = T_PUNCH2 + 3.2
N = int(DUR * FPS)
while len(taus) < N:
    taus.append(taus[-1] + dt)
TAUS = np.array(taus)


def tau_to_t(tau):
    return int(np.searchsorted(TAUS, tau)) * dt


# ------------------------------------------------------------ special poses
def lying_pose(x):
    hip = np.array([x, 0.24])
    neck = np.array([x + 0.92, 0.3])
    head = np.array([x + 1.3, 0.31])
    sh = hip + (neck - hip) * 0.86
    return {"hip": hip, "neck": neck, "head": head, "shoulder": sh,
            "knee1": np.array([x - 0.78, 0.13]), "foot1": np.array([x - 1.56, 0.12]),
            "knee2": np.array([x - 0.62, 0.42]), "foot2": np.array([x - 1.32, 0.2]),
            "elbow1": sh + [0.42, -0.08], "hand1": sh + [0.92, -0.17],
            "elbow2": sh + [0.15, -0.12], "hand2": sh + [0.6, -0.17]}


def kneel_pose(x, t):
    br = 0.02 * math.sin(t * 5)
    hip = np.array([x + 0.2, 0.82 + br])
    lean = 0.55
    neck = hip + dirv(lean) * 0.92
    head = neck + dirv(lean + 0.9) * 0.36
    sh = hip + dirv(lean) * 0.79
    return {"hip": hip, "neck": neck, "head": head, "shoulder": sh,
            "knee1": np.array([x + 0.55, 0.13]), "foot1": np.array([x - 0.25, 0.1]),
            "knee2": np.array([x + 0.42, 0.13]), "foot2": np.array([x - 0.38, 0.1]),
            "elbow1": sh + [0.18, -0.55], "hand1": sh + [0.4, -1.05],
            "elbow2": sh + [0.08, -0.56], "hand2": sh + [0.28, -1.06]}


# ------------------------------------------------------------ drawing helpers
def lane_cam(s, wx, sx, ground_sy):
    c = Camera()
    c.s, c.wx, c.wy, c.sx, c.sy = s, wx, 0.0, sx, ground_sy
    return c


def draw_track(canvas, cam, y0, y1, alpha, start_alpha):
    gy = cam.sy
    canvas.drawLine(0, gy, W, gy, paint(WHITE, 0.7 * alpha, max(1.5, 0.04 * cam.s)))
    # distance ticks scrolling with the world
    step = 1.5
    k0 = math.floor((cam.wx - cam.sx / cam.s) / step) - 1
    k1 = math.ceil((cam.wx + (W - cam.sx) / cam.s) / step) + 1
    for k in range(k0, k1):
        sx, _ = cam.pt((k * step, 0))
        canvas.drawLine(sx, gy + 10, sx - 0.25 * cam.s, gy + 0.28 * cam.s, paint(WHITE, 0.18 * alpha, 2))
    lane2 = gy + 0.55 * cam.s
    if lane2 < y1:
        canvas.drawLine(0, lane2, W, lane2, dashed(WHITE, 0.12 * alpha, 2, 30, 26, -cam.wx * cam.s))
    if start_alpha > 0:
        sx, _ = cam.pt((0.9, 0))
        canvas.drawLine(sx, gy - 2, sx - 0.5 * cam.s, gy + 0.5 * cam.s, paint(WHITE, 0.6 * start_alpha, 0.09 * cam.s))


class Streaks:
    def __init__(self, n=40, seed=8):
        r = np.random.default_rng(seed)
        self.y = r.uniform(0, 1, n)
        self.o = r.uniform(0, 1, n)
        self.l = r.uniform(0.5, 1.4, n)
        self.a = r.uniform(0.04, 0.16, n)

    def draw(self, canvas, y0, y1, scroll, amount):
        if amount <= 0.01:
            return
        for y, o, l, a in zip(self.y, self.o, self.l, self.a):
            sy = y0 + (y1 - y0) * (0.12 + 0.8 * y)
            length = 120 * l * amount
            x = W + 200 - ((scroll * (0.5 + l) + o * (W + 400)) % (W + 400))
            canvas.drawLine(x, sy, x + length, sy, paint(WHITE, a * amount, 2))


def render(stills=None):
    os.makedirs(OUT, exist_ok=True)
    env, fig, txt = Layer(), Layer(), Layer()
    post = Post()
    pe, po = Particles(5), Particles(6)
    streaks = Streaks()
    events = []
    writer = None if stills else VideoWriter(os.path.join(OUT, NAME + "_video.mp4"))

    f_lab = font(30, "Inter-Bold")
    f_lab_s = font(24, "Inter-Bold")
    f_cap = font(24, "Inter-SemiBold")
    f_num = font(92, "InterDisplay-Bold")
    f_p1 = fit_font("EGO COMPETES WITH OTHERS.", 44, "Inter-SemiBold", 4, 940)
    f_p2 = fit_font("OBSESSION", 132, "InterDisplay-Black", 4, 960)
    f_p3 = fit_font("COMPETES WITH YESTERDAY.", 60, "InterDisplay-Bold", 6, 960)

    ph = {"E": 0.0, "R0": 0.7, "R1": 2.1, "R2": 4.0, "O": 0.0, "G": 0.5}
    contact = {k: 0 for k in ph}
    ox = 0.0
    prev_tau = 0.0
    last_rank, last_day, cyc_done = 3, 1, 0
    ghost_vis = {}
    fall_pivot = None
    trip_frozen = None
    look_prev = None
    redness = 0.0
    oglow = 0.0
    for fi in range(N):
        t = fi * dt
        tau = taus[fi]
        dtau = tau - prev_tau
        prev_tau = tau
        draw_now = stills is None or fi in stills

        # ---------------- split geometry
        wsplit = smoothstep(TAU_SPLIT_A, TAU_SPLIT_B, tau)
        split = 960 * (1 - wsplit)

        # ---------------- top lane simulation
        run_in = smoothstep(GO, GO + 0.35, tau)
        bu = burst(tau)
        ex = ego_x(tau)
        e_rate = (V_E / STRIDE) * 2 * math.pi * (1 + 0.35 * bu) * run_in
        if tau > TRIP:
            e_rate *= max(0, 1 - (tau - TRIP) / 0.25)
        ph["E"] += e_rate * dtau
        for i in range(3):
            ph[f"R{i}"] += (6.3 / STRIDE) * 2 * math.pi * run_in * dtau
        tgt, lk = look(tau)
        tgt_rel = rival_rel(tgt, tau) if tgt is not None else 0
        looking_back = lk * (1.0 if tgt is not None and tgt_rel < 0 else 0.0)
        if tgt is not None and look_prev != tgt and lk > 0.05:
            events.append((t, "lock", 0, tgt))
            redness = min(0.65, redness + 0.13)
        look_prev = tgt if lk > 0.05 else None
        inten_e = (0.85 + 0.25 * bu) * run_in
        je = run_pose(ex, ph["E"], inten_e, 0, 0.12 * bu - 0.22 * looking_back, -0.9 * looking_back + 0.25 * lk * (1 - looking_back))
        if tau > TRIP:
            if trip_frozen is None:
                trip_frozen = je
                fall_pivot = je["foot1"] if je["foot1"][0] > je["foot2"][0] else je["foot2"]
                fall_pivot = fall_pivot.copy()
                events.append((t, "trip", 0, 0))
            u = (tau - TRIP)
            slide = ex - ego_x(TRIP)
            rot = rotate_pose(trip_frozen, fall_pivot, -1.35 * ease_out(u / 0.42))
            rot = {k: v + [slide, 0] for k, v in rot.items()}
            jl = lying_pose(ex + 0.2)
            je = blend_pose(rot, jl, smoothstep(0.22, 0.6, u))
            je = blend_pose(je, kneel_pose(ex + 0.2, t), smoothstep(2.0, 3.0, u))
            redness = min(0.92, redness + dtau * 0.8)
        rivals = []
        for i in range(3):
            rx = ego_x_nominal(tau) + rival_rel(i, tau) if tau > GO else rival_rel(i, tau) - 0.0
            jr = run_pose(rx, ph[f"R{i}"], 0.9 * run_in, 0, 0.0)
            rivals.append((jr, RIVALS[i][1], rx))
        rank = 1 + sum(1 for i in range(3) if (rival_rel(i, tau) > 0.15 or (tau > TRIP + 0.2)))
        if tau > GO + 0.2 and rank != last_rank:
            events.append((t, "rank", 0, rank))
            last_rank = rank

        # ---------------- bottom lane simulation
        vo = v_obs(tau)
        ox += vo * dtau
        oglow = max(0.0, oglow - dtau * 1.5)
        ph["O"] += (vo / STRIDE) * 2 * math.pi * dtau if tau > GO else 0
        ph["G"] += (vo / STRIDE) * 2 * math.pi * dtau if tau > GO else 0
        inten_o = smoothstep(GO, GO + 0.3, tau) * (0.85 + 0.2 * smoothstep(GO, TAU_FPASS, tau))
        jo = run_pose(ox, ph["O"], inten_o, 0, 0.0, 0.05)
        ci = None
        for i in range(len(CYC_D)):
            if CYC_START[i] <= tau < CYC_START[i] + CYC_D[i]:
                ci = i
        if tau <= GO:
            ci, grel, galpha = 0, CYC_DELTA[0], 1.0
        elif ci is not None:
            grel = ghost_rel(ci, tau)
            galpha = smoothstep(CYC_START[ci], CYC_START[ci] + 0.22, tau) if ci > 0 else 1.0
        else:
            grel, galpha = None, 0.0
        # cycle completions -> dissolve
        while cyc_done < len(CYC_D) and tau >= CYC_START[cyc_done] + CYC_D[cyc_done]:
            gx_end = ox + GHOST_END
            jg_end = run_pose(gx_end, ph["G"], inten_o)
            segs = pose_points(jg_end)
            pts = []
            n = 260 if cyc_done == len(CYC_D) - 1 else 90
            for _ in range(n):
                a, b = segs[po.rng.integers(len(segs))]
                u = po.rng.random()
                pts.append(jg_end[a] * (1 - u) + jg_end[b] * u)
            final = cyc_done == len(CYC_D) - 1
            po.emit(np.array(pts), vel=(vo * 0.55, 0.5 if not final else 1.2), spread=0.5 if not final else 1.3,
                    life=(0.5, 1.1) if not final else (1.2, 2.4), size=(0.02, 0.05))
            events.append((t, "pass", 0, cyc_done))
            oglow = 1.0 if final else 0.45
            cyc_done += 1
        day = DAYS[cyc_done]
        if day != last_day:
            last_day = day
        jg = run_pose(ox + grel, ph["G"], inten_o) if grel is not None else None

        pe.step(dtau)
        po.step(dtau)

        # footstep contacts
        for k, phase, gain in (("E", ph["E"], 1), ("O", ph["O"], 1)):
            for leg in range(2):
                c = math.floor((phase + leg * math.pi - (math.pi / 2 + 0.3)) / (2 * math.pi))
                key = k + str(leg)
                if contact.get(key) is None:
                    contact[key] = c
                if c != contact[key]:
                    contact[key] = c
                    if (k == "E" and tau < TRIP) or (k == "O" and tau > GO):
                        events.append((t, "step_" + k, 0, wsplit))

        if not draw_now:
            continue

        # ================================================= draw
        for L in (env, fig, txt):
            L.clear()
        master = smoothstep(0, 0.6, t) * (1 - smoothstep(DUR - 0.35, DUR, t))

        # ---------------- TOP LANE
        if split > 2:
            top_dim = 1 - 0.6 * smoothstep(TRIP + 1.2, TRIP + 2.6, tau)
            gsy = split - 960 * 0.18
            yo = split - 960
            cam = lane_cam(112, ex + 0.6, W * 0.42, gsy)
            for L in (env, fig, txt):
                L.canvas.save()
                L.canvas.clipRect(skia.Rect(0, 0, W, split))
            # back rows (parallax)
            for row in (2, 1):
                sc, up = ROWS[row]
                rc = lane_cam(112 * sc, cam.wx, cam.sx, gsy - up)
                env.canvas.drawLine(0, rc.sy, W, rc.sy, paint(WHITE, 0.16 * top_dim, 1.5))
            for jr, row, rx in sorted(rivals, key=lambda r: -r[1]):
                sc, up = ROWS[row]
                rc = lane_cam(112 * sc, cam.wx, cam.sx, gsy - up)
                draw_figure(env.canvas, jr, rc, GREY, 0.55 * top_dim, 0.6)
            draw_track(env.canvas, cam, 0, split, top_dim, 1 - smoothstep(GO, GO + 0.5, tau))
            ecol = mix(WHITE, RED, redness)
            draw_figure(fig.canvas, je, cam, ecol, top_dim * (0.75 + 0.25 * (1 - smoothstep(TRIP, TRIP + 1.5, tau))))
            pe.draw(fig.canvas, cam, WHITE, RED)
            # sight line
            if tgt is not None and lk > 0.02:
                jr, row, rx = rivals[tgt]
                sc, up = ROWS[row]
                rc = lane_cam(112 * sc, cam.wx, cam.sx, gsy - up)
                a = cam.pt(je["head"])
                b = rc.pt(jr["head"])
                fig.canvas.drawLine(*a, *b, dashed(RED, 0.9 * lk, 4, 16, 12, -t * 120))
                fig.canvas.drawCircle(*b, HEAD_R * rc.s * 1.6, paint(RED, 0.8 * lk, 3))
            # labels
            hx, hy = cam.pt(je["head"])
            la = smoothstep(0.2, 0.8, t) * top_dim
            draw_spaced(txt.canvas, "EGO", hx, hy - (HEAD_R + 0.5) * cam.s, f_lab, 6, paint(ecol, la))
            jr, row, rx = rivals[1]
            sc, up = ROWS[row]
            rc = lane_cam(112 * sc, cam.wx, cam.sx, gsy - up)
            rhx, rhy = rc.pt(jr["head"])
            oa = smoothstep(0.3, 0.9, t) * (1 - smoothstep(GO + 0.6, GO + 1.3, tau))
            draw_spaced(txt.canvas, "OTHERS", rhx + 0.4 * rc.s, gsy + 0.62 * cam.s + 30, f_lab_s, 5, paint(GREY, oa))
            # rank HUD
            rcol = RED if rank >= 3 or tau > TRIP else WHITE
            ha = smoothstep(0.3, 0.9, t) * (0.4 + 0.6 * top_dim)
            draw_spaced(txt.canvas, "RANK", W / 2, 236 + yo, f_cap, 10, paint(WHITE, 0.7 * ha))
            draw_spaced(txt.canvas, "LAST" if tau > TRIP + 0.25 else f"#{rank}", W / 2, 330 + yo, f_num, 4, paint(rcol, ha))
            for L in (env, fig, txt):
                L.canvas.restore()
            # divider
            env.canvas.drawLine(0, split, W, split, paint(WHITE, 0.22, 2))

        # ---------------- BOTTOM LANE
        y0 = split
        hgt = H - y0
        gsy = y0 + hgt * (0.66 + 0.06 * wsplit)
        s_b = 112 - 8 * wsplit
        camb = lane_cam(s_b, ox + 0.9, W * (0.40 + 0.04 * wsplit), gsy)
        for L in (env, fig, txt):
            L.canvas.save()
            L.canvas.clipRect(skia.Rect(0, y0, W, H))
        spd = clamp((vo - 6.5) / 2.5)
        streaks.draw(env.canvas, y0, gsy, ox * s_b * 1.2, spd)
        draw_track(env.canvas, camb, y0, H, 1.0, 1 - smoothstep(GO, GO + 0.5, tau))
        if jg is not None and galpha > 0.01:
            draw_figure(env.canvas, jg, camb, WHITE, 0.32 * galpha, 0.7)
            ghx, ghy = camb.pt(jg["head"])
            if tau < TAU_SPLIT_A or ci == len(CYC_D) - 1:
                draw_spaced(txt.canvas, "YESTERDAY", camb.pt(jg["hip"])[0], camb.sy + 0.62 * camb.s + 30, f_lab_s, 5,
                            paint(WHITE, 0.45 * galpha * smoothstep(0.2, 0.8, t)))
        po.draw(fig.canvas, camb, WHITE, WHITE)
        draw_figure(fig.canvas, jo, camb, WHITE, 1.0)
        if oglow > 0:
            hx, hy = camb.pt(jo["hip"])
            fig.canvas.drawCircle(hx, hy - 0.6 * camb.s, 1.1 * camb.s, paint(WHITE, 0.08 * oglow))
        hx, hy = camb.pt(jo["head"])
        la = smoothstep(0.3, 0.9, t) * (1 - smoothstep(T_PUNCH1 - 0.6, T_PUNCH1, t))
        draw_spaced(txt.canvas, "OBSESSION", hx, hy - (HEAD_R + 0.5) * camb.s, f_lab, 6, paint(WHITE, la))
        # day HUD
        hy0 = 1062 + (236 - 1062) * wsplit
        dpulse = 0
        da = smoothstep(0.3, 0.9, t) * (1 - 0.5 * smoothstep(T_PUNCH1 - 0.3, T_PUNCH1 + 0.3, t))
        dcol = RED if cyc_done == len(CYC_D) else WHITE
        draw_spaced(txt.canvas, "DAY", W / 2, hy0, f_cap, 10, paint(WHITE, 0.7 * da))
        draw_spaced(txt.canvas, str(day), W / 2, hy0 + 94, f_num, 4, paint(dcol, da))
        for L in (env, fig, txt):
            L.canvas.restore()

        # ---------------- punchline
        tc = txt.canvas

        def reveal(t0):
            u = ease_out((t - t0) / 0.45)
            return u, (1 - u) * 34
        if t >= T_PUNCH1:
            u, off = reveal(T_PUNCH1)
            draw_runs(tc, [("EGO", paint(RED, u)), (" COMPETES WITH OTHERS.", paint(WHITE, u * 0.8))],
                      W / 2, 560 + off, f_p1, 4)
        if t >= T_PUNCH2:
            u, off = reveal(T_PUNCH2)
            draw_spaced(tc, "OBSESSION", W / 2, 735 + off, f_p2, 4, paint(WHITE, u))
            u2, off2 = reveal(T_PUNCH2 + 0.18)
            draw_spaced(tc, "COMPETES WITH YESTERDAY.", W / 2, 828 + off2, f_p3, 6, paint(WHITE, u2 * 0.92))

        # ---------------- composite
        flash = 0.0
        if t >= T_FINAL:
            flash = math.exp(-(t - T_FINAL) * 3.0)
        e = bloom(env.rgb(), (0.9, (4, 0.6), (22, 0.3)))
        g = bloom(fig.rgb(), (1.0, (5, 0.9), (18, 0.8), (60, 0.55 + flash)))
        x = bloom(txt.rgb(), (1.0, (6, 0.7), (26, 0.45)))
        img = (e + g + x) * master + flash * 0.05
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
    m.add_bed(sfx.drone(DUR, rise_at=T_FINAL), gain=0.5, fade_in=1.0, fade_out=2.5, stop=DUR)
    # race start: beep, beep, BEEP
    m.add(GO - 0.9, sfx.beep(660), 0.6, 0, 0.2)
    m.add(GO - 0.45, sfx.beep(660), 0.6, 0, 0.2)
    m.add(GO, sfx.beep(1320, 0.45), 0.7, 0, 0.3)
    m.add(GO + 0.02, sfx.whoosh(0.6, 300, 6000, 0.3, seed=2), 0.5, 0, 0.2)
    npass = 0
    for t, kind, pan, extra in events:
        if kind == "step_E":
            m.add(t, sfx.step_light(int(t * 97)), 0.22, -0.3, 0.1)
        elif kind == "step_O":
            g = 0.22 + 0.25 * extra
            m.add(t, sfx.step_heavy(int(t * 89)), g, 0.25 * (1 - extra), 0.2)
        elif kind == "lock":
            m.add(t, sfx.lock_on(extra), 0.55, -0.35, 0.3)
        elif kind == "rank":
            m.add(t, sfx.tick(1800 if extra >= 3 else 2600, 0.5), 0.6, -0.3, 0.1)
        elif kind == "trip":
            m.add(t, sfx.body_fall(), 1.0, -0.2, 0.4)
            m.add(t + 0.15, sfx.glitch(3), 0.6, -0.2, 0.2)
            m.add(t + 0.1, sfx.power_down(2.0), 0.4, -0.2, 0.4)
        elif kind == "pass":
            final = extra == len(CYC_D) - 1
            if final:
                continue
            npass += 1
            f = 440 * 2 ** (min(npass, 14) * 2 / 12)
            m.add(t - 0.05, sfx.whoosh(0.35, 800, 9000, 0.6, seed=npass), 0.25, 0.2, 0.2)
            m.add(t, sfx.chime(f, 0.3), 0.45, 0.15, 0.5)
    tf = tau_to_t(TAU_FPASS)
    m.add(tf - 2.6, sfx.riser(2.6), 0.5, 0, 0.3)
    m.add(tf - 0.2, sfx.heartbeat(), 0.85, 0, 0.3)
    m.add(tf + 0.75, sfx.heartbeat(), 0.7, 0, 0.3)
    m.add(T_FINAL, sfx.boom(4.0), 1.0, 0, 0.5)
    m.add(T_FINAL, sfx.sparkle(2.0), 0.7, 0.1, 0.6)
    m.add(tau_to_t(TAU_SPLIT_A), sfx.whoosh(1.0, 120, 2500, 0.7, seed=12), 0.45, 0, 0.4)
    m.add(T_PUNCH1, sfx.whoosh(0.5, 800, 9000, 0.5, seed=8), 0.35, -0.2, 0.3)
    m.add(T_PUNCH1 + 0.05, sfx.text_hit(1), 0.55, 0, 0.4)
    m.add(T_PUNCH2 - 0.05, sfx.whoosh(0.5, 600, 9000, 0.6, seed=9), 0.45, 0.2, 0.3)
    m.add(T_PUNCH2 + 0.05, sfx.text_hit(2), 0.85, 0, 0.5)
    m.add(T_PUNCH2 + 0.25, sfx.text_hit(3) * 0.6, 0.6, 0, 0.6)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}s frames {N} trip {tau_to_t(TRIP):.2f}s final {T_FINAL:.2f}s")
    if "--stills" in sys.argv:
        ts = [0.6, 2.2, 3.0, 5.0, 6.6, tau_to_t(TRIP) + 0.15, tau_to_t(TRIP) + 1.2, tau_to_t(TRIP) + 3.2,
              tau_to_t(TAU_SPLIT_A + 0.6), 14.0, tau_to_t(TAU_FPASS), T_PUNCH2 + 1.5]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
