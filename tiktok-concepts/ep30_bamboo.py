"""EP30 - PATIENCE VS IMPATIENCE  (the bamboo)

One clear scene, big characters. Two gardeners, two plots, YEAR counter.
YEAR 1  both plant a seed and water it. Nothing grows. Impatience taps his foot.
YEAR 2  Impatience digs his seed up ("NOTHING?!") and plants flowers: they grow
        fast and bloom red. He points and laughs at Patience watering bare dirt.
YEAR 3  winter: his flowers die. He plants again. Patience keeps watering.
YEAR 4  same. Camera dives UNDERGROUND: under Patience's plot a huge root
        network has been growing the whole time.
YEAR 5  the bamboo explodes out of the ground and shoots to the sky; the camera
        follows it up, then pulls back. Impatience stares, jaw dropped.
END (black, centred) 4 YEARS UNDERGROUND. / 6 WEEKS TO THE SKY.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import FPS, H, RED, WHITE, W, Camera, Particles, build_pose, clamp, draw_spaced, ease_out, font, mix, paint, smoothstep
from kit import CX, GREY, Log, Video, blend, caption, crossed, draw_body, ending, kneel, mirror, sit, stand
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep30_bamboo"
dt = 1 / FPS
IMP_X, PAT_X = -2.55, 0.9            # gardeners
PLOT_I, PLOT_P = -1.3, 2.2          # plots
YEARS = [0.0, 3.2, 6.4, 9.0, 12.2]  # start of years 1..5
WINTERS = [(5.4, 6.4), (8.2, 9.0)]
UNDER = (10.0, 11.8)
SHOOT = 12.6
TILT = (13.0, 15.2)
PULL = (15.2, 16.4)
END_T = 16.9
DUR = 20.9
BAMBOO_H = 30.0
FLOWERS = [(3.9, 5.4), (6.7, 8.2), (9.3, 99.0)]   # (planted, dies)


def year(t):
    return sum(1 for y in YEARS if t >= y)


def winter(t):
    return max(smoothstep(a, a + 0.3, t) * (1 - smoothstep(b - 0.3, b, t)) for a, b in WINTERS)


def bamboo_h(t):
    if t < SHOOT:
        return 0.0
    u = (t - SHOOT) / (TILT[1] - SHOOT)
    return BAMBOO_H * clamp(u) ** 1.6


def watering(x, t):
    j = stand(x, 0.25, 1.35, 0.25, 0.4, 0.3, 0.35)
    return j


def target(t):
    """camera (wx, wy, scale)."""
    if t < UNDER[0]:
        return 0.0, 1.6, 125
    if t < UNDER[1]:
        return PLOT_P - 0.6, -1.6, 140
    if t < SHOOT:
        return 0.0, 1.6, 125
    if t < TILT[0]:
        return 0.6, 1.8, 125
    if t < TILT[1]:
        return PLOT_P - 0.4, max(1.8, bamboo_h(t) - 3.0), 125
    s_full = (1500 - 380) / (BAMBOO_H + 2.0)
    return 0.2, (BAMBOO_H + 2.0) / 2 - 1.0, s_full


def flower(c, cam, x, grow, dead, k):
    if grow <= 0.01:
        return
    h = 1.7 * grow
    droop = 0.6 * dead
    base = np.array([x + 0.35 * k, 0.0])
    top = base + np.array([0.35 * droop, h * (1 - 0.45 * dead)])
    col = mix(RED, GREY, dead)
    c.drawLine(*cam.pt(base), *cam.pt(top), paint(mix(WHITE, GREY, dead), 0.9, max(2, 0.04 * cam.s)))
    r = (0.12 + 0.12 * grow) * cam.s
    tx, ty = cam.pt(top)
    for q in range(5):
        a = q * 1.256 + 0.3 * k
        c.drawCircle(tx + math.cos(a) * r * 0.8, ty + math.sin(a) * r * 0.8, r * 0.6, paint(col, 0.95))
    c.drawCircle(tx, ty, r * 0.4, paint(WHITE, 0.9))


def roots(c, cam, x, grow, t, big=True):
    rng = np.random.default_rng(3 if big else 4)
    if grow <= 0:
        return

    def branch(p, ang, L, depth):
        if depth == 0 or L < 0.08:
            return
        end = p + np.array([math.sin(ang), -math.cos(ang)]) * L * min(1, grow * 1.3)
        c.drawLine(*cam.pt(p), *cam.pt(end), paint(WHITE, 0.85, max(1.5, 0.03 * cam.s * depth / 4)))
        for da in (-0.55, 0.5):
            branch(end, ang + da + rng.normal(0, 0.15), L * 0.72, depth - 1)

    for a in (-1.0, -0.4, 0.2, 0.8):
        branch(np.array([x, -0.05]), a, 1.1 if big else 0.25, 6 if big else 2)


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    drops = Particles(2)
    soil = Particles(3)
    snow = Particles(4)
    rng = np.random.default_rng(5)
    cam = Camera()
    cam.sx, cam.sy = CX, 1250.0
    cam.wx, cam.wy, cam.s = target(0.0)
    for fi in range(v.n):
        t = fi * dt
        y = year(t)
        for k, ty in enumerate(YEARS):
            if t >= ty + 0.05:
                log.once(f"y{k}", ty + 0.05, "year", k + 1)
        for k, (tp, td) in enumerate(FLOWERS):
            if t >= tp:
                log.once(f"fl{k}", tp, "plant", k)
            if t >= td:
                log.once(f"fd{k}", td, "die", k)
        for key, tt, kind in (("go", 0.0, "go"), ("dig", 3.4, "dig"), ("lol", 4.6, "lol"), ("under", UNDER[0], "under"),
                              ("rumble", SHOOT - 0.6, "rumble"), ("shoot", SHOOT, "shoot"), ("pull", PULL[0], "pull"),
                              ("end", END_T, "end"), ("end2", END_T + 1.0, "end2")):
            if t >= tt:
                log.once(key, tt, kind)
        watering_p = t < SHOOT - 0.3 and not (UNDER[0] <= t < UNDER[1])
        if watering_p and rng.random() < 0.6:
            drops.emit(np.array([[PAT_X + 1.05, 1.25]]), vel=(0.6, -1.0), spread=0.3, life=(0.3, 0.5), size=(0.02, 0.04))
        if t < 3.0 and rng.random() < 0.5:
            drops.emit(np.array([[IMP_X + 1.05, 1.25]]), vel=(0.6, -1.0), spread=0.3, life=(0.3, 0.5), size=(0.02, 0.04))
        if 3.3 <= t < 3.8 and rng.random() < 0.8:
            soil.emit(np.array([[PLOT_I, 0.1]]), vel=(-0.5, 2.0), spread=0.8, life=(0.3, 0.6), size=(0.03, 0.06))
        if SHOOT <= t < SHOOT + 0.3:
            soil.emit(np.array([[PLOT_P, 0.1]] * 6), vel=(0, 3.0), spread=1.5, life=(0.4, 0.9), size=(0.04, 0.09))
        if winter(t) > 0.05 and rng.random() < 0.9:
            snow.emit(np.array([[rng.uniform(-4.5, 4.0), 5.0]]), vel=(0.2, -1.2), spread=0.2, life=(2.0, 3.0), size=(0.02, 0.04))
        drops.step(dt)
        soil.step(dt)
        snow.step(dt)
        wx, wy, s = target(t)
        k_ = 0.12 if t < TILT[0] else 0.25 if t < TILT[1] else 0.08
        cam.wx += (wx - cam.wx) * k_
        cam.wy += (wy - cam.wy) * k_
        cam.s = math.exp(math.log(cam.s) + (math.log(s) - math.log(cam.s)) * k_)
        shake = 10 * smoothstep(SHOOT - 0.6, SHOOT - 0.4, t) * (1 - smoothstep(SHOOT + 0.3, SHOOT + 0.7, t))
        cam.sx = CX + shake * math.sin(t * 80)
        if not v.wants(fi):
            continue

        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        w = winter(t)
        gy = cam.pt((0, 0))[1]
        # soil
        sp = skia.Paint(AntiAlias=True)
        sp.setShader(skia.GradientShader.MakeLinear([skia.Point(0, gy), skia.Point(0, gy + 4 * cam.s)],
                                                    [skia.Color4f(0.09, 0.09, 0.1, 1), skia.Color4f(0.02, 0.02, 0.02, 1)]))
        e.drawRect(skia.Rect(0, gy, W, H), sp)
        e.drawLine(0, gy, W, gy, paint(mix(WHITE, WHITE, w), 0.55 + 0.35 * w, 3 + 3 * w))
        for px in (PLOT_I, PLOT_P):
            l, tp = cam.pt((px - 0.7, 0.12))
            r, _ = cam.pt((px + 0.7, 0.0))
            mound = skia.Path()
            mound.moveTo(l, gy)
            mound.quadTo((l + r) / 2, tp - 6, r, gy)
            e.drawPath(mound, paint(WHITE, 0.5, 3))
        # roots (underground reveal)
        root_g = smoothstep(0.0, UNDER[1], t)
        if cam.wy < 0.8 or t >= SHOOT:
            roots(f_, cam, PLOT_P, root_g, t, True)
            roots(f_, cam, PLOT_I, 0.4, t, False)
        if UNDER[0] + 0.2 <= t < UNDER[1]:
            a = smoothstep(UNDER[0] + 0.2, UNDER[0] + 0.4, t) * (1 - smoothstep(UNDER[1] - 0.3, UNDER[1], t))
            draw_spaced(oc, "MEANWHILE, UNDERGROUND...", CX, 560, font(44, "InterDisplay-Black"), 2, paint(WHITE, a))
        # Impatience's flowers
        for k, (tp, td) in enumerate(FLOWERS):
            if t < tp:
                continue
            if k < len(FLOWERS) - 1 and t >= FLOWERS[k + 1][0]:
                continue
            grow = ease_out(min(1, (t - tp) / 0.6))
            dead = smoothstep(td - 0.5, td + 0.2, t)
            for q in range(3):
                flower(f_, cam, PLOT_I - 0.35, grow * (1 - 0.15 * (q == 1)), dead, q)
        # bamboo
        h = bamboo_h(t)
        if h > 0:
            base = np.array([PLOT_P, 0.0])
            seg = 1.1
            n = int(h / seg) + 1
            for q in range(n):
                y0 = q * seg
                y1 = min(h, (q + 1) * seg)
                wdt = max(3, 0.16 * cam.s)
                f_.drawLine(*cam.pt((PLOT_P, y0)), *cam.pt((PLOT_P, y1 - 0.04)), paint(WHITE, 1.0, wdt))
                f_.drawLine(*cam.pt((PLOT_P - 0.12, y1)), *cam.pt((PLOT_P + 0.12, y1)), paint(WHITE, 0.9, max(2, 0.05 * cam.s)))
                if q % 2 == 1 and y1 < h - 0.5:
                    side = 1 if q % 4 == 1 else -1
                    lf = skia.Path()
                    p0 = cam.pt((PLOT_P, y1))
                    p1 = cam.pt((PLOT_P + side * 0.9, y1 + 0.4))
                    lf.moveTo(*p0)
                    lf.quadTo(*cam.pt((PLOT_P + side * 0.5, y1 + 0.45)), *p1)
                    lf.quadTo(*cam.pt((PLOT_P + side * 0.45, y1 + 0.1)), *p0)
                    f_.drawPath(lf, paint(WHITE, 0.85))
            if t < TILT[1]:
                tx, ty = cam.pt((PLOT_P, h))
                f_.drawCircle(tx, ty, 0.5 * cam.s, paint(WHITE, 0.08))
        drops.draw(f_, cam, WHITE, WHITE)
        soil.draw(f_, cam, WHITE, GREY)
        snow.draw(f_, cam, WHITE, WHITE)
        # ---------- IMPATIENCE
        if t < 2.0:
            ji = watering(IMP_X, t)
        elif t < 3.2:                                            # taps foot, arms crossed
            ji = crossed(IMP_X)
            ji["foot1"] = ji["foot1"] + [0, 0.08 * abs(math.sin(t * 12))]
        elif t < 3.9:                                            # digs it up
            dig = abs(math.sin((t - 3.2) * 9))
            ji = build_pose(np.array([IMP_X + 0.4, 1.2]), np.array([IMP_X + 0.55, 0.02]), np.array([IMP_X + 0.1, 0.02]),
                            0.9, 0.3 + 0.6 * dig, 0.2 + 0.5 * dig, 0.2, 0.2, 0.6)
        elif t < 4.5:
            ji = kneel(IMP_X + 0.4, t, 0.5)
        elif t < 5.4:                                            # points and laughs at Patience
            ji = stand(IMP_X, -0.12, 1.55, 0.3, 0.05, 0.3, -0.3, 0.03 * abs(math.sin(t * 14)))
        elif t < SHOOT:
            ji = crossed(IMP_X) if winter(t) < 0.5 else stand(IMP_X, 0.3, 0.1, 0.05, 0.2, 0.1, 0.7)
            if 6.6 <= t < 7.0 or 9.2 <= t < 9.6:
                ji = kneel(IMP_X + 0.4, t, 0.5)
        else:
            ji = stand(IMP_X, -0.15, 0.4, 0.35, 0.3, 0.3, -0.5)   # looks up, stunned
        draw_body(hc, ji, cam, RED, 1.0, 0.1)
        if t < 2.0:
            hx, hy = cam.pt(ji["hand1"])
            hc.drawRect(skia.Rect(hx, hy - 0.15 * cam.s, hx + 0.3 * cam.s, hy + 0.1 * cam.s), paint(RED, 1.0, 3, cap=False))
        # ---------- PATIENCE
        if t < SHOOT - 0.3:
            jp = watering(PAT_X, t)
            if winter(t) > 0.3:
                jp = {k: vv + [0, -0.03 * abs(math.sin(t * 20))] for k, vv in jp.items()}
        elif t < PULL[0]:
            jp = blend(watering(PAT_X, t), stand(PAT_X, -0.1, 0.3, 0.25, 0.2, 0.2, -0.45), smoothstep(SHOOT - 0.3, SHOOT, t))
        else:
            js = sit(PAT_X - 0.3, 0.0, t, 0.1)
            js = {k: vv + [0, -0.1] for k, vv in js.items()}
            jp = js
        draw_body(hc, jp, cam, WHITE, 1.0, 0.2)
        if t < SHOOT - 0.3:
            hx, hy = cam.pt(jp["hand1"])
            hc.drawRect(skia.Rect(hx, hy - 0.15 * cam.s, hx + 0.3 * cam.s, hy + 0.1 * cam.s), paint(WHITE, 1.0, 3, cap=False))
            hc.drawLine(hx + 0.3 * cam.s, hy - 0.05 * cam.s, hx + 0.45 * cam.s, hy + 0.08 * cam.s, paint(WHITE, 1.0, 3))
        # labels
        la = (1 - smoothstep(TILT[0], TILT[0] + 0.3, t)) + smoothstep(PULL[0], PULL[1], t) * 0.0
        for j, nme, col in ((ji, "IMPATIENCE", RED), (jp, "PATIENCE", WHITE)):
            sx, _ = cam.pt((j["hip"][0], 0))
            draw_spaced(tc, nme, sx, gy + 46, font(26, "Inter-Bold"), 4, paint(col, la))
        # callouts
        if 3.3 <= t < 4.0:
            hx, hy = cam.pt(ji["head"])
            draw_spaced(oc, "NOTHING?!", hx + 40, hy - 70, font(52, "InterDisplay-Black"), 2, paint(RED, 1.0))
        if 4.6 <= t < 5.4:
            hx, hy = cam.pt(ji["head"])
            draw_spaced(oc, "LOL", hx + 30, hy - 70, font(60, "InterDisplay-Black"), 2, paint(RED, 1.0))
        if SHOOT + 0.3 <= t < TILT[1] - 0.3:
            draw_spaced(oc, f"{int(bamboo_h(t))} M", CX, 640, font(110, "InterDisplay-Black"), 4, paint(WHITE, 1.0))
        # HUD
        ha = smoothstep(1.6, 1.9, t) * (1 - smoothstep(END_T - 0.6, END_T - 0.3, t))
        draw_spaced(oc, "YEAR", CX, 360, font(24, "Inter-SemiBold"), 12, paint(WHITE, 0.7 * ha))
        draw_spaced(oc, str(y), CX, 470, font(104, "InterDisplay-Bold"), 4, paint(RED if y == 5 else WHITE, ha))
        if t < 1.8:
            caption(oc, "PATIENCE VS IMPATIENCE", 560, 1 - smoothstep(1.4, 1.8, t), WHITE, 56)
        ending(oc, t, END_T - 0.3, [(END_T, "4 YEARS", WHITE, 110), (END_T + 0.25, "UNDERGROUND.", WHITE, 100),
                                    (END_T + 1.0, "6 WEEKS", RED, 110), (END_T + 1.25, "TO THE SKY.", RED, 100)], gap=125)
        flash = math.exp(-(t - SHOOT) * 3) if t >= SHOOT else 0.0
        v.compose(fi, t, flash=flash * 0.8, dim=0.25 * w, fade_in=0.0)
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=SHOOT), gain=0.4, fade_in=0.3, fade_out=2.0, stop=DUR)
    t_ = 0.3
    while t_ < SHOOT - 0.3:                                             # water drops (patience)
        m.add(t_, sfx.tick(1800 + 300 * (int(t_ * 5) % 3), 0.2), 0.25, 0.3, 0.3)
        t_ += 0.45
    for t, kind, _, extra in events:
        if kind == "go":
            m.add(0.02, sfx.text_hit(5), 0.6, 0, 0.4)
        elif kind == "year":
            m.add(t, sfx.whoosh(0.4, 300, 6000, 0.6, seed=extra), 0.4, 0, 0.3)
            m.add(t + 0.05, sfx.tick(2400, 0.5), 0.5, 0, 0.1)
        elif kind == "dig":
            for q in range(4):
                m.add(t + q * 0.17, sfx.dig(q, 0.8), 0.6, -0.4, 0.2)
            m.add(t + 0.1, sfx.text_hit(2), 0.6, -0.4, 0.4)
        elif kind == "plant":
            m.add(t + 0.2, sfx.sparkle(0.8, 50, extra), 0.5, -0.4, 0.4)
            m.add(t + 0.3, sfx.chime(880, 0.25), 0.45, -0.4, 0.4)
        elif kind == "lol":
            m.add(t, sfx.laugh(4, 5, 165, 0.55), 0.55, -0.4, 0.4)
        elif kind == "die":
            if extra < 2:
                m.add(t - 0.4, sfx.power_down(0.9), 0.5, -0.4, 0.4)
                m.add(t - 0.6, sfx.whoosh(1.0, 200, 3000, 0.5, seed=7 + extra), 0.4, 0, 0.4)
        elif kind == "under":
            m.add(t, sfx.whoosh(0.6, 80, 1500, 0.6, seed=11), 0.6, 0, 0.4)
            m.add(t + 0.3, sfx.heartbeat(), 0.6, 0, 0.3)
            m.add(t + 0.5, sfx.riser(1.2), 0.35, 0, 0.3)
        elif kind == "rumble":
            m.add(t, sfx.bandnoise(1.0, 30, 300, 4) * np.linspace(0.2, 1, sfx.SR), 0.9, 0.3, 0.3)
        elif kind == "shoot":
            m.add(t, sfx.boom(4.0), 1.0, 0.2, 0.5)
            m.add(t, sfx.riser(TILT[1] - t), 0.7, 0, 0.3)
            m.add(t + 0.2, sfx.sparkle(2.4, 100, 3), 0.6, 0.2, 0.6)
        elif kind == "pull":
            m.add(t, sfx.whoosh(1.2, 100, 2500, 0.6, seed=13), 0.5, 0, 0.4)
            for q, f in enumerate((660, 880, 1320)):
                m.add(t + 0.3 + 0.05 * q, sfx.chime(f, 0.3), 0.5, 0, 0.6)
        elif kind == "end":
            m.add(t, sfx.text_hit(1), 0.7, 0, 0.4)
        elif kind == "end2":
            m.add(t, sfx.text_hit(3), 0.95, 0, 0.5)
            m.add(t, sfx.boom(2.0), 0.45, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [0.6, 2.5, 3.5, 4.2, 5.0, 5.9, 7.4, 8.6, 10.6, 11.5, 12.4, 12.9, 13.8, 14.8, 16.0, 19.0]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
