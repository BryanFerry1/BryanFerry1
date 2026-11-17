"""EP24 - EGO VS OBSESSION  (friday night)

Split screen, moving from the first frame. Every Friday the same text:
"PARTY TONIGHT?"
EGO        "OMW!" -> club: red strobes, disco ball, his crew dancing with him.
           FRIENDS goes up (12 -> 34).
OBSESSION  "CAN'T. WORKING." -> desk, laptop glow, chart on the screen rising.
           Friends' texts turn sour (YOU'VE CHANGED. / BORING. / WHATEVER.).
           FRIENDS drops 12 -> 2.
FRIDAY 52  Bottom: launch day, spotlight, crowd, the 2 friends who stayed clap.
           Top: the same party, same song.
END        (scene fades to black, centred) SOME FRIDAYS COST YOU FRIENDS. /
           OTHERS COST YOU YOUR FUTURE.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import (FPS, L_FARM, L_UARM, RED, WHITE, W, clamp, draw_spaced, ease_out, font, ik, mix, paint,
                    smoothstep, spaced_width)
from kit import (CX, GREY, Log, Video, arms_up, blend, caption, clap, draw_body, draw_phone_small, ending,
                 lane_cam, mirror, sit, stand)
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep24_friday_night"
dt = 1 / FPS
S = 118.0
LANES = {"EGO": (330, 935, 860), "OBSESSION": (965, 1565, 1475)}
PX = 0.2                       # main figure x (world)
FIRST = 2.5
LAUNCH = 11.2
END_T = 14.4
DUR = 19.0
SOUR = ["YOU'VE CHANGED.", "BORING.", "WE MISS YOU.", "WHATEVER.", "FORGET IT.", "..."]


def fridays():
    ts, t, gap = [], FIRST, 1.5
    while t < LAUNCH - 0.5:
        ts.append(t)
        t += gap
        gap = max(0.55, gap * 0.82)
    return ts


FR = fridays()


def friday_num(t):
    if t < FIRST:
        return 1
    if t >= LAUNCH:
        return 52
    return min(51, int(1 + 50 * clamp((t - FIRST) / (LAUNCH - 0.3 - FIRST)) ** 1.3))


def friends(n, t):
    u = clamp((t - FIRST) / (LAUNCH - 0.5 - FIRST))
    return int(round(12 + 22 * u)) if n == "EGO" else int(round(12 - 10 * u ** 0.8))


def msg(c, x, y, text, alpha, col, mine=False):
    """Phone-style message bubble (opaque, readable)."""
    if alpha < 0.01:
        return
    f = font(26, "InterDisplay-Black")
    w = spaced_width(text, f, 1) + 34
    h = 50
    x = min(max(x, 80 + w / 2), 880 - w / 2)
    r = skia.Rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2)
    c.drawRoundRect(r, 22, 22, paint(col if mine else (0, 0, 0), 0.95 * alpha))
    if not mine:
        c.drawRoundRect(r, 22, 22, paint(col, alpha, 3))
    draw_spaced(c, text, x, y + 9, f, 1, paint((0, 0, 0) if mine else col, alpha))


def dance(x, t, ph=0.0):
    b = abs(math.sin(t * 7 + ph))
    return stand(x, -0.05 + 0.1 * math.sin(t * 3.5 + ph), 2.3 + 0.5 * math.sin(t * 7 + ph), 0.9 + 0.6 * b,
                 0.4, 1.2, -0.2, 0.06 * b)


def desk_pose(x, t):
    j = sit(x - 0.25, 0.72, t, 0.25)
    sh = j["shoulder"]
    tap = 0.03 * math.sin(t * 38)
    j["hand1"] = sh + np.array([0.75, -0.1 + tap])
    j["hand2"] = sh + np.array([0.7, -0.12 - tap])
    j["elbow1"] = ik(sh, j["hand1"], L_UARM, L_FARM, -1)
    j["elbow2"] = ik(sh, j["hand2"], L_UARM, L_FARM, -1)
    return j


def desk(e, f_, cam, t, chart_u):
    e.drawLine(*cam.pt((PX + 0.35, 1.05)), *cam.pt((PX + 1.65, 1.05)), paint(WHITE, 0.75, 4))
    for lx in (PX + 0.45, PX + 1.55):
        e.drawLine(*cam.pt((lx, 1.05)), *cam.pt((lx, 0.0)), paint(WHITE, 0.55, 3))
    # laptop screen (back view tilted) + chart
    l, tp = cam.pt((PX + 0.85, 1.85))
    r, b = cam.pt((PX + 1.6, 1.08))
    f_.drawRoundRect(skia.Rect(l, tp, r, b), 6, 6, paint((0, 0, 0), 1.0))
    f_.drawRoundRect(skia.Rect(l, tp, r, b), 6, 6, paint(WHITE, 0.9, 3))
    p = skia.Path()
    n = 12
    for k in range(n + 1):
        u = k / n * chart_u
        px = l + 10 + (r - l - 20) * k / n
        py = b - 10 - (b - tp - 20) * (0.1 + 0.85 * u ** 2.2)
        (p.moveTo if k == 0 else p.lineTo)(px, py)
    f_.drawPath(p, paint(RED, 1.0, 3))
    f_.drawCircle((l + r) / 2, (tp + b) / 2, 0.9 * cam.s, paint(WHITE, 0.04))


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    for fi in range(v.n):
        t = fi * dt
        for k, ft in enumerate(FR):
            if t >= ft:
                log.once(f"f{k}", ft, "friday", k)
        for key, tt, kind in (("go", 0.0, "go"), ("launch", LAUNCH, "launch"), ("end", END_T, "end"),
                              ("e2", END_T + 0.9, "end2")):
            if t >= tt:
                log.once(key, tt, kind)
        if not v.wants(fi):
            continue
        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        launch = t >= LAUNCH
        cur = max([k for k, ft in enumerate(FR) if t >= ft], default=-1)
        age = t - FR[cur] if cur >= 0 else 9
        for n, (y0, y1, gy) in LANES.items():
            cam = lane_cam(S, gy, 0.0)
            cam.sx = CX - 30
            for L in (v.env, v.fig, v.hero, v.txt):
                L.canvas.save()
                L.canvas.clipRect(skia.Rect(0, y0, W, y1))
            e.drawLine(60, gy, W - 60, gy, paint(WHITE, 0.5, 2.5))
            if n == "EGO":
                club = t >= FIRST + 0.4
                if club:
                    # red strobes + disco ball
                    if int(t * 6) % 2 == 0:
                        e.drawRect(skia.Rect(0, y0, W, y1), paint(RED, 0.10))
                    bx, by = cam.pt((PX + 0.2, 4.0))
                    e.drawLine(bx, y0, bx, by - 28, paint(WHITE, 0.4, 2))
                    e.drawCircle(bx, by, 28, paint(WHITE, 0.85, 3))
                    for k in range(6):
                        ang = t * 2 + k * 1.05
                        f_.drawLine(bx, by, bx + math.cos(ang) * 420, by + abs(math.sin(ang)) * 420, paint(WHITE, 0.05, 6))
                    for k, fx in enumerate((-2.0, -1.2, 1.5, 2.3)):
                        fa = 0.5 if not launch else 0.25
                        draw_body(e, dance(PX + fx, t, k * 1.3), cam, GREY, fa)
                    j = dance(PX, t)
                    if launch:
                        j = dance(PX, t * 0.5)
                else:
                    j = stand(PX, 0.08, 0.9, 0.2, 1.3, 0.2, 0.4)
                draw_body(hc, j, cam, RED, 1.0, 0.15)
                if not club:
                    draw_phone_small(f_, cam, j["hand1"] + [0.05, 0.1], 1.0)
            else:
                if not launch:
                    chart_u = clamp((t - FIRST) / (LAUNCH - FIRST))
                    desk(e, f_, cam, t, chart_u)
                    j = desk_pose(PX, t)
                    draw_body(hc, j, cam, WHITE, 1.0, 0.25)
                else:
                    # launch: spotlight, crowd, the two friends who stayed
                    sp = skia.Path()
                    sx_, _ = cam.pt((PX, 0))
                    sp.moveTo(sx_ - 30, y0 + 5)
                    sp.lineTo(sx_ + 30, y0 + 5)
                    sp.lineTo(sx_ + 300, gy)
                    sp.lineTo(sx_ - 300, gy)
                    sp.close()
                    pt = skia.Paint(AntiAlias=True)
                    pt.setShader(skia.GradientShader.MakeLinear([skia.Point(0, y0), skia.Point(0, gy)],
                                                                [skia.Color4f(1, 1, 1, 0), skia.Color4f(1, 1, 1, 0.12)]))
                    e.drawPath(sp, pt)
                    draw_spaced(tc, "LAUNCH DAY", sx_, y0 + 80, font(44, "InterDisplay-Black"), 6,
                                paint(RED, smoothstep(LAUNCH + 0.2, LAUNCH + 0.4, t)))
                    for k, fx in enumerate((-1.5, 1.5)):
                        jf = clap(PX + fx, t + k)
                        if fx > 0:
                            jf = mirror(jf, PX + fx)
                        draw_body(hc, jf, cam, WHITE, 0.85)
                    j = blend(stand(PX), arms_up(PX, t), smoothstep(LAUNCH + 0.2, LAUNCH + 0.6, t))
                    draw_body(hc, j, cam, WHITE, 1.0, 0.35)
                    for k in range(8):
                        hx = 110 + 100 * k
                        bob = 5 * abs(math.sin(t * 10 + k))
                        e.drawCircle(hx, gy + 45 - bob, 16, paint(GREY, 0.6))
            # messages
            hx, hy = cam.pt(j["head"])
            if cur >= 0 and not launch and age < 1.6:
                a_in = smoothstep(0, 0.12, age) * (1 - smoothstep(1.3, 1.6, age))
                if n == "EGO":
                    msg(oc, 250, y0 + 170, "PARTY TONIGHT?", a_in, WHITE)
                    if age > 0.3:
                        msg(oc, 330, y0 + 240, "OMW!", a_in, RED)
                else:
                    if cur < 2:
                        msg(oc, 250, y0 + 170, "PARTY TONIGHT?", a_in, WHITE)
                        if age > 0.3:
                            msg(oc, 330, y0 + 240, "CAN'T. WORKING.", a_in, WHITE, mine=True)
                    else:
                        msg(oc, 260, y0 + 170 + 30 * (cur % 2), SOUR[(cur - 2) % len(SOUR)], a_in, WHITE)
            # labels + counters
            lx, _ = cam.pt((PX, 0))
            draw_spaced(tc, n, lx, gy + 38, font(24, "Inter-Bold"), 5, paint(RED if n == "EGO" else WHITE, 1.0))
            ca = smoothstep(2.2, 2.5, t)
            draw_spaced(tc, "FRIENDS", 740, y0 + 55, font(20, "Inter-Bold"), 3, paint(WHITE, 0.6 * ca))
            fv = friends(n, t)
            draw_spaced(tc, str(fv), 740, y0 + 120, font(64, "InterDisplay-Black"), 2,
                        paint(RED if (n == "OBSESSION" and fv <= 3) or n == "EGO" else WHITE, ca))
            for L in (v.env, v.fig, v.hero, v.txt):
                L.canvas.restore()

        oc.drawRect(skia.Rect(0, 935, W, 965), paint((0, 0, 0), 1.0))
        fn = friday_num(t)
        draw_spaced(oc, f"FRIDAY {fn}", CX, 962, font(34, "InterDisplay-Black"), 3,
                    paint(RED if fn >= 52 else WHITE, smoothstep(2.2, 2.5, t)))
        if t < 2.4:
            caption(oc, "EGO VS OBSESSION", 405, 1 - smoothstep(2.0, 2.4, t), WHITE, 54)
        ending(oc, t, END_T - 0.3, [(END_T, "SOME FRIDAYS", WHITE, 82), (END_T + 0.25, "COST YOU FRIENDS.", WHITE, 82),
                                    (END_T + 1.0, "OTHERS COST YOU", RED, 82), (END_T + 1.25, "YOUR FUTURE.", RED, 82)],
               gap=118)
        flash = math.exp(-(t - LAUNCH) * 3) if t >= LAUNCH else 0.0
        white = 0.35 * max(0.0, 1 - (t - LAUNCH) / 0.2) if LAUNCH <= t < LAUNCH + 0.2 else 0.0
        v.compose(fi, t, flash=flash * 0.8, white=white, fade_in=0.0)
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=LAUNCH), gain=0.35, fade_in=0.3, fade_out=2.0, stop=DUR)
    # club beat in the top lane (muffled kick), from the first party to the end text
    t_ = FIRST + 0.4
    k = 0
    while t_ < END_T:
        m.add(t_, sfx.step_heavy(k) * 0.9, 0.35, -0.4, 0.05)
        if k % 2:
            m.add(t_, sfx.tick(5000, 0.15), 0.2, -0.4, 0.05)
        t_ += 0.25
        k += 1
    for t, kind, _, extra in events:
        if kind == "go":
            m.add(0.02, sfx.text_hit(5), 0.6, 0, 0.4)
        elif kind == "friday":
            m.add(t, sfx.beep(1250, 0.07, 0.5), 0.5, 0, 0.2)
            m.add(t + 0.08, sfx.beep(1650, 0.07, 0.5), 0.5, 0, 0.2)
            m.add(t + 0.3, sfx.chime(880, 0.2), 0.35, -0.4, 0.3)
            if extra >= 2:
                m.add(t + 0.05, sfx.power_down(0.5), 0.3, 0.4, 0.3)
            for q in range(5):
                m.add(t + 0.3 + q * 0.07, sfx.tick(2800, 0.2), 0.25, 0.4, 0.05)
        elif kind == "launch":
            m.add(t, sfx.spot_on(), 0.7, 0.3, 0.4)
            m.add(t + 0.1, sfx.boom(3.5), 0.9, 0, 0.5)
            m.add(t + 0.2, sfx.applause(3.0, 60, 4), 0.55, 0.3, 0.3)
        elif kind == "end":
            m.add(t - 0.3, sfx.whoosh(0.4, 200, 4000, 0.6, seed=3), 0.4, 0, 0.3)
            m.add(t, sfx.text_hit(1), 0.6, 0, 0.4)
        elif kind == "end2":
            m.add(t, sfx.text_hit(3), 0.95, 0, 0.5)
            m.add(t, sfx.boom(2.0), 0.45, 0, 0.4)
    m.add(LAUNCH - 2.0, sfx.riser(2.0), 0.45, 0, 0.3)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}, fridays {len(FR)}")
    if "--stills" in sys.argv:
        ts = [0.3, 1.5, 2.9, 3.4, 5.0, 7.0, 9.0, 10.6, 11.6, 13.0, 14.6, 16.5]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
