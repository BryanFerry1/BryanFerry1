"""EP22 - EGO VS OBSESSION  (when the camera is off)

Split screen (top EGO, bottom OBSESSION), moving from the first frame.
Each room has a wall camera with a red REC light.
REC ON   both train; Ego flexes for the lens between reps.
REC OFF  Ego drops the bar and slides onto the couch with his phone.
         Obsession keeps training exactly the same.
Faster and faster on/off cycles, DAY 1 -> 364. Followers: Ego 1.2M, Obsession 34.
Obsession grows, Ego doesn't.
DAY 365  THE COMPETITION, 200 KG. Ego can't lift it (crash, red, on his knees).
         Obsession presses it overhead.
END      EGO TRAINED FOR THE CAMERA. / OBSESSION TRAINED FOR THIS.
         ...BUT EGO HAS 1.2M FOLLOWERS.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import FPS, L_FARM, L_UARM, RED, WHITE, W, clamp, draw_spaced, ease_out, font, ik, mix, paint, smoothstep
from kit import (CX, GREY, Log, Video, blend, caption, curl, draw_body, draw_phone_small, flex, kneel,
                 lane_cam, sit, stand)
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep22_camera_off"
dt = 1 / FPS
S = 112.0
LANES = {"EGO": (330, 935, 860), "OBSESSION": (965, 1565, 1475)}
GYM_X, COUCH_X = 0.6, -2.5
SX = CX

ON = [(0.0, 2.6), (4.4, 5.8), (7.0, 7.6), (8.1, 8.6), (9.0, 9.4), (9.8, 10.1), (10.5, 10.8)]
COMP = 11.4
GRIP = 12.2
LIFT_A, LOCK = 12.6, 13.3
EGO_DROP = 13.7
P1, P2, P3 = 14.7, 15.5, 16.7
DUR = 19.8


def rec_on(t):
    return t < COMP and any(a <= t < b for a, b in ON)


def on_amount(t):
    """0..1 smooth version for blending poses (0.25 s transitions)."""
    best = 0.0
    for a, b in ON:
        best = max(best, smoothstep(a - 0.05, a + 0.2, t) * (1 - smoothstep(b, b + 0.25, t)))
    return best if t < COMP else 0.0


def day(t):
    if t < 7.0:
        return 1 if t < 4.4 else 2
    if t < COMP:
        return int(2 + 362 * clamp((t - 7.0) / (COMP - 0.2 - 7.0)) ** 1.3)
    return 365


def followers(n, t):
    if n == "OBSESSION":
        return 3 + int(31 * clamp(t / COMP))
    return int(1200 + 1_198_800 * clamp(t / COMP) ** 2.4)


def fmt(k):
    if k >= 1_000_000:
        return f"{k / 1e6:.1f}M"
    if k >= 1000:
        return f"{k / 1000:.1f}K"
    return str(k)


def lift_pose(x, h, t, shake=0.0):
    """Hands on a heavy bar at height h (world y). Floor -> hip -> overhead."""
    low = 1 - clamp((h - 0.4) / 0.8)
    hip = np.array([x - 0.25 * low, 1.52 - 0.45 * low])
    from engine import build_pose
    j = build_pose(hip, np.array([x + 0.2, 0.02]), np.array([x - 0.2, 0.02]), 0.9 * low, 0.3, 0.3, 0.2, 0.2,
                   0.3 * low - 0.15 * (h > 1.8))
    bar = np.array([x + 0.1 + shake * 0.04 * math.sin(t * 50), h + shake * 0.03 * math.sin(t * 61)])
    sh = j["shoulder"]
    for i, off in ((1, 0.0), (2, 0.05)):
        hand = bar + [off, 0]
        j[f"hand{i}"] = hand
        j[f"elbow{i}"] = ik(sh, hand, L_UARM, L_FARM, 1 if h < 1.6 else -1)
    return j, bar


def draw_plate(c, cam, bar, alpha, col, label=None, size=0.55):
    cx, cy = cam.pt(bar)
    for r, a in ((size, 1.0), (size * 0.76, 0.6)):
        c.drawCircle(cx, cy, r * cam.s, paint((0, 0, 0), 1.0))
        c.drawCircle(cx, cy, r * cam.s, paint(col, alpha * a, 4))
    c.drawCircle(cx, cy, 0.08 * cam.s, paint(col, alpha))
    if label:
        draw_spaced(c, label, cx + (size + 0.75) * cam.s, cy + 10, font(30, "InterDisplay-Black"), 2, paint(col, alpha))


def wall_cam(c, tc, y0, on, t):
    x, y = 820, y0 + 120
    r = skia.Rect(x - 50, y - 26, x + 30, y + 26)
    c.drawRoundRect(r, 8, 8, paint((0, 0, 0), 1.0))
    c.drawRoundRect(r, 8, 8, paint(WHITE, 0.85, 3))
    c.drawCircle(x - 60, y, 16, paint(WHITE, 0.85, 3))
    c.drawLine(x + 30, y - 26, x + 50, y - 50, paint(WHITE, 0.6, 3))
    if on:
        blink = 0.6 + 0.4 * (int(t * 2.5) % 2)
        c.drawCircle(x + 6, y - 40, 9, paint(RED, blink))
        draw_spaced(tc, "REC", x - 10, y + 56, font(24, "InterDisplay-Black"), 3, paint(RED, blink))
    else:
        draw_spaced(tc, "OFF", x - 10, y + 56, font(24, "InterDisplay-Black"), 3, paint(GREY, 0.8))


def couch(c, cam, alpha):
    x = COUCH_X
    p = skia.Path()
    pts = [(x - 1.0, 0.1), (x - 1.0, 1.4), (x - 0.75, 1.5), (x - 0.6, 0.8), (x + 0.9, 0.8), (x + 1.05, 1.05), (x + 1.15, 0.1)]
    p.moveTo(*cam.pt(pts[0]))
    for q in pts[1:]:
        p.lineTo(*cam.pt(q))
    p.close()
    c.drawPath(p, paint((0, 0, 0), alpha))
    c.drawPath(p, paint(WHITE, 0.7 * alpha, 4))


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    prev_on = True
    rep_ph = 0.0
    for fi in range(v.n):
        t = fi * dt
        on = rec_on(t)
        if on != prev_on and t < COMP:
            log.add(t, "rec_on" if on else "rec_off")
        prev_on = on
        rep_speed = 1.0 + 1.6 * smoothstep(7.0, 9.0, t)
        old = rep_ph
        rep_ph += dt * rep_speed / 1.1
        if t < COMP and int(old) != int(rep_ph):
            log.add(t, "rep_O")
            if on:
                log.add(t + 0.05, "rep_E")
        for key, tt, kind in (("go", 0.0, "go"), ("comp", COMP, "comp"), ("grip", GRIP, "grip"),
                              ("lock", LOCK, "lock"), ("drop", EGO_DROP, "drop"), ("p1", P1, "p1"),
                              ("p2", P2, "p2"), ("p3", P3, "p3")):
            if t >= tt:
                log.once(key, tt, kind)
        if not v.wants(fi):
            continue

        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        oa = on_amount(t)
        comp = t >= COMP
        g_o = smoothstep(4.4, COMP - 0.4, t) if t >= 4.4 else 0.0
        c_ = math.sin(math.pi * (rep_ph % 1.0))
        for n, (y0, y1, gy) in LANES.items():
            cam = lane_cam(S, gy, 0.0)
            cam.sx = SX
            for L in (v.env, v.fig, v.hero, v.txt):
                L.canvas.save()
                L.canvas.clipRect(skia.Rect(0, y0, W, y1))
            e.drawLine(60, gy, W - 60, gy, paint(WHITE, 0.5, 2.5))
            if not comp:
                wall_cam(e, tc, y0, rec_on(t), t)
                if n == "EGO":
                    couch(e, cam, 1.0)
            else:
                # stage: spotlight + crowd heads
                sp = skia.Path()
                sx_, _ = cam.pt((GYM_X, 0))
                sp.moveTo(sx_ - 30, y0 + 5)
                sp.lineTo(sx_ + 30, y0 + 5)
                sp.lineTo(sx_ + 260, gy)
                sp.lineTo(sx_ - 260, gy)
                sp.close()
                pt = skia.Paint(AntiAlias=True)
                pt.setShader(skia.GradientShader.MakeLinear([skia.Point(0, y0), skia.Point(0, gy)],
                                                            [skia.Color4f(1, 1, 1, 0.0), skia.Color4f(1, 1, 1, 0.1)]))
                e.drawPath(sp, pt)
                lab_x = cam.pt((GYM_X, 0))[0]
                for k in range(9):
                    hx = 110 + 95 * k
                    if abs(hx - lab_x) < 110:
                        continue
                    bob = 4 * abs(math.sin(t * 10 + k)) if t >= LOCK else 0
                    e.drawCircle(hx, gy + 40 - bob, 18, paint(GREY, 0.5))
            if n == "EGO":
                if not comp:
                    jt = curl(GYM_X, c_ * 0.8)
                    if int(rep_ph) % 3 == 2:
                        jt = blend(jt, flex(GYM_X, t), 0.85)
                    jc = sit(COUCH_X + 0.2, 0.8, t, 0.9)
                    jc = {k: vv for k, vv in jc.items()}
                    j = blend(jc, jt, oa)
                    draw_body(hc, j, cam, RED, 1.0, 0.15)
                    if oa > 0.5:
                        bar = (j["hand1"] + j["hand2"]) / 2
                        draw_plate(hc, cam, bar, 1.0, RED, size=0.3)
                    else:
                        hc.drawCircle(*cam.pt((GYM_X + 0.4, 0.3)), 0.3 * S, paint(RED, 0.6, 3))
                        draw_phone_small(f_, cam, j["hand1"] + [0.05, 0.12], 1.0)
                else:
                    if t < GRIP:
                        j = stand(GYM_X - 0.6, -0.1, 0.4, 0.35, 1.9, 1.95, -0.2)
                        bar = np.array([GYM_X + 0.1, 0.55])
                    elif t < EGO_DROP:
                        u = smoothstep(LIFT_A, LIFT_A + 0.5, t)
                        h = 0.55 + 0.25 * u - 0.1 * smoothstep(EGO_DROP - 0.4, EGO_DROP, t)
                        j, bar = lift_pose(GYM_X, h, t, shake=smoothstep(LIFT_A, LIFT_A + 0.3, t) * 1.5)
                    else:
                        j = kneel(GYM_X - 1.1, t, 1.0)
                        bar = np.array([GYM_X + 0.3, 0.55])
                    col = mix(RED, GREY, smoothstep(EGO_DROP, EGO_DROP + 1.0, t))
                    draw_body(hc, j, cam, col, 1.0, 0.15)
                    draw_plate(hc, cam, bar, 1.0, WHITE, "200 KG")
            else:
                if not comp:
                    j = curl(GYM_X, c_)
                    draw_body(hc, j, cam, WHITE, 1.0, g_o)
                    bar = (j["hand1"] + j["hand2"]) / 2
                    draw_plate(hc, cam, bar, 1.0, WHITE, size=0.3 + 0.1 * g_o)
                else:
                    if t < GRIP:
                        j = stand(GYM_X - 0.6, 0.05, 0.2, 0.15, 0.3, 0.3, 0.0)
                        bar = np.array([GYM_X + 0.1, 0.55])
                    else:
                        h = 0.55 + 0.7 * smoothstep(LIFT_A, LIFT_A + 0.35, t) + 1.55 * smoothstep(LIFT_A + 0.35, LOCK, t)
                        j, bar = lift_pose(GYM_X, h, t, shake=0.5 * smoothstep(LIFT_A, LIFT_A + 0.2, t) * (1 - smoothstep(LOCK - 0.1, LOCK, t)))
                    draw_body(hc, j, cam, WHITE, 1.0, 1.0)
                    draw_plate(hc, cam, bar, 1.0, RED if t >= LOCK else WHITE, "200 KG")
            # labels + followers
            lx, _ = cam.pt((GYM_X if comp or n == "OBSESSION" or oa > 0.5 else COUCH_X, 0))
            draw_spaced(tc, n, lx, gy + 38, font(24, "Inter-Bold"), 5, paint(RED if n == "EGO" else WHITE, 1.0))
            fa = smoothstep(2.2, 2.5, t)
            draw_spaced(tc, "FOLLOWERS", 200, y0 + 55, font(20, "Inter-Bold"), 3, paint(WHITE, 0.6 * fa))
            draw_spaced(tc, fmt(followers(n, t)), 200, y0 + 110, font(52, "InterDisplay-Black"), 2,
                        paint(RED if n == "EGO" else WHITE, fa))
            for L in (v.env, v.fig, v.hero, v.txt):
                L.canvas.restore()

        # divider with DAY
        oc.drawRect(skia.Rect(0, 935, W, 965), paint((0, 0, 0), 1.0))
        d = day(t)
        dtxt = f"DAY {d}" if t < COMP else "DAY 365 — COMPETITION"
        draw_spaced(oc, dtxt, CX, 962, font(34, "InterDisplay-Black"), 3, paint(RED if d >= 365 else WHITE, smoothstep(2.2, 2.5, t)))
        if t < 2.4:
            caption(oc, "EGO VS OBSESSION", 405, 1 - smoothstep(2.0, 2.4, t), WHITE, 54)
        if 2.6 <= t < 4.4:
            caption(oc, "CAMERA OFF.", 1050, smoothstep(2.65, 2.8, t) * (1 - smoothstep(4.1, 4.4, t)), WHITE, 40)
        if t >= P1:
            a = smoothstep(P1 - 0.2, P1 + 0.2, t)
            oc.drawRect(skia.Rect(0, 620, W, 1000), paint((0, 0, 0), 0.85 * a))
            caption(oc, "EGO TRAINED FOR THE CAMERA.", 720, smoothstep(P1, P1 + 0.3, t), WHITE, 50, band=False)
        if t >= P2:
            caption(oc, "OBSESSION TRAINED FOR THIS.", 815, smoothstep(P2, P2 + 0.3, t), RED, 54, band=False)
        if t >= P3:
            caption(oc, "...BUT EGO HAS 1.2M FOLLOWERS.", 925, 0.85 * smoothstep(P3, P3 + 0.3, t), WHITE, 40, band=False)
        flash = math.exp(-(t - LOCK) * 3) if t >= LOCK else 0.0
        white = 0.4 * max(0.0, 1 - (t - COMP) / 0.2) if COMP <= t < COMP + 0.2 else 0.0
        v.compose(fi, t, flash=flash * 0.8, white=white, fade_in=0.0)
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=LOCK), gain=0.4, fade_in=0.3, fade_out=2.0, stop=DUR)
    last = {}
    for t, kind, _, extra in events:
        if kind == "go":
            m.add(0.0, sfx.beep(1500, 0.15), 0.5, 0.6, 0.2)
            m.add(0.02, sfx.text_hit(5), 0.6, 0, 0.4)
        elif kind == "rec_on":
            m.add(t, sfx.beep(1500, 0.12), 0.5, 0.6, 0.2)
            m.add(t + 0.05, sfx.whoosh(0.25, 800, 8000, 0.5, seed=int(t * 10)), 0.4, -0.3, 0.2)
        elif kind == "rec_off":
            m.add(t, sfx.tick(600, 0.6), 0.6, 0.6, 0.1)
            m.add(t + 0.05, sfx.power_down(0.5), 0.35, -0.3, 0.2)
            if t < 6:
                m.add(t + 0.35, sfx.body_fall() * 0.4, 0.4, -0.5, 0.3)
        elif kind in ("rep_O", "rep_E"):
            if t - last.get(kind, -1) < 0.15:
                continue
            last[kind] = t
            m.add(t, sfx.plate_clank(int(t * 37), 0.4) * 0.6, 0.25, 0.3 if kind == "rep_O" else -0.3, 0.2)
        elif kind == "comp":
            m.add(t, sfx.text_hit(2), 0.8, 0, 0.4)
            m.add(t, sfx.spot_on(), 0.7, 0, 0.4)
            m.add(t + 0.1, sfx.applause(1.6, 40, 3), 0.4, 0, 0.3)
        elif kind == "grip":
            m.add(t, sfx.breath(3, 0.8), 0.6, 0, 0.2)
            m.add(t + 0.4, sfx.heartbeat(), 0.8, 0, 0.3)
            m.add(t + 0.4, sfx.rattle(1.2, 5), 0.5, -0.3, 0.2)
            m.add(t, sfx.riser(LOCK - t), 0.5, 0, 0.3)
        elif kind == "lock":
            m.add(t, sfx.boom(4.0), 1.0, 0, 0.5)
            m.add(t, sfx.plate_clank(9, 1.6), 0.6, 0.3, 0.4)
            m.add(t + 0.2, sfx.applause(3.0, 55, 6), 0.55, 0.3, 0.3)
        elif kind == "drop":
            m.add(t, sfx.plate_clank(77, 2.0), 0.9, -0.3, 0.4)
            m.add(t, sfx.boom(1.6), 0.5, -0.3, 0.4)
            m.add(t + 0.1, sfx.power_down(1.4), 0.4, -0.3, 0.4)
        elif kind in ("p1", "p2", "p3"):
            m.add(t, sfx.text_hit({"p1": 1, "p2": 3, "p3": 2}[kind]), 0.95 if kind == "p2" else 0.6, 0, 0.4)
            if kind == "p2":
                m.add(t, sfx.boom(2.0), 0.4, 0, 0.4)
            if kind == "p3":
                m.add(t + 0.1, sfx.chime(990, 0.25), 0.4, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [0.1, 1.3, 3.2, 5.0, 6.5, 8.3, 9.6, 11.8, 12.9, 13.5, 14.2, 17.5]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
