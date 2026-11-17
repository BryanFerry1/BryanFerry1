"""EP25 - EGO VS OBSESSION  (tug of war over the pit)

One shared scene, moving from the first frame: two platforms, a glowing red pit
in the middle, a rope across. EGO (left, crowd behind him) vs OBSESSION (right).
A tug meter at the top shows who is winning: the outcome builds up step by step.
The camera alternates wide shots and zooms on each character in action:
  zoom EGO: pulls hard, crowd chants, he is winning.
  zoom OBSESSION: feet sliding towards the edge, heels digging in.
  wide: Obsession one step from the void.
  zoom EGO: lets go with one hand to wave at his crowd.
  zoom OBSESSION: plants his feet, red aura, takes a step back.
  wide: momentum flips, hand over hand.
  zoom EGO's feet sliding at the edge.
  slow motion: last heave, Ego falls into the pit.
END (black, centred) EGO PULLS FOR THE CROWD. / OBSESSION PULLS / UNTIL IT'S OVER.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import (FPS, H, L_FARM, L_UARM, RED, WHITE, W, Camera, Particles, build_pose, clamp, draw_spaced,
                    ease_out, font, ik, mix, paint, rotate_pose, smoothstep)
from kit import CX, GREY, Log, Video, blend, caption, crossed, draw_body, draw_heart, ending, mirror, stand
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep25_tug_of_war"
dt = 1 / FPS
EDGE = 1.25                     # pit from -EDGE to +EDGE
ROPE_Y = 1.3
E0, O0 = -2.7, 2.7              # rest positions (rope offset m = 0)
WAVE = (7.0, 8.6)
FLIP = 9.6
FALL = 13.05
END_T = 15.6
DUR = 19.6

M_KF = [(0.0, 0.0), (1.0, 0.0), (3.0, -0.45), (5.5, -0.95), (7.0, -1.12), (9.6, -1.12), (11.0, -0.2),
        (12.2, 0.75), (13.05, 1.38), (14.0, 1.38)]

SHOTS = [  # (t, target, scale)
    (0.0, "wide", 100), (2.5, "EGO", 205), (4.1, "OBS_FEET", 215), (5.6, "wide", 100), (7.0, "EGO", 215),
    (8.6, "OBS", 220), (9.9, "wide", 100), (11.8, "EGO_FEET", 220), (12.7, "wide", 100), (14.6, "OBS", 170),
]


def keys(t, kf):
    if t <= kf[0][0]:
        return kf[0][1]
    for (t0, v0), (t1, v1) in zip(kf, kf[1:]):
        if t <= t1:
            u = (t - t0) / (t1 - t0)
            return v0 + (v1 - v0) * u * u * (3 - 2 * u)
    return kf[-1][1]


def m_of(t):
    return keys(t, M_KF)


def puller(x, t, strain, facing, one_hand=0.0, ph=0.0):
    """Leaning back, both hands on the rope at ROPE_Y. facing +1 = rope to the right."""
    shake = 0.02 * strain * math.sin(t * 37 + ph)
    hip = np.array([0.0, 1.05 - 0.12 * strain + shake])
    j = build_pose(hip, np.array([0.55, 0.02]), np.array([-0.45, 0.02]), -0.38 - 0.15 * strain, 1.5, 1.4,
                   0.1, 0.1, 0.15)
    sh = j["shoulder"]
    for i, off in ((1, 0.95), (2, 0.65)):
        tgt = np.array([off, ROPE_Y])
        if i == 2 and one_hand > 0:
            tgt = tgt * (1 - one_hand) + (sh + np.array([-0.2, 0.95])) * one_hand
        j[f"hand{i}"] = tgt
        j[f"elbow{i}"] = ik(sh, tgt, L_UARM, L_FARM, -1)
    j = {k: vv + [x, 0] for k, vv in j.items()}
    if facing < 0:
        j = mirror(j, x)
    return j


def target(t, m):
    xe, xo = E0 + m, O0 + m
    cur = SHOTS[0]
    for s in SHOTS:
        if t >= s[0]:
            cur = s
    _, who, s = cur
    if who == "wide":
        return m, 1.5, s
    if who == "EGO":
        return xe + 0.2, 1.5, s
    if who == "OBS":
        return xo - 0.2, 1.5, s
    if who == "OBS_FEET":
        return xo - 0.6, 0.6, s
    if who == "EGO_FEET":
        return xe + 0.7, 0.6, s
    return 0.0, 1.9, s


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    dust = Particles(2)
    aura = Particles(3)
    rng = np.random.default_rng(5)
    cam = Camera()
    cam.sx, cam.sy = CX, 1050.0
    cam.wx, cam.wy, cam.s = target(0.0, 0.0)
    frozen = None
    for fi in range(v.n):
        t = fi * dt
        m = m_of(t)
        dm = (m_of(t + 0.03) - m_of(t - 0.03)) / 0.06
        # ---------- events
        for k, (ts, who, s) in enumerate(SHOTS[1:], 1):
            if t >= ts:
                log.once(f"cut{k}", ts, "cut", k)
        for key, tt, kind in (("go", 0.0, "go"), ("pull", 1.0, "pull"), ("wave", WAVE[0], "wave"),
                              ("plant", 8.7, "plant"), ("flip", FLIP, "flip"), ("fall", FALL, "fall"),
                              ("end", END_T, "end"), ("end2", END_T + 0.9, "end2")):
            if t >= tt:
                log.once(key, tt, kind)
        if dm < -0.1 and rng.random() < 0.6:          # obsession's heels sliding
            dust.emit(np.array([[O0 + m - 0.45, 0.05]]) + rng.normal(0, 0.05, (2, 2)), vel=(0.8, 0.6), spread=0.4,
                      life=(0.3, 0.6), size=(0.02, 0.05))
        if dm > 0.1 and t < FALL and rng.random() < 0.6:
            dust.emit(np.array([[E0 + m + 0.5, 0.05]]) + rng.normal(0, 0.05, (2, 2)), vel=(-0.8, 0.6), spread=0.4,
                      life=(0.3, 0.6), size=(0.02, 0.05))
        if t >= 8.7 and t < 14.5 and rng.random() < 0.7:
            aura.emit(np.array([[O0 + m + rng.normal(0, 0.35), rng.uniform(0.3, 2.3)]]), vel=(0, 1.3), spread=0.4,
                      life=(0.5, 1.0), size=(0.02, 0.05))
        dust.step(dt)
        aura.step(dt)
        # ---------- camera (fast ease toward each shot)
        wx, wy, s = target(t, m)
        snap = any(abs(t - ts) < dt * 0.6 for ts, _, _ in SHOTS[1:])
        k_ = 0.5 if snap else 0.2
        cam.wx += (wx - cam.wx) * k_
        cam.wy += (wy - cam.wy) * k_
        cam.s = math.exp(math.log(cam.s) + (math.log(s) - math.log(cam.s)) * k_)
        sh = 0.0
        if t >= FALL:
            sh = 12 * math.exp(-(t - FALL) * 4)
        cam.sx = CX + sh * math.sin(t * 80)
        if not v.wants(fi):
            continue

        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        # ---------- scene
        gy = cam.pt((0, 0))[1]
        l, _ = cam.pt((-EDGE, 0))
        r, _ = cam.pt((EDGE, 0))
        e.drawLine(-50, gy, l, gy, paint(WHITE, 0.7, 3))
        e.drawLine(r, gy, W + 50, gy, paint(WHITE, 0.7, 3))
        for px in (l, r):
            e.drawLine(px, gy, px, H, paint(WHITE, 0.5, 3))
        pit = skia.Paint(AntiAlias=True)
        pit.setShader(skia.GradientShader.MakeLinear([skia.Point(0, gy), skia.Point(0, gy + 6 * cam.s)],
                                                     [skia.Color4f(0, 0, 0, 1), skia.Color4f(0.5, 0.03, 0.04, 1)]))
        e.drawRect(skia.Rect(l + 2, gy + 2, r - 2, H), pit)
        for k in range(5):                                   # embers rising from the pit
            ex = -EDGE + 0.3 + (k * 0.53 + t * 0.07 * (k + 1)) % (2 * EDGE - 0.6)
            ey = -3.0 + ((t * 0.9 + k * 0.7) % 3.0)
            f_.drawCircle(*cam.pt((ex, ey)), max(2, 0.03 * cam.s), paint(RED, 0.7))
        # crowd behind ego
        for k in range(6):
            cx_ = -5.0 + 0.42 * k + m * 0.3
            hop = 0.08 * abs(math.sin(t * 9 + k)) * (1 if t < FALL else 0)
            a = 0.55 if t < FALL else 0.3
            hx, hy = cam.pt((cx_, 1.25 + hop))
            e.drawCircle(hx, hy, 0.24 * cam.s, paint(GREY, a))
            bl, bt = cam.pt((cx_ - 0.3, 0.98 + hop))
            br, bb = cam.pt((cx_ + 0.3, 0.0))
            e.drawRoundRect(skia.Rect(bl, bt, br, bb), 0.15 * cam.s, 0.15 * cam.s, paint(GREY, 0.7 * a))
        # chants + hearts
        if 1.0 <= t < FALL:
            if int(t * 2) % 2 == 0:
                hx, hy = cam.pt((-4.0 + m * 0.3, 2.35))
                draw_spaced(tc, "EGO! EGO!", hx, hy, font(max(18, 0.3 * cam.s), "InterDisplay-Black"), 2, paint(RED, 0.9))
            for k in range(3):
                age = (t * 0.8 + k * 0.33) % 1.0
                hx, hy = cam.pt((-4.8 + 0.6 * k + m * 0.3, 1.8 + age * 1.4))
                draw_heart(f_, hx, hy, max(8, 0.12 * cam.s), 0.9 * (1 - age))
        # ---------- characters
        xe, xo = E0 + m, O0 + m
        strain_e = 0.6 + 0.4 * smoothstep(FLIP, 12.5, t)
        strain_o = 0.5 + 0.5 * smoothstep(3.0, 6.5, t) - 0.2 * smoothstep(8.7, 9.6, t)
        wave = smoothstep(WAVE[0], WAVE[0] + 0.3, t) * (1 - smoothstep(WAVE[1] - 0.3, WAVE[1], t))
        rope_e = rope_o = None
        if t < FALL:
            je = puller(xe, t, strain_e, 1, wave, 0.0)
            if wave > 0:
                je["hand2"] = je["hand2"] + [0, 0.12 * math.sin(t * 14) * wave]
        else:
            if frozen is None:
                frozen = puller(xe, t, 1.0, 1)
            u = t - FALL
            fx = -EDGE + 0.1 + 0.4 * min(1, u * 2)
            fy = -9.0 * u * u
            je = rotate_pose(frozen, frozen["hip"], -1.2 * min(1, u * 1.5))
            je = {k: vv + [fx - frozen["hip"][0], fy] for k, vv in je.items()}
        col_e = RED
        draw_body(hc, je, cam, col_e, 1.0 if t < FALL + 0.6 else max(0.0, 1 - (t - FALL - 0.6) * 2), 0.2)
        if t < 8.6 or t >= 14.6:
            jo = puller(xo, t, strain_o, -1, 0.0, 1.3)
        else:
            jo = puller(xo, t, strain_o, -1, 0.0, 1.3)
        if t >= FALL + 0.4:
            jo = blend(jo, crossed(xo), smoothstep(FALL + 0.4, FALL + 1.0, t))
        draw_body(hc, jo, cam, mix(WHITE, RED, 0.25 * smoothstep(8.7, 10, t)), 1.0, 0.45)
        aura.draw(f_, cam, RED, RED)
        dust.draw(f_, cam, WHITE, GREY)
        # rope
        ea = je["hand1"] if t < FALL else None
        oa = jo["hand2"] if t < FALL + 0.4 else None
        if ea is not None and oa is not None:
            mid = (ea + oa) / 2 + np.array([0, -0.12 + 0.04 * math.sin(t * 9)])
            p = skia.Path()
            p.moveTo(*cam.pt(ea))
            p.quadTo(*cam.pt(mid), *cam.pt(oa))
            f_.drawPath(p, paint(WHITE, 1.0, max(3, 0.06 * cam.s)))
            # marker flag at the rope centre
            fx_, fy_ = cam.pt((m, ROPE_Y - 0.1))
            fp = skia.Path()
            fp.moveTo(fx_, fy_)
            fp.lineTo(fx_ - 0.2 * cam.s, fy_ + 0.5 * cam.s)
            fp.lineTo(fx_ + 0.2 * cam.s, fy_ + 0.5 * cam.s)
            fp.close()
            f_.drawPath(fp, paint(RED, 1.0))
        elif oa is not None:                                  # slack rope falling into the pit
            u = t - FALL
            p = skia.Path()
            p.moveTo(*cam.pt(oa))
            p.quadTo(*cam.pt((EDGE + 0.1, 0.3)), *cam.pt((EDGE - 0.2, -0.5 - 3 * min(u, 0.4))))
            f_.drawPath(p, paint(WHITE, 1.0, max(3, 0.06 * cam.s)))
        else:
            hand = jo["hand2"]
            u = t - FALL
            p = skia.Path()
            p.moveTo(*cam.pt(hand))
            p.quadTo(*cam.pt((EDGE + 0.15, 0.3)), *cam.pt((EDGE - 0.15, -1.6)))
            f_.drawPath(p, paint(WHITE, 0.8, max(3, 0.06 * cam.s)))
        # labels
        for j, nme, col in ((je, "EGO", RED), (jo, "OBSESSION", WHITE)):
            if nme == "EGO" and t >= FALL + 0.3:
                continue
            fxx = (j["foot1"][0] + j["foot2"][0]) / 2
            sx, sy = cam.pt((fxx, 0))
            draw_spaced(tc, nme, sx, sy + max(30, 0.35 * cam.s), font(max(22, 0.24 * cam.s), "Inter-Bold"), 4, paint(col, 1.0))
        # ---------- tug meter (top HUD)
        ma = smoothstep(2.0, 2.4, t) * (1 - smoothstep(END_T - 0.6, END_T - 0.3, t))
        if ma > 0.01:
            x0, x1, y = 170, 790, 450
            oc.drawLine(x0, y, x1, y, paint(WHITE, 0.6 * ma, 4))
            oc.drawLine(CX, y - 16, CX, y + 16, paint(WHITE, 0.6 * ma, 3))
            px = CX + (x1 - CX) * clamp(m / 1.38, -1, 1)
            oc.drawCircle(px, y, 16, paint(RED, ma))
            draw_spaced(oc, "EGO", x0 + 10, y - 28, font(24, "Inter-Bold"), 3, paint(RED, ma))
            draw_spaced(oc, "OBSESSION", x1 - 40, y - 28, font(24, "Inter-Bold"), 3, paint(WHITE, ma))
        if t < 2.3:
            caption(oc, "EGO VS OBSESSION", 640, 1 - smoothstep(1.9, 2.3, t), WHITE, 64)
        ending(oc, t, END_T - 0.3, [(END_T, "EGO PULLS", RED, 86), (END_T + 0.25, "FOR THE CROWD.", RED, 86),
                                    (END_T + 1.0, "OBSESSION PULLS", WHITE, 86), (END_T + 1.25, "UNTIL IT'S OVER.", WHITE, 86)],
               gap=118)
        slow = smoothstep(12.6, 12.8, t) * (1 - smoothstep(13.3, 13.5, t))
        flash = math.exp(-(t - FALL - 0.3) * 3) if t >= FALL + 0.3 else 0.0
        white = 0.08 * max(0.0, 1 - min(abs(t - ts) for ts, _, _ in SHOTS[1:]) / 0.05)
        v.compose(fi, t, flash=flash, glow=0.3 * slow, white=white, fade_in=0.0)
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=FALL), gain=0.42, fade_in=0.3, fade_out=2.0, stop=DUR)
    m.add(1.0, sfx.rattle(FALL - 1.0, 7), 0.35, 0, 0.2)          # rope creak / strain all along
    t_ = 1.2
    k = 0
    while t_ < FALL:                                            # crowd chant: two hits per beat
        m.add(t_, sfx.punch_block(k) * 0.6, 0.35, -0.5, 0.3)
        m.add(t_ + 0.18, sfx.punch_block(k + 1) * 0.6, 0.35, -0.5, 0.3)
        t_ += 0.5
        k += 2
    for t, kind, _, extra in events:
        if kind == "go":
            m.add(0.02, sfx.text_hit(5), 0.7, 0, 0.4)
        elif kind == "pull":
            m.add(t, sfx.breath(1, 0.9), 0.6, -0.3, 0.2)
            m.add(t + 0.2, sfx.breath(2, 0.9), 0.6, 0.3, 0.2)
        elif kind == "cut":
            m.add(t - 0.05, sfx.whoosh(0.25, 500, 9000, 0.6, seed=extra), 0.45, 0, 0.2)
            m.add(t, sfx.punch_hit(extra, 0.6), 0.35, 0, 0.2)
        elif kind == "wave":
            m.add(t, sfx.applause(1.5, 45, 2), 0.5, -0.5, 0.3)
            m.add(t + 0.1, sfx.chime(880, 0.3), 0.4, -0.4, 0.4)
        elif kind == "plant":
            m.add(t, sfx.step_heavy(3), 0.9, 0.4, 0.3)
            m.add(t + 0.1, sfx.heartbeat(), 0.8, 0, 0.3)
            m.add(t + 0.85, sfx.heartbeat(), 0.85, 0, 0.3)
        elif kind == "flip":
            m.add(t, sfx.power_up(70), 0.9, 0.3, 0.4)
            for q in range(8):
                m.add(t + 0.35 + q * 0.38, sfx.punch_hit(20 + q, 0.6), 0.4, 0.3, 0.2)
            m.add(t + 0.8, sfx.riser(FALL - t - 0.8), 0.5, 0, 0.3)
        elif kind == "fall":
            m.add(t - 0.1, sfx.whoosh(1.0, 100, 5000, 0.5, seed=8), 0.8, -0.2, 0.4)
            m.add(t + 0.3, sfx.boom(4.0), 1.0, 0, 0.5)
            m.add(t + 0.35, sfx.power_down(1.5), 0.5, -0.2, 0.4)
        elif kind == "end":
            m.add(t, sfx.text_hit(1), 0.7, 0, 0.4)
        elif kind == "end2":
            m.add(t, sfx.text_hit(3), 0.95, 0, 0.5)
            m.add(t, sfx.boom(2.0), 0.45, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [0.3, 1.6, 3.2, 4.8, 6.3, 7.6, 9.2, 10.6, 12.1, 13.0, 13.6, 14.9, 17.5]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
