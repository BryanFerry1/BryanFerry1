"""EP29 - EGO VS OBSESSION  (the rematch, sequel of EP07)

Same ring as EP07, zooms format, three rounds.
ROUND 1  EGO dominates: jab after jab, Obsession's head snaps back.
ROUND 2  EGO's uppercut: Obsession goes down. The count starts... and EGO turns
         his back, walks to the ropes and celebrates with the crowd (phones,
         flashes, arms up). Behind him, at 7, Obsession gets up (red aura).
         Ego turns around: shocked.
ROUND 3  Obsession is relentless, pushes Ego to the ropes. Final cross: K.O.
         Obsession doesn't celebrate. He just walks back to his corner.
END (black, centred) LAST TIME EGO WON. / THIS TIME HE CELEBRATED / TOO EARLY.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import FPS, RED, WHITE, W, Camera, Particles, clamp, draw_spaced, ease_out, font, mix, paint, rotate_pose, run_pose, smoothstep
from kit import CX, GREY, Log, Video, arms_up, blend, caption, draw_body, ending, flex, stand
import ep07_ego_wins as e7
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep29_ring_rematch"
dt = 1 / FPS
R2, R3 = 5.0, 10.0
E_JABS = [1.4, 1.7, 2.0, 2.7, 3.0, 3.3, 3.9, 4.2, 4.5]
UPPER = 6.4
COUNT = [6.9 + 0.32 * i for i in range(7)]       # 1..7
O_RISE = (8.0, 8.9)
TURN = 9.3
O_PUNCH = [10.4, 10.65, 10.9, 11.4, 11.65, 11.9, 12.2, 12.45, 12.7, 12.95]
E_BLOCK = {10.4, 10.65, 10.9, 11.4}
KO = 13.45
WALK = 14.3
END_T = 15.8
DUR = 19.8

SHOTS = [(0.0, "wide", 110), (1.6, "EGO", 195), (2.6, "OBS", 205), (3.6, "wide", 110), (5.6, "EGO", 205),
         (6.8, "wide", 110), (7.3, "EGO", 185), (8.2, "OBS", 195), (9.3, "EGO", 215), (9.9, "wide", 110),
         (11.4, "OBS", 190), (12.4, "EGO", 200), (13.1, "wide", 118), (14.2, "OBS", 170)]


def pulse(t, t0, rise=0.08, hold=0.05, fall=0.16):
    return e7.pulse(t, t0, rise, hold, fall)


def keys(t, kf):
    return e7.keys(t, kf)


EX = [(0, -1.2), (R2, -1.0), (6.9, -1.0), (7.6, -2.6), (TURN + 0.6, -2.6), (10.3, -1.6), (12.9, -2.6), (KO, -2.6)]
OX = [(0, 1.2), (R2, 1.0), (UPPER, 0.9), (R3, 0.9), (10.3, 0.0), (12.9, -1.3), (KO, -1.3), (WALK, -1.1), (16.0, 2.4)]


def target(t, xe, xo):
    cur = SHOTS[0]
    for s in SHOTS:
        if t >= s[0]:
            cur = s
    _, who, s = cur
    if who == "wide":
        return (xe + xo) / 2 * 0.6, 1.6, s
    if who == "EGO":
        return xe + 0.3, 1.7, s
    if who == "OBS":
        return xo - 0.3, 1.6 if not (O_RISE[0] - 1.2 <= t < O_RISE[1]) else 1.0, s
    return 0.0, 1.6, s


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    sparks = Particles(9)
    aura = Particles(10)
    rng = np.random.default_rng(5)
    cam = Camera()
    cam.sx, cam.sy = CX, 1240.0
    cam.wx, cam.wy, cam.s = target(0.0, -1.2, 1.2)
    frozen_o = frozen_e = None
    flashes = []
    next_flash = 7.1
    for fi in range(v.n):
        t = fi * dt
        xe, xo = keys(t, EX), keys(t, OX)
        for k, (ts, who, s) in enumerate(SHOTS[1:], 1):
            if t >= ts:
                log.once(f"cut{k}", ts, "cut", k)
        for i, tj in enumerate(E_JABS):
            if t >= tj:
                log.once(f"ej{i}", tj, "hit", i)
        for i, tj in enumerate(O_PUNCH):
            if t >= tj:
                log.once(f"op{i}", tj, "block" if tj in E_BLOCK else "hit", i)
        for i, tc_ in enumerate(COUNT):
            if t >= tc_:
                log.once(f"c{i}", tc_, "count", i + 1)
        for key, tt, kind in (("bell1", 0.5, "bell"), ("bell2", R2, "bell"), ("bell3", R3, "bell"), ("upper", UPPER, "ko1"),
                              ("party", 7.2, "party"), ("rise", O_RISE[0], "rise"), ("turn", TURN, "turn"),
                              ("ko", KO, "ko2"), ("walk", WALK, "walk"), ("end", END_T, "end"), ("end2", END_T + 1.0, "end2")):
            if t >= tt:
                log.once(key, tt, kind)
        while 7.1 <= t < TURN and t >= next_flash:
            flashes.append((next_flash, int(rng.integers(8))))
            log.add(next_flash, "shutter", len(flashes))
            next_flash += rng.uniform(0.12, 0.3)
        if O_RISE[0] - 0.3 <= t < 13.0 and rng.random() < 0.7:
            aura.emit(np.array([[xo + rng.normal(0, 0.35), rng.uniform(0.3, 2.3)]]), vel=(0, 1.2), spread=0.4,
                      life=(0.5, 1.0), size=(0.02, 0.05))
        sparks.step(dt)
        aura.step(dt)
        wx, wy, s = target(t, xe, xo)
        snap = any(abs(t - ts) < dt * 0.6 for ts, _, _ in SHOTS[1:])
        k_ = 0.5 if snap else 0.2
        cam.wx += (wx - cam.wx) * k_
        cam.wy += (wy - cam.wy) * k_
        cam.s = math.exp(math.log(cam.s) + (math.log(s) - math.log(cam.s)) * k_)
        shake = 0.0
        for tt, a in ((UPPER, 12.0), (KO, 16.0)):
            if t >= tt:
                shake = max(shake, a * math.exp(-(t - tt) * 5))
        cam.sx = CX + shake * math.sin(t * 85)
        if not v.wants(fi):
            continue

        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        e7.draw_spot(e, cam, 1.0, 0.0)
        e7.draw_ring(e, cam, 1.0, 0.0)
        party = smoothstep(7.1, 7.5, t) * (1 - smoothstep(TURN, TURN + 0.4, t))
        e7.draw_crowd(e, cam, t, 1.0, party, party, flashes, t)
        # ---------- EGO
        if t < UPPER - 0.3 or (R2 <= t < UPPER - 0.3):
            jab = max([pulse(t, tj) for tj in E_JABS] + [0.0])
            je = e7.boxer(xe, t, t, jab=jab, bob_ph=0.0)
        elif t < 6.9:
            up = smoothstep(UPPER - 0.25, UPPER + 0.02, t) * (1 - smoothstep(UPPER + 0.2, UPPER + 0.5, t))
            je = e7.boxer(xe, t, t, upper=up)
        elif t < TURN:
            w = smoothstep(6.9, 7.3, t)
            cele = blend(arms_up(0, t), flex(0, t), 0.5 + 0.5 * math.sin(t * 3))
            cele = {k: vv + [xe, 0] for k, vv in cele.items()}
            je = blend(e7.boxer(xe, t, t), cele, w)
        elif t < R3:
            je = e7.boxer(xe, t, t, lean_extra=-0.35, guard=0.3)
            je["head"] = je["head"] + [-0.08, 0.05]
        elif t < KO:
            hits = [tj for tj in O_PUNCH if tj not in E_BLOCK]
            hit = max([pulse(t, tj + 0.06, 0.06, 0.05, 0.25) for tj in hits] + [0.0])
            je = e7.boxer(xe, t, t, hit=hit, tired=smoothstep(11.0, 12.9, t))
        else:
            if frozen_e is None:
                frozen_e = e7.boxer(xe, t, t, hit=1.0)
            u = (t - KO) / 0.7
            rot = rotate_pose(frozen_e, frozen_e["foot2"].copy(), 1.5 * ease_out(min(1, u * 1.2)))
            je = blend(rot, e7.supine(xe + 0.4), smoothstep(0.45, 1.0, u))
            je = e7.mirror(je, xe + 0.1)
        col_e = mix(RED, mix(RED, GREY, 0.5), smoothstep(KO, KO + 1.0, t))
        draw_body(hc, je, cam, col_e, 1.0, 0.25)
        e7.draw_gloves(hc, cam, je, RED, 1.0)
        # ---------- OBSESSION (mirrored, faces left)
        if t < UPPER:
            hit = max([pulse(t, tj + 0.06, 0.06, 0.05, 0.25) for tj in E_JABS] + [0.0])
            jo = e7.boxer(0.0, t, t, hit=hit, bob_ph=1.3)
            jo = e7.mirror({k: vv + [xo, 0] for k, vv in jo.items()}, xo)
        elif t < O_RISE[0]:
            if frozen_o is None:
                jf = e7.boxer(0.0, t, t, hit=1.0)
                frozen_o = (jf, jf["foot2"].copy())
            jf, pv = frozen_o
            u = (t - UPPER) / 0.7
            rot = rotate_pose(jf, pv, 1.5 * ease_out(min(1, u * 1.2)))
            jo = blend(rot, e7.supine(0.3), smoothstep(0.45, 1.0, u))
            jo = e7.mirror({k: vv + [xo, 0] for k, vv in jo.items()}, xo)
        elif t < O_RISE[1]:
            u = smoothstep(*O_RISE, t)
            jo = blend(e7.supine(0.3), e7.kneel(0.0, t, 1.0), smoothstep(0.0, 0.5, u))
            jo = blend(jo, e7.boxer(0.0, t, t), smoothstep(0.5, 1.0, u))
            jo = e7.mirror({k: vv + [xo, 0] for k, vv in jo.items()}, xo)
        elif t < WALK:
            jab = max([pulse(t, tj) for tj in O_PUNCH] + [0.0])
            cross = pulse(t, KO - 0.12, 0.12, 0.25, 0.35)
            jo = e7.boxer(0.0, t, t, jab=jab if t < KO - 0.3 else 0.0, cross=cross, bob_ph=1.3)
            jo = e7.mirror({k: vv + [xo, 0] for k, vv in jo.items()}, xo)
        else:
            walk = run_pose(xo, (t - WALK) * 6, 0.3)
            jo = blend(e7.mirror({k: vv + [xo, 0] for k, vv in e7.boxer(0.0, t, t).items()}, xo), walk,
                       smoothstep(WALK, WALK + 0.4, t))
        col_o = mix(WHITE, RED, 0.3 * smoothstep(O_RISE[0], O_RISE[1], t))
        draw_body(hc, jo, cam, col_o, 1.0, 0.45 * smoothstep(O_RISE[0], O_RISE[1], t))
        e7.draw_gloves(hc, cam, jo, WHITE, 1.0)
        aura.draw(f_, cam, RED, RED)
        if O_RISE[0] <= t < O_RISE[0] + 0.8:
            age = t - O_RISE[0]
            cx_, cy_ = cam.pt((xo, 1.1))
            f_.drawCircle(cx_, cy_, (0.5 + 3.0 * ease_out(age / 0.8)) * cam.s, paint(RED, 0.6 * (1 - age / 0.8), 6))
        if t >= KO and "sparkK" not in log.seen:
            log.seen.add("sparkK")
        # ---------- texts
        la = 1 - smoothstep(150, 185, cam.s)
        for j, nme, col in ((je, "EGO", RED), (jo, "OBSESSION", WHITE)):
            sx, _ = cam.pt((j["hip"][0], 0))
            draw_spaced(tc, nme, sx, cam.pt((0, 0))[1] + 46, font(26, "Inter-Bold"), 5, paint(col, la))
        if 7.35 <= t < 8.15:
            hx, hy = cam.pt(je["head"])
            draw_spaced(oc, "TOO EASY!", min(max(hx, 300), 660), hy - 0.8 * cam.s, font(48, "InterDisplay-Black"), 2, paint(RED, 1.0))
        if TURN <= t < R3:
            hx, hy = cam.pt(je["head"])
            draw_spaced(oc, "?!", hx, hy - 0.7 * cam.s, font(90, "InterDisplay-Black"), 2, paint(RED, 1.0))
        for i, tc_ in enumerate(COUNT):
            age = t - tc_
            if 0 <= age < 0.32:
                pop = 1 + 0.5 * math.exp(-age * 14)
                draw_spaced(oc, str(i + 1), CX, 700, font(170 * pop, "InterDisplay-Black"), 0, paint(RED, 1 - smoothstep(0.24, 0.32, age)))
        if KO + 0.2 <= t < END_T - 0.3:
            age = t - KO - 0.2
            pop = 1 + 0.6 * math.exp(-age * 10)
            draw_spaced(oc, "K.O.", CX, 760, font(200 * pop, "InterDisplay-Black"), 8, paint(RED, smoothstep(0, 0.08, age)))
        rnd = 1 if t < R2 else 2 if t < R3 else 3
        ha = smoothstep(1.6, 1.9, t) * (1 - smoothstep(END_T - 0.6, END_T - 0.3, t))
        draw_spaced(oc, "ROUND", CX, 360, font(24, "Inter-SemiBold"), 12, paint(WHITE, 0.7 * ha))
        draw_spaced(oc, str(rnd), CX, 470, font(104, "InterDisplay-Bold"), 4, paint(RED if rnd == 3 else WHITE, ha))
        if t < 1.8:
            a = 1 - smoothstep(1.4, 1.8, t)
            caption(oc, "EGO VS OBSESSION", 540, a, WHITE, 64)
            caption(oc, "THE REMATCH", 620, a, RED, 50, band=False)
        ending(oc, t, END_T - 0.3, [(END_T, "LAST TIME", WHITE, 92), (END_T + 0.25, "EGO WON.", WHITE, 92),
                                    (END_T + 1.0, "THIS TIME HE", RED, 92), (END_T + 1.25, "CELEBRATED", RED, 92),
                                    (END_T + 1.5, "TOO EARLY.", RED, 92)], gap=112)
        flash = 0.0
        for tt, a in ((UPPER, 0.5), (KO, 1.0)):
            if t >= tt:
                flash = max(flash, a * math.exp(-(t - tt) * 4))
        white = 0.08 * max(0.0, 1 - min(abs(t - ts) for ts, _, _ in SHOTS[1:]) / 0.05)
        v.compose(fi, t, flash=flash, white=white, glow=0.25 * smoothstep(O_RISE[0], O_RISE[1], t), fade_in=0.0)
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=KO), gain=0.42, fade_in=0.3, fade_out=2.0, stop=DUR)
    m.add(0.02, sfx.spot_on(), 0.7, 0, 0.4)
    m.add(0.1, sfx.text_hit(5), 0.6, 0, 0.4)
    for t, kind, _, extra in events:
        if kind == "cut":
            m.add(t - 0.05, sfx.whoosh(0.25, 500, 9000, 0.6, seed=extra), 0.4, 0, 0.2)
        elif kind == "bell":
            m.add(t, sfx.bell(), 0.75, 0, 0.5)
        elif kind == "hit":
            m.add(t - 0.05, sfx.swish(extra), 0.45, 0, 0.1)
            m.add(t + 0.04, sfx.punch_hit(extra + int(t * 10), 0.8), 0.75, 0, 0.25)
        elif kind == "block":
            m.add(t + 0.04, sfx.punch_block(extra), 0.65, 0, 0.2)
        elif kind == "ko1":
            m.add(t - 0.2, sfx.whoosh(0.4, 300, 6000, 0.8, seed=2), 0.7, 0, 0.3)
            m.add(t, sfx.punch_hit(77, 1.6), 1.0, 0.2, 0.4)
            m.add(t + 0.5, sfx.body_fall(), 0.8, 0.2, 0.4)
        elif kind == "count":
            m.add(t, sfx.text_hit(extra), 0.5 + 0.04 * extra, 0, 0.3)
        elif kind == "party":
            m.add(t, sfx.applause(2.0, 50, 3), 0.55, -0.4, 0.3)
            m.add(t, sfx.laugh(9, 4, 170, 0.5), 0.4, -0.4, 0.4)
        elif kind == "shutter":
            m.add(t, sfx.shutter(extra), 0.3, -0.5, 0.2)
        elif kind == "rise":
            m.add(t - 0.3, sfx.power_up(70), 0.9, 0.3, 0.4)
            m.add(t + 0.2, sfx.heartbeat(), 0.8, 0.3, 0.3)
        elif kind == "turn":
            m.add(t, sfx.glitch(4), 0.6, -0.3, 0.2)
            m.add(t + 0.1, sfx.text_hit(2), 0.6, -0.3, 0.4)
        elif kind == "ko2":
            m.add(t - 0.35, sfx.whoosh(0.5, 200, 7000, 0.85, seed=21), 0.9, 0, 0.3)
            m.add(t, sfx.punch_hit(99, 2.2), 1.0, -0.2, 0.5)
            m.add(t, sfx.boom(4.5), 1.0, 0, 0.5)
            m.add(t + 0.7, sfx.body_fall(), 0.9, -0.3, 0.4)
            m.add(t + 0.8, sfx.bell(780, 3.0), 0.7, 0, 0.5)
        elif kind == "walk":
            for q in range(5):
                m.add(t + 0.1 + q * 0.38, sfx.step_heavy(q), 0.4, 0.3, 0.2)
        elif kind == "end":
            m.add(t, sfx.text_hit(1), 0.7, 0, 0.4)
        elif kind == "end2":
            m.add(t, sfx.text_hit(3), 0.95, 0, 0.5)
            m.add(t, sfx.boom(2.0), 0.45, 0, 0.4)
    m.add(KO - 2.2, sfx.riser(2.2), 0.5, 0, 0.3)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [0.5, 1.8, 2.9, 4.3, 6.1, 6.6, 7.0, 7.8, 8.5, 9.5, 10.6, 11.8, 12.7, 13.6, 14.6, 18.0]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
