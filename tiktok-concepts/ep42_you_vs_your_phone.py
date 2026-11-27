"""EP42 - YOU VS YOUR PHONE  (edit-friendly: big drop at 10.0 s)

  0.0  dark. A giant red phone lights up: PING. A guy on a chair looks up.
  2.0  a red cable shoots out of the screen and clips onto his neck: a leash.
       Notifications fly at him, the badge climbs 1 -> 99+.
  4.0  zoom: his face lit by the screen. The clock runs: 11 PM -> 3 AM.
  6.0  wide: the phone is huge, he is tiny, hunched, notifications raining.
  8.0  he stands up, pulls against the leash, leaning back... NO.
  9.65 black. silence.
 10.0  DROP: the leash SNAPS, he punches the screen: it cracks, explodes, the
       phone falls flat. Shockwave, aura.
 10.8  he walks away, one step per second, the sun rises behind him.
 END   IT WAS NEVER A PHONE. / IT WAS A LEASH.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import (FPS, H, L_FARM, L_UARM, RED, WHITE, W, Camera, Particles, clamp, draw_spaced, ease_out, font,
                    ik, paint, rotate_pose, run_pose, smoothstep)
from kit import Log, Shards, Video, blend, caption, draw_body, ending, mirror, sit, stand
from ep34_courage_vs_fear import aura, ring
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep42_you_vs_your_phone"
dt = 1 / FPS
SCX, SCY = 450.0, 960.0
PING = 0.5
LEASH = 2.0
CLOCK = (4.0, 6.0)
STANDUP = (8.0, 9.5)
BLACK = (9.65, 10.0)
DROP = 10.0
STEPS = [10.9, 11.9, 12.9, 13.9]
END_T = 16.4
DUR = 20.4
PX0, PX1, PY0, PY1 = 1.0, 4.0, 0.15, 6.0          # phone body (world)
YX = -1.2                                         # you


def you_pose(t):
    if t < STANDUP[0]:
        hunch = smoothstep(2.0, 6.5, t)
        j = sit(YX, 0.75, t, 0.1 + 0.6 * hunch)
        j["head"] = j["neck"] + np.array([0.18 + 0.1 * hunch, 0.3 - 0.08 * hunch])
        if t > LEASH:
            pull = 0.06 * math.sin(t * 2.3) * hunch
            j = {k: v + [pull, 0] for k, v in j.items()}
        return j
    if t < DROP:
        u = smoothstep(STANDUP[0], STANDUP[0] + 0.6, t)
        st = stand(YX, -0.25, 0.4, 0.3, 0.3, 0.3, -0.25)
        j = blend(sit(YX, 0.75, t, 0.7), st, u)
        # hand grabs the leash at the neck
        j["hand2"] = j["neck"] + np.array([0.15, -0.05])
        j["elbow2"] = ik(j["shoulder"], j["hand2"], L_UARM, L_FARM, -1)
        return {k: v + [0.01 * math.sin(t * 50) * u, 0] for k, v in j.items()}
    if t < DROP + 0.5:
        u = smoothstep(DROP, DROP + 0.12, t)
        a = stand(YX, -0.25, 0.4, 0.3, 0.3, 0.3, -0.25)
        b = stand(YX + 0.35, 0.2, 1.57, -0.4, 0.05, 0.6, 0.0)       # punch
        return blend(a, b, u)
    if t < STEPS[0] - 0.4:
        return stand(YX + 0.35, -0.02, 0.35, 0.3, 1.2, 1.2, -0.08)
    # walk away to the left (facing left), one step per beat
    x = walk_x(t)
    k = sum(1 for s in STEPS if t >= s - 0.4)
    ph = (t - (STEPS[min(k, len(STEPS)) - 1] - 0.4)) / 0.4 * math.pi if k <= len(STEPS) else 0.0
    j = run_pose(x, (k * math.pi) + min(math.pi, ph), 0.35, 0, -0.02, -0.05)
    return mirror(j, x)


def walk_x(t):
    x = YX + 0.35
    for s in STEPS:
        x -= 0.9 * ease_out(clamp((t - (s - 0.4)) / 0.4))
    return x


# ------------------------------------------------------------------ phone
def phone_ang(t):
    if t < DROP + 0.15:
        return 0.0
    return -1.55 * ease_out(clamp((t - DROP - 0.15) / 0.55)) ** 1.5


def phone_pts(t):
    ang = phone_ang(t)
    piv = np.array([PX1, 0.0])
    R = np.array([[math.cos(ang), -math.sin(ang)], [math.sin(ang), math.cos(ang)]])
    return lambda p: piv + R @ (np.array(p, float) - piv)


def draw_phone(c, f_, tc, cam, t, badge):
    P = phone_pts(t)
    sw = max(4, 0.07 * cam.s)
    body = skia.Path()
    corners = [(PX0, PY0), (PX0, PY1), (PX1, PY1), (PX1, PY0)]
    for k, q in enumerate(corners):
        (body.moveTo if k == 0 else body.lineTo)(*cam.pt(P(q)))
    body.close()
    c.drawPath(body, paint((0.05, 0.0, 0.01), 1.0))
    c.drawPath(body, paint(RED, 1.0, sw))
    on = smoothstep(PING - 0.1, PING + 0.1, t) * (1.0 if t < DROP else 0.0)
    scr = skia.Path()
    for k, q in enumerate([(PX0 + 0.22, PY0 + 0.55), (PX0 + 0.22, PY1 - 0.5), (PX1 - 0.22, PY1 - 0.5),
                           (PX1 - 0.22, PY0 + 0.55)]):
        (scr.moveTo if k == 0 else scr.lineTo)(*cam.pt(P(q)))
    scr.close()
    if on > 0:
        f_.drawPath(scr, paint(WHITE, 0.16 * on + 0.05 * on * math.sin(t * 9)))
        # app tiles
        for r_ in range(4):
            for c_ in range(3):
                x0 = PX0 + 0.5 + c_ * 0.85
                y0 = PY1 - 1.2 - r_ * 0.95
                rr = skia.Rect(*cam.pt(P((x0, y0 + 0.55))), *cam.pt(P((x0 + 0.55, y0))))
                c.drawRoundRect(rr, 0.1 * cam.s, 0.1 * cam.s, paint(WHITE, 0.25 * on, 3))
    c.drawPath(scr, paint(RED, 0.6, max(2, 0.03 * cam.s)))
    c.drawLine(*cam.pt(P((PX0 + 1.2, PY1 - 0.25))), *cam.pt(P((PX1 - 1.2, PY1 - 0.25))), paint(RED, 0.8, sw * 0.8))
    if badge and t < DROP:
        bx, by = cam.pt(P((PX1 - 0.05, PY1 - 0.05)))
        r = 0.38 * cam.s * (1 + 0.3 * math.exp(-((t * 4) % 1.0) * 6))
        tc.drawCircle(bx, by, r, paint(RED, 1.0))
        draw_spaced(tc, badge, bx, by + r * 0.35, font(max(12, r * 0.85), "InterDisplay-Black"), 0, paint(WHITE, 1.0))


def cracks(c, cam, t):
    if t < DROP:
        return
    P = phone_pts(t)
    hit = np.array([PX0 + 0.9, 2.6])
    rng = np.random.default_rng(7)
    g = ease_out(clamp((t - DROP) / 0.15))
    for q in range(9):
        a = q * 2 * math.pi / 9 + rng.uniform(-0.2, 0.2)
        p = hit.copy()
        path = skia.Path()
        path.moveTo(*cam.pt(P(p)))
        for st in range(4):
            p = p + np.array([math.cos(a), math.sin(a)]) * rng.uniform(0.3, 0.7) * g
            a += rng.uniform(-0.4, 0.4)
            p = np.clip(p, [PX0 + 0.25, PY0 + 0.6], [PX1 - 0.25, PY1 - 0.55])
            path.lineTo(*cam.pt(P(p)))
        c.drawPath(path, paint(WHITE, 0.9, max(2, 0.03 * cam.s)))


def leash_pts(t, j):
    a = np.array([PX0 + 0.3, 2.9])
    b = j["neck"] + np.array([0.02, 0.0])
    tight = smoothstep(STANDUP[0], STANDUP[0] + 0.5, t)
    sag = 0.6 * (1 - tight)
    mid = (a + b) / 2 + np.array([0, -sag])
    return [(1 - u) ** 2 * a + 2 * (1 - u) * u * mid + u * u * b for u in np.linspace(0, 1, 24)]


def camera(t, j):
    if t < LEASH:
        u = ease_out(smoothstep(0.0, LEASH, t))
        a, b = (150.0, 2.0, 3.4), (112.0, 1.0, 3.0)
    elif t < CLOCK[0]:
        u = (t - LEASH) / (CLOCK[0] - LEASH)
        a, b = (115.0, 0.9, 2.9), (125.0, 0.6, 2.8)
    elif t < CLOCK[1]:
        u = (t - CLOCK[0]) / (CLOCK[1] - CLOCK[0])
        a, b = (300.0, YX + 0.6, 1.95), (330.0, YX + 0.6, 1.95)
    elif t < STANDUP[0]:
        u = (t - CLOCK[1]) / (STANDUP[0] - CLOCK[1])
        a, b = (100.0, 1.4, 3.3), (92.0, 1.4, 3.4)
    elif t < DROP:
        u = ease_out((t - STANDUP[0]) / (DROP - STANDUP[0]))
        a, b = (190.0, YX + 0.8, 1.9), (235.0, YX + 0.6, 1.8)
    elif t < STEPS[0]:
        u = (t - DROP) / (STEPS[0] - DROP)
        a, b = (112.0, 1.0, 2.9), (118.0, 1.0, 2.8)
    elif t < STEPS[2]:
        u = (t - STEPS[0]) / (STEPS[2] - STEPS[0])
        x = walk_x(t)
        a, b = (230.0, x - 0.2, 1.4), (240.0, x - 0.2, 1.4)
    else:
        u = ease_out(clamp((t - STEPS[2]) / 3.5))
        x = walk_x(t)
        a, b = (200.0, x + 0.3, 1.6), (72.0, -1.3, 4.2)
    return tuple(a[i] + (b[i] - a[i]) * clamp(u) for i in range(3))


CUTS = [LEASH, CLOCK[0], CLOCK[1], STANDUP[0], DROP, STEPS[0], STEPS[2]]


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    embers = Particles(5)
    shards = Shards(9)
    notes = []                                    # flying notifications: [t0, y0, dy, seed]
    rng = np.random.default_rng(3)
    for fi in range(v.n):
        t = fi * dt
        for key, tt, kind in (("ping", PING, "ping"), ("leash", LEASH, "leash"), ("clock", CLOCK[0], "clock"),
                              ("rain", CLOCK[1], "rain"), ("stand", STANDUP[0], "stand"), ("no", 9.0, "no"),
                              ("drop", DROP, "drop"), ("fall", DROP + 0.7, "fall"), ("end", END_T, "end"),
                              ("end2", END_T + 1.3, "end2")):
            if t >= tt:
                log.once(key, tt, kind)
        for k, s in enumerate(STEPS):
            if t >= s:
                log.once(f"step{k}", s, "step", k)
        j = you_pose(t)
        if LEASH <= t < STANDUP[1] and rng.random() < (0.25 if t < 6 else 0.5):
            notes.append([t, rng.uniform(2.0, 5.2), rng.uniform(-0.8, 0.2), rng.integers(0, 1000)])
            log.add(t, "note", int(rng.integers(0, 9)))
        if abs(t - DROP) < dt / 2:
            for p in leash_pts(t, j)[2:-2:2]:
                shards.burst(p[0] - 0.05, p[0] + 0.05, p[1] - 0.05, p[1] + 0.05, 3, vx=(-4, 4), vy=(1, 6),
                             size=(0.06, 0.15))
            shards.burst(PX0 + 0.3, PX0 + 2.0, 1.5, 4.0, 70, vx=(-3, 6), vy=(0, 7), size=(0.1, 0.3), life=(1.0, 2.0))
            embers.emit(np.tile(j["neck"], (80, 1)) + rng.normal(0, 0.3, (80, 2)), vel=(0, 2.0), spread=3.0,
                        life=(0.5, 1.4), size=(0.03, 0.08))
        aura_a = 0.0
        if STANDUP[0] < t < DROP:
            aura_a = 0.3 * smoothstep(STANDUP[0], BLACK[0], t)
        elif t >= DROP:
            aura_a = 1.0
        if aura_a > 0.05 and rng.random() < 0.55:
            pts = np.array([j["hip"], j["neck"], j["foot1"]]) + rng.normal(0, 0.15, (3, 2))
            embers.emit(pts, vel=(0, 1.2 + 1.5 * aura_a), spread=0.35, life=(0.6, 1.3), size=(0.03, 0.06))
        embers.step(dt)
        shards.step(dt)
        if not v.wants(fi):
            continue
        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        s, wx, wy = camera(t, j)
        cam = Camera()
        cam.s, cam.wx, cam.wy, cam.sx, cam.sy = s, wx, wy, SCX, SCY
        shake = 0.0
        for t0, amp in ((PING, 8), (LEASH, 12), (DROP, 34), (DROP + 0.7, 26)):
            if t0 <= t < t0 + 0.5:
                shake = max(shake, amp * (1 - (t - t0) / 0.5))
        for s_ in STEPS:
            if s_ <= t < s_ + 0.3:
                shake = max(shake, 10 * (1 - (t - s_) / 0.3))
        if STANDUP[0] < t < BLACK[0]:
            shake = max(shake, 4)
        if shake:
            cam.sx += shake * math.sin(t * 97)
            cam.sy += shake * math.cos(t * 83)
        gy = cam.pt((0, 0))[1]
        e.drawLine(0, gy, W, gy, paint(WHITE, 0.45, 2.5))
        # sunrise after the drop
        if t > DROP + 0.8:
            sa = smoothstep(DROP + 0.8, DROP + 3.0, t)
            sx, sy = cam.pt((-6.8, -1.2 + 3.0 * sa))
            e.drawCircle(sx, sy, 1.3 * cam.s, paint(WHITE, 0.85 * sa, 5))
        # chair
        if t < DROP + 0.6:
            cw = max(3, 0.04 * cam.s)
            e.drawLine(*cam.pt((YX - 0.35, 0.75)), *cam.pt((YX + 0.3, 0.75)), paint(WHITE, 0.5, cw))
            e.drawLine(*cam.pt((YX - 0.35, 0.75)), *cam.pt((YX - 0.45, 1.6)), paint(WHITE, 0.5, cw))
            e.drawLine(*cam.pt((YX, 0.75)), *cam.pt((YX, 0.0)), paint(WHITE, 0.4, cw))
        # light beam from the screen to his face
        if PING < t < DROP:
            beam = skia.Path()
            beam.moveTo(*cam.pt((PX0 + 0.22, PY1 - 0.5)))
            beam.lineTo(*cam.pt((PX0 + 0.22, PY0 + 0.55)))
            beam.lineTo(*cam.pt(j["head"] + [0.1, -0.2]))
            beam.lineTo(*cam.pt(j["head"] + [0.1, 0.2]))
            beam.close()
            e.drawPath(beam, paint(WHITE, 0.05))
        badge = None
        if t >= PING:
            n = int(1 + 98 * smoothstep(LEASH, 7.0, t))
            badge = "99+" if n >= 99 else str(n)
        draw_phone(e, f_, tc, cam, t, badge)
        cracks(e, cam, t)
        # notifications flying at him
        for t0, y0, dy, sd in notes:
            u = (t - t0) / 0.9
            if 0 <= u < 1:
                x = PX0 - 0.1 + (j["head"][0] + 0.4 - PX0 + 0.1) * u
                y = y0 + (j["head"][1] + dy - y0) * u
                bx, by = cam.pt((x, y))
                w_, h_ = 0.75 * cam.s, 0.32 * cam.s
                r = skia.Rect(bx - w_ / 2, by - h_ / 2, bx + w_ / 2, by + h_ / 2)
                f_.drawRoundRect(r, h_ * 0.3, h_ * 0.3, paint(RED, 0.9 * (1 - u ** 3)))
                f_.drawLine(bx - w_ * 0.3, by - h_ * 0.1, bx + w_ * 0.3, by - h_ * 0.1, paint(WHITE, 0.9 * (1 - u ** 3), 3))
                f_.drawLine(bx - w_ * 0.3, by + h_ * 0.15, bx + w_ * 0.1, by + h_ * 0.15, paint(WHITE, 0.7 * (1 - u ** 3), 3))
        # leash
        if LEASH <= t < DROP:
            g = ease_out(clamp((t - LEASH) / 0.3))
            pts = leash_pts(t, j)
            m = max(2, int(len(pts) * g))
            path = skia.Path()
            path.moveTo(*cam.pt(pts[0]))
            for p in pts[1:m]:
                path.lineTo(*cam.pt(p + np.array([0, 0.03 * math.sin(t * 60) * (t > STANDUP[0])])))
            hc.drawPath(path, paint(RED, 1.0, max(3, 0.05 * cam.s)))
            if g >= 1:
                nx, ny = cam.pt(j["neck"])
                hc.drawCircle(nx, ny, 0.13 * cam.s, paint(RED, 1.0, max(3, 0.05 * cam.s)))
        shards.draw(hc, cam, RED)
        aura(f_, cam, j, aura_a, t)
        embers.draw(f_, cam, WHITE, WHITE)
        draw_body(hc, j, cam, WHITE, 1.0)
        # face lit (eyes) in the zoom
        if CLOCK[0] <= t < CLOCK[1]:
            hx, hy = cam.pt(j["head"])
            r = 0.29 * cam.s
            for dx in (0.25, 0.65):
                hc.drawOval(skia.Rect(hx + dx * r - 0.12 * r, hy - 0.12 * r, hx + dx * r + 0.12 * r, hy + 0.02 * r),
                            paint((0, 0, 0), 1.0))
        if STANDUP[0] + 0.9 < t < BLACK[0]:
            hx, hy = cam.pt(j["head"])
            draw_spaced(tc, "NO.", min(max(hx, 260), 640), max(640, hy - 0.75 * cam.s), font(90, "InterDisplay-Black"),
                        4, paint(WHITE, smoothstep(STANDUP[0] + 0.9, STANDUP[0] + 1.1, t)))
        for s_ in STEPS:
            ring(e, cam, (j["foot1"][0], 0.05), t, s_, 1.6, WHITE, 0.45, 0.06)
        ring(f_, cam, (PX0 + 0.9, 2.6), t, DROP, 5.0, WHITE, 0.8, 0.12)
        ring(f_, cam, (2.5, 0.2), t, DROP + 0.7, 4.0, RED, 0.6, 0.08)
        # labels
        if 2.2 < t < CLOCK[0] or CLOCK[1] <= t < STANDUP[0]:
            lx, _ = cam.pt((YX, 0))
            draw_spaced(tc, "YOU", lx, gy + 50, font(32, "Inter-Bold"), 6, paint(WHITE, 1.0))
            px_, _ = cam.pt(((PX0 + PX1) / 2, 0))
            draw_spaced(tc, "YOUR PHONE", px_, gy + 50, font(32, "Inter-Bold"), 6, paint(RED, 1.0))
        # clock
        if CLOCK[0] <= t < STANDUP[0] + 0.8:
            mins = int(23 * 60 + (4 * 60 + 47) * smoothstep(CLOCK[0], STANDUP[0], t)) % (24 * 60)
            hh, mm = mins // 60, mins % 60
            ampm = "AM" if hh < 12 else "PM"
            h12 = hh % 12 or 12
            draw_spaced(oc, f"{h12}:{mm:02d} {ampm}", 470, 470, font(92, "InterDisplay-Black"), 3,
                        paint(RED if hh < 12 else WHITE, 1.0))
        if 0.6 < t < LEASH:
            caption(oc, "YOU VS YOUR PHONE", 1500, smoothstep(0.6, 0.9, t) * (1 - smoothstep(1.7, 2.0, t)), WHITE, 60,
                    band=False)
        ending(oc, t, END_T - 0.3, [(END_T, "IT WAS NEVER", WHITE, 100), (END_T + 0.3, "A PHONE.", WHITE, 110),
                                    (END_T + 1.1, "IT WAS", RED, 110), (END_T + 1.4, "A LEASH.", RED, 130)], gap=130)
        white = 0.0
        for t0, a in ((DROP, 0.85), (DROP + 0.7, 0.4), (PING, 0.15)):
            if t0 <= t < t0 + 0.35:
                white = max(white, a * (1 - (t - t0) / 0.35) ** 2)
        for c_ in CUTS:
            if c_ <= t < c_ + 0.1 and c_ != DROP:
                white = max(white, 0.07)
        dim = 0.0
        if BLACK[0] <= t < BLACK[1]:
            dim, white = 1.0, 0.0
        flash = 0.5 * math.exp(-(t - DROP) * 3) if t >= DROP else 0.0
        v.compose(fi, t, flash=flash, glow=0.15 * aura_a, white=white, dim=dim, fade_in=0.0)
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DROP, rise_at=7.0), gain=0.3, fade_in=0.3, fade_out=0.4, stop=BLACK[0])
    lastn = -1.0
    for t, kind, _, extra in events:
        if kind == "ping":
            m.add(t, sfx.chime(1760, 0.35), 0.7, 0, 0.4)
            m.add(t + 0.12, sfx.chime(2349, 0.3), 0.6, 0, 0.4)
        elif kind == "note":
            if t - lastn > 0.18:
                m.add(t, sfx.beep(1500 + 150 * extra, 0.08, 0.3), 0.35, 0, 0.2)
                lastn = t
        elif kind == "leash":
            m.add(t, sfx.whoosh(0.3, 600, 9000, 0.4, seed=3), 0.6, 0, 0.2)
            m.add(t + 0.3, sfx.plate_clank(2, 0.6), 0.6, 0, 0.3)
        elif kind == "clock":
            for q in range(14):
                m.add(t + q * 0.14, sfx.tick(2600, 0.25), 0.35, 0, 0.1)
        elif kind == "rain":
            m.add(t, sfx.power_down(1.8), 0.4, 0, 0.4)
        elif kind == "stand":
            m.add(t, sfx.breath(3, 0.9), 0.6, 0, 0.3)
            m.add(t, sfx.riser(BLACK[0] - t), 0.6, 0, 0.4)
            m.add(t + 0.3, sfx.rattle(1.0, 5), 0.4, 0, 0.3)
        elif kind == "no":
            m.add(t, sfx.text_hit(2), 0.7, 0, 0.4)
        elif kind == "drop":
            m.add(t, sfx.boom(3.5), 1.0, 0, 0.6)
            m.add(t, sfx.shatter(1, 1.5), 1.0, 0, 0.5)
            m.add(t, sfx.punch_hit(4, 1.5), 0.9, 0, 0.3)
        elif kind == "fall":
            m.add(t, sfx.boom(2.5), 0.8, 0, 0.5)
            m.add(t, sfx.body_fall(), 0.8, 0, 0.3)
        elif kind == "step":
            m.add(t, sfx.step_heavy(extra), 1.0, 0, 0.3)
            m.add(t, sfx.boom(1.2), 0.4, 0, 0.3)
        elif kind == "end":
            m.add(t, sfx.text_hit(1), 0.7, 0, 0.4)
        elif kind == "end2":
            m.add(t, sfx.text_hit(3), 0.9, 0, 0.5)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [0.3, 1.2, 2.6, 3.6, 4.8, 6.8, 8.5, 9.4, 10.1, 10.5, 11.5, 12.6, 14.0, 15.6, 18.5]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
