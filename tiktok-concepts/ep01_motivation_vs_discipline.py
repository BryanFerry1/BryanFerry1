"""EP01 - MOTIVATION vs DISCIPLINE  (the staircase)

Story (~24 s, 1080x1920, 30 fps):
  0-1.5s   Two glowing figures at the foot of an endless staircase. DAY 1.
  1.2s     MOTIVATION bolts up the stairs, sprinting. DISCIPLINE starts
           calmly, one step at a time.
  ~4.5s    Motivation slows down, its light flickers and turns red.
  ~7.5s    Motivation stops, bent over, exhausted. Discipline keeps going.
  ~11s     Slow motion: Discipline walks past. Motivation crumbles into
           red embers.
  ~16s     Camera pulls back: the whole staircase. Discipline reaches the
           top, raises its arms next to a red flag. DAY 365.  BOOM.
  end      "MOTIVATION GETS YOU STARTED."  /  "DISCIPLINE GETS YOU THERE."

Usage:
  python ep01_motivation_vs_discipline.py            # full render -> out/
  python ep01_motivation_vs_discipline.py --stills   # a few preview PNGs
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import (HEAD_R, FPS, H, RED, WHITE, W, Camera, Layer, Particles, Post, VideoWriter,
                    blend_pose, bloom, build_pose, clamp, draw_figure, draw_runs,
                    draw_spaced, ease_out, font, mix, mux, paint, pose_points,
                    smoothstep)
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep01_motivation_vs_discipline"

# ------------------------------------------------------------ world
SW, SH = 0.9, 0.62           # step width / height (world units)
NS = 30                      # number of steps
S_STOP = 18                  # slot where Motivation gives up
P_END = NS + 1.0             # slot where Discipline stops (on the summit)
FLAG_X = (NS + 2.6) * SW


def floor_y(x):
    if x < 0:
        return 0.0
    i = int(x // SW)
    return NS * SH if i >= NS else (i + 1) * SH


def slot(k):
    x = (k + 0.5) * SW
    return np.array([x, floor_y(x)])


# ------------------------------------------------------------ timing (sim time tau)
M_START, M_V, M_DEC, M_STOPT = 1.2, 4.0, 4.4, 7.5
D_START, D_V, D_P0 = 1.5, 2.3, -4.0


def p_motivation(tau):
    p0 = -1.0
    if tau <= M_START:
        return p0
    pd = p0 + M_V * (M_DEC - M_START)
    if tau <= M_DEC:
        return p0 + M_V * (tau - M_START)
    T = M_STOPT - M_DEC
    u = min(tau - M_DEC, T)
    return pd + M_V * u - M_V * u * u / (2 * T)


def v_motivation(tau):
    if tau <= M_START:
        return 0.0
    if tau <= M_DEC:
        return M_V
    return max(0.0, M_V * (1 - (tau - M_DEC) / (M_STOPT - M_DEC)))


TAU_ARR_LIN = D_START + (P_END - D_P0) / D_V


def p_discipline(tau):
    if tau <= D_START:
        return D_P0
    p = D_P0 + D_V * (tau - D_START)
    # ease into the final stop over the last half slot
    if p > P_END - 0.5:
        over = p - (P_END - 0.5)
        p = P_END - 0.5 + 0.5 * (1 - math.exp(-over / 0.5))
    return p


TAU_PASS = D_START + (S_STOP - D_P0) / D_V       # Discipline reaches Motivation
TAU_ARRIVE = D_START + (P_END - 0.25 - D_P0) / D_V
SLOW_A, SLOW_B, SLOW_RATE = TAU_PASS - 0.55, TAU_PASS + 0.45, 0.32
TAU_DISSOLVE = TAU_PASS - 0.1


def rate(tau):
    # smooth dip into slow motion
    w = smoothstep(SLOW_A - 0.25, SLOW_A, tau) * (1 - smoothstep(SLOW_B, SLOW_B + 0.3, tau))
    return 1 - (1 - SLOW_RATE) * w


# real-time timeline
dt = 1 / FPS
taus = [0.0]
while True:
    t_real = len(taus) * dt
    taus.append(taus[-1] + rate(taus[-1]) * dt)
    if taus[-1] > TAU_ARRIVE and len(taus) * dt > 0:
        break
T_ARRIVE = len(taus) * dt
T_PUNCH1 = T_ARRIVE + 1.25
T_PUNCH2 = T_PUNCH1 + 1.35
DUR = T_PUNCH2 + 3.4
N = int(DUR * FPS)
while len(taus) < N:
    taus.append(taus[-1] + dt)


def tau_to_t(tau):
    i = int(np.searchsorted(np.array(taus), tau))
    return i * dt


def day_of(tau):
    u = clamp((tau - D_START) / (TAU_ARRIVE - D_START))
    return int(round(1 + 364 * u ** 2.4))


# ------------------------------------------------------------ poses
def walk_pose(p, speed, t):
    k = math.floor(p)
    f = p - k
    run = clamp((speed - 2.5) / 1.5)
    fe = f * f * (3 - 2 * f)
    planted = slot(k)
    a, b = slot(k - 1), slot(k + 1)
    swing = a + (b - a) * fe
    lift = math.sin(math.pi * f) * (abs(b[1] - a[1]) * 0.55 + 0.18 + 0.12 * run)
    swing = swing + np.array([0, lift])
    mid = (slot(k - 1) + slot(k)) / 2 * (1 - f) + (slot(k) + slot(k + 1)) / 2 * f
    moving = clamp(speed / 1.0)
    bob = -0.05 * abs(math.sin(math.pi * f)) * moving
    breath = 0.015 * math.sin(t * 2.4) * (1 - moving)
    hip = np.array([mid[0] + 0.05 + 0.1 * run, mid[1] + 1.32 + bob + breath])
    # keep both feet reachable
    for fp in (planted, swing - np.array([0, lift])):
        dx = abs(fp[0] - hip[0])
        hmax = fp[1] + math.sqrt(max((1.58) ** 2 - dx * dx, 0.1))
        hip[1] = min(hip[1], hmax)
    lean = 0.08 + 0.12 * moving + 0.28 * run
    A = (0.15 + 0.35 * moving + 0.45 * run)
    ph = math.pi * p
    arm1 = A * math.sin(ph) + 0.1 * moving
    arm2 = -A * math.sin(ph) + 0.1 * moving
    bend = 0.25 + 0.3 * moving + 1.0 * run
    if k % 2 == 0:
        f1, f2 = planted, swing
    else:
        f1, f2 = swing, planted
    return build_pose(hip, f1, f2, lean, arm1, arm2, bend, bend, 0.05 + 0.1 * run)


def tired_pose(t, sink=0.0):
    a, b = slot(S_STOP - 1), slot(S_STOP)
    mid = (a + b) / 2
    br = math.sin(t * 2 * math.pi * 1.5)
    hip = np.array([mid[0] - 0.05, mid[1] + 1.12 - 0.04 * br - sink])
    lean = 1.05 + 0.04 * br + 0.25 * sink
    j = build_pose(hip, b, a, lean, 0.3, 0.15, 0.3, 0.2, 0.45)
    return j


def victory_pose(t, w):
    a, b = slot(P_END - 1), slot(P_END)
    mid = (a + b) / 2
    hip = np.array([mid[0] + 0.05, mid[1] + 1.38])
    up = math.pi - 0.45
    j = build_pose(hip, b, a, 0.02, up + 0.06 * math.sin(t * 3), math.pi + 0.5, 0.1, -0.1, -0.25)
    return j


# ------------------------------------------------------------ scene drawing
def stair_path(cam):
    path = skia.Path()
    x0 = -14
    path.moveTo(*cam.pt((x0, 0)))
    path.lineTo(*cam.pt((0, 0)))
    for i in range(NS):
        path.lineTo(*cam.pt((i * SW, (i + 1) * SH)))
        path.lineTo(*cam.pt(((i + 1) * SW, (i + 1) * SH)))
    path.lineTo(*cam.pt(((NS + 14) * SW, NS * SH)))
    return path


def stair_fill(cam):
    path = stair_path(cam)
    path.lineTo(*cam.pt(((NS + 14) * SW, -30)))
    path.lineTo(*cam.pt((-14, -30)))
    path.close()
    return path


def draw_flag(canvas, cam, t, alpha, color=RED):
    base = np.array([FLAG_X, NS * SH])
    top = base + np.array([0, 2.9])
    canvas.drawLine(*cam.pt(base), *cam.pt(top), paint(WHITE, alpha * 0.9, 0.07 * cam.s))
    path = skia.Path()
    path.moveTo(*cam.pt(top))
    n = 12
    L, Hh = 1.35, 0.85
    for i in range(1, n + 1):
        u = i / n
        wv = math.sin(u * 3.2 - t * 5.5) * 0.12 * u
        path.lineTo(*cam.pt((top[0] + L * u, top[1] - 0.04 + wv - u * 0.04)))
    for i in range(n, -1, -1):
        u = i / n
        wv = math.sin(u * 3.2 - t * 5.5 + 0.4) * 0.12 * u
        path.lineTo(*cam.pt((top[0] + L * u, top[1] - Hh + wv + u * 0.04)))
    path.close()
    canvas.drawPath(path, paint(color, alpha))


class Motes:
    def __init__(self, n=70, seed=4):
        r = np.random.default_rng(seed)
        self.x, self.y = r.uniform(0, W, n), r.uniform(0, H, n)
        self.z = r.uniform(0.15, 0.6, n)
        self.a = r.uniform(0.05, 0.22, n)
        self.ph = r.uniform(0, 6.28, n)

    def draw(self, canvas, cam, t):
        for x, y, z, a, ph in zip(self.x, self.y, self.z, self.a, self.ph):
            sx = (x - cam.wx * 60 * z + math.sin(t * 0.3 + ph) * 12) % W
            sy = (y + cam.wy * 60 * z - t * 8 * z) % H
            canvas.drawCircle(sx, sy, 1.2 + 2.0 * z, paint(WHITE, a * (0.6 + 0.4 * math.sin(t + ph))))


# flicker pattern for the dying Motivation
_fr = np.random.default_rng(21)
FLICK = np.ones(N)
i = 0
while i < N:
    if _fr.random() < 0.09:
        L = _fr.integers(1, 4)
        FLICK[i:i + L] = _fr.uniform(0.15, 0.6)
        i += L + _fr.integers(2, 6)
    i += 1


def render(stills=None):
    os.makedirs(OUT, exist_ok=True)
    env, fig, txt = Layer(), Layer(), Layer()
    post = Post()
    cam = Camera()
    parts = Particles()
    motes = Motes()
    events = []          # (t_real, kind, pan, extra)
    lastk = {"M": math.floor(p_motivation(0)), "D": math.floor(p_discipline(0))}
    last_day = 1
    dissolved = False
    ember_pos = None
    writer = None if stills else VideoWriter(os.path.join(OUT, NAME + "_video.mp4"))
    frames = range(N) if not stills else stills

    f_label = font(30, "Inter-Bold")
    f_daylab = font(28, "Inter-SemiBold")
    f_day = font(112, "InterDisplay-Bold")
    f_p1 = font(40, "Inter-SemiBold")
    f_p2 = font(124, "InterDisplay-Black")
    f_p3 = font(58, "InterDisplay-Bold")

    prev_tau = 0.0
    sim_frames = range(N)
    for fi in sim_frames:
        t = fi * dt
        tau = taus[fi]
        dtau = tau - prev_tau
        prev_tau = tau
        draw_now = (stills is None) or (fi in stills)

        # ---------------- characters
        pm, vm = p_motivation(tau), v_motivation(tau)
        pd = p_discipline(tau)
        vd = D_V if D_START < tau and pd < P_END - 0.05 else 0.0
        jm = walk_pose(pm, vm, t)
        w_tired = smoothstep(M_STOPT - 0.9, M_STOPT + 0.2, tau)
        sink = 0.18 * smoothstep(TAU_DISSOLVE, TAU_DISSOLVE + 1.2, tau)
        jm = blend_pose(jm, tired_pose(t, sink), w_tired)
        jd = walk_pose(pd, vd, t)
        w_vic = smoothstep(TAU_ARRIVE + 0.1, TAU_ARRIVE + 0.6, tau)
        jd = blend_pose(jd, victory_pose(t, w_vic), w_vic)

        # Motivation's light: fading, flickering, turning red
        fade = smoothstep(M_DEC, M_STOPT + 1.5, tau)
        m_bright = 1 - 0.45 * fade
        if tau > M_DEC + 0.6:
            m_bright *= FLICK[fi] if fade > 0.1 else 1
        m_col = mix(WHITE, RED, smoothstep(M_DEC + 0.5, M_STOPT + 1.0, tau) * 0.9)
        m_alpha = m_bright * (1 - smoothstep(TAU_DISSOLVE, TAU_DISSOLVE + 0.9, tau))

        # footstep events
        for who, p, v in (("M", pm, vm), ("D", pd, vd)):
            k = math.floor(p)
            if k != lastk[who] and v > 0.05:
                events.append((t, "step_" + who, (slot(k)[0] - cam.wx) * cam.s / W * 1.4, v))
            lastk[who] = k
        if fade > 0.1 and FLICK[fi] < 0.99 and (fi == 0 or FLICK[fi - 1] >= 0.99) and m_alpha > 0.05:
            events.append((t, "glitch", 0.0, fi))
        d = day_of(tau)
        if d != last_day:
            events.append((t, "tick", 0.0, d))
            last_day = d

        # dissolve into embers
        if tau >= TAU_DISSOLVE and tau < TAU_DISSOLVE + 1.0:
            rng = parts.rng
            segs = pose_points(jm)
            n = int(55 * dtau / 0.033)
            pts = []
            for _ in range(n):
                a, b = segs[rng.integers(len(segs))]
                u = rng.random()
                pts.append(jm[a] * (1 - u) + jm[b] * u + rng.normal(0, 0.04, 2))
            if rng.random() < 0.5:
                pts += list(jm["head"] + rng.normal(0, HEAD_R_EMIT, (10, 2)))
            parts.emit(np.array(pts), vel=(0.5, 0.7), spread=0.6, size=(0.02, 0.05))
            if not dissolved:
                dissolved = True
                ember_pos = slot(S_STOP) + np.array([-0.2, 0.05])
        parts.step(dtau)

        # ---------------- camera
        if tau < TAU_PASS + 1.0:
            pts = [jm["head"] + [0, 0.6], jm["foot1"], slot(pm + vm * 0.5) + [0.6, 3.2], jd["head"] + [0, 0.6], jd["foot2"],
                   jd["foot1"] - [1.2, 0]]
            if tau < 1.5:
                pts = [p * 1 for p in pts] + [slot(-6), slot(2) + [0, 3.4]]
            cam.fit(pts, (120, 780, W - 120, 1480), 118, 0.16)
        elif tau < TAU_ARRIVE - 2.6:
            pts = [jd["head"] + [0, 0.7], jd["foot1"] - [1.6, 0.2], slot(pd + 3) + [0, 0.5]]
            cam.fit(pts, (160, 800, W - 160, 1480), 100, 0.06)
        else:
            pts = [slot(S_STOP - 3) + [0, -0.4], ((NS + 4.2) * SW, NS * SH + 3.6)]
            cam.fit(pts, (70, 980, W - 70, 1640), 200, 0.04)

        if not draw_now:
            continue

        # ---------------- draw
        for L in (env, fig, txt):
            L.clear()
        c = env.canvas
        intro = smoothstep(0.0, 0.9, t)
        outro = 1 - smoothstep(DUR - 0.35, DUR, t)
        master = intro * outro

        motes.draw(c, cam, t)
        # faint mass under the staircase
        grad = skia.GradientShader.MakeLinear(
            [skia.Point(0, cam.pt((0, NS * SH))[1]), skia.Point(0, cam.pt((0, -2))[1])],
            [skia.Color4f(1, 1, 1, 0.0), skia.Color4f(1, 1, 1, 0.022)])
        pf = skia.Paint(AntiAlias=True)
        pf.setShader(grad)
        c.drawPath(stair_fill(cam), pf)
        c.drawPath(stair_path(cam), paint(WHITE, 0.75, max(1.6, 0.045 * cam.s)))
        # summit flag
        flag_a = smoothstep(TAU_ARRIVE - 5, TAU_ARRIVE - 3, tau)
        draw_flag(fig.canvas, cam, t, flag_a)

        # ember remnant where Motivation died
        if ember_pos is not None:
            ea = smoothstep(TAU_DISSOLVE + 0.3, TAU_DISSOLVE + 1.4, tau) * (0.75 + 0.25 * math.sin(t * 4))
            sx, sy = cam.pt(ember_pos)
            fig.canvas.drawCircle(sx, sy, max(4.0, 0.08 * cam.s), paint(RED, ea))
            fig.canvas.drawCircle(sx + 0.12 * cam.s, sy - 0.02 * cam.s, max(2.5, 0.05 * cam.s), paint(RED, ea * 0.7))

        f = fig.canvas
        if m_alpha > 0.003:
            draw_figure(f, jm, cam, m_col, m_alpha)
        parts.draw(f, cam, WHITE, RED)
        d_glow = 1.0 + 0.6 * smoothstep(TAU_ARRIVE, TAU_ARRIVE + 0.3, tau) * math.exp(-max(0, tau - TAU_ARRIVE - 0.3) * 1.2)
        draw_figure(f, jd, cam, WHITE, min(1, d_glow))

        # labels
        lab_size = clamp(cam.s / 95, 0.55, 1.0)
        for j, name, col, a in (
                (jm, "MOTIVATION", m_col, m_alpha * smoothstep(0.3, 1.0, t) * (1 - smoothstep(TAU_PASS - 1.4, TAU_PASS - 0.7, tau))),
                (jd, "DISCIPLINE", WHITE, smoothstep(0.5, 1.2, t) * (1 - smoothstep(TAU_ARRIVE - 2.5, TAU_ARRIVE - 1.5, tau)))):
            if a <= 0.01:
                continue
            hx, hy = cam.pt(j["head"])
            fl = font(30 * lab_size, "Inter-Bold")
            draw_spaced(txt.canvas, name, hx, hy - (HEAD_R + 0.55) * cam.s - 6, fl, 5 * lab_size, paint(col, a))

        # day counter
        tc = txt.canvas
        dc_a = smoothstep(0.4, 1.1, t) * (1 - 0.45 * smoothstep(T_PUNCH1 - 0.3, T_PUNCH1 + 0.3, t))
        day = day_of(tau)
        pulse = math.exp(-max(0, t - T_ARRIVE) * 2.5) if t >= T_ARRIVE else 0
        draw_spaced(tc, "DAY", W / 2, 268, f_daylab, 12, paint(WHITE, dc_a * 0.7))
        dcol = mix(WHITE, RED, smoothstep(T_ARRIVE - 0.05, T_ARRIVE + 0.1, t))
        draw_spaced(tc, str(day), W / 2, 388, f_day, 4, paint(dcol, dc_a))

        # punchline
        def reveal(t0):
            u = ease_out((t - t0) / 0.45)
            return u, (1 - u) * 34
        if t >= T_PUNCH1:
            u, off = reveal(T_PUNCH1)
            draw_runs(tc, [("MOTIVATION", paint(RED, u)),
                           (" GETS YOU STARTED.", paint(WHITE, u * 0.8))],
                      W / 2, 600 + off, f_p1, 4)
        if t >= T_PUNCH2:
            u, off = reveal(T_PUNCH2)
            draw_spaced(tc, "DISCIPLINE", W / 2, 768 + off, f_p2, 4, paint(WHITE, u))
            u2, off2 = reveal(T_PUNCH2 + 0.18)
            draw_spaced(tc, "GETS YOU THERE.", W / 2, 858 + off2, f_p3, 7, paint(WHITE, u2 * 0.92))

        # ---------------- composite
        flash = 0.0
        if t >= T_ARRIVE:
            flash = 0.35 * math.exp(-(t - T_ARRIVE) * 3.0)
        e = bloom(env.rgb(), (0.9, (4, 0.7), (22, 0.35)))
        g = bloom(fig.rgb(), (1.0, (5, 0.9), (18, 0.8), (60, 0.55 + flash * 2)))
        x = bloom(txt.rgb(), (1.0, (6, 0.7), (26, 0.45)))
        img = (e + g + x) * master
        frame = post.apply(img, fi)
        if stills:
            import PIL.Image
            PIL.Image.fromarray(frame).save(os.path.join(OUT, f"still_{fi:04d}.png"))
        else:
            writer.write(frame)
        if fi % 60 == 0:
            print(f"frame {fi}/{N}", flush=True)

    if stills:
        return
    writer.close()
    build_audio(events, os.path.join(OUT, NAME + "_sfx.wav"))
    mux(os.path.join(OUT, NAME + "_video.mp4"), os.path.join(OUT, NAME + "_sfx.wav"),
        os.path.join(OUT, NAME + ".mp4"))
    os.remove(os.path.join(OUT, NAME + "_video.mp4"))
    print("done", os.path.join(OUT, NAME + ".mp4"))


HEAD_R_EMIT = 0.18


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=T_ARRIVE), gain=0.55, fade_in=1.2, fade_out=2.5, stop=DUR)
    # second, darker layer that swells while Motivation dies, then falls away
    pad = sfx.drone(DUR, seed=9) * 0.6
    tt = np.arange(len(pad)) / sfx.SR
    pad *= np.clip((tt - tau_to_t(M_DEC)) / 3, 0, 1) * (1 - np.clip((tt - tau_to_t(TAU_DISSOLVE + 1.5)) / 2, 0, 1))
    m.add(0, pad * 0.7, 1.0, 0, 0.3)

    n_tick = 0
    last_tick = -1
    for t, kind, pan, extra in events:
        pan = float(np.clip(pan, -0.8, 0.8))
        if kind == "step_M":
            m.add(t, sfx.step_light(int(t * 100)), 0.32 * (0.5 + 0.5 * min(1, extra / 3)), pan, 0.15)
        elif kind == "step_D":
            m.add(t, sfx.step_heavy(int(t * 100)), 0.55, pan, 0.25)
        elif kind == "glitch":
            m.add(t, sfx.glitch(extra), 0.5, pan, 0.2)
        elif kind == "tick":
            if t - last_tick > 0.07:
                n_tick += 1
                m.add(t, sfx.tick(2400 + (n_tick % 2) * 300), 0.35, 0.0, 0.05)
                last_tick = t

    m.add(tau_to_t(M_DEC + 0.4), sfx.power_down(3.0), 0.55, -0.1, 0.4)
    tp = tau_to_t(SLOW_A)
    m.add(tp - 0.6, sfx.whoosh(1.0, 200, 3000, 0.85, seed=3), 0.7, 0, 0.5)
    m.add(tp + 0.15, sfx.heartbeat(), 0.9, 0, 0.3)
    m.add(tp + 1.05, sfx.heartbeat(), 0.75, 0, 0.3)
    m.add(tau_to_t(TAU_DISSOLVE), sfx.sparkle(2.2), 0.8, 0.1, 0.6)
    m.add(T_ARRIVE - 3.0, sfx.riser(3.0), 0.55, 0, 0.3)
    m.add(T_ARRIVE + 0.02, sfx.boom(4.0), 1.0, 0, 0.5)
    m.add(T_PUNCH1, sfx.whoosh(0.5, 800, 9000, 0.5, seed=8), 0.35, -0.2, 0.3)
    m.add(T_PUNCH1 + 0.05, sfx.text_hit(1), 0.55, 0, 0.4)
    m.add(T_PUNCH2 - 0.05, sfx.whoosh(0.5, 600, 9000, 0.6, seed=9), 0.45, 0.2, 0.3)
    m.add(T_PUNCH2 + 0.05, sfx.text_hit(2), 0.85, 0, 0.5)
    m.add(T_PUNCH2 + 0.25, sfx.text_hit(3) * 0.6, 0.6, 0, 0.6)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}s  frames {N}  arrive {T_ARRIVE:.2f}s  pass(t) {tau_to_t(TAU_PASS):.2f}s")
    if "--stills" in sys.argv:
        ts = [0.5, 2.5, 5.0, 8.0, tau_to_t(TAU_PASS), tau_to_t(TAU_PASS) + 1.5, T_ARRIVE - 1.5, T_ARRIVE + 0.3, DUR - 0.6]
        render(stills=sorted(int(x * FPS) for x in ts))
    else:
        render()
