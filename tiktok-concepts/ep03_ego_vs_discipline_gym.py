"""EP03 - EGO vs DISCIPLINE  (the bench press)

HOOK  "ONE OF THEM IS ABOUT TO GET HURT."
TOP     EGO loads plate after plate (60 -> 180 KG) while a crowd films him with
        phones. He lowers the bar, shakes, flickers red... and gets crushed.
        The crowd lowers their phones and walks away.
BOTTOM  DISCIPLINE, alone, light bar. Rep after rep, week after week, one plate
        at a time. Then the bottom takes the full screen: WEEK 52, 180 KG,
        final rep in slow motion, lockout, BOOM.
PUNCH   "LEAVE YOUR" / "EGO" / "AT THE DOOR."
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import (FPS, H, HEAD_R, L_FARM, L_UARM, RED, WHITE, W, Camera, Layer,
                    Post, VideoWriter, blend_pose, bloom, build_pose, clamp, draw_figure,
                    draw_runs, draw_spaced, ease_out, fit_font, font, ik, mix, mux, paint,
                    run_pose, smoothstep)
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep03_ego_vs_discipline_gym"
GREY = (0.55, 0.55, 0.58)
dt = 1 / FPS
BY = 0.78                     # bench pad height

# ------------------------------------------------------------ script (tau)
EGO_LOADS = [(1.5, 100), (2.7, 140), (3.9, 180)]
E_DOWN_A, E_DOWN_B, CRASH = 5.0, 6.4, 9.0
TAU_SPLIT_A, TAU_SPLIT_B = 11.0, 12.2

REP_D = [1.8] * 6 + [0.62] * 7 + [3.0]
WEEKS = [1, 2, 3, 4, 5, 6, 8, 12, 18, 25, 33, 41, 48, 52]
REP_START = [0.9]
for d in REP_D[:-1]:
    REP_START.append(REP_START[-1] + d)
FINAL = len(REP_D) - 1
TAU_LOCK = REP_START[FINAL] + 0.85 * REP_D[FINAL]


def kg_of_week(w):
    return int(round((60 + 120 * (w - 1) / 51) / 5) * 5)


def plates_for(kg):
    """Per-side plate radii (world units), biggest first."""
    side = (kg - 20) / 2
    out = []
    for w, r in ((20, 0.34), (10, 0.27), (5, 0.2), (2.5, 0.15)):
        while side >= w - 1e-6:
            out.append(r)
            side -= w
    return out


def ego_kg(tau):
    kg = 60
    for t0, k in EGO_LOADS:
        if tau >= t0:
            kg = k
    return kg


def rate(tau):
    r = 1.0
    w = smoothstep(CRASH - 0.55, CRASH - 0.3, tau) * (1 - smoothstep(CRASH + 0.35, CRASH + 0.6, tau))
    r -= 0.6 * w
    a = REP_START[FINAL] + 0.3 * REP_D[FINAL]
    w = smoothstep(a - 0.2, a, tau) * (1 - smoothstep(TAU_LOCK + 0.1, TAU_LOCK + 0.4, tau))
    r -= 0.45 * w
    return r


taus = [0.0]
while taus[-1] < TAU_LOCK:
    taus.append(taus[-1] + rate(taus[-1]) * dt)
T_LOCK = len(taus) * dt
T_P1 = T_LOCK + 1.0
T_P2 = T_P1 + 0.7
T_P3 = T_P2 + 0.45
DUR = T_P3 + 3.0
N = int(DUR * FPS)
while len(taus) < N:
    taus.append(taus[-1] + dt)
TAUS = np.array(taus)


def tau_to_t(tau):
    return int(np.searchsorted(TAUS, tau)) * dt


# ------------------------------------------------------------ lifter
def lifter_pose(x0, h, crash=0.0, tremble=(0.0, 0.0)):
    """Lying on a bench, head to the right. h: 0 = bar on chest, 1 = lockout."""
    press = 0.1 * crash
    hip = np.array([x0, BY + 0.13])
    neck = np.array([x0 + 0.93, BY + 0.15 - press])
    head = np.array([neck[0] + 0.37, BY + 0.2 - press * 0.5])
    sh = hip + (neck - hip) * 0.86
    by = sh[1] + 0.24 + (L_UARM + L_FARM - 0.1 - 0.24) * h
    bar = np.array([sh[0] + 0.04 + tremble[0], by + tremble[1]])
    j = {"hip": hip, "neck": neck, "head": head, "shoulder": sh}
    for i, (fx, fy) in enumerate(((x0 - 1.25, 0.04), (x0 - 1.05, 0.04)), 1):
        foot = np.array([fx, fy])
        j[f"foot{i}"] = foot
        j[f"knee{i}"] = ik(hip, foot, 0.8, 0.8, -1)
    for i, off in ((1, 0.0), (2, 0.04)):
        hand = bar + [off, 0]
        j[f"hand{i}"] = hand
        j[f"elbow{i}"] = ik(sh, hand, L_UARM, L_FARM, -1)
    return j, bar


def draw_bench(c, cam, x0, alpha, rack=True):
    p = paint(WHITE, 0.8 * alpha, 0.14 * cam.s)
    c.drawLine(*cam.pt((x0 - 0.35, BY - 0.05)), *cam.pt((x0 + 1.5, BY - 0.05)), p)
    pl = paint(WHITE, 0.6 * alpha, 0.07 * cam.s)
    for lx in (x0 - 0.15, x0 + 1.3):
        c.drawLine(*cam.pt((lx, BY - 0.1)), *cam.pt((lx, 0.0)), pl)
    if rack:
        rx = x0 + 1.75
        c.drawLine(*cam.pt((rx, 0)), *cam.pt((rx, 2.45)), paint(WHITE, 0.55 * alpha, 0.08 * cam.s))
        c.drawLine(*cam.pt((rx, 2.12)), *cam.pt((rx - 0.22, 2.2)), paint(WHITE, 0.55 * alpha, 0.06 * cam.s))
        c.drawLine(*cam.pt((rx - 0.35, 0)), *cam.pt((rx + 0.35, 0)), paint(WHITE, 0.55 * alpha, 0.08 * cam.s))


def draw_plates(c, cam, bar, radii, col, alpha, fly=None):
    """Plate stack seen edge-on along the bar axis; nearest plate drawn last."""
    n = len(radii)
    for i in range(n - 1, -1, -1):
        r = radii[i]
        off = np.array([0.075, -0.05]) * i
        if fly is not None and i == n - 1:
            off = off + [fly, 0]
        cx, cy = cam.pt(bar + off)
        c.drawCircle(cx, cy, r * cam.s, paint((0, 0, 0), 1.0))
        a = alpha * (0.55 + 0.45 * (i == n - 1 or True) * (1 - 0.08 * (n - 1 - i)))
        c.drawCircle(cx, cy, r * cam.s, paint(col, a, max(2, 0.05 * cam.s)))
        c.drawCircle(cx, cy, r * cam.s * 0.62, paint(col, a * 0.35, max(1, 0.02 * cam.s)))
    cx, cy = cam.pt(bar + np.array([0.075, -0.05]) * max(0, n - 1) + [0.03, -0.02])
    c.drawCircle(cx, cy, 0.07 * cam.s, paint(col, alpha))


def mirror(j, cx):
    return {k: np.array([2 * cx - v[0], v[1]]) for k, v in j.items()}


def lane_cam(s, wx, sx, sy):
    c = Camera()
    c.s, c.wx, c.wy, c.sx, c.sy = s, wx, 0.0, sx, sy
    return c


# spectators: (world x, row, facing -1 = looks left)
SPECS = [(-2.9, 1, 1), (-1.9, 2, 1), (3.0, 1, -1), (4.0, 2, -1), (-4.1, 2, 1)]
ROWS = {1: (0.80, 70), 2: (0.66, 128)}


def spectator_pose(x, t, i, leave, walk_x, walk_ph):
    film = build_pose(np.array([x, 1.52 + 0.01 * math.sin(t * 2 + i)]), np.array([x + 0.12, 0.02]),
                      np.array([x - 0.12, 0.02]), 0.02, 2.15 + 0.05 * math.sin(t * 1.5 + i), 0.15,
                      0.55, 0.25, 0.12)
    if leave <= 0:
        return film, True
    walk = run_pose(walk_x, walk_ph, 0.45)
    walk = {k: v + [0, 0] for k, v in walk.items()}
    return blend_pose(film, walk, smoothstep(0, 0.35, leave)), leave < 0.3


def render(stills=None):
    os.makedirs(OUT, exist_ok=True)
    env, fig, txt = Layer(), Layer(), Layer()
    post = Post()
    events = []
    writer = None if stills else VideoWriter(os.path.join(OUT, NAME + "_video.mp4"))
    f_lab = font(30, "Inter-Bold")
    f_cap = font(24, "Inter-SemiBold")
    f_num = font(92, "InterDisplay-Bold")
    f_hook1 = fit_font("ONE OF THEM IS ABOUT TO", 52, "InterDisplay-Bold", 4, 960)
    f_hook2 = font(118, "InterDisplay-Black")
    f_p1 = font(50, "InterDisplay-Bold")
    f_p2 = font(220, "InterDisplay-Black")
    f_p3 = fit_font("AT THE DOOR.", 74, "InterDisplay-Bold", 8, 960)

    rng = np.random.default_rng(4)
    flashes = []           # (tau, spectator index)
    prev_tau = 0.0
    last_kg_e, last_rep = 60, -1
    spec_walk = [0.0] * len(SPECS)
    spec_ph = [i * 1.3 for i in range(len(SPECS))]
    shake = 0.0
    for fi in range(N):
        t = fi * dt
        tau = taus[fi]
        dtau = tau - prev_tau
        prev_tau = tau
        draw_now = stills is None or fi in stills
        wsplit = smoothstep(TAU_SPLIT_A, TAU_SPLIT_B, tau)
        split = 960 * (1 - wsplit)

        # ---------------- EGO
        kg_e = ego_kg(tau)
        if kg_e != last_kg_e:
            events.append((t, "load_e", 0, kg_e))
            for k in rng.choice(len(SPECS), 3, replace=False):
                flashes.append((tau + rng.uniform(0.05, 0.4), int(k)))
            last_kg_e = kg_e
        fly_e = None
        for t0, k in EGO_LOADS:
            if t0 <= tau < t0 + 0.3:
                fly_e = 3.2 * (1 - ease_out((tau - t0) / 0.3))
        stress = smoothstep(E_DOWN_A, CRASH, tau)
        if tau < E_DOWN_A:
            h = 1.0
        elif tau < E_DOWN_B:
            h = 1 - 0.85 * smoothstep(E_DOWN_A, E_DOWN_B, tau)
        elif tau < CRASH:
            u = (tau - E_DOWN_B) / (CRASH - E_DOWN_B)
            h = 0.15 + 0.22 * math.sin(u * math.pi) * (1 - 0.3 * u) + 0.03 * math.sin(tau * 9)
        else:
            h = 0.15 - 0.27 * ease_out((tau - CRASH) / 0.12)
        crash = smoothstep(CRASH, CRASH + 0.12, tau)
        amp = (0.012 + 0.05 * stress ** 2) * (1 - crash) * (tau > E_DOWN_A - 0.5)
        trem = (amp * math.sin(t * 61) + amp * 0.6 * math.sin(t * 97), amp * 0.7 * math.sin(t * 73))
        je, bar_e = lifter_pose(0.0, h, crash, trem)
        redness = clamp(0.2 * (kg_e - 60) / 120 + 0.55 * stress + 0.3 * crash)
        if tau >= CRASH and not any(e[1] == "crash" for e in events):
            events.append((t, "crash", 0, 0))
            shake = 1.0
        shake = max(0.0, shake - dtau * 2.2)

        # spectators leave after the crash
        leave = max(0.0, tau - (CRASH + 0.7))
        for i in range(len(SPECS)):
            if leave > 0:
                spec_walk[i] += 2.4 * dtau * smoothstep(0, 0.4, leave)
                spec_ph[i] += (2.4 / 2.6) * 2 * math.pi * dtau

        # ---------------- DISCIPLINE
        ri = max(i for i in range(len(REP_D)) if REP_START[i] <= tau) if tau >= REP_START[0] else 0
        u = clamp((tau - REP_START[ri]) / REP_D[ri]) if tau >= REP_START[0] else 0.0
        if ri < FINAL:
            hd = 0.5 + 0.5 * math.cos(2 * math.pi * u)
            trd = (0.0, 0.0)
        else:
            if u < 0.3:
                hd = 1 - 0.95 * smoothstep(0, 0.3, u)
            elif u < 0.72:
                v = (u - 0.3) / 0.42
                hd = 0.05 + 0.33 * v ** 1.3
            else:
                hd = 0.38 + 0.62 * ease_out((u - 0.72) / 0.13)
            a = 0.04 * smoothstep(0.3, 0.7, u) * (1 - smoothstep(0.8, 0.86, u))
            trd = (a * math.sin(t * 59), a * 0.7 * math.sin(t * 83))
        week = WEEKS[ri]
        kg_d = kg_of_week(week)
        if ri != last_rep:
            if ri > 0:
                events.append((t, "rep_d", 0, ri))
                if plates_for(kg_of_week(WEEKS[ri])) != plates_for(kg_of_week(WEEKS[ri - 1])):
                    events.append((t + 0.05, "load_d", 0, ri))
            last_rep = ri
        fly_d = None
        if ri > 0 and plates_for(kg_d) != plates_for(kg_of_week(WEEKS[ri - 1])):
            fu = (tau - REP_START[ri]) / min(0.25, REP_D[ri] * 0.4)
            if fu < 1:
                fly_d = 2.6 * (1 - ease_out(fu))
        jd, bar_d = lifter_pose(0.0, hd, 0.0, trd)
        if ri == FINAL and tau >= TAU_LOCK and not any(e[1] == "lock" for e in events):
            events.append((t, "lock", 0, 0))

        if not draw_now:
            continue

        # ================================================= draw
        for L in (env, fig, txt):
            L.clear()
        master = smoothstep(0, 0.4, t) * (1 - smoothstep(DUR - 0.35, DUR, t))
        hook_a = smoothstep(0.1, 0.35, t) * (1 - smoothstep(2.6, 3.0, t))
        hud_a = smoothstep(2.6, 3.2, t)

        # ---------------- TOP: EGO
        if split > 2:
            yo = split - 960
            sx_shake = shake * 14 * math.sin(t * 90)
            sy_shake = shake * 10 * math.sin(t * 77)
            gsy = 860 + yo + sy_shake
            top_dim = 1 - 0.6 * smoothstep(CRASH + 1.5, CRASH + 3.0, tau)
            cam = lane_cam(122, 0.55, W / 2 + sx_shake, gsy)
            for L in (env, fig, txt):
                L.canvas.save()
                L.canvas.clipRect(skia.Rect(0, 0, W, split))
            env.canvas.drawLine(0, gsy, W, gsy, paint(WHITE, 0.55 * top_dim, 2.5))
            # crowd
            for i in sorted(range(len(SPECS)), key=lambda i: -SPECS[i][1]):
                x, row, face = SPECS[i]
                sc, up = ROWS[row]
                rc = lane_cam(122 * sc, cam.wx, cam.sx, gsy - up)
                if i == 0:
                    env.canvas.drawLine(0, rc.sy, W, rc.sy, paint(WHITE, 0.12 * top_dim, 1.5))
                away = -1 if x < 0.55 else 1
                wx = x + away * spec_walk[i]
                jp, filming = spectator_pose(wx, t, i, leave, wx, spec_ph[i])
                if face < 0 and leave <= 0.35:
                    jp = mirror(jp, wx)
                if away < 0 and leave > 0.35:
                    jp = mirror(jp, wx)
                sa = 0.5 * top_dim * (1 - smoothstep(1.2, 2.2, leave))
                draw_figure(env.canvas, jp, rc, GREY, sa, 0.6)
                if filming and sa > 0.02:
                    hx, hy = rc.pt(jp["hand1"])
                    pw, ph_ = 0.17 * rc.s, 0.3 * rc.s
                    env.canvas.drawRoundRect(skia.Rect(hx - pw / 2, hy - ph_, hx + pw / 2, hy), 4, 4,
                                             paint(WHITE, 0.85 * sa / 0.5 * (1 - smoothstep(0, 0.3, leave))))
                    if (int(t * 2) + i) % 2 == 0:
                        fig.canvas.drawCircle(hx + pw * 0.25, hy - ph_ * 0.85, 3.5, paint(RED, 0.9 * top_dim))
                    for ft, k in flashes:
                        if k == i and 0 <= tau - ft < 0.25:
                            fa = 1 - (tau - ft) / 0.25
                            fig.canvas.drawCircle(hx, hy - ph_ * 0.5, (0.4 + 0.6 * fa) * rc.s * 0.6, paint(WHITE, 0.9 * fa))
            draw_bench(env.canvas, cam, 0.0, top_dim)
            ecol = mix(WHITE, RED, redness)
            flick = 1.0
            if stress > 0.4 and (int(t * 30) * 7919) % 11 == 0:
                flick = 0.35
            ea = top_dim * flick * (1 - 0.35 * smoothstep(CRASH, CRASH + 1.5, tau))
            draw_figure(fig.canvas, je, cam, ecol, ea)
            draw_plates(fig.canvas, cam, bar_e, plates_for(kg_e), ecol if crash > 0 else WHITE, ea, fly_e)
            # red impact flash
            if tau >= CRASH:
                fa = math.exp(-(tau - CRASH) * 3.0)
                fig.canvas.drawRect(skia.Rect(0, 0, W, split), paint(RED, 0.25 * fa))
            hx, hy = cam.pt((0.55, 0))
            draw_spaced(txt.canvas, "EGO", hx, gsy + 50, f_lab, 6, paint(ecol, top_dim * smoothstep(0.2, 0.7, t) * (1 - hook_a)))
            kcol = RED if kg_e >= 140 else WHITE
            draw_spaced(txt.canvas, "DAY 1", W / 2, 236 + yo, f_cap, 10, paint(WHITE, 0.7 * hud_a * top_dim))
            draw_spaced(txt.canvas, f"{kg_e} KG", W / 2, 330 + yo, f_num, 4, paint(kcol, hud_a * (0.4 + 0.6 * top_dim)))
            for L in (env, fig, txt):
                L.canvas.restore()
            env.canvas.drawLine(0, split, W, split, paint(WHITE, 0.22, 2))

        # ---------------- BOTTOM: DISCIPLINE
        y0 = split
        hgt = H - y0
        gsy = y0 + hgt * (0.70 + 0.0 * wsplit)
        s_b = 128 + 32 * wsplit
        camb = lane_cam(s_b, 0.55, W / 2, gsy)
        for L in (env, fig, txt):
            L.canvas.save()
            L.canvas.clipRect(skia.Rect(0, y0, W, H))
        env.canvas.drawLine(0, gsy, W, gsy, paint(WHITE, 0.55, 2.5))
        draw_bench(env.canvas, camb, 0.0, 1.0)
        glow = 0.0
        if tau >= TAU_LOCK:
            glow = math.exp(-(tau - TAU_LOCK) * 1.5)
        draw_figure(fig.canvas, jd, camb, WHITE, 1.0)
        draw_plates(fig.canvas, camb, bar_d, plates_for(kg_d), WHITE, 1.0, fly_d)
        hx, hy = camb.pt((0.55, 0))
        la = smoothstep(0.2, 0.7, t) * (1 - smoothstep(T_P1 - 0.5, T_P1, t)) * (1 - hook_a)
        draw_spaced(txt.canvas, "DISCIPLINE", hx, gsy + 50, f_lab, 6, paint(WHITE, la))
        hy0 = 1062 + (236 - 1062) * wsplit
        da = hud_a * (1 - 0.6 * smoothstep(T_P1 - 0.3, T_P1 + 0.3, t))
        dcol = RED if tau >= TAU_LOCK else WHITE
        draw_spaced(txt.canvas, f"WEEK {week}", W / 2, hy0, f_cap, 10, paint(WHITE, 0.7 * da))
        draw_spaced(txt.canvas, f"{kg_d} KG", W / 2, hy0 + 94, f_num, 4, paint(dcol, da))
        for L in (env, fig, txt):
            L.canvas.restore()

        # ---------------- HOOK
        tc = txt.canvas
        if hook_a > 0.01:
            env.canvas.drawRect(skia.Rect(0, 820, W, 1100), paint((0, 0, 0), 0.92 * hook_a))
            fig.canvas.drawRect(skia.Rect(0, 820, W, 1100), paint((0, 0, 0), 0.92 * hook_a))
            env.canvas.drawLine(90, 822, W - 90, 822, paint(RED, 0.6 * hook_a, 2))
            env.canvas.drawLine(90, 1098, W - 90, 1098, paint(RED, 0.6 * hook_a, 2))
            pop = 1 + 0.08 * (1 - ease_out((t - 0.1) / 0.3))
            draw_spaced(tc, "ONE OF THEM IS ABOUT TO", W / 2, 925, f_hook1, 4, paint(WHITE, hook_a))
            f2 = font(118 * pop, "InterDisplay-Black")
            draw_runs(tc, [("GET", paint(WHITE, hook_a)), (" HURT.", paint(RED, hook_a))], W / 2, 1050, f2, 6)

        # ---------------- PUNCHLINE
        def reveal(t0, d=0.4):
            u = ease_out((t - t0) / d)
            return u, (1 - u) * 34
        if t >= T_P1:
            u, off = reveal(T_P1)
            draw_spaced(tc, "LEAVE YOUR", W / 2, 520 + off, f_p1, 10, paint(WHITE, u * 0.85))
        if t >= T_P2:
            u, off = reveal(T_P2, 0.3)
            sc = 1 + 0.25 * (1 - u)
            draw_spaced(tc, "EGO", W / 2, 735 + off * 0.3, font(220 * sc, "InterDisplay-Black"), 10, paint(RED, u))
        if t >= T_P3:
            u, off = reveal(T_P3)
            draw_spaced(tc, "AT THE DOOR.", W / 2, 840 + off, f_p3, 8, paint(WHITE, u * 0.95))

        # ---------------- composite
        flash = 0.0
        if t >= T_LOCK:
            flash = math.exp(-(t - T_LOCK) * 3.0)
        e = bloom(env.rgb(), (0.9, (4, 0.6), (22, 0.3)))
        g = bloom(fig.rgb(), (1.0, (5, 0.9), (18, 0.8), (60, 0.55 + flash)))
        x = bloom(txt.rgb(), (1.0, (6, 0.7), (26, 0.45)))
        img = (e + g + x) * master
        frame = post.apply(img, fi)
        if stills:
            import PIL.Image
            PIL.Image.fromarray(frame).save(os.path.join(OUT, f"still_{fi:04d}.png"))
        else:
            writer.write(frame)
        if fi % 90 == 0:
            print(f"frame {fi}/{N}", flush=True)

    # shutter sounds for flashes
    for ft, k in flashes:
        events.append((tau_to_t(ft), "shutter", 0, k))
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
    m.add_bed(sfx.drone(DUR, rise_at=T_LOCK), gain=0.5, fade_in=0.8, fade_out=2.5, stop=DUR)
    # hook
    m.add(0.1, sfx.text_hit(5), 0.9, 0, 0.4)
    m.add(2.55, sfx.whoosh(0.6, 300, 7000, 0.6, seed=3), 0.4, 0, 0.3)
    n_rep = 0
    for t, kind, pan, extra in events:
        if kind == "load_e":
            m.add(t + 0.28, sfx.plate_clank(extra, 1.0), 0.9, -0.25, 0.35)
        elif kind == "shutter":
            m.add(t, sfx.shutter(extra), 0.5, -0.5 + 0.25 * extra, 0.2)
        elif kind == "rep_d":
            n_rep += 1
            m.add(t - 0.05, sfx.breath(extra, 0.35 if extra > 6 else 0.5), 0.6, 0.2, 0.2)
            m.add(t, sfx.tick(2200, 0.4), 0.5, 0, 0.1)
        elif kind == "load_d":
            m.add(t + 0.15, sfx.plate_clank(100 + extra, 0.8), 0.6, 0.25, 0.35)
        elif kind == "crash":
            m.add(t, sfx.plate_clank(77, 2.0), 1.0, -0.2, 0.5)
            m.add(t, sfx.boom(3.0), 0.8, 0, 0.4)
            m.add(t + 0.05, sfx.glitch(5), 0.7, -0.2, 0.2)
            m.add(t + 0.3, sfx.power_down(2.2), 0.4, -0.2, 0.4)
        elif kind == "lock":
            m.add(t, sfx.boom(4.0), 1.0, 0, 0.5)
            m.add(t, sfx.plate_clank(88, 1.4), 0.7, 0, 0.5)
            m.add(t, sfx.sparkle(1.8), 0.6, 0.1, 0.6)
    # Ego's struggle: rattle + heartbeat
    m.add(tau_to_t(E_DOWN_B), sfx.rattle(tau_to_t(CRASH) - tau_to_t(E_DOWN_B), 2), 0.7, -0.25, 0.2)
    m.add(tau_to_t(CRASH) - 2.0, sfx.heartbeat(), 0.7, 0, 0.3)
    m.add(tau_to_t(CRASH) - 1.1, sfx.heartbeat(), 0.85, 0, 0.3)
    m.add(tau_to_t(E_DOWN_A), sfx.breath(9, 1.2), 0.5, -0.25, 0.2)
    m.add(tau_to_t(TAU_SPLIT_A), sfx.whoosh(1.0, 120, 2500, 0.7, seed=12), 0.45, 0, 0.4)
    # final rep: rattle + heartbeat + riser
    fa = tau_to_t(REP_START[FINAL] + 0.3 * REP_D[FINAL])
    m.add(fa, sfx.rattle(T_LOCK - fa, 9), 0.6, 0.2, 0.2)
    m.add(T_LOCK - 2.6, sfx.riser(2.6), 0.5, 0, 0.3)
    m.add(fa + 0.1, sfx.heartbeat(), 0.8, 0, 0.3)
    m.add(fa + 1.0, sfx.heartbeat(), 0.9, 0, 0.3)
    m.add(T_LOCK - 0.5, sfx.breath(31, 0.6), 0.8, 0.2, 0.2)
    # punchline
    m.add(T_P1, sfx.whoosh(0.5, 800, 9000, 0.5, seed=8), 0.35, -0.2, 0.3)
    m.add(T_P1 + 0.05, sfx.text_hit(1), 0.45, 0, 0.4)
    m.add(T_P2, sfx.text_hit(2), 0.95, 0, 0.5)
    m.add(T_P2, sfx.boom(2.0), 0.35, 0, 0.4)
    m.add(T_P3, sfx.text_hit(3), 0.5, 0, 0.5)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}s frames {N} crash {tau_to_t(CRASH):.2f}s lock {T_LOCK:.2f}s")
    if "--stills" in sys.argv:
        ts = [1.2, 2.0, 3.4, 4.6, 6.2, 8.0, tau_to_t(CRASH) + 0.2, tau_to_t(CRASH) + 1.8,
              tau_to_t(TAU_SPLIT_A + 0.6), 14.0, T_LOCK - 1.2, T_LOCK + 0.15, T_P3 + 1.2]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
